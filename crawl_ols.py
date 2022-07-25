from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

import psycopg2
from itertools import product
from time import sleep

# 전역변수 세팅
BASE_URL = 'https://ols.sbiz.or.kr/ols/man/SMAN051M/page.do'
DETAIL_URL = 'https://ols.sbiz.or.kr/ols/man/SMAN052M/page.do?bltwtrSeq='
category = {
    '서비스안내' : 'service'
   ,'대출정보' : 'loans'
   ,'기타' : 'etc'
}


def insert_ols(params):
  """
  DB 입력
  :param params: 크롤링 파라미터
  :return:
  """
  sql = """INSERT INTO tb_crawling_ols_intrf(id, title, gb, reg_dt, contents, view_cnt, url, interface_dt)
           VALUES(%s, %s, %s, %s, %s, %s, %s, now());"""
  conn = None

  try:
    conn = psycopg2.connect(host='58.120.227.138', dbname='kt_jalnagage', user='postgres', password='Wjdrlwjd1!', port=5432)
    cur = conn.cursor()

    cur.execute(sql, params)
    conn.commit()
    cur.close()

  except (Exception, psycopg2.DatabaseError) as error:
    print(error)
  finally:
    if conn is not None:
      conn.close()

def execute_browser():
  """
  크롬 브라우저 실행
  :return: 크롬 브라우저
  """
  options = webdriver.ChromeOptions()
  options.add_argument("--headless")
  options.add_argument("--no-sandbox")
  options.add_argument("--disable-gpu")
  options.add_argument("--single-process")
  options.add_argument("--disable-dev-shm-usage")
  browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
  return browser

def get_recent_id(browser):
  """
  최신 게시글 ID 추출
  :param browser: 크롬 브라우저
  :return: 
  """
  browser.get(BASE_URL)
  return int(browser.find_element(by=By.CLASS_NAME, value='nt_01').text)

def get_max_id():
  """
  기존 크롤링 데이터 중 max ID 추출
  :return: 
  """
  sql = """
          select COALESCE(MAX(ID),0) 
          from tb_crawling_ols_intrf;
       """
  conn = None
  max_id = 0

  try:
    conn = psycopg2.connect(host='58.120.227.138', dbname='kt_jalnagage', user='postgres', password='Wjdrlwjd1!', port=5432)
    cur = conn.cursor()

    cur.execute(sql)
    max_id = cur.fetchone()[0]


  except (Exception, psycopg2.DatabaseError) as error:
    print(error)
  finally:
    if conn is not None:
      conn.close()

  return max_id

def crawl_detail_page(browser, max_id, recent_id) :
  for i in range(max_id + 1, recent_id + 1):
    try:
      title = ''
      gb = ''
      reg_dt = ''
      view_cnt = ''
      content = ''
      url = DETAIL_URL + str(i)
      browser.get(url)

      detail = browser.find_element(by=By.CLASS_NAME, value='board_view')
      title = detail.find_element(by=By.CLASS_NAME, value='fl_l').text

      detail_infos = detail.find_element(by=By.CLASS_NAME, value='bvt_class').find_elements(by=By.TAG_NAME, value='li')
      for detail_info in detail_infos:
        key = detail_info.text
        value = detail_info.text.split(':')[-1]
        if '구분' in key:
          gb = category[value]
        elif '등록일' in key:
          reg_dt = value
        elif '조회수' in key:
          view_cnt = value

      content = detail.find_element(by=By.ID, value='cntnDiv').text
      insert_ols([str(i), title, gb, reg_dt, content, view_cnt, url])

    except Exception as e:
      print('없는 페이지 pass' + str(i))
      continue

if __name__ == "__main__":
  print("crawl_ols.py 실행")
  browser = execute_browser()

  try:
    recent_id = get_recent_id(browser)
    max_id = get_max_id()
    crawl_detail_page(browser, max_id, recent_id)

  except Exception as e:
    print("crawl_ols.py 오류")
    print(e)
  finally:
    browser.quit()
    print("crawl_ols.py 종료")