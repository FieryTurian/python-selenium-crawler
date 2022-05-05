"""Crawler

A placeholder for a very nice description of our crawler :)
"""
import argparse
import time
import os

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
    chrome_options.add_argument('--lang=en-gb')
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


def allow_cookies(driver):
    # We open and read the full datalist of the priv-accept project.
    with open('accept_words.txt', encoding='utf8') as acceptwords_file:
        accept_words = acceptwords_file.read().splitlines()

    # For testing purposes
    # time.sleep(50)

    # For allowing the cookies on the RU webpage (www.ru.nl). This is still hard-coded. When trying 'Akkoord' as is
    # given by NU.nl, for some reason this XPATH does not work. The strange thing is that while testing this XPATH
    # with 'Akkoord', the devtools inspector DOES actually recognize the element. But then selenium gives an error...
    # I am still trying to resolve this problem.

    # Another comment I would like to make is that the file with accept words contains all kinds of languages BUT
    # Dutch. When I visit microsoft for example, I automatically get referred to the Dutch page, and I am unsure
    # whether I should first go to the english page and then make use of the list of words, or whether I am allowed
    # to add the Dutch words for accepting cookies to this list. (The assignments states does state I could add words
    # though...)

    # Initialise the allow_all_cookies variable to None. If we are able to find an element using one of the words in
    # the list, it becomes something and the code breaks out of the loop. It then clicks on this found element.
    allow_all_cookies = None
    # Currently, however, it does not yet use the words in the list due to the  comment/uncertainty I mentioned above.
    for accept_word in accept_words:
        allow_all_cookies = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[normalize-space()='Alle cookies toestaan' or @value='Alle cookies toestaan']"))
        )
        if allow_all_cookies:
            break

    if allow_all_cookies:
        allow_all_cookies.click()


def take_screenshots_pre_consent(params, driver, url):
    if params['mobile']:
        driver.save_screenshot(f'../crawl_data/{url}_mobile_pre_consent.png')
    else:
        driver.save_screenshot(f'../crawl_data/{url}_desktop_pre_consent.png')


def crawl_url(params, url):
    # Change the current working directory to the directory of the running file:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    chrome_options = set_webdriver_options(params)
    driver = webdriver.Chrome(executable_path="../drivers/chromedriver.exe", chrome_options=chrome_options)

    website_domain = "https://" + url
    driver.get(website_domain)

    # time.sleep(10)
    # take_screenshots_pre_consent(params, driver, url)
    # allow_cookies(driver)

    requests_url = driver.requests
    driver.quit()

    return requests_url


def crawl_list(params, domain_list):
    requests_url_list = []
    for domain in domain_list.values():
        requests_url = crawl_url(domain, params)
        requests_url_list.append(requests_url)

    print("Please wait, we are trying to crawl your entire input list")
    return requests_url_list


def main():
    args = parse_arguments()
    if args['input']:
        tranco_domains = read_tranco_top_500(args['input'])
        requests_list = crawl_list(tranco_domains, args)
        print(requests_list)

    if args['url']:
        requests = crawl_url(args, args['url'])
        print(requests)

    print("End of main()")


if __name__ == '__main__':
    main()
