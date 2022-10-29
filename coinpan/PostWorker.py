import re

from PyQt6.QtCore import QThread

from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep

import Config

class PostWorker(QThread):
    """
    게시글 크롤링 쓰레드
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.method = None

    def run(self):
        if self.method == "execute_browser":
            self.execute_browser()
        elif self.method == "crawl_past":
            self.crawl_past()
        elif self.method == "crawl_recent":
            self.crawl_recent()

    def set_function(self, method):
        self.method = method

    def execute_browser(self):
        self.parent.info("크롬 브라우저가 실행됩니다. 크롤링 전 로그인을 진행하시기 바랍니다.")
        self.browser = webdriver.Chrome(executable_path='/ipynb/chromedriver_mac')
        self.browser.get(Config.LOGIN_URL)

    def crawl_past(self):
        self.parent.debug("과거 순으로 게시글 크롤링 시작")
        self.parent.click_start()
        for i in range(5):
            sleep(1)
        self.parent.click_stop()
        self.parent.debug("과거 순으로 게시글 크롤링 종료")

    def crawl_recent(self):
        self.parent.debug("최신 순으로 게시글 크롤링 시작")
        self.parent.click_start()
        self.go_to_page10() # 10 페이지로 이동

        recent_no = 0
        while True:
            recent_no = self.go_to_next_post(recent_no)
            detail = self.crawl_detail()
            print(detail)

            if recent_no < 0:
                break

        # self.parent.debug(detail)
        self.parent.click_stop()
        self.parent.debug("최신 순으로 게시글 크롤링 종료")

    def go_to_page10(self):
        self.browser.get(Config.BOARD_URL)
        pagination = self.browser.find_element(by=By.CLASS_NAME, value='pagination')
        lis = pagination.find_elements(by=By.TAG_NAME, value='li')
        for li in lis:
            a = li.find_element(by=By.TAG_NAME, value='a')
            if '10' in a.get_attribute('href'):
                a.click()
                break

    def go_to_next_post(self, recent_no):
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

    def crawl_detail(self):
        """
        게시글 상세 페이지 추출
        :return: 제목, 닉네임, 레벨, 추천, 비추천, 댓글, 조회수, 등록일, 본문, 이미지(리스트), 댓글
        """
        detail = []
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
        images_list = []
        for image in images:
            images_list.append(image.get_attribute('src'))
        detail.append(images_list)

        # 댓글 추출
        comment = self.browser.find_element(by=By.ID, value='comment')
        lis = comment.find_elements(by=By.TAG_NAME, value='li')
        comments = ''
        for i, li in enumerate(lis):
            nickname_info = li.find_element(by=By.CLASS_NAME, value='nick_name')
            img = nickname_info.find_element(by=By.TAG_NAME, value='img')
            level = img.get_attribute('alt')
            nickname = nickname_info.text
            comments += nickname.replace("|","").replace("\n","") + level + li.find_element(by=By.CLASS_NAME, value='contents_bar').text + "\n"
        detail.append(comments)

        return detail