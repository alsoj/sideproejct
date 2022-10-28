import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6 import uic

import logging
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

from time import sleep, time
import requests
from datetime import datetime
from pandas import DataFrame

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

import coinpan_config

# UI영역
form_class = uic.loadUiType("coinpan_crawler.ui")[0]
class CoinpanCrawler(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.price_worker = PriceWorker(self)
        self.post_worker = PostWorker(self)

        self.btn_price.clicked.connect(self.crawl_price)
        self.btn_browser.clicked.connect(self.execute_browser)
        self.btn_start.clicked.connect(self.crawl_post)
        self.btn_stop.clicked.connect(self.click_stop)

        self.debug("코인판 크롤링 프로그램이 실행되었습니다.")

    def debug(self, text): # 디버그 로그 출력
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_browser.append(f"[{now}] " + text)

    def info(self, text):  # 정보 로그 출력
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_browser.append(f'<p style="color:green">[{now}] {text}</p>')

    def error(self, text):  # 에러 로그 출력
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_browser.append(f'<p style="color:red">[{now}] {text}</p>')

    def crawl_price(self):
        # 실시간 시세 크롤링
        self.price_worker.start()

    def execute_browser(self):
        # 크롬 브라우저 로딩
        self.post_worker.execute_browser()

    def crawl_post(self):
        crawl_type = self.get_crawl_type()  # 크롤링 타입 체크(최신/과거)

        if crawl_type == "R":
            self.post_worker.set_function("crawl_recent")
            self.post_worker.start()  # 최신 크롤링
        elif crawl_type == "P":
            self.post_worker.set_function("crawl_past")
            self.post_worker.start()  # 과거 크롤링

    def click_start(self):
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

    def click_stop(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)


    def get_crawl_type(self):
        if self.radio_recent.isChecked():
            return "R"
        else:
            return "P"

class PostWorker(QThread):
    """
    게시글 크롤링 쓰레드
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.method = None

    def run(self):
        if self.method == "execute_browser":
            self.execute_browser()
        elif self.method == "crawl_past":
            self.crawl_past()
        elif self.method == "crawl_recent":
            self.crawl_recent()

    def set_function(self, method):
        self.method = method

    def execute_browser(self):
        self.parent.debug("크롬 브라우저가 실행됩니다. 크롤링 전 로그인을 진행하시기 바랍니다.")
        self.browser = webdriver.Chrome(executable_path='/Users/alsoj/Workspace/kmong/ipynb/chromedriver_mac')
        self.browser.get(coinpan_config.LOGIN_URL)

    def crawl_past(self):
        self.parent.debug("과거 순으로 게시글 크롤링 시작")
        self.parent.click_start()
        for i in range(5):
            sleep(1)
        self.parent.click_stop()
        self.parent.debug("과거 순으로 게시글 크롤링 종료")

    def crawl_recent(self):
        self.parent.debug("최신 순으로 게시글 크롤링 시작")
        self.parent.click_start()
        for i in range(5):
            sleep(1)
        self.parent.click_stop()
        self.parent.debug("최신 순으로 게시글 크롤링 종료")

    def go_to_board(self, isRecent):
        print(isRecent)
        # self.browser.get(coinpan_config.BOARD_URL)





class PriceWorker(QThread):
    """
    실시간 시세 크롤링 쓰레드
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def run(self):
        self.parent.btn_price.setEnabled(False)
        self.parent.info("실시간 시세 추출 시작")
        result = get_price()
        filename = export_excel(result)
        self.parent.debug("파일 저장 경로 : " + filename)
        self.parent.info("실시간 시세 추출 종료")
        self.parent.btn_price.setEnabled(True)

def get_price():
    """
    실시간 시세 API 호출
    :return: 실시간 시세 API
    """
    now = round(time())
    response = requests.get(coinpan_config.API_URL + str(now))
    data = response.json()

    prices = DataFrame(
        columns=['순번1', '순번2', '가상화폐', '거래소', '실시간시세(KRW)', '실시간시세(USD)', '24시간변동액', '24시간변동률', '한국프리미엄',
                 '한국프리미엄(%)', '거래량'])

    for i, exchange in enumerate(coinpan_config.API_EXCHANGE):
        if exchange in data['prices']:
            for j, coin in enumerate(coinpan_config.API_COIN):
                if coin in data['prices'][exchange]:
                    price = data['prices'][exchange][coin]
                    prices.loc[len(prices)] = [j, i, coin, exchange,
                                                round(float(price['now_price'] or 0), 2),
                                                round(float(price['now_price_usd'] or 0), 4),
                                                round(float(price['diff_24hr'] or 0), 2),
                                                round(float(price['diff_24hr_percent'] or 0), 2),
                                                round(float(price['korea_premium'] or 0), 2),
                                                round(float(price['korea_premium_percent'] or 0), 2),
                                                round(float(price['units_traded'] or 0), 2)]
    result = prices.sort_values(by=['순번1','순번2'])
    result = result.drop(['순번1','순번2'], axis=1)
    result = result.reset_index(drop=True)
    return result

def export_excel(result):
    """
    엑셀 export 함수
    :param result: 실시간 시세 Dataframe
    :return filename : 경로 및 파일명
    """
    filename = coinpan_config.OUTPUT_DIR + datetime.now().strftime('%Y%m%d%H%M%S') + coinpan_config.PRICE_FILENAME
    result.to_excel(filename, index=False)
    return filename

if __name__ == "__main__":
    logging.info("프로그램 기동")
    app = QApplication(sys.argv)
    coinpan_crawelr = CoinpanCrawler()
    coinpan_crawelr.show()
    app.exec()