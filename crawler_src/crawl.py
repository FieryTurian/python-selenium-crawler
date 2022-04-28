"""Crawler

A placeholder for a very nice description of our crawler :)
"""
import argparse
import time

import pandas as pd

from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


WINDOW_SIZE = "1920x1080"


def parse_arguments():
    """Parse the command line ArgumentParser

    Returns
    -------
    dict
        A dictionary with the values for all command line arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mobile", action="store_true", required=False,
                        help="Enable mobile crawl mode.")
    parser.add_argument("-u", "--url", action="store", type=str, required=False,
                        help="A single URL or domain to crawl.")
    parser.add_argument("-i", "--input", action="store", type=str, required=False,
                        help="A path to a CSV file containing domains to crawl and their Tranco ranks.")
    parser.add_argument("-v", "--view", action="store", type=str, required=True,
                        choices=["headless", "headful"],
                        help="Choose between headless and headful modes of the crawler.")
    arguments = parser.parse_args()

    if (not arguments.url and not arguments.input) or (arguments.url and arguments.input):
        parser.error("Invalid input: please provide either the -u or -i argument.")

    return vars(arguments)


def read_tranco_top_500(file_path):
    """Read a csv file containing domains to crawl and their Tranco ranks

    Parameters
    ----------
    file_path: str
        The path to the csv file

    Returns
    -------
    dict
        A dictionary with the Tranco ranks and the corresponding domain
    """
    tranco_df = pd.read_csv(file_path, header=0, index_col=0, squeeze=True)
    tranco_dict = tranco_df.to_dict()
    return tranco_dict


def set_webdriver_options(params):
    """Set the correct options for the Chrome webdriver

    Parameters
    ----------
    params: dict
        A dictionary with the values for all command line arguments

    Returns
    -------
    selenium.webdriver.chrome.options.Options
        ChromeOptions that are used to customize the ChromeDriver session
    """
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--start-maximized')
    # To remove the "Chrome is being controlled by automated test software" notification:
    chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])

    if params['view'] == "headless":
        chrome_options.add_argument('--headless')
        chrome_options.add_argument(f'--window-size={WINDOW_SIZE}')

    if params['mobile']:
        mobile_emulation = {"deviceName": "iPhone X"}
        chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)

    return chrome_options


def crawl_url(url, params):
    chrome_options = set_webdriver_options(params)
    # driver = webdriver.Chrome(executable_path="drivers/chromedriver.exe", chrome_options=chrome_options)
    driver = webdriver.Chrome(executable_path="../drivers/chromedriver.exe", chrome_options=chrome_options)

    website_domain = "https://" + url
    driver.get(website_domain)
    time.sleep(10)

    if params['mobile']:
        # driver.save_screenshot(f'crawl_data/{url}_mobile_pre_consent.png')
        driver.save_screenshot(f'../crawl_data/{url}_mobile_pre_consent.png')
    else:
        # driver.save_screenshot(f'crawl_data/{url}_desktop_pre_consent.png')
        driver.save_screenshot(f'../crawl_data/{url}_desktop_pre_consent.png')

    requests = driver.requests
    print(requests)
    print(type(requests))
    driver.quit()

    # # link for switching to English
    # en_link = driver.find_element(
    #     By.CSS_SELECTOR, "li.language:nth-child(2) > span:nth-child(2) > a:nth-child(1)")
    # en_link.click()
    #
    # # we now want to click the Allow all cookies button
    # # The following fails sine the allow all button takes a while to load
    # # driver.find_element(By.CLASS_NAME, "btn_alow_true")
    # # instead we wait until it becomes clickable
    # allow_all = WebDriverWait(driver, 10).until(
    #     EC.element_to_be_clickable((By.CLASS_NAME, "btn_allow_true")))
    #
    # if allow_all:
    #     allow_all.click()
    # driver.quit()
    # print("I am here :D")

    return requests


def crawl_list(domain_list, params):
    requests_list = []
    for domain in domain_list.values():
        requests = crawl_url(domain, params)
        requests_list.append(requests)

    print("Please give us a moment, we are trying to crawl your entire input list :D")
    return requests_list


if __name__ == '__main__':
    args = parse_arguments()
    if args['input']:
        tranco_domains = read_tranco_top_500(args['input'])
        requests_list = crawl_list(tranco_domains, args)

    if args['url']:
        requests = crawl_url(args['url'], args)

    print("Hello world!")
