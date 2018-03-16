from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException
from time import sleep
import pickle, json, os
from pprint import pprint

def bypass_suspicious_login(browser, verify_code_mail, username):
    '''
    try:
        close_button = browser.find_element_by_xpath("[text()='Close']")
        ActionChains(browser).move_to_element(close_button).click().perform()
        print("[{}]\tClick 'Close' button".format(username))
    except NoSuchElementException:
        pass
    '''

    try:
        this_was_me_button = browser.find_element_by_xpath("//button[@name='choice'][text()='This Was Me']")
        ActionChains(browser).move_to_element(this_was_me_button).click().perform()
        print("[{}]\tClick 'This Was Me'".format(username))
    except NoSuchElementException:
        pass

    try:
        back_button = browser.find_element_by_xpath("//a[@class='_rg5d7'][text()='Go Back']")
        sleep(0.10)
        ActionChains(browser).move_to_element(back_button).click().perform()
        print("[{}]\tClick 'Go Back' link".format(username))
    except NoSuchElementException:
        pass

    try:
        next_button = browser.find_element_by_xpath("//button[text()='Next']")
        ActionChains(browser).move_to_element(next_button).click().perform()
        print("[{}]\tClick 'Next'".format(username))
        print('[{}]\tA security code wast sent to your phone'.format(username))
        message = 'A security code wast sent to your phone'
        pickle.dump({'cookie': browser.get_cookies(), 'url': browser.current_url}, open('sessions/{}_session.pkl'.format(username), 'wb'))
        sleep(0.10)
        return False, message
    except NoSuchElementException:
        pass        

    try:
        if verify_code_mail:
            user_email = browser.find_element_by_xpath("//label[@for='choice_1']").text
        else: 
            radio_phone = browser.find_element_by_xpath("//label[@for='choice_0']")
            user_phone = radio_phone.text 
            try:
                (ActionChains(browser)
                 .move_to_element(radio_phone)
                 .click().perform())
            except:
                print("[{}]\tUnable to click phone button".format(username))
                return False, "Unable to click phone button"
    except:
        print("[{}]\tUnable to locate email or phone button, maybe bypass_suspicious_login=True isn't needed anymore.".format(username))
        return True, "Unable to locate email or phone button, maybe bypass_suspicious_login=True isn't needed anymore."

    send_security_code_button = browser.find_element_by_xpath(("//button[text()='Send Security Code']"))
    (ActionChains(browser)
     .move_to_element(send_security_code_button)
     .click()
     .perform())
    
    print("[{}]\tClick 'Send Security Code' button".format(username))

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

    security_code_field = browser.find_element_by_xpath(("//input[@id='security_code']"))
    (ActionChains(browser)
    .move_to_element(security_code_field)
    .click().send_keys(security_code).perform())
    print("[{}]\tWrite the security code: ".format(username, security_code))    
    
    submit_security_code_button = browser.find_element_by_xpath(("//button[text()='Submit']"))
    (ActionChains(browser)
    .move_to_element(submit_security_code_button)
    .click().perform())
    print("[{}]\tClick 'Submit' button".format(username))

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
    
    browser.get('https://www.instagram.com')
    cookie_loaded = False
    session_loaded = False

    try:
        browser.get('https://www.google.com')
        for cookie in pickle.load(open('cookies/{}_cookie.pkl'.format(username), 'rb')):
            browser.add_cookie(cookie)
            cookie_loaded = True
    except (WebDriverException, OSError, IOError):
        print("[{}]\tCookie file not found, creating cookie...".format(username))

    # Check if we have a session open for example for challenge required
    if not cookie_loaded:
        try:
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

    browser.get('https://www.instagram.com')
    login_elem = browser.find_elements_by_xpath("//*[contains(text(), 'Log in')]")
    
    if len(login_elem) == 0 and cookie_loaded is True:
        # Login success delete old session if exist
        print("[{}]\tLogin restored from cookie. Delete old session.".format(username))
        if os.path.exists('sessions/{}_session.pkl'.format(username)):
            os.remove('sessions/{}_session.pkl'.format(username))
        return True, browser.get_cookies()

    if cookie_loaded:
        print("[{}]\tIssue with cookie for user " + username + ". Creating new cookie...".format(username))

    if switch_language:
        try:
            browser.find_element_by_xpath("//select[@class='_fsoey']/option[text()='English']").click()
        except Exception as e:
            pass

    login_elem = browser.find_element_by_xpath("//article/div/div/p/a[text()='Log in']")
    if login_elem is not None:
        ActionChains(browser).move_to_element(login_elem).click().perform()
        print("[{}]\tClick 'Log in' button".format(username))

    input_username = browser.find_elements_by_xpath("//input[@name='username']")

    ActionChains(browser).move_to_element(input_username[0]).click().send_keys(username).perform()
    print("[{}]\tWrite username".format(username))
    sleep(1)
    input_password = browser.find_elements_by_xpath("//input[@name='password']")
    ActionChains(browser).move_to_element(input_password[0]).click().send_keys(password).perform()
    print("[{}]\tWrite password".format(username))
    
    login_button = browser.find_element_by_xpath("//form/span/button[text()='Log in']")
    ActionChains(browser).move_to_element(login_button).click().perform()
    print("[{}]\tClick 'Log in' button".format(username))

    try:
        error_message = browser.find_element_by_xpath("//p[@id='slfErrorAlert']").text
        if error_message != None and error_message != '':
            print("[{}]\tError message: {}".format(username, error_message))            
            if 'user' in error_message.lower() or 'password' in error_message.lower(): 
                print("[{}]\tCredentials are invalid".format(username))
                return False, error_message
    except:
        pass

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
    print("[{}]\tCheck for login success.".format(username))
    nav = browser.find_elements_by_xpath('//nav')
    print()
    if len(nav) == 2:
        pickle.dump(browser.get_cookies(), open('cookies/{}_cookie.pkl'.format(username), 'wb'))
        # Login success delete old session if exist
        if os.path.exists('sessions/{}_session.pkl'.format(username)):
            os.remove('sessions/{}_session.pkl'.format(username))
        return True, browser.get_cookies()
    else:
        return False, "Unable to login"
