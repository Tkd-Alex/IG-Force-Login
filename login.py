from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys
from time import sleep
import pickle, json, os, random, time
from pprint import pprint

def wasme(browser, username):
    try:
        this_was_me_button = browser.find_element_by_xpath("//button[@name='choice'][text()='This Was Me']")
        ActionChains(browser).move_to_element(this_was_me_button).click().perform()
        print("[{}]\tClick 'This Was Me'".format(username))
    except NoSuchElementException:
        pass

def bypass_suspicious_login(browser, verify_code_mail, username):
    # First of all check if was me windows is enable
    wasme(browser, username)

    # If the sessions is waiting for a security code we need to go back 
    try:
        back_button = browser.find_element_by_xpath("//a[@class='_rg5d7'][text()='Go Back']")
        sleep(0.10)
        ActionChains(browser).move_to_element(back_button).click().perform()
        print("[{}]\tClick 'Go Back' link".format(username))
    except NoSuchElementException:
        pass

    # Handle for windows with Next button (only mail or phone detected). The send message is wrong.
    try:
        message = "A security code wast sent to your"
        try:
            phone_number = browser.find_element_by_xpath("//input[@id='phone_number']").get_attribute('value')
            print("[{}]\tPhone number in input field: {}".format(username, phone_number))
            message += ' {}'.format(phone_number)
        except:
            pass

        next_button = browser.find_element_by_xpath("//button[text()='Next']")
        ActionChains(browser).move_to_element(next_button).click().perform()

        print("[{}]\tClick 'Next'".format(username))
        print('[{}]\t{}'.format(username, message))
        pickle.dump({'cookie': browser.get_cookies(), 'url': browser.current_url}, open('sessions/{}_session.pkl'.format(username), 'wb'))
        sleep(0.10)
        return False, message
    except NoSuchElementException:
        pass        

    # If verify_code_mail is True, get the text with mail address.
    # Else catch radio_button, and try to click. If the click fails maybe the radio is not present.     
    try:
        if verify_code_mail:
            user_email = browser.find_element_by_xpath("//label[@for='choice_1']").text
        else: 
            radio_phone = browser.find_element_by_xpath("//label[@for='choice_0']")
            user_phone = radio_phone.text 
            try:
                (ActionChains(browser).move_to_element(radio_phone).click().perform())
            except:
                pass
    except NoSuchElementException:
        print("[{}]\tUnable to locate email or phone button, maybe bypass_suspicious_login=True isn't needed anymore.".format(username))
        return True, "Unable to locate email or phone button, maybe bypass_suspicious_login=True isn't needed anymore."

    try:
        send_security_code_button = browser.find_element_by_xpath(("//button[text()='Send Security Code']"))
        (ActionChains(browser).move_to_element(send_security_code_button).click().perform())
        print("[{}]\tClick 'Send Security Code' button".format(username))
    except NoSuchElementException:
        print("[{}]\tUnable to find/click security code".format(username))
        return False, "Unable to find/click security code"

    print('[{}]\tInstagram detected an unusual login attempt'.format(username))
    if verify_code_mail:
        print('[{}]\tA security code wast sent to your {}'.format(username, user_email))
        message = 'A security code wast sent to your {}'.format(user_email)
    else: 
        print('[{}]\tA security code wast sent to your {}'.format(username, user_phone))
        message = 'A security code wast sent to your {}'.format(user_phone)
    
    pickle.dump({'cookie': browser.get_cookies(), 'url': browser.current_url}, open('sessions/{}_session.pkl'.format(username), 'wb'))
    sleep(0.10)
    return False, message
    
def send_code(browser, username, security_code):
    browser.get('https://www.instagram.com')

    try:
        browser.get('https://www.google.com')
        session = pickle.load(open('sessions/{}_session.pkl'.format(username), 'rb'))
        for cookie in session['cookie']:
            browser.add_cookie(cookie)
        
        browser.get(session['url'])
        print("[{}]\tRestore old session. Current url: {}".format(username, session['url']))
    except (WebDriverException, OSError, IOError):
        print("[{}]\tSession file not found.".format(username))

    try:
        security_code_field = browser.find_element_by_xpath(("//input[@id='security_code']"))
        (ActionChains(browser).move_to_element(security_code_field).click().send_keys(security_code).perform())
        print("[{}]\tWrite the security code: {}".format(username, security_code))
    except NoSuchElementException:
        return False, "Unable to find security_code input"    
    
    try:
        submit_security_code_button = browser.find_element_by_xpath(("//button[text()='Submit']"))
        (ActionChains(browser).move_to_element(submit_security_code_button).click().perform())
        print("[{}]\tClick 'Submit' button".format(username))
    except NoSuchElementException:
        return False, "Unable to submit verification code"    

    try:
        sleep(0.10)
        wrong_login = browser.find_element_by_xpath(("//p[text()='Please check the code we sent you and try again.']"))
        if wrong_login is not None:
            print('[{}]\tWrong security code! Please check the code Instagram sent you and try again.'.format(username))
            return False, 'Wrong security code! Please check the code Instagram sent you and try again.'
    except NoSuchElementException:
        pass

    return check_login(browser, username)

def login_user(browser,
               username,
               password,
               switch_language=True,
               bypass_suspicious_attempt=False,
               verify_code_mail=True):

    # Going to instagram for create fake cookie sessions.
    browser.get('https://www.instagram.com')
    cookie_loaded = False
    session_loaded = False

    # Try to loading cookie for restoring session.
    try:
        if os.path.isfile('cookies/{}_cookie.pkl'.format(username)):
            browser.get('https://www.google.com')
            for cookie in pickle.load(open('cookies/{}_cookie.pkl'.format(username), 'rb')):
                browser.add_cookie(cookie)
                cookie_loaded = True
    except (WebDriverException, OSError, IOError):
        print("[{}]\tCookie file not found, creating cookie...".format(username))

    # Check if we have a session open for example for challenge required
    if not cookie_loaded:
        try:
            if os.path.isfile('sessions/{}_session.pkl'.format(username).format(username)):
                browser.get('https://www.google.com')
                session = pickle.load(open('sessions/{}_session.pkl'.format(username), 'rb'))
                for cookie in session['cookie']:
                    browser.add_cookie(cookie)
                    session_loaded = True
        except (WebDriverException, OSError, IOError):
            print("[{}]\tSession file not found.".format(username))
    else:
        print("[{}]\tCookie successfully loaded.".format(username))

    if session_loaded is True:
        print("[{}]\tSession successfully loaded.".format(username))

    # If the sessions is not restored start with Log in
    browser.get('https://www.instagram.com')
    login_elem = browser.find_elements_by_xpath("//*[contains(text(), 'Log in')]")
    
    if len(login_elem) == 0 and cookie_loaded is True:
        # Login success delete old session if exist
        print("[{}]\tLogin restored from cookie. Delete old session.".format(username))
        if os.path.isfile('sessions/{}_session.pkl'.format(username)):
            os.remove('sessions/{}_session.pkl'.format(username))

        # The sessions is gone, relogin:
        if 'challenge' in browser.current_url:
            os.remove('cookies/{}_cookie.pkl'.format(username))
            browser.delete_all_cookies()
            browser.get('https://www.google.com')
            sleep(1)
            browser.get('https://www.instagram.com')
            print("[{}]\tThe session is compromised, re-login".format(username))
        else:        
            return True, browser.get_cookies()

    if switch_language:
        try:
            browser.find_element_by_xpath("//select[@class='_fsoey']/option[text()='English']").click()
        except Exception as e:
            pass

    login_elem = browser.find_element_by_xpath("//article/div/div/p/a[text()='Log in']")
    if login_elem is not None:
        ActionChains(browser).move_to_element(login_elem).click().perform()
        print("[{}]\tClick 'Log in' button".format(username))

    # Populate username and password
    input_username = browser.find_elements_by_xpath("//input[@name='username']")
    ActionChains(browser).move_to_element(input_username[0]).click().send_keys(username).perform()
    print("[{}]\tWrite username".format(username))
    sleep(1)

    input_password = browser.find_elements_by_xpath("//input[@name='password']")
    ActionChains(browser).move_to_element(input_password[0]).click().send_keys(password).perform()
    print("[{}]\tWrite password".format(username))

    '''
    try:
        show_password = browser.find_element_by_xpath("//a[@class='_97sa5'][text()='Show']")
        ActionChains(browser).move_to_element(show_password).click().perform()
        print("[{}]\tShow password link".format(username))
    except NoSuchElementException:
        pass
    '''

    login_button = browser.find_element_by_xpath("//form/span/button[text()='Log in']")
    ActionChains(browser).move_to_element(login_button).click().perform()
    print("[{}]\tClick 'Log in' button".format(username))

    # Check if there is a error. If error contains user or password maybe the credentials is wrong. Return with error message
    try:
        error_message = browser.find_element_by_xpath("//p[@id='slfErrorAlert']").text
        if error_message != None and error_message != '':
            print("[{}]\tError message: {}".format(username, error_message))            
            if 'user' in error_message.lower() or 'password' in error_message.lower(): 
                print("[{}]\tCredentials are invalid".format(username))
                return False, error_message
    except:
        pass

    # Start bypass_suspicious_attempt
    if bypass_suspicious_attempt is True:
        status, message = bypass_suspicious_login(browser, verify_code_mail, username)
        if not status: 
            return status, message
    try:
        if 'challenge' in browser.current_url and bypass_suspicious_attempt is False:
            # Challenge required save session and ask user what he want to do
            pickle.dump({'cookie': browser.get_cookies(), 'url': browser.current_url}, open('sessions/{}_session.pkl'.format(username), 'wb'))
            print("[{}]\tChallenge required. Ask a code or confirm 'was me'".format(username))
            return False, "Challenge required. Ask a code or confirm 'was me'"
    except:
        pass

    return check_login(browser, username)

def check_login(browser, username):
    print("[{}]\tCheck login...".format(username))
    nav = browser.find_elements_by_xpath('//nav')
    print()
    if len(nav) == 2:
        pickle.dump(browser.get_cookies(), open('cookies/{}_cookie.pkl'.format(username), 'wb'))
        # Login success delete old session if exist
        if os.path.isfile('sessions/{}_session.pkl'.format(username)):
            os.remove('sessions/{}_session.pkl'.format(username))

        # After login maybe was me checked
        wasme(browser, username)
        return True, browser.get_cookies()
    else:
        return False, "Unable to login"

def login_windscribe(browser):
    try:
        print("[VPN]\tWindscribe!")
        browser.get("chrome-extension://hnmpcagpplmpfojmgmnngilcnanddlhb/html/reactPopUp.html")
        print("[VPN]\tOpen extension page")
        
        sleep(3)
        username = browser.find_element_by_xpath(("//input[@type='text']"))
        ActionChains(browser).move_to_element(username).click().send_keys("tkdalex").perform()
        print("[VPN]\tWrite username")
        
        password = browser.find_element_by_xpath(("//input[@type='password']"))
        ActionChains(browser).move_to_element(password).click().send_keys("alessandro96").perform()
        print("[VPN]\tWrite password")

        password.send_keys(Keys.RETURN)
        print("[VPN]\tSubmit form")
        
        sleep(5)
        print("[VPN]\tSwitch tab")
        browser.switch_to.window(browser.window_handles[0])

        try:
            print("[VPN]\tGoing to location page")
            location = browser.find_element_by_xpath("//a[@class='locationChooser']")
            ActionChains(browser).move_to_element(location).click().perform()
            
            countrylist = browser.find_elements_by_xpath("//div[@class='allowed location_item']")
            random.seed(time.clock())
            country = random.choice(countrylist)
            print("[VPN]\tRandom country: {}".format(country.text))
            ActionChains(browser).move_to_element(country).click().perform()
        except:
            pass

        sleep(5)

    except Exception as e:
        # If windscribe fails try with hola
        print("[Error]\t{}".format(e))
        poweron_hola(browser)
    
def poweron_hola(browser):
    try:
        print("[VPN]\tHola!")
        countrylist = [
            'AF','AL','DZ','AX','AS','AD','AO','AP','AI','AQ','AG','AR','AM','AW','AU','AT','AZ','BS','BH','JE','BD','BB','BY','BE','BZ','BJ','BM','BT','BO','BQ','BA','WF',
            'BW','BV','BR','IO','BN','BG','BF','BI','KH','CM','CA','CV','KY','CF','TD','CL','CN','CX','CC','CO','KM','CG','CK','CR','HR','CU','CW','CY','CZ','CD','DK','EH',
            'DJ','DM','DO','TP','EC','EG','SV','GQ','ER','EU','EE','ET','FK','FO','FJ','FI','FR','FX','GF','PF','TF','GA','GM','GE','DE','GH','GI','GB','GR','GL','GD','WS',
            'GP','GU','GT','GG','GN','GW','GY','HT','HM','HN','HK','HU','IS','IN','ID','IR','IQ','IE','IM','IL','IT','JM','JP','JO','KZ','KE','KI','KW','KG','LA','LV','YE',
            'LB','LS','LR','LY','LI','LT','LU','MO','MK','MG','MW','MY','MV','ML','MT','MH','MQ','MR','MU','YT','MX','FM','MD','MC','MN','ME','MS','MA','MZ','MM','NA','YU',
            'NR','NP','NL','AN','NC','NZ','NI','NE','NG','NU','NF','KP','MP','NO','OM','PK','PW','PS','PA','PG','PY','PE','PH','PN','PL','PT','PR','QA','RE','RO','RU','ZM',
            'RW','BL','SH','KN','LC','MF','PM','VC','SM','SX','ST','SA','SN','RS','SC','SL','SG','SK','SI','SB','SO','ZA','GS','KR','SS','ES','LK','SD','SR','SJ','SZ','ZW',
            'SE','CH','SY','TW','TJ','TZ','TH','TL','TG','TK','TO','TT','TN','TR','TM','TC','TV','UG','UA','AE','UK','US','UM','UY','UZ','VU','VA','VE','VN','VG','VI'
        ]
        random.seed(time.clock())
        coutry = random.choice(countrylist)
        print("[VPN]\tCountry random: {}".format(coutry))
        print("[VPN]\tGoing to instagram.com")
        browser.get("http://hola.org/access/instagram.com/using/vpn-{}?go=2".format(coutry.lower()))
        sleep(6)
        # Create custom exstension.crx. Not need switchtab
        #browser.switch_to.window(browser.window_handles[0])
        #print("[VPN]\tSwitch tab")

    except Exception as e:
        # If hola fails try with windscribe
        print("[Error]\t{}".format(e))
        login_windscribe(browser)
