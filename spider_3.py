"""
Keep seraching jobs and insert the job info into DB

WARNING: If you are concern about account security, please do not use the official
upwork account, you can register sockpuppet and paste the username and password
in this python file

"""
from threading import Thread, RLock
import threading
import datetime
from time import sleep
import logging
import logging.config
import logging.handlers
import argparse
import os
import sys
import json

import upwork
from selenium import webdriver
from pprint import pprint

#upwork username
USERNAME = ""
#upwork password
PASSWORD = ""

PUBLIC_KEY = ""
SECRET_KEY = ""

SLEEP_TIME = 60*60
KILL = False
LOGGER = None
KEY_LS = ["python", "java", "php", "javascript"]

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

def setup_log(level):
    LOGGING_CONF = {
        'version': 1,
        'disable_existing_loggers': True,

        'formatters': {
            'standard': {
                'format': "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
            },
        },

        'handlers': {
            "file_handler": {
                "class": "logging.handlers.RotatingFileHandler",
                'level': 'DEBUG',
                "formatter": "standard",
                "filename": "spider.log",
                "maxBytes": 20*1024*1024,
                "backupCount": 5,
                "encoding": "utf8"
            },
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'DEBUG',
                'formatter': 'standard',
                'stream': 'ext://sys.stdout',
            },
        },

        'loggers': {
            '': {
                'handlers': ['file_handler', 'console'],
                'level': level,
                'propagate': False,
            },
        }
    }
    logging.config.dictConfig(LOGGING_CONF)
    global LOGGER
    LOGGER = logging.getLogger("spider")


class Client(object):
    lock = RLock()

    def __init__(self):
        self.client = self.get_client()

    def get_client(self):
        """Emulation of desktop app.
        Your keys should be created with project type "Desktop".

        Returns: ``odesk.Client`` instance ready to work.
        """
        client = upwork.Client(PUBLIC_KEY, SECRET_KEY)

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

        LOGGER.debug('Retrieving keys.... ')
        access_token, access_token_secret = client.auth.get_access_token(verifier)
        LOGGER.debug('OK')

        client = upwork.Client(PUBLIC_KEY, SECRET_KEY,
                              oauth_access_token=access_token,
                              oauth_access_token_secret=access_token_secret)
        return client

    def search_jobs(self, *args, **kargs):
        LOGGER.debug("search_jobs enter lock")
        with self.lock:
            try:
                LOGGER.debug(threading.currentThread().name + "search_jobs get lock")
                sleep(2)
                result = self.client.provider_v2.search_jobs(*args, **kargs)
                LOGGER.debug(threading.currentThread().name + "search_jobs get result")
                return result
            except Exception as e:
                LOGGER.exception(e)

    def get_job_profile(self, *args, **kargs):
        LOGGER.debug("get_job_profile enter lock")
        with self.lock:
            try:
                LOGGER.debug(threading.currentThread().name + "get_job_profile get lock")
                sleep(2)
                result = self.client.job.get_job_profile(*args, **kargs)
                LOGGER.debug(threading.currentThread().name + "get_job_profile get result")
                return result
            except Exception as e:
                LOGGER.exception(e)


class Job_Finder(Thread):

    client = None

    def __init__(self, client, query_ls):
        self.client = client
        self.query_ls = query_ls
        super(Job_Finder, self).__init__()

    def run(self):
        query_ls = self.query_ls
        sleep_time = 0
        while True:
            try:
                sleep(1)
                #check if need to break
                if KILL:
                    return

                if sleep_time > 0:
                    sleep_time = sleep_time - 1
                else:
                    try:
                        self.query_jobs(query_ls)
                    except Exception as e:
                        LOGGER.error(e)
                        raise
                    sleep_time = int(SLEEP_TIME)

            except Exception as e:
                LOGGER.exception(e)
                sleep(10)

    def query_jobs(self, query_ls):
        for key in query_ls:
            if KILL:
                return
            LOGGER.debug(
                'start to search jobs for {key}'.format(key=key)
            )
            output = []
            jobs = self.client.search_jobs(
                data={
                    "q": key,
                    "page_size": "100",
                }
            )
            if jobs:
                output.extend(jobs)
            jobs = self.client.search_jobs(
                data={
                    "skills": key,
                    "page_size": "100",
                }
            )
            if jobs:
                output.extend(jobs)
            job_ls = output

            #make list unique
            job_ids = []
            unique_jobs = []
            for job in job_ls:
                if job["id"] not in job_ids:
                    job_ids.append(job["id"])
                    unique_jobs.append(job)

            LOGGER.info(
                'found ' + str(len(unique_jobs)) + " jobs in " + key
            )


def main():
    setup_log(logging.INFO)

    client = Client()

    job_finder = Job_Finder(client, KEY_LS)
    job_finder.start()

    try:
        while True:
            print "press ctrl + c to cancel ", raw_input(">")
    except KeyboardInterrupt:
        global KILL
        KILL = True
    except Exception as e:
        LOGGER.exception(e)
    finally:
        job_finder.join()


if __name__ == '__main__':
    main()


