from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

import psycopg2
import datetime
import crawl_config

# 전역변수 세팅
BASE_URL = 'http://10.217.58.126:18883/news/?menu=1&menuid=44&action=index'

def delete_news():
  """
    DB 삭제 - 당일자 데이터 삭제 후 재크롤링
    """
  sql = """DELETE FROM tb_crawling_news_intrf
            WHERE reg_dt = to_char(now(), 'YYYYMMDD')
         """
  conn = None

  try:
    conn = psycopg2.connect(host=crawl_config.DATABASE_CONFIG['host'],
                            dbname=crawl_config.DATABASE_CONFIG['dbname'],
                            user=crawl_config.DATABASE_CONFIG['user'],
                            password=crawl_config.DATABASE_CONFIG['password'],
                            port=crawl_config.DATABASE_CONFIG['port'])
    cur = conn.cursor()

    cur.execute(sql)
    conn.commit()
    cur.close()

  except (Exception, psycopg2.DatabaseError) as error:
    print(error)
  finally:
    if conn is not None:
      conn.close()

def insert_news(params):
  """
  DB 입력
  :param params: 입력 파라미터
  """
  sql = """INSERT INTO tb_crawling_news_intrf(id, title, contents, gb, reg_dt, url, interface_dt)
           VALUES((select coalesce(max(id),0)+1 from tb_crawling_news_intrf), %s, %s, %s, %s, %s, now());"""
  conn = None

  try:
    conn = psycopg2.connect(host=crawl_config.DATABASE_CONFIG['host'],
                            dbname=crawl_config.DATABASE_CONFIG['dbname'],
                            user=crawl_config.DATABASE_CONFIG['user'],
                            password=crawl_config.DATABASE_CONFIG['password'],
                            port=crawl_config.DATABASE_CONFIG['port'])

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
  browser = webdriver.Chrome(executable_path='/interface/crawler/chromedriver', options=options)
  return browser

def get_today():
  """
  오늘 날짜 추출
  :return: 오늘 날짜(YYYYMMDD)
  """
  return datetime.datetime.now().strftime('%Y%m%d')

def get_crawl_target(browser, today):
  """
  크롤링 대상 기사 url 추출
  :param browser: 크롬 브라우저
  :param today: 오늘 날짜(크롤링 대상)
  :return crawl_list : 추출 대상 url
  """
  browser.get(BASE_URL)
  table = browser.find_element(by=By.XPATH,
                               value='/html/body/table/tbody/tr[1]/td[2]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[2]/td[1]/table[2]/tbody/tr[2]/td/table/tbody')
  rows = table.find_elements(by=By.TAG_NAME, value='tr')
  crawl_list = []

  for row in rows:
    tds = row.find_elements(by=By.TAG_NAME, value='td')
    tds.reverse()  # 날짜부터 확인 가능하도록

    isToday = False
    for td in tds:
      if today == td.text.replace("[", "").replace("]", "").replace("/", "").strip():
        isToday = True

      a_tag = td.find_elements(by=By.TAG_NAME, value='a')
      if isToday and len(a_tag) > 0:
        crawl_list.append(a_tag[0].get_attribute('href'))

  return crawl_list

def crawl_detail_page(browser, crawl_target):
  """
  상세 페이지 크롤링
  :param browser: 크롬 브라우저
  :param browser: 크롤링 대상 url
  """
  browser.get(crawl_target)
  title = browser.find_element(by=By.CLASS_NAME, value='view_ltit').text
  contents = browser.find_element(by=By.ID, value='ContentsLayertext').text
  url = browser.current_url
  today = get_today()

  insert_news([title, contents, 'news', today, url])

if __name__ == "__main__":
  print("crawl_news.py 실행")
  browser = execute_browser()

  try:
    delete_news()  # 당일자 데이터 삭제 후 크롤링 진행

    today = get_today()
    crawl_list = get_crawl_target(browser, today)

    for crawl_target in crawl_list:
      crawl_detail_page(browser, crawl_target)

  except Exception as e:
    print("crawl_news.py 오류")
    print(e)
  finally:
    browser.quit()
    print("crawl_news.py 종료")