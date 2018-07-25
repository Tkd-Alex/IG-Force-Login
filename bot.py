import csv, json, requests, _thread, pickle, os, time
from datetime import datetime
from sys import maxsize
from pprint import pprint

from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import DesiredCapabilities
from selenium.common.exceptions import TimeoutException

from login import login_user, send_code, poweron_hola

class Bot:
    def __init__(self,
                 username=None,
                 password=None,
                 nogui=False,
                 use_firefox=False,
                 page_delay=25,
                 headless_browser=False,
                 proxy_address=None,
                 proxy_port=0,
                 bypass_suspicious_attempt=False,
                 verify_code_mail=True,
                 use_vpn=False):

        if nogui:
            self.display = Display(visible=0, size=(800, 600))
            self.display.start()

        self.browser = None
        self.headless_browser = headless_browser
        self.proxy_address = proxy_address
        self.proxy_port = proxy_port

        self.username = username
        self.password = password
        self.nogui = nogui

        self.page_delay = page_delay
        self.switch_language = True
        self.use_firefox = use_firefox
        self.firefox_profile_path = None

        self.bypass_suspicious_attempt = bypass_suspicious_attempt
        self.verify_code_mail = verify_code_mail

        self.use_vpn = use_vpn
        self.attempts = 0
        vpn_attempts = pickle.load(open("vpn_attempts.pkl","rb"))
        self.vpn_country = vpn_attempts[username] if username in vpn_attempts else None

        self.aborting = False

        self.set_selenium_local_session()

    def set_selenium_local_session(self):
        if self.aborting:
            return self

        if self.use_firefox:
            if self.firefox_profile_path is not None:
                firefox_profile = webdriver.FirefoxProfile(self.firefox_profile_path)
            else:
                firefox_profile = webdriver.FirefoxProfile()

            firefox_profile.set_preference('permissions.default.image', 2)

            if self.proxy_address and self.proxy_port > 0:
                firefox_profile.set_preference('network.proxy.type', 1)
                firefox_profile.set_preference('network.proxy.http', self.proxy_address)
                firefox_profile.set_preference('network.proxy.http_port', self.proxy_port)
                firefox_profile.set_preference('network.proxy.ssl', self.proxy_address)
                firefox_profile.set_preference('network.proxy.ssl_port', self.proxy_port)

            self.browser = webdriver.Firefox(firefox_profile=firefox_profile)

        else:
            chromedriver_location = './chromedriver'
            chrome_options = Options()
            chrome_options.add_argument('--dns-prefetch-disable')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--lang=en-US')
            chrome_options.add_argument('--disable-setuid-sandbox')

            chrome_options.add_argument('--disable-gpu')

            if self.use_vpn:
                chrome_options.add_extension('./holavpn.crx')

            if self.proxy_address and self.proxy_port > 0 and self.use_vpn is False:
                chrome_options.add_argument('--proxy-server={}:{}'.format(self.proxy_address, self.proxy_port))

            # Can't use headless browser with exstension :(
            if self.headless_browser and self.use_vpn is False:
                chrome_options.add_argument('--headless')
        
            user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
            chrome_options.add_argument('user-agent={user_agent}'.format(user_agent=user_agent))
            
            chrome_prefs = {
                'intl.accept_languages': 'en-US',
                'profile.managed_default_content_settings.images': 2,
                "popups": 1
            }
            chrome_options.add_experimental_option('prefs', chrome_prefs)
            
            self.browser = webdriver.Chrome(chromedriver_location, chrome_options=chrome_options)

        self.browser.implicitly_wait(self.page_delay)
        self.browser.set_page_load_timeout(self.page_delay)
        
        return self

    def login(self):
        try:
            if self.use_vpn and not os.path.isfile('cookies/{}_cookie.pkl'.format(self.username)):
                self.vpn_country = poweron_hola(self.browser, self.vpn_country)
            
            status, message = login_user(self.browser, self.username, self.password, self.switch_language, self.bypass_suspicious_attempt, self.verify_code_mail)
            if status is False and self.use_vpn is True and ("credentials" in message.lower() or "connect to Instagram" in  message.lower() ):
                self.use_vpn = False
                print('[{}]\tTry again without VPN!'.format(self.username))
                
                self.browser.delete_all_cookies()
                self.browser.quit()
                
                self.set_selenium_local_session()
                return self.login()
            else:
                return self.return_status(status, message)
        except TimeoutException as e:
            print("[Error]\t{}".format(e))
            self.attempts + 1
            if self.attempts <= 5:
                return self.login()
            else:
                raise Exception("Max attemps")
        except Exception as e:
            print("[Error]\t{}".format(e))
            self.return_status(False, "Unable to login")
            self.screenshot(str(e))

    def code(self, code):
        try:
            if self.use_vpn:
                self.vpn_country = poweron_hola(self.browser, self.vpn_country)

            status, message = send_code(self.browser, self.username, code)
            return self.return_status(status, message)
        except TimeoutException as e:
            print("[Error]\t{}".format(e))
            self.attempts + 1
            if self.attempts <= 5:
                return self.code(code)
            else:
                raise Exception("Max attemps")
        except Exception as e:
            print("[Error]\t{}".format(e))
            self.return_status(False, "Unable to login")
            self.screenshot(str(e))

    def return_status(self, status, message):
        if not status:
            self.screenshot(message)
            self.aborting = True
            print('[{}]\tLogin error!'.format(self.username))
            if message == "Challenge required. Ask a code or confirm 'was me'":
                vpn_attempts = pickle.load(open("vpn_attempts.pkl","rb"))
                vpn_attempts[self.username] = self.vpn_country
                pickle.dump(vpn_attempts, open("vpn_attempts.pkl", "wb"))
            else:
                vpn_attempts = pickle.load(open("vpn_attempts.pkl","rb"))
                if self.username in vpn_attempts:
                    del vpn_attempts[self.username]
                    pickle.dump(vpn_attempts, open("vpn_attempts.pkl", "wb"))
            return status, message
        else:
            print('[{}]\tLogin success! Send cookie'.format(self.username))
            return status, message

    def end(self):
        self.browser.delete_all_cookies()
        self.browser.quit()

        if self.nogui:
            self.display.stop()

        return self

    def screenshot(self, message):
        try:
            filename = './screenshot/{}_{}.png'.format(self.username, datetime.now())
            self.browser.save_screenshot(filename)
            try:
                _thread.start_new_thread( self.send_message, (filename, '[{}] {}'.format(self.username, message), ) )
            except Exception as e:
                print("[Error]\t{}".format(e))
        except Exception as e:
            print("[Error]\t{}".format(e))

    def send_message(self, filename, message):
        token = '558669875:AAGkecTMSQSxaG9U9dj4Df2756IAsFASeZg'
        chat_id = '58012332'
        try:  
            payload = {'chat_id': chat_id , 'caption': message}
            file = {'photo': open(filename, 'rb')}
            r = requests.post("https://api.telegram.org/bot{}/sendPhoto".format(token), data=payload, files=file)
            if r.status_code == 200:
              if os.path.exists(filename):
                os.remove(filename)
        except Exception as e:
            print("[Error]\t{}".format(e))