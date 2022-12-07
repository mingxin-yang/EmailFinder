import requests
from random import randint
from bs4 import BeautifulSoup
from emailfinder.utils.exception import GoogleCaptcha, GoogleCookiePolicies
from emailfinder.utils.agent import user_agent
from emailfinder.utils.file.email_parser import get_emails
from emailfinder.utils.color_print import print_info, print_ok

def search(target, proxies=None, total=50):
    emails = set()
    start = 0
    num = 50 if total > 50 else total
    iterations = int(total / num)
    if (total % num) != 0:
        iterations += 1
    url_base = f"https://www.google.com/search?q=intext:@{target}&num={num}"
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
    for ip in ips:
        try:
            response = requests.get(ip_check_url, proxies={'http': "http://" + ip}, timeout=5)
            print_info(f"IP: {ip} - {response.text.strip()}")
            if response.text.strip() == ip.split(':')[0]:
                print_ok(f"当前代理IP：{ip}")
                ip_can_use = ip
                break
        except Exception as e:
            print(e)
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
                                    headers=user_agent.get(randint(0, len(user_agent) - 1)),
                                    allow_redirects=False,
                                    cookies=cookies,
                                    verify=False,
                                    proxies=proxies
                                    )
            text = response.text
            if response.status_code == 302:
                raise GoogleCookiePolicies()
                # print_info("use ScraperApi")
                # payload = {'api_key': '', 'url': url}
                # response = requests.get('http://api.scraperapi.com', params=payload, timeout=10000)
                # if response.status_code == 200:
                #     text = response.text
                # else:
                #     raise ValueError('scraperapi status code: {}'.format(response.status_code))
            if "detected unusual traffic" in text:
                raise GoogleCaptcha()
            emails = emails.union(get_emails(target, text))
            soup = BeautifulSoup(text, "html.parser")
            # h3 is the title of every result
            if len(soup.find_all("h3")) < num:
                break
        except Exception as ex:
            raise ex  # It's left over... but it stays there
        start += 1
    emails = list(emails)
    if len(emails) > 0:
        print_ok("Google discovered {} emails".format(len(list(emails))))
    else:
        print_info("Google did not discover any email IDs")
    return emails
