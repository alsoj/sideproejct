from PyQt6.QtWidgets import QMainWindow
from datetime import datetime
from PyQt6 import uic

# UI영역
from coinpan.PostWorker import PostWorker
from coinpan.PriceWorker import PriceWorker

form_class = uic.loadUiType("CoinpanCrawler.ui")[0]
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