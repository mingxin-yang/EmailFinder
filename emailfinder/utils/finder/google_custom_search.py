import requests
from random import randint
from emailfinder.utils.exception import GoogleCustomSearchException
from emailfinder.utils.agent import user_agent
from emailfinder.utils.file.email_parser import get_emails
from emailfinder.utils.color_print import print_info, print_ok


def search(target, proxies=None, total=50):
    emails = set()
    start = 0
    max_num = 5
    # https://developers.google.com/custom-search/v1/using_rest
    url_base = f"https://www.googleapis.com/customsearch/v1?" \
               f"key=AIzaSyAt7DzWYqriL0pW94IJFaOVkcQtp61KQf8&cx=046d87ee726f14a27&q={target}"
    while start < max_num:
        try:
            url = url_base + f"&start={start * 10 + 1}"
            response = requests.get(url,
                                    headers=user_agent.get(randint(0, len(user_agent) - 1)),
                                    proxies=proxies
                                    )

            text = response.text
            if response.status_code != 200:
                raise GoogleCustomSearchException(text)

            rp_json = response.json()
            emails = emails.union(get_emails(target, text))
            # print(rp_json['queries'].get('nextPage', '没了'))
            if rp_json['queries'].get('nextPage', '') == '':
                break
        except Exception as ex:
            raise ex  # It's left over... but it stays there
        start += 1
    emails = list(emails)
    if len(emails) > 0:
        print_ok("Google Custom Search discovered {} emails".format(len(list(emails))))
    else:
        print_info("Google Custom Search did not discover any email IDs")
    return emails
