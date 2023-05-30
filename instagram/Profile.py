from time import sleep

from PyQt6.QtCore import QThread

from Common import get_headers, debug, info, error
import Config
import requests

class ProfileWorker(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.browser = parent.browser
        self.log_browser = parent.log_browser
        self.target_id = None
        self.user_profile = None

    def run(self):
        try:
            self.user_profile = get_profile(self.browser, self.target_id)
            self.parent.after_profile()
        except Exception as e:
            error(self.log_browser, f"Profile Run 실행 중 오류 메시지 : {str(e)}")

    def set_log_browser(self, log_browser):
        self.log_browser = log_browser

    def set_browser(self, browser):
        self.browser = browser

    def set_target_id(self, target_id):
        self.target_id = target_id


# 타임라인 추출
def get_profile(browser, user_id):
    browser.get(Config.BASE_URL + user_id)
    headers = get_headers(browser)

    profile_url = Config.PROFILE_URL + user_id
    res = requests.get(profile_url, headers=headers)
    user_profile = res.json()['data']['user']

    return user_profile
