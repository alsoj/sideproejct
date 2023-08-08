from time import sleep

from PyQt6.QtCore import QThread
from selenium.webdriver.common.by import By
import Config
from Common import debug, info, error, is_null

class LoginWorker(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.login_id, self.login_pw = None, None

    def run(self):
        self.login_id = self.parent.login_id
        self.login_pw = self.parent.login_pw

        if self.login():
            self.parent.after_login()
        else:
            self.parent.button_activate(True)

    def login(self):
        is_login = False

        # 필수 값 체크
        if is_null(self.login_id) or is_null(self.login_pw):
            error(self.parent.log_browser, "인스타그램 ID와 PW를 입력해주세요.")
            return is_login

        self.parent.browser.get(Config.LOGIN_URL)
        sleep(5)

        if 'accounts' in self.parent.browser.current_url:
            inputs = self.get_login_input(5)
            inputs[0].clear()
            inputs[1].clear()
            inputs[0].send_keys(self.login_id.strip())
            inputs[1].send_keys(self.login_pw.strip())
            inputs[1].submit()
            sleep(5)

            if '잘못된 비밀번호' in self.parent.browser.page_source:
                error(self.parent.log_browser, '잘못된 비밀번호입니다.')
            elif '입력한 사용자 이름' in self.parent.browser.page_source:
                error(self.parent.log_browser, '잘못된 사용자 ID입니다.')
            elif '문제가 발생' in self.parent.browser.page_source:
                error(self.parent.log_browser, '일시적인 문제가 발생하였습니다.')
            elif '비정상적인' in self.parent.browser.page_source:
                error(self.parent.log_browser, '비정상적인 로그인 시도로 감지되었습니다.')
            else:
                info(self.parent.log_browser, f'로그인에 성공했습니다. ID : {self.login_id}')
                is_login = True
        else:  # 이미 로그인된 상태
            info(self.parent.log_browser, f'로그인에 성공했습니다. ID : {self.login_id}')
            is_login = True

        return is_login

    def get_login_input(self, retries):
        inputs = None
        while retries > 0:
            try:
                inputs = self.parent.browser.find_elements(by=By.TAG_NAME, value='input')
                if len(inputs) > 0:
                    retries = 0
            except Exception as e:
                retries -= 1
                sleep(2)
        return inputs
