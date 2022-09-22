import sys
from PyQt6.QtWidgets import *
from PyQt6 import uic

import time
import requests
from bs4 import BeautifulSoup
import telegram

# 전역변수 - 검색어
moneys_keword = '%C0%CC%C1%F6%BF%EE+%B1%E2%C0%DA' # 이지운 기자
fnnews_keyword1 = '최두선 기자'
fnnews_keyword2 = '김민기 기자'
etoday_keyword = '설경진 기자'
asiae_keyword = '박형수 기자'

# 전역변수 - 검색 URL
moneys_search_url = f'https://moneys.mt.co.kr/search.html?kwd={moneys_keword}'
fnnews_search_url1 = f'https://www.fnnews.com/search?search_txt={fnnews_keyword1}&page=0'
fnnews_search_url2 = f'https://www.fnnews.com/search?search_txt={fnnews_keyword2}&page=0'
etoday_search_url = f'https://www.etoday.co.kr/search/?keyword={etoday_keyword}'
asiae_search_url = f'https://www.asiae.co.kr/search/index.htm'
asiae_data = {'kwd': asiae_keyword, 'type': 'all', 'sort': 'NEWDATE'}

# 전역변수 - API 토큰
telgram_api_token = '5645768266:AAFNGWyAGXQwXKB0gdCr-P4tOugCnQ8b8cw'
telegram_chat_id = -1001701299096

# UI영역
form_class = uic.loadUiType("telegram_news_bot.ui")[0]
class NewsCrawler(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        print("UI 실행")
        self.btn_start.clicked.connect(self.btn_start_clicked)

    def btn_start_clicked(self):
        self.btn_start.setEnabled(False)
        QApplication.processEvents()
        self.start_crwaling()

    def start_crwaling(self):
        print("크롤링 시작")
        # 가장 최근 기사 수집
        recent_article = Article()
        recent_article.moneys_article = get_moneys_article_url(moneys_search_url)
        recent_article.fnnews_article1 = get_fnnews_article_url(fnnews_search_url1)
        recent_article.fnnews_article2 = get_fnnews_article_url(fnnews_search_url2)
        recent_article.etoday_article = get_etoday_article_url(etoday_search_url)
        recent_article.asiae_article = get_asiae_article_url(asiae_search_url, asiae_data)

        while True:
            moneys_article = get_moneys_article_url(moneys_search_url)
            fnnews_article1 = get_fnnews_article_url(fnnews_search_url1)
            fnnews_article2 = get_fnnews_article_url(fnnews_search_url2)
            etoday_article = get_etoday_article_url(etoday_search_url)
            asiae_article = get_asiae_article_url(asiae_search_url, asiae_data)

            if recent_article.moneys_article != moneys_article:
                send_telegram(moneys_article)
                recent_article.moneys_article = moneys_article
                print("머니S에 신규 기사(이지운 기자)가 등록되었습니다.")
                QApplication.processEvents()

            if recent_article.fnnews_article1 != fnnews_article1:
                send_telegram(fnnews_article1)
                recent_article.fnnews_article1 = fnnews_article1
                print("파이낸셜뉴스에 신규 기사(최두선 기자)가 등록되었습니다.")
                QApplication.processEvents()

            if recent_article.fnnews_article2 != fnnews_article2:
                send_telegram(fnnews_article2)
                recent_article.fnnews_article2 = fnnews_article2
                print("파이낸셜뉴스에 신규 기사(김민기 기자)가 등록되었습니다.")
                QApplication.processEvents()

            if recent_article.etoday_article != etoday_article:
                send_telegram(etoday_article)
                recent_article.etoday_article = etoday_article
                print("이투데이에 신규 기사(설경진 기자)가 등록되었습니다.")
                QApplication.processEvents()

            if recent_article.asiae_article != asiae_article:
                send_telegram(asiae_article)
                recent_article.asiae_article = asiae_article
                print("아시아경제에 신규 기사(박형수 기자)가 등록되었습니다.")
                QApplication.processEvents()

            QApplication.processEvents()
            time.sleep(60)

class Article:
    def __init__(self):
        self.moneys_article = ''
        self.fnnews_article1 = ''
        self.fnnews_article2 = ''
        self.etoday_article = ''
        self.asiae_article = ''

def send_telegram(message):
    bot = telegram.Bot(token=telgram_api_token)
    chat_id = telegram_chat_id
    bot.sendMessage(chat_id=chat_id, text=message)

def get_moneys_article_url(search_url):
    moneys_res = requests.get(search_url)
    moneys_html = moneys_res.text
    moneys_soup = BeautifulSoup(moneys_html, 'html.parser')
    ul = moneys_soup.select_one('#content > form > div.lst_1.mgt5 > ul')
    lis = ul.select('li')
    article_url = lis[0].select_one('a').attrs['href']
    return article_url

def get_fnnews_article_url(search_url):
    fnnews_res = requests.get(search_url)
    fnnews_html = fnnews_res.text
    fnnews_soup = BeautifulSoup(fnnews_html, 'html.parser')
    ul = fnnews_soup.select_one('.list_art')
    lis = ul.select('li')
    article_url = lis[0].select_one('a').attrs['href']
    prefix_url = 'https://www.fnnews.com'
    return prefix_url+article_url

def get_etoday_article_url(search_url):
    etoday_res = requests.get(search_url)
    etoday_html = etoday_res.text
    etoday_soup = BeautifulSoup(etoday_html, 'html.parser')
    ul = etoday_soup.select_one('#list_W')
    lis = etoday_soup.select('.sp_newslist')
    article_url = lis[0].select_one('a').attrs['href']
    prefix_url = 'https://www.etoday.co.kr/'
    return prefix_url+article_url

def get_asiae_article_url(search_url, search_data):
    asiae_res = requests.post(search_url, data=search_data)
    asiae_html = asiae_res.text
    asiae_soup = BeautifulSoup(asiae_html, 'html.parser')
    ul = asiae_soup.select_one('.news_lst')
    lis = ul.select('li')
    article_url = lis[0].select_one('a').attrs['href']
    prefix_url = 'https:'
    return prefix_url+article_url


if __name__ == "__main__":
    print("프로그램 기동")
    app = QApplication(sys.argv)
    news_crawler = NewsCrawler()
    news_crawler.show()
    app.exec()