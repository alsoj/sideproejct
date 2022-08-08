import sys
from PyQt6.QtWidgets import *
from PyQt6 import uic

# 어플리케이션 패키지
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

import requests
from bs4 import BeautifulSoup

from openpyxl import Workbook, load_workbook
from openpyxl.drawing.image import Image

import datetime
from time import sleep

import PIL
import io
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 전역변수 - 파일 관련
FILE_PATH = './output/'
FILE_SUFFIX = '.xlsx'
FILE_NAME = ''

ROOT_URL = ''
MEDIA_NAME = ''
AD_INFO_LIST = []
AD_INFO_SET = set()
LANDING_INFO_SET = set()

form_class = uic.loadUiType("ad_crawler.ui")[0]

class AdCrawler_Window(QMainWindow, form_class):
  def __init__(self):
    super().__init__()
    self.setupUi(self)
    self.btn_start.clicked.connect(self.btn_start_clicked)

  # 로그 삭제
  def clear_log(self):
    self.log_browser.clear()

  # 로그 기록
  def set_log_text(self, text):
    self.log_browser.append(text)
    QApplication.processEvents()

  # 필수 입력 값 체크
  def check_input_valid(self):
    repeat_cnt = self.spin_cnt.value()
    target_url = self.edit_url.text()
    if repeat_cnt <= 0 or len(target_url) == 0:
      self.set_log_text("필수 입력 값이 입력되지 않았습니다.")
      self.set_log_text("사이트 URL과 반복횟수를 확인 해주세요.")
      return False
    else:
      return True

  def btn_start_clicked(self):
    self.clear_log()

    # 필수 입력 값 체크
    if self.check_input_valid() is not True:
      return False

    repeat_cnt = self.spin_cnt.value()
    target_url = self.edit_url.text()
    device_type = "P" if self.radio_pc.isChecked() else "M"

    self.progress_bar.setMaximum(repeat_cnt)
    self.set_log_text("#######################################")
    self.set_log_text(f"크롤링 작업 시작(반복횟수 : {repeat_cnt}회)")
    self.set_log_text("#######################################")

    browser = get_browser(self, device_type)
    browser.get(target_url)

    # 전역 변수 세팅 및 초기화
    set_global_variables(browser, device_type)

    # 엑셀 파일 생성
    create_excel()

    self.set_log_text(f"매체명 : {MEDIA_NAME}")
    self.set_log_text(f"파일명 : {FILE_NAME}")

    for i in range(1, repeat_cnt+1):
      set_crawl_init() # 크롤링 정보 초기화
      crawl_ad(browser) # 크롤링 진행
      for ad_info in AD_INFO_LIST:
        is_exist = check_update_excel(ad_info['url'])

        if is_exist is False:
          landing_info = get_landing_info(browser, ad_info)
          if is_not_dup(landing_info['url']):
            excel_input = get_excel_input(ad_info, landing_info, repeat_cnt)
            insert_excel(excel_input)

      self.set_log_text(f"{i}회 진행 완료")
      self.progress_bar.setValue(i)
      QApplication.processEvents()


# 크롬 브라우저 로드
def get_browser(self, device):
  self.set_log_text("크롬 브라우저 로딩 중 입니다.")

  options = webdriver.ChromeOptions()
  options.add_argument("headless")

  if device == 'M':
    mobile_emulation = {"deviceName": "iPhone X"}
    options.add_experimental_option("mobileEmulation", mobile_emulation)

  browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
  browser.maximize_window()

  self.set_log_text("크롬 브라우저 로딩 완료 되었습니다.")
  return browser

# 브라우저 Tab close
def close_new_tabs(browser):
  tabs = browser.window_handles
  while len(tabs) != 1:
    browser.switch_to.window(tabs[1])
    browser.close()
    tabs = browser.window_handles
  browser.switch_to.window(tabs[0])

# 전역변수 세팅 및 초기화
def set_global_variables(browser, device):
  global ROOT_URL
  ROOT_URL = get_root_url(browser)
  global MEDIA_NAME
  MEDIA_NAME = get_media_name(browser)

  if device == "P":
    device_type = "PC"
  else:
    device_type = "MOBILE"

  global FILE_NAME
  FILE_NAME = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + f"_{MEDIA_NAME}_{device_type}" + FILE_SUFFIX

def set_crawl_init():
  global AD_INFO_LIST
  AD_INFO_LIST = []
  global AD_INFO_SET
  AD_INFO_SET = set()
  global LANDING_INFO_SET
  LANDING_INFO_SET = set()

# 엑셀 파일 생성
def create_excel():
  wb = Workbook()
  ws = wb.active

  sub = ['매체','기기','썸네일','텍스트','새로고침','노출','타이틀','광고URL','랜딩페이지URL']
  for kwd, j in zip(sub, list(range(1, len(sub) + 1))):
    ws.cell(row=1, column=j).value = kwd

  ws.column_dimensions['C'].width = 50
  ws.column_dimensions['D'].width = 20
  ws.column_dimensions['G'].width = 20
  ws.column_dimensions['H'].width = 50
  ws.column_dimensions['I'].width = 50

  wb.save(FILE_PATH + FILE_NAME)

# 엑셀 파일 광고 존재 여부 확인 후 업데이트
def check_update_excel(ad_url):
  wb = load_workbook(FILE_PATH + FILE_NAME, data_only=True)
  ws = wb.active

  for index, row in enumerate(ws.rows, start=1):
    if ad_url == row[7].value:
      ws.cell(row=index, column=6).value = row[5].value + 1
      wb.save(FILE_PATH + FILE_NAME)
      return True
  return False

# 엑셀 파일 insert (존재 하지 않는 경우)
def insert_excel(excel_input):
  wb = load_workbook(FILE_PATH + FILE_NAME, data_only=True)
  ws = wb.active

  rownum = ws.max_row+1
  ws.row_dimensions[rownum].height = 70
  ws['A'+str(rownum)] = excel_input['media']
  ws['B'+str(rownum)] = excel_input['device']
  image = excel_input['thumb']
  if type(image) != str:
    image.height = 85
    ws.add_image(image, 'C'+str(rownum))
  else:
    ws['C'+str(rownum)] = image
  ws['D'+str(rownum)] = excel_input['text']
  ws['E'+str(rownum)] = excel_input['repeat_cnt']
  ws['F'+str(rownum)] = excel_input['ad_cnt']
  ws['G'+str(rownum)] = excel_input['langding_title']
  ws['H'+str(rownum)] = excel_input['ad_url']
  ws['I'+str(rownum)] = excel_input['landing_url']

  wb.save(FILE_PATH + FILE_NAME)

# 메인 URL 추출
def get_root_url(browser):
  return browser.current_url.split('/')[2]

# 매체 명 추출
def get_media_name(browser):
  root_url = browser.current_url.split('/')[2]
  media_name = root_url.replace("www.", "")
  media_name = media_name.replace(".com", "")
  media_name = media_name.replace(".co.kr", "")
  media_name = media_name.replace(".kr", "")
  media_name = media_name.replace(".net", "")
  media_name = media_name.replace("m.", "")
  media_name = media_name.replace("mobile.", "")

  return media_name

# 광고 여부 판단
def isAd(href):
  if href is None:
    return False
  elif ROOT_URL in href:
    return False
  elif 'ad' in href:
    if 'whythisad' in href \
      or 'adsense/support' in href \
      or 'reader' in href \
      or 'header' in href:
      return False
    else:
      return True
  elif 'javascript' in href \
    or MEDIA_NAME in href \
    or 'youtube' in href \
    or 'weather' in href \
    or 'facebook' in href \
    or 'twitter' in href \
    or 'newsstand.naver' in href \
    or 'media.naver' in href:
    return False
  else:
    return True

# 광고 정보 추출(from a 태그)
def get_a_info(a_tag):
  ad_info = {}
  text = ''
  image = ''
  url = ''

  try:
    text = a_tag.text
    url = a_tag.get_attribute('href')
    images = a_tag.find_elements(by=By.TAG_NAME, value='img')
    if len(images) > 0:
      image = images[0].get_attribute('src')

  except Exception as e:
    pass

  finally:
    ad_info['text'] = text
    ad_info['image'] = image
    ad_info['url'] = url
    return ad_info

# 랜딩 페이지 정보 추출(from ad_info)
def get_landing_info(browser, ad_info):
  landing_info = {}
  landing_title = ''
  landing_url = ''

  try:
    # res = requests.get(ad_info['url'])
    # soup = BeautifulSoup(res.content, "html.parser")
    # landing_title = soup.find("title").get_text()
    # landing_url = res.url
    browser.switch_to.new_window('tab')
    browser.get(ad_info['url'])
    landing_title = browser.title
    landing_url = browser.current_url
    close_new_tabs(browser)

  except Exception as e:
    pass

  finally:
    landing_info['title'] = landing_title
    landing_info['url'] = landing_url

  return landing_info

# 이미지 추출
def get_image(image_url):
  img = ''
  try:
    if len(image_url) > 0:
      headers = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
      http = urllib3.PoolManager()
      r = http.request('GET', image_url, headers=headers)
      image_file = io.BytesIO(r.data)
      img = Image(image_file)
  except Exception as e:
    pass

  finally:
    return img

# 페이지에 존재하는 모든 광고 수집
def crawl_ad(browser):
  try:
    # 해당 iframe에서 광고 추출
    a_tags = browser.find_elements(by=By.TAG_NAME, value='a')

    for a_tag in a_tags:
      if isAd(a_tag.get_attribute('href')):
        ad_info = get_a_info(a_tag)
        set_ad_info(ad_info)

    # 하위 iframe 조회 및 step into
    iframes = browser.find_elements(by=By.TAG_NAME, value='iframe')

    # 브라우저에 iframe이 있는 경우 순서대로 iframe으로 in
    if len(iframes) > 0:
      for i in range(len(iframes)):
        browser.switch_to.frame(i)  # iframe으로 IN
        crawl_ad(browser)
        browser.switch_to.parent_frame()  # iframe에서 OUT

  except Exception as e:
    print(str(e)[0:30])
    pass

# ad info 세팅
def set_ad_info(ad_info):
  global AD_INFO_SET
  if (len(ad_info['text']) > 0 or len(ad_info['image']) > 0) and ad_info['url'] not in AD_INFO_SET:
    global AD_INFO_LIST
    AD_INFO_LIST.append(ad_info)
    AD_INFO_SET.add(ad_info['url'])

# 엑셀 입력 값 세팅
def get_excel_input(ad_info, landing_info, repeat_cnt):
  excel_input = {}
  excel_input['media'] = MEDIA_NAME
  excel_input['device'] = 'PC'
  excel_input['thumb'] = get_image(ad_info['image'])
  excel_input['text'] = ad_info['text']
  excel_input['repeat_cnt'] = repeat_cnt
  excel_input['ad_cnt'] = 1
  excel_input['langding_title'] = landing_info['title']
  excel_input['ad_url'] = ad_info['url']
  excel_input['landing_url'] = landing_info['url']
  return excel_input

# 랜딩 페이지 기 등록 여부 확인
def is_not_dup(landing_url):
  global LANDING_INFO_SET
  if landing_url not in LANDING_INFO_SET:
    LANDING_INFO_SET.add(landing_url)
    return True
  else:
    return False


if __name__ == "__main__":
  app = QApplication(sys.argv)
  AdCrawler = AdCrawler_Window()
  AdCrawler.show()
  app.exec()