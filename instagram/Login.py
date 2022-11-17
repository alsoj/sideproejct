from time import sleep

from PyQt6.QtCore import QThread
from selenium.webdriver.common.by import By
import Config

class LoginWorker(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def run(self):
        if self.parent.login_id is None or self.parent.login_pw is None:
            self.parent.error("인스타그램 ID와 PW를 입력해주세요.")
            self.terminate()

        self.parent.browser.get(Config.LOGIN_URL)
        sleep(3)

        if 'accounts' in self.parent.browser.current_url:
            inputs = self.parent.browser.find_elements(by=By.TAG_NAME, value='input')
            inputs[0].clear()
            inputs[1].clear()
            inputs[0].send_keys(self.parent.login_id)
            inputs[1].send_keys(self.parent.login_pw)
            inputs[1].submit()
            sleep(3)

            if '잘못된 비밀번호' in self.parent.browser.page_source:
                self.parent.error('잘못된 비밀번호입니다.')
                self.terminate()
            elif '입력한 사용자 이름' in self.parent.browser.page_source:
                self.parent.error('잘못된 사용자 ID입니다.')
                self.terminate()
            elif '문제가 발생' in self.parent.browser.page_source:
                self.parent.error('일시적인 문제가 발생하였습니다.')
                self.terminate()
            else:
                self.parent.info(f'로그인에 성공했습니다. ID : {self.parent.login_id}')
