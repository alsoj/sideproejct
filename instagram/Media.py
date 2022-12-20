from time import sleep

from PyQt6.QtCore import QThread

import Common

from Common import get_datetime
import requests

class MediaWorker(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def run(self):
        try:
            for target_short_code in self.parent.target_short_code_list:
                try:
                    self.parent.target_list.extend(get_media(self.parent.browser, target_short_code))
                except Exception as e:
                    Common.error(self.parent.log_browser, f"Media Run 실행 중 오류 대상 : {target_short_code}")
                    Common.error(self.parent.log_browser, f"Media Run 실행 중 오류 메시지 : {str(e)}")
                    continue

            self.parent.callback()
        except Exception as e:
            Common.error(self.parent.log_browser, f"Media Run 실행 중 오류 메시지 : {str(e)}")

# 좋아요 수, 댓글 수 추출
def get_media(browser, short_code):
    media_url = f'https://www.instagram.com/p/{short_code}/'

    browser.get(media_url)
    sleep(3)
    res = browser.page_source
    app_id = Common.get_app_id(res)
    media_id = Common.get_media_id(res)
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

    api_url = f'https://www.instagram.com/api/v1/media/{media_id}/info/'
    res = requests.get(api_url, headers=headers)
    data = res.json()
    item_list = data['items']
    target_list = []
    for item in item_list:
        username = item['user']['username']
        taken_at = get_datetime(item['taken_at'])
        code = item['code']
        like_count = item['like_count']
        comment_count = item['comment_count']
        target_list.append([username, taken_at, code, like_count, comment_count])

    return target_list