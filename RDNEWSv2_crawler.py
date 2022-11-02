import sys

from PyQt6.QtCore import QDate, QThread
from PyQt6.QtWidgets import *

from PyQt6.QtWidgets import QMainWindow
from datetime import datetime, timedelta
from PyQt6 import uic

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

from time import sleep


form_class = uic.loadUiType("RDNEWSv2_crawler.ui")[0]
class RDNEWSCrawler(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.news_worker = NewsWorker(self)

        # 날짜 기본 세팅
        self.input_start_ymd.setDate(QDate(datetime.now()-timedelta(days=7)))
        self.input_end_ymd.setDate(QDate(datetime.now()))

        # 작업 시작 클릭 시
        self.btn_start.clicked.connect(self.crawl_news)

    def debug(self, text):  # 디버그 로그 출력
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_browser.append(f"[{now}] " + text)

    def crawl_news(self):
        background_yn = "Y" if self.chk_background.isChecked() > 0 else "N"
        options = get_option(background_yn)
        self.browser = webdriver.Chrome(executable_path='/Users/alsoj/Workspace/kmong/ipynb/chromedriver_mac', options=options)
        self.news_worker.start()

    def closeEvent(self, QCloseEvent):
        self.browser.quit()

class NewsWorker(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def run(self):
        self.parent.btn_start.setEnabled(False)
        self.parent.debug("크롤링이 시작됩니다!!")
        sleep(3)
        self.parent.debug("크롤링이 종료됩니다!!")
        self.parent.btn_start.setEnabled(True)

def get_option(background_yn):
    # 백그라운드 실행 세팅
    options = webdriver.ChromeOptions()
    if background_yn == "Y":
        options.add_argument("headless")
    return options

if __name__ == "__main__":
    app = QApplication(sys.argv)
    news_crawler = RDNEWSCrawler()
    news_crawler.show()
    app.exec()