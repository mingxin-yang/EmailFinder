import json
import re
import sys
from random import randint

import requests
from bs4 import BeautifulSoup
from loguru import logger

from RecaptchaResolver.solution import Solution

# driver = webdriver.Chrome()
# dr = webdriver.Chrome()
# webdriver = Chrome()
user_agent = {
    0: {
        'User-agent': 'Mozilla/5.0 (Linux; Android 10; SM-A205U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.86 Mobile Safari/537.36'},
    1: {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko'},
    2: {
        'User-agent': 'Opera/9.80 (Linux armv7l) Presto/2.12.407 Version/12.51 , D50u-D1-UHD/V1.5.16-UHD (Vizio, D50u-D1, Wireless)'},
    3: {
        'User-agent': 'BrightSign/7.1.95 (XT1143) Mozilla/5.0 (Unknown; Linux arm) AppleWebKit/537.36 (KHTML, like Gecko) QtWebEngine/5.6.0 Chrome/45.0.2454.101 Safari/537.36'},
    4: {
        'User-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.24 Safari/537.36'},
    5: {
        'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36'},
    6: {
        'User-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36'}
}


def get_emails(target, text):
    regex = r"[a-zA-Z0-9_\.+-]+@" + target
    # 匹配em、strong、span标签

    new_text = re.sub('<(em|strong|b).*?>', '', text)
    new_text = re.sub('</(em|strong|b)>', '', new_text)
    emails = re.findall(regex, new_text)
    return emails


CLIENT_KEY = 'a5d61ed9fcfae93f8d227322e8ed4eff83d05e0312351'


def search(target, proxies=None, total=200):
    emails = set()
    start = 0
    num = 50 if total > 50 else total
    iterations = int(total / num)
    if (total % num) != 0:
        iterations += 1
    url_base = f"https://www.google.com/search?q=intext:@{target}&num={num}"
    cookies = {"CONSENT": "YES+srp.gws"}
    while start < iterations:
        try:
            url = url_base + f"&start={start}"
            print(url)
            try:
                with open('cookies.json', 'r') as f:
                    cookies = json.load(f)
            except json.decoder.JSONDecodeError:
                print('cookies.json is empty')
                pass

            s = requests.Session()
            if isinstance(cookies, list):
                for cookie in cookies:
                    s.cookies.set(cookie['name'], cookie['value'])
            else:
                s.cookies = cookies
            response = s.get(url, headers=user_agent.get(randint(0, len(user_agent) - 1)), proxies=proxies, verify=False)
            logger.info(response.status_code)
            text = response.text

            if response.status_code == 302:
                print('302')
                url = response.headers['Location']
                text = Solution(url).resolve()
                # params = parse.parse_qs(parse.urlparse(url).query)
                # # response = requests.get(url, headers=user_agent.get(randint(0, len(user_agent) - 1)),
                # #                     allow_redirects=False,
                # #                     cookies=cookies,
                # #                     verify=False,
                # #                     proxies=proxies)
                #
                # dr.get(url)
                # soup = BeautifulSoup(dr.page_source, "html.parser")
                # # print(soup)
                # # captcha_text = response.text
                # # # print(soup)
                # # print("302界面", response.text)
                # # soup = BeautifulSoup(captcha_text, "html.parser")
                # site_key = soup.find('div', id='recaptcha').attrs['data-sitekey']
                # text = handle_captcha(url, site_key, params)
                # print(text)
            elif response.status_code == 429:
                print('429')
                url = response.url
                text = Solution(url).resolve()
            elif "detected unusual traffic" in text:
                raise "detected unusual traffic"
            emails = emails.union(get_emails(target, text))
            print(emails)
            soup = BeautifulSoup(text, "html.parser")
            # h3 is the title of every result
            if len(soup.find_all("h3")) < num:
                break
        except Exception as ex:
            raise ex  # It's left over... but it stays there
        start += 1
    emails = list(emails)
    if len(emails) > 0:
        print("Google discovered {} emails".format(len(list(emails))))
    else:
        print("Google did not discover any email IDs")
    return emails


def search_google_api(target, proxies=None):
    emails = set()
    start = 0
    max_num = 5
    # https://developers.google.com/custom-search/v1/using_rest
    url_base = f"https://www.googleapis.com/customsearch/v1?" \
               f"key=AIzaSyAt7DzWYqriL0pW94IJFaOVkcQtp61KQf8&cx=046d87ee726f14a27&q={target}"
    while start < max_num:
        try:
            url = url_base + f"&start={start*10+1}"
            response = requests.get(url,
                                    headers=user_agent.get(randint(0, len(user_agent) - 1)),
                                    proxies=proxies
                                    )
            text = response.text
            json = response.json()
            emails = emails.union(get_emails(target, text))
            # soup = BeautifulSoup(text, "html.parser")
            # # h3 is the title of every result
            # if len(soup.find_all("h3")) < num:
            #     break
            print(json['queries'].get('nextPage', '没了'))
            if json['queries'].get('nextPage', '') == '':
                break
        except Exception as ex:
            raise ex  # It's left over... but it stays there
        start += 1
    emails = list(emails)
    if len(emails) > 0:
        print("Google Custom Search discovered {} emails".format(len(list(emails))))
    else:
        print("Google Custom Search did not discover any email IDs")
    return emails


if __name__ == '__main__':
    # for i in range(0, 20):
    search(sys.argv[1])
        # time.sleep(10)
    # url = "https://www.google.com/recaptcha/api2/demo"
    # text = handle_captcha(url, "6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-")
    # print(text)
