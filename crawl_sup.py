from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

import psycopg2
from itertools import product
from time import sleep

# 전역변수 세팅
KEYWORD_LIST = ['정책','창업','대출']
TAB_LIST = ['supportmeasures','businessinfo','notice'] #지원시책, 사업정보, 알림정보
URL = 'https://www.sbiz.or.kr/sup/search/Search.do'
TARGET_KEYWORD = ''
TARGET_TAB = ''
CRAWL_LIST = list(product(KEYWORD_LIST, TAB_LIST))
category = {
    '정책' : 'policy'
   ,'창업' : 'startup'
   ,'대출' : 'loans'
}


def insert_sup(params):
  """
  DB 입력
  :param params: 입력 값 리스트
  :return:
  """
  sql = """INSERT INTO tb_crawling_sup_intrf(id, title, contents, gb, resource_from, reg_dt, url, interface_dt)
           VALUES((select coalesce(max(id),0)+1 from tb_crawling_sup_intrf), %s, %s, %s, %s, %s, %s, now());"""
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


def search_keyword(browser, keyword):
  """
  검색어 입력 후 조회
  :param browser: 크롬 브라우저
  :param keyword: 검색어
  :return:
  """
  try:
    input_search = browser.find_element(by=By.ID, value='searchQuery')
    input_search.send_keys(keyword)
    input_search.submit()

  except Exception as e:
    print("search_keyword 실행 중 오류 발생" + str(e))

def select_tab(browser, tab):
  """
  탭 선택
  :param browser: 크롬 브라우저
  :param tab: 선택 탭
  :return:
  """
  try:
    gss_list = browser.find_element(by=By.CLASS_NAME, value='gss_list')
    tab_list = gss_list.find_elements(by=By.TAG_NAME, value='a')
    for selected_tab in tab_list:
      if tab in selected_tab.get_attribute('href'):
        selected_tab.click()
        break

  except Exception as e:
    print("select_tab 실행 중 오류 발생 : " + str(e))

def get_detail_info(browser):
  """
  상세 페이지 조회
  :param browser: 크롬 브라우저 
  :return: 상세 페이지 제목, 상세 페이지 내용
  """
  title = ''
  content = ''

  retries = 3
  while (retries > 0):
    try:
      global TARGET_TAB
      if TARGET_TAB == 'supportmeasures':
        browser.switch_to.window(window_name=browser.window_handles[-1])
        # title = WebDriverWait(browser, 3).until(EC.presence_of_element_located((By.CLASS_NAME, "fl_l"))).find_element(by=By.TAG_NAME, value='p').text
        title = browser.find_element(by=By.CLASS_NAME, value='fl_l').find_element(by=By.TAG_NAME, value='p').text
        content = browser.find_element(by=By.CLASS_NAME, value='bv_cp').text

        browser.close()
        browser.switch_to.window(window_name=browser.window_handles[0])

      elif TARGET_TAB == 'businessinfo':
        popup = browser.find_element(by=By.ID, value='layer_pop')
        # title = WebDriverWait(popup, 3).until(EC.presence_of_element_located((By.CLASS_NAME, "fl_l"))).find_element(by=By.TAG_NAME, value='p').text
        title = popup.find_element(by=By.CLASS_NAME, value='fl_l').find_element(by=By.TAG_NAME, value='p').text
        content = popup.find_element(by=By.CLASS_NAME, value='bv_c').text
        popup.find_element(by=By.CLASS_NAME, value='closeBtn').click()

      elif TARGET_TAB == 'notice':
        browser.switch_to.window(window_name=browser.window_handles[-1])
        # title = WebDriverWait(browser, 3).until(EC.presence_of_element_located((By.CLASS_NAME, "fl_l"))).find_element(by=By.TAG_NAME, value='p').text
        title = browser.find_element(by=By.CLASS_NAME, value='fl_l').find_element(by=By.TAG_NAME, value='p').text
        content = browser.find_element(by=By.CLASS_NAME, value='bv_c').text

        browser.close()
        browser.switch_to.window(window_name=browser.window_handles[0])

      break

    except Exception as e:
      print(e)
      retries = retries - 1
      sleep(3)
      continue

  return title, content

def insert_sup_info(browser):
  """
  상세 페이지 조회
  :param browser: 
  :return: 
  """
  try:
    business_list = browser.find_element(by=By.CLASS_NAME, value='business_list')
    page_list = business_list.find_elements(by=By.CLASS_NAME, value='bl_r')
    for page in page_list:
      temp_list = []
      temp_list.append(page.find_element(by=By.CLASS_NAME, value='bl_source').text.split(':')[1].strip())
      temp_list.append(page.find_element(by=By.CLASS_NAME, value='bl_date').text.split(':')[1].strip())
      url = page.find_element(by=By.TAG_NAME, value='a').get_attribute('href')
      if url.startswith('javascript'):
        temp_list.append('http://www.sbiz.or.kr' + url.split('\'')[1])
      else:
        temp_list.append(url)

      # page.find_element(by=By.TAG_NAME, value='a').click()
      a_tag = page.find_element(by=By.TAG_NAME, value='a')
      browser.execute_script("arguments[0].click();", a_tag)
      sleep(1)
      title, content = get_detail_info(browser)

      temp_list = [title, content, category[TARGET_KEYWORD]] + temp_list
      insert_sup(temp_list)
  except Exception as e:
    print("insert_sup_info 실행 중 오류 발생 : " + str(e))

def go_next_page(browser, keyword):
  """
  해당 검색어에서 다음 페이지 이동
  :param browser: 크롬 브라우저
  :param keyword: 검색어
  :return: 페이지 이동 여부
  """
  try:
    input_search = browser.find_element(by=By.ID, value='searchQuery')
    input_search.send_keys(keyword)

    paging = browser.find_element(by=By.CLASS_NAME, value='paging')
    current_page = paging.find_element(by=By.TAG_NAME, value='strong')
    paging_list = paging.find_elements(by=By.TAG_NAME, value='a')

    next_page = int(current_page.text) + 1

    for page in paging_list:
      if (page.get_attribute('title') == '페이징' and int(page.text.strip()) == next_page) \
          or (page.get_attribute('class') == 'p_next' and page.get_attribute('onclick') is not None):
        page.click()
        return True

    return False
  except Exception as e:
    print("go_next_page 실행 중 오류 발생 :" + str(e))

if __name__ == "__main__":
  print("crawl_sup.py 실행")
  browser = execute_browser()

  try:
    for task in CRAWL_LIST:
      TARGET_KEYWORD, TARGET_TAB = task

      print("검색어:", TARGET_KEYWORD, " | 탭 :",TARGET_TAB)

      browser.get(URL)
      search_keyword(browser, TARGET_KEYWORD)
      select_tab(browser, TARGET_TAB)

      go = True
      while (go):
        try:
          insert_sup_info(browser)
          go = go_next_page(browser, TARGET_KEYWORD)
        except Exception as e:
          print("while 수행 중 오류 발생 : " + str(e))

  except Exception as e:
    print("crawl_sup.py 오류")
    print(e)
  finally:
    browser.quit()
    print("crawl_sup.py 종료")