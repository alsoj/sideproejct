import sys

from PyQt6.QtCore import QDate, QThread
from PyQt6.QtWidgets import *

from PyQt6.QtWidgets import QMainWindow
from datetime import datetime
from PyQt6 import uic

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")
options.add_argument("--single-process")
options.add_argument("--disable-dev-shm-usage")

form_class = uic.loadUiType("google_news.ui")[0]
class NewsCrawler(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        # self.browser = webdriver.Chrome(executable_path='/Users/alsoj/Workspace/kmong/ipynb/chromedriver_mac', options=options)
        self.news_worker = NewsWorker(self)

        # 오늘 날짜로 기본 세팅
        today = datetime.now().strftime('%Y-%m-%d')
        self.edit_date.setDate(QDate.fromString(today, 'yyyy-MM-dd'))
        self.button_start.clicked.connect(self.crawl_news)
        self.result_browser.setOpenExternalLinks(True)

    def crawl_news(self):
        self.result_browser.clear()
        self.keyword = self.edit_keyword.text()
        date = self.edit_date.date().toPyDate()
        self.search_date = str(date.month) + "/" + str(date.day) + "/" + str(date.year)
        self.news_worker.start()

    def debug(self, text):  # 디버그 로그 출력
        self.result_browser.append(text)


    def closeEvent(self, QCloseEvent):
        self.browser.quit()

class NewsWorker(QThread):
    """
    실시간 시세 크롤링 쓰레드
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def run(self):
        keyword = self.parent.keyword
        min_date = self.parent.search_date
        max_date = self.parent.search_date
        url = f'https://www.google.com/search?q={keyword}&tbs=cdr%3A1%2Ccd_min%3A{min_date}%2Ccd_max%3A{max_date}&tbm=nws'
        self.parent.browser.get(url)

        is_finished = False
        while not is_finished:
            self.crawl_articles()
            is_finished = self.go_to_next_page()

        self.parent.debug("########## 추출이 종료되었습니다. ##########")

    def crawl_articles(self):
        try:
            div = self.parent.browser.find_element(by=By.ID, value='search')
            articles = div.find_elements(by=By.CLASS_NAME, value='SoaBEf')
            for article in articles:
                content = article.find_element(by=By.CLASS_NAME, value='iRPxbe')
                href = article.find_element(by=By.TAG_NAME, value='a').get_attribute('href')
                pub = content.find_element(by=By.CLASS_NAME, value='CEMjEf').text
                title = content.find_element(by=By.CLASS_NAME, value='mCBkyc').text
                detail = content.find_element(by=By.CLASS_NAME, value='GI74Re').text

                a_tag = make_a_tag(href, title)
                self.parent.debug("[매체]  " + pub)
                self.parent.debug("[제목]  " + a_tag)
                self.parent.debug("[내용]  " + detail)
                self.parent.debug("")

        except Exception as e:
            print("크롤링 중 오류 발생", e)

    def go_to_next_page(self):
        try:
            table = self.parent.browser.find_element(by=By.TAG_NAME, value='table')
            tds = table.find_elements(by=By.TAG_NAME, value='td')
            td = tds[-1]
            if td.get_attribute('role') == 'heading':
                td.find_element(by=By.TAG_NAME, value='a').click()
                is_finished = False
            else:
                is_finished = True
        except Exception as e:
            is_finished = True
        finally:
            return is_finished

def make_a_tag(href, title):
    return f"<a href='{href}'>{title}</a>"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    news_crawler = NewsCrawler()
    news_crawler.show()
    app.exec()