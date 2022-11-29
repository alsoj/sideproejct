from time import sleep

from PyQt6.QtCore import QThread
import json

from selenium.webdriver.common.by import By
import Config
from Common import get_datetime
import Common

class CommentWorker(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def run(self):
        try:
            for short_code in self.parent.comment_short_code_list:
                self.parent.comment_list.append(get_comments(self.parent.browser, short_code))
            self.parent.callback()
        except Exception as e:
            Common.error(self.parent.log_browser, f"Comment Run 실행 중 오류 메시지 : {str(e)}")

# 댓글 추출
def get_comments(browser, short_code):
    end_cursor = ''
    variables = {'shortcode': short_code, 'first': 50, 'after': end_cursor}
    has_next_page = True
    rownum = 0
    comment_list = []

    while has_next_page:
        variables['after'] = end_cursor
        json_variables = str(json.dumps(variables))
        url = f'{Config.COMMENT_URL}&variables={json_variables}'

        browser.get(url)
        sleep(3)

        content = browser.find_element(by=By.TAG_NAME, value='pre').text
        data = json.loads(content)

        if 'data' in data:
            has_next_page = data['data']['shortcode_media']['edge_media_to_parent_comment']['page_info']['has_next_page']
            end_cursor = data['data']['shortcode_media']['edge_media_to_parent_comment']['page_info']['end_cursor']
            comments = data['data']['shortcode_media']['edge_media_to_parent_comment']['edges']

            for comment in comments:
                rownum += 1
                username = comment['node']['owner']['username']
                comment_text = comment['node']['text']
                created_at = get_datetime(comment['node']['created_at'])
                comment_list.append([short_code, rownum, 1, username, comment_text, created_at])
                co_comments = comment['node']['edge_threaded_comments']['edges']

                for co_comment in co_comments:  # 대댓글
                    username = co_comment['node']['owner']['username']
                    comment_text = co_comment['node']['text']
                    created_at = get_datetime(co_comment['node']['created_at'])
                    comment_list.append([short_code, rownum, 2, username, comment_text, created_at])

        else:
            has_next_page = False

    return comment_list