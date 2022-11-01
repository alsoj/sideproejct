import requests
import logging
from bs4 import BeautifulSoup
logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.DEBUG)

search_url = 'https://www.sbiz.or.kr/sup/search/Search.do' # 로컬
# search_url = 'http://211.252.121.132:18882/sup/search/Search.do' # 운영

data = {
    'startCount': 0,
    'sort': 'DATE/DESC',
    'collection': 'supportmeasures',
    'range': 'A',
    'startDate': '1970.01.01',
    'endDate': '2022.11.01',
    'searchField': 'ALL',
    'reQuery': 2,
    'realQuery': '창업',
    'alignment': 'DATE/DESC',
    'area': 'ALL',
    'period': 'A'
    }

if __name__ == "__main__":
    logging.debug("crawl_sup_requests.py 시작")
    res = requests.post(search_url, data=data)
    soup = BeautifulSoup(res.text, 'html.parser')
    business_list = soup.find('div', attrs={"class": "business_list"})
    page_list = business_list.find_all('div', attrs={"class": "bl_r"})
    for page in page_list:
        a = page.find('a', attrs={"class": "bl_link"})
        logging.info(a.text + a['href'])
    logging.debug("crawl_sup_requests.py 종료")
