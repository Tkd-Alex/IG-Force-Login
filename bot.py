import csv, json, requests, _thread
from math import ceil
import os, time
from datetime import datetime
from sys import maxsize
from pprint import pprint

from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import DesiredCapabilities

from login import login_user, send_code, login_windscribe, poweron_hola

class Bot:
    def __init__(self,
                 username=None,
                 password=None,
                 nogui=False,
                 selenium_local_session=True,
                 use_firefox=False,
                 page_delay=25,
                 headless_browser=False,
                 proxy_address=None,
                 proxy_port=0,
                 bypass_suspicious_attempt=False,
                 verify_code_mail=True,
                 use_vpn=False,
                 name_vpn="Windscribe"):

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
        self.name_vpn = name_vpn

        self.aborting = False

        if not os.path.exists("cookies"):
            os.makedirs("cookies")

        if selenium_local_session:
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
                if self.name_vpn == "Hola":
                    chrome_options.add_extension('./holavpn.crx')
                else:
                    chrome_options.add_extension('./windscribe.crx')

            if self.proxy_address and self.proxy_port > 0 and self.use_vpn is False:
                chrome_options.add_argument('--proxy-server={}:{}'.format(self.proxy_address, self.proxy_port))

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
            if self.use_vpn:
                if self.name_vpn == "Hola":
                    poweron_hola(self.browser)
                else:
                    login_windscribe(self.browser)
            
            status, message = login_user(self.browser, self.username, self.password, self.switch_language, self.bypass_suspicious_attempt, self.verify_code_mail) 
            return self.return_status(status, message)

        except Exception as e:
            print("[Error]\t{}".format(e))
            self.screenshot(str(e))

    def code(self, code):
        try:
            if self.use_vpn:
                login_windscribe(self.browser)

            status, message = send_code(self.browser, self.username, code)
            return self.return_status(status, message)

        except Exception as e:
            print("[Error]\t{}".format(e))
            self.screenshot(str(e))

    def return_status(self, status, message):
        if not status:
            self.screenshot(message)
            self.aborting = True
            print('[{}]\tLogin error!'.format(self.username))
            return status, message
        else:
            print('[{}]\tLoggin success! Send cookie'.format(self.username))
            # The logger login is put inside ViralBot
            #try:
            #    with open('history_login.txt', 'a') as f:
            #        f.write("{}\t{}\t{}\n".format(datetime.now(), self.username, "VPN" if self.use_vpn else "{}:{}".format(self.proxy_address, self.proxy_port)))
            #except Exception as e:
            #    pass
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