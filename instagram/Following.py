from time import sleep

from PyQt6.QtCore import QThread
import json

from selenium.webdriver.common.by import By
import unicodedata
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

import Config
import Common

class FollowingWorker(QThread):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def run(self):
        try:
            graphql_endpoint = Config.FOLLOWING_URL + '&variables={}'
            variables = {'id': self.parent.target_pk_id, 'first': 50, 'after': ''}
            url = graphql_endpoint.format(str(json.dumps(variables)))

            sc_rolled = 0
            rownum = 0
            has_next_data = True

            while has_next_data:
                sleep(2)
                self.parent.browser.get(url)
                follow_list = []

                pre = self.parent.browser.find_element(by=By.TAG_NAME, value="pre").text
                data = json.loads(pre)['data']['user']['edge_follow']

                # get followers
                page_info = data['page_info']
                edges = data['edges']
                for user in edges:
                    try:
                        rownum += 1
                        username = ILLEGAL_CHARACTERS_RE.sub(r'', user['node']['username'])
                        fullname = ILLEGAL_CHARACTERS_RE.sub(r'', unicodedata.normalize('NFC', user['node']['full_name']))
                        follow_list.append([username, fullname])

                        if rownum % 100 == 0:
                            Common.debug(self.parent.log_browser, f"팔로잉 추출 진행 중. 건 수 : {str(rownum)}")

                    except Exception as e:
                        pass

                self.parent.save_excel(follow_list)

                has_next_data = page_info['has_next_page']
                if has_next_data:
                    variables['after'] = page_info['end_cursor']
                    url = graphql_endpoint.format(str(json.dumps(variables)))
                    sc_rolled += 1

                    if sc_rolled > 91:
                        Common.info(self.parent.log_browser, f"10분간 휴식. 현재 추출 건 수 : {str(rownum)}")
                        sleep(600)
                        sc_rolled = 0

        except Exception as e:
            Common.error(self.parent.log_browser, f"Following Run 실행 중 오류 메시지 : {e.message}")
        finally:
            self.parent.callback('following')