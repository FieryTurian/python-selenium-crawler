"""Crawler
Onno de Gouw - s1025613
Laura Kolijn - s1025724
Stefan Popa - s1027672
Denise Verbakel - s1018597

The crawler was designed using Selenium and SeleniumWire, and Python requests for some error handling. It has multiple
functionalities:
- Multiple Modes: Headless/Headful, Mobile/Desktop, Single URL/Input File
- Error Checking: TLS Errors, Timeout Errors or Domain/Other Errors
- Cookie Accepting and Cookie Accepting Error Handling
- Getting Number of Cookies/Parsing Cookies
- Webpage Screenshots
- Computing Webpage Loading Times
- Request/Response Header Parsing
- Detecting Reditections
- Detecting Third-Party Domains
- Converting Data into JSON Files
"""
import argparse
import os
import time
import json
import requests as python_requests
import pandas as pd
from tld import get_fld
from datetime import datetime

from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from selenium.common.exceptions import ElementClickInterceptedException, ElementNotInteractableException, \
    NoSuchFrameException, TimeoutException, StaleElementReferenceException, WebDriverException
from requests.exceptions import SSLError, Timeout, ConnectionError, TooManyRedirects
from tld.exceptions import TldDomainNotFound, TldBadUrl

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
        parser.error("Invalid input: please provide either the -u or -i argument!")

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
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

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
        try:
            driver.save_screenshot(f"../crawl_data/{domain}_mobile_{state}_consent.png")
        except TimeoutException:
            print("Could not take a screenshot due to a timeout error!")
    else:
        try:
            driver.save_screenshot(f"../crawl_data/{domain}_desktop_{state}_consent.png")
        except TimeoutException:
            print("Could not take a screenshot due to a timeout error!")

    print(f"{state} consent screenshot has been taken successfully!")


def check_errors(url):
    """Check if the webpage at given URL gives any errors

    Parameters
    ----------
    url: str
        The URL being accessed by the webdriver

    Returns
    ----------
    str
        A string specifying the error that has occured, or None otherwise
    """
    if not url.startswith("http"):
        url = "https://" + url

    try:
        python_requests.get(url, timeout=20)
    except SSLError:
        print("The website gave a TLS error!")
        return "TLS"
    except Timeout:
        print("The website gave a timeout error!")
        return "Timeout"
    except ConnectionError:
        print("The website has an invalid domain!")
        return "Other"
    except TooManyRedirects:
        pass

    return None


def get_url_requests_times(driver, url):
    """Retrieve the requests of the webpage found at URL and computing the start and end times of the page load as
    well as retrieving the URL after redirections

    Parameters
    ----------
    driver: seleniumwire.webdriver
        The webdriver that is used to visit the domain
    url: str
        The URL being accessed by the webdriver

    Returns
    ----------
    post_pageload_url: str
        The URL of the webpage after all potential redirections
    requests_url: list
        The requests for the URL being accessed
    pageload_start_ts: datetime
        The start time of the page loading process
    pageload_end_ts: datetime
        The end time of the page loading process
    """
    if not url.startswith("http"):
        url = "https://" + url

    pageload_start_ts = datetime.now().strftime("%d/%m/%Y %H:%M:%S.%f")
    try:
        driver.get(url)
    except TimeoutException:
        print("Could not properly load the website!")
        return None, None, pageload_start_ts, 0
    except WebDriverException:
        print("Webpage crashed!")
        return None, None, pageload_start_ts, 0
    pageload_end_ts = datetime.now().strftime("%d/%m/%Y %H:%M:%S.%f")

    post_pageload_url = driver.current_url
    requests_url = driver.requests

    return post_pageload_url, requests_url, pageload_start_ts, pageload_end_ts


def get_headers(request):
    """Retrieve the headers of a HTTP request and its response

    Parameters
    ----------
    request: seleniumwire.webdriver.requests
        A specific HTTP request

    Returns
    -------
    request_headers: dict
        A dictionary containing all the headers of the HTTP request
    response_headers: dict
        A dictionary containing all the headers of the response for the HTTP request
    """
    request_headers = request.headers
    response_headers = None

    for key in request_headers.keys():
        if len(request_headers[key]) > 512:
            request_headers[key] = request_headers[key][:512]

    # Check whether the request had any response
    if request.response:
        response_headers = request.response.headers
        for key in response_headers.keys():
            if len(response_headers[key]) > 512:
                response_headers[key] = response_headers[key][:512]

    return request_headers, response_headers


def get_third_party_domains(domain, requests):
    """Retrieve a list of all third party domains used by the requests for the given domain

    Parameters
    ----------
    domain: str
        The domain that is visited
    requests: list
        The requests for the domain

    Returns
    ----------
    list
        A list containing all third party domains used by requests
    """
    first_party_domains = [domain]
    third_party_domains = set()

    for request in requests:
        try:
            request_domain = get_fld(request.url)
            if request_domain not in first_party_domains:
                third_party_domains.add(request_domain)
        except TldDomainNotFound:
            print("Could not find TLD!")

    return list(third_party_domains)


def detect_redirections(domain, requests, post_pageload_url):
    """Detect redirections for a certain domain, in both the address bar and the requests

    Parameters
    ----------
    domain: str
        The domain that is visited
    requests: list
        The requests for the domain
    post_pageload_url: str
        The URL of the webpage at domain after all potential redirections

    Returns
    ----------
    list
        A dictionary containing all redirection pairs
    """
    redirections = []

    # Detect address bar redirections
    if domain != get_fld(post_pageload_url):
        redirections.append((domain, get_fld(post_pageload_url)))

    # Detect redirections in the requests
    for request in requests:
        request_url = request.url

        if request.response:
            response_headers = request.response.headers

            if "location" in response_headers:
                try:
                    location = response_headers['location']
                    if get_fld(location) != get_fld(request_url):
                        redirections.append((get_fld(request_url), get_fld(location)))
                except TldBadUrl:
                    print("An invalid URL format was found!")
                    pass

    return redirections


def search_element_using_xpath(driver, accept_word):
    """Search for the accept word using the XPATH

    Parameters
    ----------
    driver: seleniumwire.webdriver
        The webdriver that is used to visit the domain
    accept_word: str
        The accept cookies word to be searched

    Returns
    ----------
    list
        A list of all elements containing the accept word, None otherwise
    """
    # noinspection PyBroadException
    try:
        allow_all_cookies = driver.find_elements(
            # Long and complicated XPATH. Searches case-insensitive for an accept word in Button values or Text.
            By.XPATH, "//*[(normalize-space(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
                      "'abcdefghijklmnopqrstuvwxyz')) = \"" + accept_word + "\" or translate(@value, "
                      "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = \"" + accept_word + "\")"
                      "and not(self::span)]"
        )
        return allow_all_cookies
    except Exception:
        return None


def try_clicking_element(element):
    """Check whether a WebElement can be clicked

    Parameters
    ----------
    element: selenium.WebElement
        The element to be clicked

    Returns
    ----------
    bool
        A boolean value specifying whether the element was clicked or not
    status: str
        Specifying the status of clicking the element
    """
    if element and element.is_displayed():
        try:
            element.click()
            status = "clicked"
            return True, status
        except (ElementClickInterceptedException, ElementNotInteractableException):
            status = "errored"
            return False, status
    else:
        status = "not_found"
        return False, status


def search_and_click_iframes(driver, status, accept_word):
    """Look for a WebElement containing the accept word in different iframes

    Parameters
    ----------
    driver: seleniumwire.webdriver
        The webdriver that is used to visit the domain
    status: str
        Specifying the status of clicking the element
    accept_word: str
        The accept cookies word to be searched

    Returns
    ----------
    bool
        A boolean value specifying whether the element was clicked or not
    status: str
        Specifying the status of clicking an element in different iframes
    """
    try:
        list_of_iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for frame in list_of_iframes:
            try:
                driver.switch_to.frame(frame)
            except (NoSuchFrameException, StaleElementReferenceException, WebDriverException):
                pass

            allow_all_cookies = search_element_using_xpath(driver, accept_word)

            if allow_all_cookies:
                for element in allow_all_cookies:
                    bool_val, status = try_clicking_element(element)
                    if bool_val:
                        return True, status
                if status == "errored":
                    break
            else:
                status = "not_found"

            try:
                driver.switch_to.default_content()
            except TimeoutException:
                print("Timed out: could not switch to default content")
                pass
        return False, status

    except TimeoutException:
        print("Timed Out: could not find iframe elements!")
        return False, "errored"


def allow_cookies(driver):
    """Look for the button for accepting cookies and accepts the cookies, if possible, otherwise logs the error given

    Parameters
    ----------
    driver: seleniumwire.webdriver
        The webdriver that is used to visit the domain

    Returns
    ----------
    bool
        A boolean value specifying whether cookies were accepted or not
    status: str
        Specifying the status of accepting cookies
    """
    status = ""

    # We open and read the full datalist of the priv-accept project.
    with open("accept_words.txt", encoding="utf8") as acceptwords_file:
        accept_words = acceptwords_file.read().splitlines()

    for accept_word in accept_words:

        accepted_via_iframe, status = search_and_click_iframes(driver, status, accept_word)
        if accepted_via_iframe:
            return accepted_via_iframe, status
        else:
            allow_all_cookies = search_element_using_xpath(driver, accept_word)

            if allow_all_cookies:
                for element in allow_all_cookies:
                    bool_val, status = try_clicking_element(element)
                    if bool_val:
                        return True, status
                if status == "errored":
                    break
            else:
                status = "not_found"

    return False, status


def consent_error_logging(status, domain):
    """Log the errors for accepting the cookies of a certain domain webpage

    Parameters
    ----------
    status: str
        Specifying the status of accepting cookies
    domain: str
        The domain that is visited

    Returns
    ----------
    str
        A log message specifying the status of accepting the cookies
    """
    if status == "clicked":
        logging = f"The cookies for {domain} are accepted!"
    elif status == "not_found":
        logging = f"There was no cookie consent button found for {domain}!"
    else:
        logging = f"An error occurred while trying to click the cookie consent button for {domain}!"

    return logging


def get_nr_cookies(request):
    """Count the number of cookies being sent with a request

    Parameters
    ----------
    request: seleniumwire.webdriver.requests
        A specific HTTP request

    Returns
    ----------
    int
        The number of cookies sent by the request
    """
    nr_cookies = 0
    request_headers = request.headers

    if "cookie" in request_headers:
        cookies = request_headers['cookie'].split("; ")
        nr_cookies = len(cookies)

    return nr_cookies


def cookie_parser(cookie):
    """Parse a cookie string and create a dictionary with information regarding the cookie settings and value
    Taken from https://stackoverflow.com/questions/21522586/python-convert-set-cookies-response-to-dict-of-cookies

    Parameters
    ----------
    cookie: str
        A specific cookie string

    Returns
    ----------
    dict
        A dictionary containing various information given in the cookie string
    """
    cookie_dict = {}

    for item in cookie.split(';'):
        item = item.strip()

        if not item:
            continue
        if '=' not in item:
            cookie_dict[item] = True
            continue
        name, value = item.split('=', 1)
        cookie_dict[name] = value

    return cookie_dict


def get_response_cookies(response_headers, cookies):
    """Retrieve the cookies being set by a certain response

    Parameters
    ----------
    response_headers: dict
        The headers of a response for a HTTP request
    cookies: list
        A list containing all the cookies being set by responses
    """
    for key, cookie in response_headers.items():
        if key == "set-cookie":
            cookie = response_headers[key]
            cookie_dict = cookie_parser(cookie)
            if cookie_dict.values():
                cookie_dict.update({"size": len(list(cookie_dict.values())[0])})
                cookies.append(cookie_dict)


def get_all_cookies(requests):
    """Retrieve all the cookies being set by the responses of all HTTP requests for a specific domain

    Parameters
    ----------
    requests: list
        The requests for a specific domain

    Returns
    ----------
    dict
        A dictionary containing all the unique cookies set by responses
    """
    cookies = []

    for request in requests:
        if request.response:
            get_response_cookies(request.response.headers, cookies)

    # Remove the duplicates
    return [dict(t) for t in {tuple(dictionary.items()) for dictionary in cookies}]


def build_requests_list(requests_url):
    """Build the list of requests with the information that needs to be stored in the JSON file

    Parameters
    ----------
    requests_url: list
        A list with the requests for the URL being accessed

    Returns
    -------
    list
        A list with the requests parsed in the format that is needed for the JSON file
    """
    requests_list = []
    for request in requests_url:
        url = request.url
        timestamp = request.date
        request_headers, response_headers = get_headers(request)
        nr_cookies = get_nr_cookies(request)
        requests_list.append({"request_url": url,
                              "timestamp": timestamp.strftime("%d/%m/%Y %H:%M:%S.%f"),
                              "request_headers": dict(request_headers),
                              "response_headers": dict(response_headers) if response_headers else response_headers,
                              "nr_cookies": nr_cookies})
    return requests_list


def crawl_url(params, domain, rank):
    """Access a webpage, take screenshots, accept cookies and create a dictionary
    containing various information about the webpage visit

    Parameters
    ----------
    params: dict
        A dictionary with the values for all command line arguments
    domain: str
        The domain that is visited
    rank: int
        The tranco rank of the domain that is being visited

    Returns
    ----------
    dict
        A dictionary containing various information retrieved from the URL being accessed by the webdriver
    """
    chrome_options = set_webdriver_options(params)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), chrome_options=chrome_options)

    error = check_errors(domain)

    url_dict = {"website_domain": domain,
                "tranco_rank": rank,
                "crawl_mode": "Mobile" if params["mobile"] else "Desktop"}

    if error is None:
        post_pageload_url, requests_url, pageload_start_ts, pageload_end_ts = get_url_requests_times(driver, domain)
        if post_pageload_url:
            time.sleep(10)
            take_screenshots_consent(params, driver, domain, "pre")

            # Skip latimes.com on mobile due to weird iframe location
            if domain == "latimes.com" and params["mobile"]:
                status = "errored"
                print(consent_error_logging(status, domain))
            else:
                cookies_accepted, status = allow_cookies(driver)
                print(consent_error_logging(status, domain))

                if cookies_accepted:
                    time.sleep(10)
                    take_screenshots_consent(params, driver, domain, "post")

            driver.quit()

            # Now it is time to process the gathered data:
            requests_list = build_requests_list(requests_url)
            url_dict.update({"pageload_start_ts": pageload_start_ts,
                             "pageload_end_ts": pageload_end_ts,
                             "post_pageload_url": post_pageload_url,
                             "consent_status": status,
                             "cookies": get_all_cookies(requests_url),
                             "third_party_domains": get_third_party_domains(domain, requests_url),
                             "redirect_pairs": detect_redirections(domain, requests_url, post_pageload_url),
                             "requests_list": requests_list})
        else:
            url_dict.update({"error": "Timeout"})
    else:
        url_dict.update({"error": error})

    return url_dict


def crawl_list(params, domain_list):
    """Crawl all the domains in the list and create a JSON file per domain

    Parameters
    ----------
    params: dict
        A dictionary with the values for all command line arguments
    domain_list: dict
        A dictionary of domains to be crawled
    """
    print("Please wait, we are trying to crawl your entire input list!")
    for tranco_rank in domain_list:
        url_dict = crawl_url(params, domain_list[tranco_rank], tranco_rank)
        convert_to_json(params, domain_list[tranco_rank], url_dict)


def convert_to_json(params, domain, url_dict):
    """Create a JSON for a specific domain using the dictionary created by the crawl

    Parameters
    ----------
    params: dict
        A dictionary with the values for all command line arguments
    domain: str
        The domain that is visited
    url_dict: dict
         A dictionary containing various information retrieved from the URL being accessed by the webdriver
    """
    if params["mobile"]:
        out_file = open(f"../crawl_data/{domain}_mobile.json", "w")
    else:
        out_file = open(f"../crawl_data/{domain}_desktop.json", "w")
    json.dump(url_dict, out_file, indent=6)
    out_file.close()


def main():
    """ Parse arguments and decide whether we crawl a list of domains or a single domain
    """
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
