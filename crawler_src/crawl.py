"""Crawler

A placeholder for a very nice description of our crawler :)
"""
import argparse
import os
import time
import json

from selenium.common.exceptions import ElementClickInterceptedException, ElementNotInteractableException
from tld import get_fld
import pandas as pd
from datetime import datetime

from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

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

    print("Arguments have been parsed successfully!")
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
    tranco_df = pd.read_csv(file_path, header=0, index_col=0).squeeze("columns")
    tranco_dict = tranco_df.to_dict()

    print("The CSV file has been read successfully!")
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
    chrome_options.add_argument("--lang=en-gb")
    chrome_options.add_argument("--start-maximized")
    # To remove the "Chrome is being controlled by automated test software" notification:
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

    if params["view"] == "headless":
        chrome_options.add_argument("--headless")
        chrome_options.add_argument(f"--window-size={WINDOW_SIZE}")

    if params["mobile"]:
        mobile_emulation = {"deviceName": "iPhone X"}
        chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)

    print("The webdriver options have been set successfully!")
    return chrome_options


def take_screenshots_consent(params, driver, domain, state):
    """Take and save a screenshot of the viewport before or after accepting the cookies_accepted

    Parameters
    ----------
    params: dict
        A dictionary with the values for all command line arguments
    driver: seleniumwire.webdriver
        The webdriver that is used to visit the domain
    domain: str
        The domain that is visited
    state: str
        Indicates whether the screenshot is taken pre or post consent
    """
    if params["mobile"]:
        driver.save_screenshot(f"../crawl_data/{domain}_mobile_{state}_consent.png")
    else:
        driver.save_screenshot(f"../crawl_data/{domain}_desktop_{state}_consent.png")

    print(f"{state} consent screenshot has been taken successfully!")


def get_url_requests_times(driver, domain):
    url = "https://" + domain
    pageload_start_ts = datetime.now().strftime("%d/%m/%Y %H:%M:%S.%f")
    driver.get(url)
    pageload_end_ts = datetime.now().strftime("%d/%m/%Y %H:%M:%S.%f")
    post_pageload_url = driver.current_url
    requests_url = driver.requests

    return post_pageload_url, requests_url, pageload_start_ts, pageload_end_ts


def get_headers(request):
    request_headers = request.headers
    response_headers = None

    for key in request_headers.keys():
        if len(request_headers[key]) > 512:
            request_headers[key] = request_headers[key][:512]

    if request.response:
        response_headers = request.response.headers
        for key in response_headers.keys():
            if len(response_headers[key]) > 512:
                response_headers[key] = response_headers[key][:512]

    return request_headers, response_headers


def get_third_party_domains(domain, requests):
    first_party_domains = [domain]
    third_party_domains = set()

    for request in requests:
        request_domain = get_fld(request.url)
        if request_domain not in first_party_domains:
            third_party_domains.add(request_domain)

    return list(third_party_domains)


def allow_cookies(driver):
    status = ""

    # We open and read the full datalist of the priv-accept project.
    with open("accept_words.txt", encoding="utf8") as acceptwords_file:
        accept_words = acceptwords_file.read().splitlines()

    # Initialise the allow_all_cookies variable to None. If we are able to find an element using one of the words in
    # the list, it becomes something and the code breaks out of the loop. It then clicks on this found element.
    allow_all_cookies = None
    for accept_word in accept_words:
        print("Checking: " + accept_word)  # TODO: Remove this print. It's just here now for testing purposes.
        # noinspection PyBroadException
        try:
            allow_all_cookies = driver.find_element(
                    # Long and complicated XPATH. Searches case-insensitive for an accept word in Button values or Text.
                    By.XPATH, "//*[normalize-space(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
                               "'abcdefghijklmnopqrstuvwxyz')) = \"" + accept_word + "\" or translate(@value, "
                               "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = \"" + accept_word + "\"]"
            )
        except Exception:
            pass

        if allow_all_cookies:
            try:
                allow_all_cookies.click()
                status = "clicked"
                return True, status
            except (ElementClickInterceptedException, ElementNotInteractableException):
                status = "errored"
                break
        else:
            status = "not_found"

    return False, status


def consent_error_logging(status, domain):
    if status == "clicked":
        logging = f"The cookies for {domain} are accepted!"
    elif status == "not_found":
        logging = f"There was no cookie consent button found for {domain}!"
    else:
        logging = f"An error occurred while trying to click the cookie consent button for {domain}!"

    return logging


def get_nr_cookies(request):
    nr_cookies = 0
    request_headers = request.headers

    for key in request_headers.keys():
        if key == "cookie":
            cookies = request_headers[key].split("; ")
            nr_cookies = len(cookies)

    return nr_cookies


def crawl_url(params, domain, rank):
    chrome_options = set_webdriver_options(params)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), chrome_options=chrome_options)

    post_pageload_url, requests_url, pageload_start_ts, pageload_end_ts = get_url_requests_times(driver, domain)
    time.sleep(3)  # ToDo: Change back to 10 seconds
    # take_screenshots_consent(params, driver, domain, "pre")
    cookies_accepted, status = allow_cookies(driver)
    print(consent_error_logging(status, domain))

    if cookies_accepted:
        time.sleep(3)  # ToDo: Change to 10 seconds
        # take_screenshots_consent(params, driver, domain, "post")

    cookies = driver.get_cookies()

    driver.quit()

    # Now it is time to process the gathered data:
    url_dict = {"website_domain": domain,
                "tranco_rank": rank,
                "crawl_mode": "Mobile" if params["mobile"] else "Desktop",
                "pageload_start_ts": pageload_start_ts,
                "pageload_end_ts": pageload_end_ts,
                "post_pageload_url": post_pageload_url,
                "consent_status": status,
                "cookies": cookies,
                "third_party_domains": get_third_party_domains(domain, requests_url),
                "requests_list": []}

    for request in requests_url:
        url = request.url
        timestamp = request.date
        request_headers, response_headers = get_headers(request)
        nr_cookies = get_nr_cookies(request)
        url_dict["requests_list"].append({"request_url": url,
                                          "timestamp": timestamp.strftime("%d/%m/%Y %H:%M:%S.%f"),
                                          "request_headers": dict(request_headers),
                                          "response_headers": dict(response_headers) if response_headers else
                                          response_headers,
                                          "nr_cookies": nr_cookies})

    return url_dict


def crawl_list(params, domain_list):
    print("Please wait, we are trying to crawl your entire input list!")
    for tranco_rank in domain_list.keys():
        url_dict = crawl_url(params, domain_list[tranco_rank], tranco_rank)
        convert_to_json(params, domain_list[tranco_rank], url_dict)


def convert_to_json(params, domain, url_dict):
    if params["mobile"]:
        out_file = open(f"../crawl_data/{domain}_mobile.json", "w")
    else:
        out_file = open(f"../crawl_data/{domain}_desktop.json", "w")
    json.dump(url_dict, out_file, indent=6)
    out_file.close()


def main():
    args = parse_arguments()
    if args["input"]:
        tranco_domains = read_tranco_top_500(args["input"])
        crawl_list(args, tranco_domains)

    if args["url"]:
        tranco_rank = None
        tranco_domains = read_tranco_top_500("tranco-top-500-safe.csv")
        for rank in tranco_domains.keys():
            if tranco_domains[rank] == args["url"]:
                tranco_rank = rank
                break

        url_dict = crawl_url(args, args["url"], tranco_rank)
        convert_to_json(args, args["url"], url_dict)

    print("The crawl has completed successfully and your data was saved locally!")


if __name__ == '__main__':
    # Change the current working directory to the directory of the running file:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    main()
