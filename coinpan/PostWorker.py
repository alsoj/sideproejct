import re

from PyQt6.QtCore import QThread

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchWindowException

import requests
from io import BytesIO
from PIL import Image

import Config

class PostWorker(QThread):
    """
    게시글 크롤링 쓰레드
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.method = None
        self.running = True
        self.browser = None

    def run(self):
        try:
            if self.method == "execute_browser":
                self.execute_browser()
            elif self.method == "crawl_past":
                self.crawl_past()
            elif self.method == "crawl_recent":
                self.crawl_recent()
        except NoSuchWindowException as e:
            self.browser = None
            self.parent.error("크롬 브라우저를 실행하여 로그인을 먼저 진행해주세요.")
            self.parent.btn_start.setEnabled(True)
            self.parent.btn_stop.setEnabled(False)

    def set_function(self, method):
        self.method = method

    def execute_browser(self):
        self.parent.info("크롬 브라우저가 실행됩니다. 크롤링 전 로그인을 진행하시기 바랍니다.")
        self.browser = webdriver.Chrome(executable_path=Config.CHROME_DIR)
        # self.browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        self.browser.get(Config.LOGIN_URL)

    def crawl_past(self):
        self.parent.debug("과거 순으로 게시글 크롤링 시작")
        self.parent.click_start()
        target_page = self.parent.edit_page.text().strip()
        self.go_to_input_page(target_page)  # 원하는 페이지로 이동

        recent_no, current_page = 0, target_page
        while self.running:
            has_next, recent_no = self.go_to_next_post(recent_no)  # 해당 페이지 내에서 끝까지 크롤링을 완료하면 -1을 반환
            if has_next is False:
                current_page = self.go_to_next_page()  # 다음(과거순) 페이지로 이동
                self.parent.debug(f"{current_page} 페이지 크롤링 진행 중")
            else:
                try:
                    detail = self.crawl_detail()
                    self.parent.ws.append(detail)
                except Exception as e:
                    self.error(str(e))
                finally:
                    self.parent.wb.save(self.parent.filename)

        self.parent.click_stop()
        self.parent.debug("과거 순으로 게시글 크롤링 종료")

    def crawl_recent(self):
        self.parent.debug("최신 순으로 게시글 크롤링 시작")
        self.parent.click_start()
        target_page = self.parent.edit_page.text().strip()
        self.go_to_input_page(target_page)  # 원하는 페이지로 이동

        recent_no, current_page = 0, target_page
        while self.running:
            recent_no = self.go_to_prev_post(recent_no)  # 해당 페이지 내에서 끝까지 크롤링을 완료하면 -1을 반환
            if recent_no < 0:
                if current_page != 1:
                    current_page = self.go_to_prev_page()  # 이전(최신순) 페이지로 이동
                    self.parent.debug(f"{current_page} 페이지 크롤링 진행 중")
                else:
                    break
            else:
                try:
                    detail = self.crawl_detail()
                    self.parent.ws.append(detail)
                except Exception as e:
                    self.error(str(e))
                finally:
                    self.parent.wb.save(self.parent.filename)

        self.parent.click_stop()
        self.parent.debug("최신 순으로 게시글 크롤링 종료")

    def go_to_input_page(self, page_no):
        self.browser.get(Config.BOARD_URL)
        while True:
            if int(page_no) > self.get_max_page():
                self.go_to_next_10_page()
            else:
                self.go_to_page_in_10_page(page_no)
                break

    def go_to_page_in_10_page(self, page_no):
        pagination = self.browser.find_element(by=By.CLASS_NAME, value='pagination')
        lis = pagination.find_elements(by=By.TAG_NAME, value='li')
        for li in lis:
            a = li.find_element(by=By.TAG_NAME, value='a')
            if str(page_no) in a.get_attribute('href'):
                a.click()
                break

    def get_max_page(self):
        pagination = self.browser.find_element(by=By.CLASS_NAME, value='pagination')
        lis = pagination.find_elements(by=By.TAG_NAME, value='li')
        for li in reversed(lis):
            if li.get_attribute('class') != 'fn_rarrow':
                return int(li.text)

    def go_to_next_10_page(self):
        pagination = self.browser.find_element(by=By.CLASS_NAME, value='pagination')
        lis = pagination.find_elements(by=By.TAG_NAME, value='li')
        for li in reversed(lis):
            li.find_element(by=By.TAG_NAME, value='a').click()
            break

    def go_to_prev_page(self):
        pagination = self.browser.find_element(by=By.CLASS_NAME, value='pagination')
        lis = pagination.find_elements(by=By.TAG_NAME, value='li')
        is_next = False
        for li in reversed(lis):
            if is_next:
                current_page = li.text.strip()
                li.find_element(by=By.TAG_NAME, value='a').click()
                return int(current_page)
            if li.get_attribute('class') == 'active':
                is_next = True

    def go_to_next_page(self):
        pagination = self.browser.find_element(by=By.CLASS_NAME, value='pagination')
        lis = pagination.find_elements(by=By.TAG_NAME, value='li')
        is_next = False
        for li in lis:
            if is_next:
                current_page = li.text.strip()
                li.find_element(by=By.TAG_NAME, value='a').click()
                return int(current_page)
            if li.get_attribute('class') == 'active':
                is_next = True

    def go_to_prev_post(self, recent_no):
        board_list = self.browser.find_element(by=By.ID, value='board_list')
        table = board_list.find_element(by=By.TAG_NAME, value='table')
        tbody = table.find_element(by=By.TAG_NAME, value='tbody')
        trs = tbody.find_elements(by=By.TAG_NAME, value='tr')

        for tr in reversed(trs):
            if 'notice' in tr.get_attribute('class'):
                return -1
            else:
                no = tr.find_element(by=By.CLASS_NAME, value='no').text

                if no.isnumeric() and int(no) > recent_no:
                    recent_no = int(no)
                    tr.find_element(by=By.CLASS_NAME, value='title').find_element(by=By.TAG_NAME, value='a').click()
                    return recent_no

    def go_to_next_post(self, recent_no):
        board_list = self.browser.find_element(by=By.ID, value='board_list')
        table = board_list.find_element(by=By.TAG_NAME, value='table')
        tbody = table.find_element(by=By.TAG_NAME, value='tbody')
        trs = tbody.find_elements(by=By.TAG_NAME, value='tr')

        for tr in trs:
            if 'notice' in tr.get_attribute('class'):
                pass
            else:
                no = tr.find_element(by=By.CLASS_NAME, value='no').text

                if recent_no == 0 or (no.isnumeric() and int(no) < recent_no):
                    recent_no = int(no)
                    title = tr.find_element(by=By.CLASS_NAME, value='title')
                    a = title.find_element(by=By.TAG_NAME, value='a')
                    a.send_keys(Keys.ENTER)
                    return True, recent_no
        return False, recent_no

    def crawl_detail(self):
        """
        게시글 상세 페이지 추출
        :return: 제목, 닉네임, 레벨, 추천, 비추천, 댓글, 조회수, 등록일, 본문, 이미지 주소, 댓글
        """
        detail = []
        pk = self.browser.current_url.split("=")[-1]
        detail.append(pk)
        post = self.browser.find_element(by=By.CLASS_NAME, value='board_read')
        detail.append(post.find_element(by=By.CLASS_NAME, value='read_header').text)
        ul = post.find_element(by=By.TAG_NAME, value='ul')
        lis = ul.find_elements(by=By.TAG_NAME, value='li')

        for i, li in enumerate(lis):
            if i == 0:  # 닉네임
                img = li.find_element(by=By.TAG_NAME, value='img')
                level = img.get_attribute('alt')
                detail.append(li.text)
                detail.append(re.sub(r'[^0-9]', '', level))
            else:
                # 추천, 비추천, 댓글, 조회수, 등록일
                detail.append(li.find_element(by=By.TAG_NAME, value='span').text)

        # 본문 추출
        content = post.find_element(by=By.CLASS_NAME, value='xe_content')
        p_tags = content.find_elements(by=By.TAG_NAME, value='p')
        text = ''
        for p in p_tags:
            text += p.text
        detail.append(text)

        # 이미지 추출
        images = content.find_elements(by=By.TAG_NAME, value='img')
        image_urls = ''
        for i, image in enumerate(images):
            try:
                url = image.get_attribute('src')
                image_urls += url + "\n"
                download_img(url, str(pk) + "_" + str(i+1))
            except Exception as e:
                pass
        detail.append(image_urls)

        # 댓글 추출
        comment = self.browser.find_element(by=By.ID, value='comment')
        lis = comment.find_elements(by=By.TAG_NAME, value='li')
        comments = ''
        for i, li in enumerate(lis):
            try:
                nickname_info = li.find_element(by=By.CLASS_NAME, value='nick_name')
                img = nickname_info.find_element(by=By.TAG_NAME, value='img')
                level = img.get_attribute('alt')
                nickname = nickname_info.text.replace("|", "").replace("\n", "")
                comment = li.find_element(by=By.CLASS_NAME, value='contents_bar').text.replace("\n", "")
                comments += nickname + level + " - " + comment + "\n"
            except Exception as e:
                pass
        detail.append(comments)

        return detail

    def resume(self):
        self.running = True

    def stop(self):
        self.running = False

##############################
# Static Method 영역
##############################
def download_img(url, filename):
    res = requests.get(url)
    img = Image.open(BytesIO(res.content))
    img.save(Config.IMAGE_DIR + filename + '.jpeg', 'JPEG')