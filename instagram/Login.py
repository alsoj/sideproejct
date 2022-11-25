from time import sleep

from PyQt6.QtCore import QThread
from selenium.webdriver.common.by import By
import Config
import Common

class LoginWorker(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.login_id, self.login_pw = None, None

    def run(self):
        if self.login():
            self.parent.button_activate(True)
            self.parent.callback()
        else:
            self.parent.button_activate(True)

    def login(self):
        is_login = False
        if self.login_id is None or self.login_pw is None \
                or len(self.login_id) == 0 or len(self.login_pw) == 0:
            Common.error(self.parent.log_browser, "인스타그램 ID와 PW를 입력해주세요.")
            return is_login

        Common.debug(self.parent.log_browser, f'로그인을 진행하고 있습니다. ID : {self.login_id}')
        self.parent.browser.get(Config.LOGIN_URL)
        sleep(3)

        if 'accounts' in self.parent.browser.current_url:
            inputs = self.parent.browser.find_elements(by=By.TAG_NAME, value='input')
            inputs[0].clear()
            inputs[1].clear()
            inputs[0].send_keys(self.login_id)
            inputs[1].send_keys(self.login_pw)
            inputs[1].submit()
            sleep(3)

            if '잘못된 비밀번호' in self.parent.browser.page_source:
                Common.error(self.parent.log_browser, '잘못된 비밀번호입니다.')
            elif '입력한 사용자 이름' in self.parent.browser.page_source:
                Common.error(self.parent.log_browser, '잘못된 사용자 ID입니다.')
            elif '문제가 발생' in self.parent.browser.page_source:
                Common.error(self.parent.log_browser, '일시적인 문제가 발생하였습니다.')
            else:
                Common.debug(self.parent.log_browser, f'로그인에 성공했습니다. ID : {self.login_id}')
                is_login = True
        else:  # 이미 로그인된 상태
            Common.debug(self.parent.log_browser, f'로그인에 성공했습니다. ID : {self.login_id}')
            is_login = True

        return is_login

    def set_login_id(self, login_id):
        self.login_id = login_id

    def set_login_pw(self, login_pw):
        self.login_pw = login_pw