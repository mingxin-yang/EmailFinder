import argparse
import requests
from emailfinder.utils.agent import user_agent
from random import randint
from emailfinder.utils.env import GOOGLE_CUSTOM_SEARCH_KEY, GOOGLE_CUSTOM_SEARCH_CX
from bs4 import BeautifulSoup
from bs4.element import Tag
from emailfinder.utils.color_print import print_info, print_ok, print_error
import random
from emailfinder.utils.exception import GoogleCaptcha, GoogleCookiePolicies
from concurrent.futures import ThreadPoolExecutor, as_completed
from parsel import Selector


def search_with_google_custom(target):
    url_base = f'https://www.googleapis.com/customsearch/v1?' \
               f'key={GOOGLE_CUSTOM_SEARCH_KEY}&cx={GOOGLE_CUSTOM_SEARCH_CX}&q=site:linkedin.com/in/' \
               f' AND "{target}"'
    url = url_base + f"&start={1}"
    try:
        response = requests.get(url,
                                headers=user_agent.get(randint(0, len(user_agent) - 1)),
                                )
        # initialize empty lists
        links_3 = []
        titles = []
        descriptions = []

        result = response.json()
        items = result['items']
        for item in items:
            links_3.append(item['link'])
            titles.append(item['title'])
            descriptions.append(item['snippet'])
    except Exception as e:
        print(e)
        raise e

    if len(links_3) > 0:
        print_ok("Google custom discovered {} linkedin links".format(len(links_3)))
    else:
        print_info("Google custom did not discover any linkedin links")

    return links_3


def get_links(text):
    links_1 = []
    titles = []
    descriptions = []
    soup = BeautifulSoup(text, 'lxml')
    result_div = soup.find_all('div', attrs={'class': 'g'})

    for r in result_div:
        # Checks if each element is present, else, raise exception
        try:
            link_1 = r.find('a', href=True)
            title = None
            title = r.find('h3')

            # returns True if a specified object is of a specified type; Tag in this instance
            if isinstance(title, Tag):
                title = title.get_text()

            description = None
            description = r.find('span', attrs={'class': 'st'})

            if isinstance(description, Tag):
                description = description.get_text()

            # Check to make sure everything is present before appending
            if link_1 != '' and title != '' and description != '':
                links_1.append(link_1['href'])
                titles.append(title)
                descriptions.append(description)


        # Next loop if one element is not present
        except Exception as e:
            print(e)
            continue

    return links_1


def search_with_google(target, proxies=None, total=10):
    links_2 = set()
    start = 0
    num = 50 if total > 50 else total
    iterations = int(total / num)
    if (total % num) != 0:
        iterations += 1
    url_base = f'https://www.google.com/search?q=site:linkedin.com/in/' \
               f' AND "{target}"&num={num}'
    cookies = {"CONSENT": "YES+srp.gws"}

    try:
        with open('ip.txt', 'r') as f:
            local_ips = f.read()
        ips = local_ips.split('\n')
        print_ok(f"Using {len(ips)} local IPs")
    except FileNotFoundError:
        ips = requests.get("http://api.proxy.ipidea.io/getProxyIp?num=100&return_type=txt&lb=1&sb=0&flow=1&regions"
                           "=&protocol=http").text.split("\r\n")
        print_info(f"Got {len(ips)} IPs from API")
        with open("ip.txt", "w") as f:
            f.write("\r\n".join(ips))

    ip_check_url = 'http://icanhazip.com/'
    ip_can_use = ''
    for i in range(len(ips)):
        random_ip = random.choice(ips)
        try:
            response = requests.get(ip_check_url, proxies={'http': "http://" + random_ip}, timeout=5)
            print_info(f"IP: {random_ip} - {response.text.strip()}")
            if response.status_code == 200:
                print_ok(f"当前代理IP：{random_ip}")
                ip_can_use = random_ip
                break
        except Exception as e:
            print_info(e)
            continue

    if not ip_can_use:
        ips = requests.get("http://api.proxy.ipidea.io/getProxyIp?num=100&return_type=txt&lb=1&sb=0&flow=1&regions"
                           "=&protocol=http").text.split("\r\n")
        ip_can_use = ips[0]
        with open("ip.txt", "w") as f:
            f.write("\r\n".join(ips))

    proxies = {'http': ip_can_use, 'https': ip_can_use}

    while start < iterations:
        try:
            url = url_base + f"&start={start}"
            response = requests.get(url,
                                    headers=user_agent.get(5),
                                    allow_redirects=False,
                                    cookies=cookies,
                                    verify=False,
                                    proxies=proxies
                                    )
            text = response.text
            if response.status_code == 302:
                raise GoogleCookiePolicies()
            if "detected unusual traffic" in text:
                raise GoogleCaptcha()
            links_2 = links_2.union(get_links(text))

            soup = BeautifulSoup(text, "html.parser")
            # h3 is the title of every result
            if len(soup.find_all("h3")) < num:
                break
        except Exception as ex:
            raise ex  # It's left over... but it stays there
        start += 1
    links_2 = list(links_2)
    if len(links_2) > 0:
        print_ok("Google discovered {} linkedin links".format(len(list(links_2))))
    else:
        print_info("Google did not discover any linkedin links")

    link_dict = {target: links_2[0]}
    return link_dict


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--nargs', nargs='+', help="Name to search", required=True)

    args = parser.parse_args()

    links = set()
    threads = 3

    with ThreadPoolExecutor(max_workers=threads) as executor:
        future_links = {executor.submit(search_with_google, name) for name in args.nargs}
        for future in as_completed(future_links):
            try:
                data = future.result()
                if data:
                    links = links.union(data)
            except Exception as exc:
                print_error(f"Error: {exc}")

    total_links = len(links)
    links_msg = f"\nTotal links: {total_links}"
    print(links_msg)
    print("-" * len(links_msg))
    if total_links > 0:
        for link in links:
            print(link)
    else:
        print("0 links :(. Closing...")
