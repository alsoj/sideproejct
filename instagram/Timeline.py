from time import sleep

from PyQt6.QtCore import QThread

from Common import get_headers, get_app_id, get_datetime, debug, info, error
from datetime import datetime
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
        self.target_date_from = None
        self.target_date_to = None
        self.result_list = []

    def run(self):
        try:
            # 헤더 세팅을 위한 초기 조회
            feed_url = Config.BASE_URL + self.target_id
            self.browser.get(feed_url)
            sleep(3)

            has_next = True
            max_id = None
            self.result_list = []

            while has_next:  # 이후 데이터 있으면 계속
                data = get_timeline(self.browser, self.target_id, max_id)
                max_id, result_list = get_detail_info(data)

                for result in result_list:
                    taken_datetime = datetime.strptime(result['taken_at'], '%Y-%m-%d %H:%M:%S')
                    taken_date = taken_datetime.date()

                    if self.target_date_from <= taken_date <= self.target_date_to:
                        self.result_list.append(result)
                        if len(self.result_list) % 10 == 0:
                            debug(self.log_browser, f"피드 추출 진행 중 : {len(self.result_list)}개 완료")

                # 마지막 데이터로 대상 여부 체크
                last_taken_datetime = datetime.strptime(result_list[-1]['taken_at'], '%Y-%m-%d %H:%M:%S')
                last_taken_date = last_taken_datetime.date()

                if max_id is None or self.target_date_from > last_taken_date:
                    has_next = False
                else:
                    sleep(3)

            self.parent.after_timeline()

        except Exception as e:
            error(self.log_browser, f"Timeline Run 실행 중 오류 메시지 : {str(e)}")
            print(f"Timeline Run 실행 중 오류 메시지 : {str(e)}")

    def set_target_id(self, target_id):
        self.target_id = target_id

    def set_target_date_from(self, date_from):
        self.target_date_from = date_from

    def set_target_date_to(self, date_to):
        self.target_date_to = date_to

# 타임라인 추출
def get_timeline(browser, user_id, max_id):
    try:
        # 헤더 세팅
        headers = get_headers(browser)
        timeline_url = f'https://www.instagram.com/api/v1/feed/user/{user_id}/username/?count=12'

        if max_id is not None:
            timeline_url += f'&max_id={max_id}'

        res = requests.get(timeline_url, headers=headers)
        data = res.json()
    except Exception as e:
        print(f"get_timeline 실행 중 오류 메시지 : {str(e)}")

    return data

def get_detail_info(data):
    try:
        if data['more_available']:
            next_max_id = data['next_max_id']
            # user = data['user']['pk']
        else:
            next_max_id = None

        item_list = data['items']
        result_list = []
        for item in item_list:

            result = {
                'username': item['user']['username'],
                'taken_at': get_datetime(item['taken_at']),
                'code': item['code'],
                'like_count': item['like_count'],
                'comment_count': item['comment_count']
            }

            if item['caption'] is not None and 'text' in item['caption']:
                result['caption'] = item['caption']['text']

            if 'carousel_media' in item:
                result['image_url'] = item['carousel_media'][0]['image_versions2']['candidates'][0]['url']
            else:
                result['image_url'] = item['image_versions2']['candidates'][0]['url']

            result_list.append(result)

    except Exception as e:
        print(f"get_detail_info 실행 중 오류 메시지 : {str(e)}")

    return next_max_id, result_list
