from time import sleep

from PyQt6.QtCore import QThread

import Common
import json

from selenium.webdriver.common.by import By
import Config
import unicodedata
from openpyxl import load_workbook
from Common import get_datetime
import requests

class TimelineWorker(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def run(self):
        self.parent.recent_list = get_timeline(self.parent.browser, self.parent.recent_user_id)
        self.parent.callback()

# 댓글 추출
def get_timeline(browser, user_id):
    timeline_url = f'https://www.instagram.com/{user_id}'
    api_url = f'https://www.instagram.com/api/v1/feed/user/{user_id}/username/?count=12'
    browser.get(timeline_url)
    res = browser.page_source
    app_id = Common.get_app_id(res)
    csrftoken = browser.get_cookie("csrftoken")['value']

    cookies = browser.get_cookies()
    header_cookie = ''
    for cookie in cookies:
        header_cookie += f"{cookie['name']}={cookie['value']}; "

    # 헤더 세팅
    headers = {}
    headers['referer'] = 'https://www.instagram.com/'
    headers['x-csrftoken'] = csrftoken
    headers['cookie'] = header_cookie
    headers['x-ig-app-id'] = app_id

    res = requests.get(api_url, headers=headers)
    data = res.json()
    item_list = data['items']
    recent_list = []
    for item in item_list:
        taken_at = get_datetime(item['taken_at'])
        code = item['code']
        like_count = item['like_count']
        comment_count = item['comment_count']
        recent_list.append([taken_at, code, like_count, comment_count])

    return recent_list