import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6 import uic

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

        self.price_worker = PriceWorker()
        self.post_worker = PostWorker()

        self.btn_price.clicked.connect(self.crawl_price)
        self.btn_browser.clicked.connect(self.execute_browser)
        self.btn_start.clicked.connect(self.crawl_post)

    def crawl_price(self):
        self.price_worker.start()

    def execute_browser(self):
        self.post_worker.start()

    def crawl_post(self):
        self.post_worker.go_to_board()

def export_excel(result):
    filename = datetime.now().strftime('%Y%m%d%H%M%S') + coinpan_config.PRICE_FILENAME
    result.to_excel('./output/' + filename, index=False)

class PriceWorker(QThread):
    def __init__(self):
        super().__init__()

    def run(self):
        print("실시간 시세 추출 시작")
        result = self.get_price()
        export_excel(result)
        print("실시간 시세 추출 끝")

    def get_price(self):
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
                                                    price['now_price'],
                                                    price['now_price_usd'],
                                                    price['diff_24hr'],
                                                    price['diff_24hr_percent'],
                                                    price['korea_premium'],
                                                    price['korea_premium_percent'],
                                                    price['units_traded']]
        result = prices.sort_values(by=['순번1','순번2'])
        result = result.drop(['순번1','순번2'], axis=1)
        result = result.reset_index(drop=True)
        return result


class PostWorker(QThread):
    def __init__(self):
        super().__init__()
        self.running =True

    def run(self):
        print("test 시작")
        self.browser = webdriver.Chrome(executable_path='/Users/alsoj/Workspace/kmong/ipynb/chromedriver_mac')
        self.browser.get(coinpan_config.LOGIN_URL)
        print("test 끝")

    def go_to_board(self):
        self.browser.get(coinpan_config.BOARD_URL)


if __name__ == "__main__":
    print("프로그램 기동")
    app = QApplication(sys.argv)
    coinpan_crawelr = CoinpanCrawler()
    coinpan_crawelr.show()
    app.exec()