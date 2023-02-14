from emailfinder.utils.finder import google_custom_search
import argparse
import requests
from emailfinder.utils.agent import user_agent
from random import randint
from emailfinder.utils.env import GOOGLE_CUSTOM_SEARCH_KEY, GOOGLE_CUSTOM_SEARCH_CX
from bs4 import BeautifulSoup
from bs4.element import Tag
from emailfinder.utils.color_print import print_info, print_ok

def search(target):
    url_base = f'https://www.googleapis.com/customsearch/v1?' \
               f'key={GOOGLE_CUSTOM_SEARCH_KEY}&cx={GOOGLE_CUSTOM_SEARCH_CX}&q=site:linkedin.com/in/' \
               f' AND "{target}"'
    url = url_base + f"&start={1}"
    try:
        response = requests.get(url,
                                headers=user_agent.get(randint(0, len(user_agent) - 1)),
                                )
        text = response.text

        print(text)

        # soup = BeautifulSoup(text, 'html.parser')
        # result_div = soup.find_all('div', attrs={'class': 'g'})
        #
        # print(result_div)

        # initialize empty lists
        links = []
        titles = []
        descriptions = []

        result = response.json()
        items = result['items']
        for item in items:
            links.append(item['link'])
            titles.append(item['title'])
            descriptions.append(item['snippet'])

        # for r in result_div:
        #     # Checks if each element is present, else, raise exception
        #     try:
        #         link = r.find('a', href=True)
        #         title = None
        #         title = r.find('h3')
        #
        #         # returns True if a specified object is of a specified type; Tag in this instance
        #         if isinstance(title, Tag):
        #             title = title.get_text()
        #
        #         description = None
        #         description = r.find('span', attrs={'class': 'st'})
        #
        #         if isinstance(description, Tag):
        #             description = description.get_text()
        #
        #         # Check to make sure everything is present before appending
        #         if link != '' and title != '' and description != '':
        #             links.append(link['href'])
        #             titles.append(title)
        #             descriptions.append(description)
        #
        #
        #     # Next loop if one element is not present
        #     except Exception as e:
        #         print(e)
        #         continue

    except Exception as e:
        print(e)
        raise e

    if len(links) > 0:
        for link in links:
            print(link)
    else:
        print("No results found")

    return links


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--name', help="Name to search", required=True)

    args = parser.parse_args()

    try:
        search(args.name)
    except KeyboardInterrupt:
        print("[-] EmailFinder has been interrupted. ")
