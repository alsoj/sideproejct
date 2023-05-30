from time import sleep

from PyQt6.QtCore import QThread

from Common import get_headers, get_app_id, get_datetime, debug, info, error
import Config
import requests

class TimelineWorker(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.browser = parent.browser
        self.log_browser = parent.log_browser
        self.target_id = None
        self.timeline = None

    def run(self):
        try:
            # 헤더 세팅을 위한 초기 조회
            feed_url = Config.BASE_URL + {self.target_id}
            self.browser.get(feed_url)
            sleep(3)

            self.timeline = get_timeline(self.browser, self.target_id)
            self.parent.after_timeline()

        except Exception as e:
            error(self.log_browser, f"Timeline Run 실행 중 오류 메시지 : {str(e)}")

    def set_target_id(self, target_id):
        self.target_id = target_id

# 타임라인 추출
def get_timeline(browser, user_id, max_id):

    # 헤더 세팅
    headers = get_headers(browser)
    timeline_url = f'https://www.instagram.com/api/v1/feed/user/{user_id}/username/?count=12'
    if max_id is not None:
        timeline_url += f'&max_id={max_id}'

    res = requests.get(timeline_url, headers=headers)
    data = res.json()

    if data['more_available'] == True:
        next_max_id = data['next_max_id']
        user = data['user']['pk']
    else:
        next_max_id = None

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