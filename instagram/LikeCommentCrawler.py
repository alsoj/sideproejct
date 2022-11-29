import os
import sys
import re

from PyQt6.QtWidgets import *
from PyQt6 import uic

from datetime import datetime
import Common
from Common import execute_browser

from ExcelExport import create_excel, write_excel
from openpyxl import Workbook, load_workbook

import Config
from Login import LoginWorker
from Comment import CommentWorker
from Timeline import TimelineWorker
from Media import MediaWorker

form_class = uic.loadUiType("LikeCommentCrawler.ui")[0]
class INSTA_Window(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.btn_start_target.clicked.connect(self.btn_start_target_clicked)  # 특정 게시물 크롤링
        self.btn_start_recent.clicked.connect(self.btn_start_recent_clicked)  # 최근 게시물 크롤링
        self.btn_start_comment.clicked.connect(self.btn_start_comment_clicked)  # 댓글 크롤링

        self.log_browser.append(" - 추출 결과는 output 폴더 하위에 저장됩니다.")
        self.log_browser.append(" - 게시글 URL 예시) https://www.instagram.com/p/Cf-vUAcLS8K/")
        self.log_browser.append(" - 과도한 크롤링은 인스타그램에서 제한될 수 있습니다.")

        self.browser = execute_browser()

        self.login_worker = LoginWorker(self)
        self.comment_worker = CommentWorker(self)
        self.recent_worker = TimelineWorker(self)
        self.media_worker = MediaWorker(self)
        self.callback_function = None

        self.comment_list = []
        self.comment_short_code_list = []
        self.recent_list = []
        self.recent_user_id_list = []
        self.target_list = []
        self.target_short_code_list = []

    def callback(self):
        try:
            # 댓글 추출 관련 콜백
            if self.callback_function == 'crawl_comment':
                self.crawl_comment()
            elif self.callback_function == 'export_excel_comment':
                filename = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_댓글 추출.xlsx'
                create_excel('comment', filename)
                count_dict = {}
                for comment_list in self.comment_list:
                    write_excel(comment_list, filename)
                    write_excel([['********************************************************']], filename)

                    for comment in comment_list:
                        count_dict = count_word(count_dict, comment[3])
                write_excel_count(count_dict, filename)
                self.button_activate(True)
                Common.debug(self.log_browser, f"저장 경로 : {os.getcwd() + Config.FILE_PATH.replace('.','')}")
                Common.debug(self.log_browser, f"댓글 추출 파일 명 : {filename}")
                Common.info(self.log_browser, f"댓글 추출이 완료 되었습니다.")

            # 최근 게시물 추출 관련 콜백
            elif self.callback_function == 'crawl_recent':
                self.crawl_recent()
            elif self.callback_function == 'export_excel_recent':
                filename = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_최근 게시물 추출.xlsx'
                create_excel('timeline', filename)
                for recent_result in self.recent_list:
                    write_excel(recent_result, filename)
                    write_excel([['********************************************************']], filename)
                self.button_activate(True)
                Common.debug(self.log_browser, f"저장 경로 : {os.getcwd() + Config.FILE_PATH.replace('.','')}")
                Common.debug(self.log_browser, f"최근 게시물 추출 파일 명 : {filename}")
                Common.info(self.log_browser, f"최근 게시물 추출이 완료 되었습니다.")

            # 특정 게시물 관련 콜백
            elif self.callback_function == 'crawl_target':
                self.crawl_target()
            elif self.callback_function == 'export_excel_target':
                filename = f'{datetime.now().strftime("%Y%m%d%H%M%S")}_특정 게시물 추출.xlsx'
                create_excel('timeline', filename)
                write_excel(self.target_list, filename)
                self.button_activate(True)
                Common.debug(self.log_browser, f"저장 경로 : {os.getcwd() + Config.FILE_PATH.replace('.','')}")
                Common.debug(self.log_browser, f"특정 게시물 추출 파일 명 : {filename}")
                Common.info(self.log_browser, f"특정 게시물 추출이 완료 되었습니다.")
        except Exception as e:
            Common.error(self.log_browser, f"callback-{self.callback_function} 실행 중 오류 메시지 : {str(e)}")

    # 특정 게시물 클릭
    def btn_start_target_clicked(self):
        try:
            self.button_activate(False)
            Common.info(self.log_browser, "특정 게시물 크롤링을 시작합니다.")
            self.set_id_pw()
            self.callback_function = 'crawl_target'
            self.login_worker.start()
        except Exception as e:
            Common.error(self.log_browser, f"btn_start_target_clicked 실행 중 오류 메시지 : {str(e)}")

    # 특정 게시물 크롤링
    def crawl_target(self):
        try:
            self.button_activate(False)
            self.callback_function = 'export_excel_target'
            self.target_list = []
            self.target_short_code_list = []
            for index, target_url in enumerate(self.edit_target.toPlainText().split("\n")):
                if len(self.target_short_code_list) < 6 and len(target_url.strip()) > 0:
                    self.target_short_code_list.append(Common.get_short_code(target_url))
            self.media_worker.start()
        except Exception as e:
            Common.error(self.log_browser, f"crawl_target 실행 중 오류 메시지 : {str(e)}")

    # 최근 게시물 크롤링 클릭
    def btn_start_recent_clicked(self):
        try:
            self.button_activate(False)
            Common.info(self.log_browser, "최근 게시물 크롤링을 시작합니다.")
            self.set_id_pw()
            self.callback_function = 'crawl_recent'
            self.login_worker.start()
        except Exception as e:
            Common.error(self.log_browser, f"btn_start_recent_clicked 실행 중 오류 메시지 : {str(e)}")

    # 최신 게시물 크롤링
    def crawl_recent(self):
        try:
            self.button_activate(False)
            self.callback_function = 'export_excel_recent'
            self.recent_list = []
            self.recent_user_id_list = []
            for index, target_user_id in enumerate(self.edit_recent.toPlainText().split("\n")):
                if len(self.recent_user_id_list) < 6 and len(target_user_id.strip()) > 0:
                    self.recent_user_id_list.append(target_user_id)
            self.recent_worker.start()
        except Exception as e:
            Common.error(self.log_browser, f"crawl_recent 실행 중 오류 메시지 : {str(e)}")

    # 댓글 크롤링 버튼 클릭
    def btn_start_comment_clicked(self):
        try:
            self.button_activate(False)
            Common.info(self.log_browser, "댓글 크롤링을 시작합니다.")
            self.set_id_pw()
            self.callback_function = 'crawl_comment'
            self.login_worker.start()
        except Exception as e:
            Common.error(self.log_browser, f"btn_start_comment_clicked 실행 중 오류 메시지 : {str(e)}")

    # 댓글 추출
    def crawl_comment(self):
        try:
            self.button_activate(False)
            self.callback_function = 'export_excel_comment'
            self.comment_list = []
            self.comment_short_code_list = []
            for index, target_url in enumerate(self.edit_comment.toPlainText().split("\n")):
                if len(self.comment_short_code_list) < 6 and len(target_url.strip()) > 0:
                    self.comment_short_code_list.append(Common.get_short_code(target_url))
            self.comment_worker.start()
        except Exception as e:
            Common.error(self.log_browser, f"crawl_comment 실행 중 오류 메시지 : {str(e)}")

    # ID/PW 세팅
    def set_id_pw(self):
        self.login_worker.set_login_id(self.edit_id.text())
        self.login_worker.set_login_pw(self.edit_pw.text())

    # 버튼 활성/비활성화
    def button_activate(self, enable):
        self.btn_start_target.setEnabled(enable)
        self.btn_start_recent.setEnabled(enable)
        self.btn_start_comment.setEnabled(enable)

    # 종료 이벤트
    def closeEvent(self, QCloseEvent):
        if hasattr(self, 'browser') and self.browser is not None:
            self.browser.quit()

def count_word(count_dict, text):
    for word in re.sub(r'[^\w\s]', ' ', text).split(' '):
        if len(word) > 0:
            if word.endswith('은') \
                or word.endswith('는') \
                or word.endswith('이') \
                or word.endswith('가') \
                or word.endswith('을') \
                or word.endswith('를') :
                word = word[:-1]
            if word in count_dict:
                count_dict[word] += 1
            else:
                count_dict[word] = 1
    return count_dict

# 엑셀 입력(단어 카운팅)
def write_excel_count(count_dict, filename):
    file_path_name = Config.FILE_PATH + filename
    wb = load_workbook(file_path_name, data_only=True)
    ws = wb.active

    for (key, value) in count_dict.items():
        ws.append([key, value])
    wb.save(file_path_name)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    INSTA = INSTA_Window()
    INSTA.show()
    app.exec()
