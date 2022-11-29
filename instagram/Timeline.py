from time import sleep

from PyQt6.QtCore import QThread

import Common
from Common import get_datetime
import requests

class TimelineWorker(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def run(self):
        try:
            for user_id in self.parent.recent_user_id_list:
                self.parent.recent_list.append(get_timeline(self.parent.browser, user_id))
            self.parent.callback()
        except Exception as e:
            Common.error(self.parent.log_browser, f"Timeline Run 실행 중 오류 메시지 : {str(e)}")

# 댓글 추출
def get_timeline(browser, user_id):
    timeline_url = f'https://www.instagram.com/{user_id}'
    api_url = f'https://www.instagram.com/api/v1/feed/user/{user_id}/username/?count=12'
    browser.get(timeline_url)
    sleep(3)
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
        if len(recent_list) < 12:
            username = item['user']['username']
            taken_at = get_datetime(item['taken_at'])
            code = item['code']
            like_count = item['like_count']
            comment_count = item['comment_count']
            recent_list.append([username, taken_at, code, like_count, comment_count])

    return recent_list