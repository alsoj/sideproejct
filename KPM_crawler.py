import sys
import os
import platform

from PyQt6.QtCore import QDate, QThread
from PyQt6.QtWidgets import *

from PyQt6.QtWidgets import QMainWindow
from datetime import datetime, timedelta
from PyQt6 import uic, QtGui, QtCore

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

from openpyxl import Workbook, load_workbook

from time import sleep
from selenium.common.exceptions import NoSuchElementException

import unicodedata
import re

# 전역변수 - 파일 관련
FILE_PATH = './output/'
FILE_PREFIX = 'KPM_'
FILE_SUFFIX = '.xlsx'
FILE_NAME = ''

# 전역변수 - 재시도 관련
SLEEP_TIME = 60
RETRY_CNT = 10

# ID/PW 세팅
f = open("KPM_account.txt", 'r')
lines = f.readlines()
ID, PW = lines[0].strip(), lines[1].strip()
f.close()

form_class = uic.loadUiType("KPM_crawler.ui")[0]
class KPMCrawler(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.news_worker = NewsWorker(self)

        # 날짜 기본 세팅
        self.input_start_ymd.setDate(QDate(datetime.now()-timedelta(days=7)))
        self.input_end_ymd.setDate(QDate(datetime.now()))
        self.scroll_bar = self.log_browser.verticalScrollBar()

        # 작업 시작 클릭 시
        self.btn_start.clicked.connect(self.crawl_news)

    def debug(self, text):  # 디버그 로그 출력
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_browser.append(f"[{now}] " + text)
        self.scroll_bar.setValue(self.scroll_bar.maximum())

    def info(self, text):  # 정보 로그 출력
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_browser.append(f'<p style="color:green">[{now}] {text}</p>')
        self.scroll_bar.setValue(self.scroll_bar.maximum())

    def error(self, text):  # 에러 로그 출력
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_browser.append(f'<p style="color:red">[{now}] {text}</p>')
        self.scroll_bar.setValue(self.scroll_bar.maximum())

    def crawl_news(self):
        if self.input_end_ymd.date().toPyDate() < self.input_start_ymd.date().toPyDate():
            self.error("오류 발생 : 종료일자는 시작일자보다 크거나 같아야 합니다.")
        else:
            background_yn = "Y" if self.chk_background.isChecked() > 0 else "N"
            options = get_option(background_yn)
            if 'macOS' in platform.platform():
                self.browser = webdriver.Chrome(executable_path='/Users/alsoj/Workspace/kmong/ipynb/chromedriver_mac', options=options)
            else:
                self.browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

            self.news_worker.start()

    def closeEvent(self, QCloseEvent):
        if hasattr(self, 'browser'):
            self.browser.quit()

class NewsWorker(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def run(self):
        try:
            self.parent.btn_start.setEnabled(False)
            self.parent.info("조선언론정보기지 크롤링 START")

            start_ymd = self.parent.input_start_ymd.date().toPyDate()
            end_ymd = self.parent.input_end_ymd.date().toPyDate()
            str_start_ymd = start_ymd.strftime("%Y%m%d")
            str_end_ymd = end_ymd.strftime("%Y%m%d")

            # 엑셀 세팅
            global FILE_NAME
            FILE_NAME = FILE_PREFIX + str_start_ymd + "_" + str_end_ymd + FILE_SUFFIX

            create_excel()
            wb = load_workbook(FILE_PATH + FILE_NAME, data_only=True)
            ws = wb.active

            ###################################
            # 메인 로직 시작
            ###################################
            login_url = 'http://www.dprkmedia.com//gate/gatemain'

            target_news = ""
            if self.parent.check_RD.isChecked():
                target_news += "&nTitle[]=로동신문"
            if self.parent.check_MH.isChecked():
                target_news += "&nTitle[]=문학신문"
            if self.parent.check_MJ.isChecked():
                target_news += "&nTitle[]=민주조선"
            if self.parent.check_PT.isChecked():
                target_news += "&nTitle[]=Pyongyang Times"
            if self.parent.check_JS.isChecked():
                target_news += "&nTitle[]=조선신보 평양지국"
            search_call_url = f'http://www.dprkmedia.com/search?ddlWhere=news&txtKeyword[]=&searchRange=title_nayong&dateRange[]={start_ymd}&dateRange[]={end_ymd}{target_news}'

            self.connect_url(login_url)
            login(self.parent.browser)
            self.parent.debug("로그인에 성공했습니다.")

            self.connect_url(search_call_url)
            article_list = get_article_list(self.parent.browser)
            article_cnt = len(article_list)
            rownum = 0
            self.parent.info(f"크롤링 대상 기사 개수 : {article_cnt}")
            for article in article_list:
                detail_url = article.get_attribute('href')
                self.parent.browser.switch_to.new_window('tab')
                self.connect_url(detail_url)
                detail_info = get_detail_info(self.parent.browser)

                ws.append(detail_info)
                wb.save(FILE_PATH + FILE_NAME)
                close_new_tabs(self.parent.browser)
                rownum += 1
                if rownum % 10 == 0:
                    self.parent.debug(f"기사 크롤링 진행 중 [{rownum} / {article_cnt}개 완료]")

            self.parent.info("조선언론정보기지 크롤링 END")
        except Exception as e:
            self.parent.error(f"크롤링 진행 중 오류 발생 : {str(e)}")
        finally:
            self.parent.browser.quit()
            self.parent.btn_start.setEnabled(True)

    def connect_url(self, url):
        retries = RETRY_CNT
        connected = False
        while retries > 0:
            try:
                self.parent.browser.get(url)
                connected = True
                break
            except Exception as e:
                retries -= 1
                self.parent.debug("응답이 없어 재시도 합니다. 남은 재시도 회수 : " + str(retries))
                sleep(SLEEP_TIME)
                continue
        return connected

# 전역 함수
def get_option(background_yn):
    # 백그라운드 실행 세팅
    options = webdriver.ChromeOptions()
    if background_yn == "Y":
        options.add_argument("headless")
    return options

def create_excel():
    # 엑셀 생성
    wb = Workbook()
    ws = wb.active

    # 제목 적기
    sub = ['신문명(좌상단)', '기사분류(우상단)', '기사제목', '기사내용', '기자명', '기사일자']
    for kwd, j in zip(sub, list(range(1, len(sub) + 1))):
        ws.cell(row=1, column=j).value = kwd

    if not os.path.isdir(FILE_PATH):
        os.mkdir(FILE_PATH)

    wb.save(FILE_PATH+FILE_NAME)

# 로그인
def login(browser):
    input_id = browser.find_element(by=By.ID, value='Login1_txt_userid')
    input_pw = browser.find_element(by=By.ID, value='Login1_txt_pwd')
    button_login = browser.find_element(by=By.ID, value='Login1_btn_login')

    input_id.clear()
    input_id.send_keys(ID)
    input_pw.clear()
    input_pw.send_keys(PW)
    button_login.click()

# 기사 리스트 조회
def get_article_list(browser):
    table_news = browser.find_element(by=By.ID, value='dgNews')
    article_list = table_news.find_elements(by=By.TAG_NAME, value='a')
    return article_list

# 신규 오픈 탭 닫기
def close_new_tabs(browser):
    tabs = browser.window_handles
    while len(tabs) != 1 :
        browser.switch_to.window(tabs[1])
        browser.close()
        tabs = browser.window_handles
    browser.switch_to.window(tabs[0])

# 페이지에서 원하는 값 추출
def find_element(browser, target):
    try:
        if target == 'media_name':
            return browser.find_element(by=By.XPATH, value='/html/body/form/table/tbody/tr[2]/td[3]/table[1]/tbody/tr[1]/td[1]/b').text.strip()
        elif target == 'section':
            return browser.find_element(by=By.XPATH, value='/html/body/form/table/tbody/tr[2]/td[3]/table[1]/tbody/tr[1]/td[2]/b').text.strip()
        elif target == 'title':
            return browser.find_element(by=By.XPATH, value='/html/body/form/table/tbody/tr[2]/td[3]/table[2]/tbody/tr[2]/td/span/b').text.strip()
        elif target == 'subtitle':
            return '\n' + browser.find_element(by=By.XPATH, value='/html/body/form/table/tbody/tr[2]/td[3]/table[2]/tbody/tr[4]/td/b').text.strip()
        elif target == 'content':
            return browser.find_element(by=By.XPATH, value='/html/body/form/table/tbody/tr[2]/td[3]/table[2]/tbody/tr[6]/td').text.strip().replace("\n\n", "\n")
        elif target == 'author':
            return browser.find_element(by=By.XPATH, value='/html/body/form/table/tbody/tr[2]/td[3]/table[2]/tbody/tr[10]/td').text.strip()
        elif target == 'date':
            return browser.find_element(by=By.XPATH, value='/html/body/form/table/tbody/tr[2]/td[3]/table[2]/tbody/tr[11]/td').text.strip()[:10]
        else:
            return ''
    except NoSuchElementException:
        return ''

def get_detail_info(browser):
    media_name = find_element(browser, 'media_name')
    media_name = unicodedata.normalize('NFKC', media_name)
    section = find_element(browser, 'section')
    section = unicodedata.normalize('NFKC', section)
    main_title = find_element(browser, 'title')
    main_title = unicodedata.normalize('NFKC', main_title)
    subtitle = find_element(browser, 'subtitle')
    subtitle = unicodedata.normalize('NFKC', subtitle)
    title = main_title + subtitle
    title = title.strip()
    content = find_element(browser, 'content')
    content = unicodedata.normalize('NFKC', content)
    author = find_element(browser, 'author')
    author = unicodedata.normalize('NFKC', author)
    date = find_element(browser, 'date')
    date = unicodedata.normalize('NFKC', date)
    return [media_name, section, title, content, author, date]


if __name__ == "__main__":
    app = QApplication(sys.argv)
    news_crawler = KPMCrawler()
    news_crawler.show()
    app.exec()