"""
This script use selenium and phantomjs to make the spider automatically pass
the auth without entering the verifier

WARNING: If you are concern about account security, please do not use the official
upwork account, you can register sockpuppet and paste the username and password
in this python file

"""
import upwork
from selenium import webdriver
from pprint import pprint

#upwork username
USERNAME = ""
#upwork password
PASSWORD = ""

PUBLIC_KEY = ""
SECRET_KEY = ""

def create_browser():
    webdriver.DesiredCapabilities.PHANTOMJS[
       'phantomjs.page.customHeaders.User-Agent'
    ] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36"
    browser = webdriver.PhantomJS()
    browser.set_window_size(1920, 1200)
    browser.set_page_load_timeout(180)
    return browser

def get_verifier(url, browser):
    browser.get(url)
    print 'try to login in {browser.current_url}'.format(browser=browser)
    #try to login
    browser.find_element_by_xpath(
        "//input[@id='login_username']").send_keys(USERNAME)
    browser.find_element_by_xpath(
        "//input[@id='login_password']").send_keys(PASSWORD)
    browser.find_element_by_xpath("//div[@class='checkbox']//label").click()
    browser.find_element_by_xpath(
        "//button[@type='submit']").click()
    print 'use password to login in'
    output = auth_get_token(browser)
    return output

def auth_get_token(browser):
    """
    authorize access and get the token then return back
    """
    msg = browser.find_element_by_xpath(
        "//div[@class='oNote']"
    ).text
    if not msg:
        browser.find_element_by_xpath(
            "//button[@type='submit']").click()

    msg = browser.find_element_by_xpath(
        "//div[@class='oNote']"
    ).text
    output = msg[msg.rindex("=")+1:]
    return output

def get_client():
    """Emulation of desktop app.
    Your keys should be created with project type "Desktop".
    Returns: ``upwork.Client`` instance ready to work.
    """
    print "Emulating desktop app"
    public_key = PUBLIC_KEY
    secret_key = SECRET_KEY

    client = upwork.Client(public_key, secret_key)
    url = client.auth.get_authorize_url()

    if USERNAME and PASSWORD:
        try:
            browser = create_browser()
            verifier = get_verifier(url, browser)
        except Exception, e:
            raise e
        finally:
            browser.quit()
    else:
        verifier = raw_input(
            'Please enter the verification code you get '
            'following this link:\n{0}\n\n> '.format(url))

    print 'Retrieving keys.... '
    access_token, access_token_secret = client.auth.get_access_token(verifier)
    print 'OK'

    # For further use you can store ``access_toket`` and
    # ``access_token_secret`` somewhere
    client = upwork.Client(public_key, secret_key,
                          oauth_access_token=access_token,
                          oauth_access_token_secret=access_token_secret)
    return client

if __name__ == '__main__':
    if not PUBLIC_KEY or not SECRET_KEY:
        print "Please set the PUBLIC_KEY and SECRET_KEY in the python script"
    else:
        client = get_client()
        try:
            print "Get jobs"
            pprint(client.provider_v2.search_jobs({'q': 'python'}))
        except Exception, e:
            print "Exception at %s %s" % (client.last_method, client.last_url)
            raise e
