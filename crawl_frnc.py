from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

import psycopg2
import datetime
from time import sleep
import crawl_config

# 전역변수 세팅
BASE_URL = 'https://franchise.ftc.go.kr'
SEARCH_URL = 'https://franchise.ftc.go.kr/mnu/00013/program/userRqst/list.do'

from enum import Enum
class Category(Enum):
    한식 = ('A01', '외식')
    치킨 = ('A02', '외식')
    기타외식 = ('A03', '외식')
    제과제빵 = ('A04', '외식')
    패스트푸드 = ('A05', '외식')
    분식 = ('A06', '외식')
    피자 = ('A07', '외식')
    커피 = ('A08', '외식')
    아이스크림_빙수 = ('A09', '외식')
    기타외국식 = ('A10', '외식')
    중식 = ('A11', '외식')
    주점 = ('A12', '외식')
    일식 = ('A13', '외식')
    서양식 = ('A14', '외식')
    음료커피외 = ('A15', '외식')
    기타서비스 = ('B01', '서비스')
    이미용 = ('B02', '서비스')
    기타교육 = ('B03', '서비스')
    교육외국어 = ('B04', '서비스')
    스포츠관련 = ('B05', '서비스')
    교육교과 = ('B06', '서비스')
    유아관련교육외 = ('B07', '서비스')
    안경 = ('B08', '서비스')
    숙박 = ('B09', '서비스')
    자동차관련 = ('B10', '서비스')
    반려동물관련 = ('B11', '서비스')
    임대 = ('B12', '서비스')
    인력파견 = ('B13', '서비스')
    세탁 = ('B14', '서비스')
    오락 = ('B15', '서비스')
    부동산중개 = ('B16', '서비스')
    배달 = ('B17', '서비스')
    PC방 = ('B18', '서비스')
    약국 = ('B19', '서비스')
    이사 = ('B20', '서비스')
    운송 = ('B21', '서비스')
    기타도소매 = ('C01', '도소매')
    화장품 = ('C02', '도소매')
    의류_패션 = ('C03', '도소매')
    건강식품 = ('C04', '도소매')
    종합소매점 = ('C05', '도소매')
    편의점 = ('C06', '도소매')
    농수산물 = ('C07', '도소매')

    def __init__(self, code, type):
        self.code = code
        self.type = type

def insert_frnc(params):
    sql = """INSERT INTO tb_crawling_frnc_intrf(id, sub_cd, franchise, education, deposit, etc, interior, interface_dt)
            VALUES(%s, %s, %s, %s, %s, %s, %s, now());"""
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
    browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return browser

def get_category_info(cate):
    try:
        category = Category[cate].code
    except Exception as e:
        category = ''
    return category


def get_list_info(tr):
    tds = tr.find_elements(by=By.TAG_NAME, value='td')
    id = tds[0].text.replace(",", "")
    url = tds[1].find_element(by=By.TAG_NAME, value='a').get_attribute('onclick').split('\'')[1]
    category = get_category_info(tds[6].text.replace(" ", "").replace("(", "").replace(")", "").replace("/", "_"))
    return id, category, url

def get_detail_info(browser):
    fran_fee = ''
    edu_fee = ''
    deposit_fee = ''
    etc_fee = ''
    interior_fee = ''
    box_flops = browser.find_elements(by=By.CLASS_NAME, value='box_flop')
    for box_flop in box_flops:
        if box_flop.find_element(by=By.TAG_NAME, value='h6').text.strip().startswith('가맹점사업자의 부담금'):
            tds = box_flop.find_elements(by=By.TAG_NAME, value='td')
            fran_fee = tds[0].text.replace(",", "")
            edu_fee = tds[1].text.replace(",", "")
            deposit_fee = tds[2].text.replace(",", "")
            etc_fee = tds[3].text.replace(",", "")
            interior_fee = tds[7].text.replace(",", "")

    return fran_fee, edu_fee, deposit_fee, etc_fee, interior_fee


def go_to_next(browser):
    pagination = browser.find_element(by=By.CLASS_NAME, value='paginationList')
    li_tags = pagination.find_elements(by=By.TAG_NAME, value='li')

    goNext = False
    page_num = 99999
    for li_tag in li_tags:
        a_tag = li_tag.find_element(by=By.TAG_NAME, value='a')
        href = a_tag.get_attribute('href')

        if href is None:
            page_num = a_tag.text
            goNext = True
        elif href.endswith(str(page_num)):
            print("마지막 페이지입니다.")
            return False
        elif goNext:
            a_tag.click()
            return True


def get_max_id():
    """
    기존 크롤링 데이터 중 max ID 추출
    :return:
    """
    sql = """
        select COALESCE(MAX(ID),0) 
        from tb_crawling_frnc_intrf;
        """
    conn = None
    max_id = 0

    try:
        conn = psycopg2.connect(host=crawl_config.DATABASE_CONFIG['host'],
                                dbname=crawl_config.DATABASE_CONFIG['dbname'],
                                user=crawl_config.DATABASE_CONFIG['user'],
                                password=crawl_config.DATABASE_CONFIG['password'],
                                port=crawl_config.DATABASE_CONFIG['port'])
        cur = conn.cursor()

        cur.execute(sql)
        max_id = cur.fetchone()[0]

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

    return max_id

if __name__ == "__main__":
    print("crawl_frnc.py 실행")
    browser = execute_browser()
    browser.get(SEARCH_URL)
    goNext = True
    try:
        while(goNext):
            tbody = browser.find_element(by=By.TAG_NAME, value='tbody')
            trs = tbody.find_elements(by=By.TAG_NAME, value='tr')

            hasNew = True
            for tr in trs:
                id, category, detail_url = get_list_info(tr)

                if int(id) > int(get_max_id()):
                    if len(category) > 0:
                        browser.switch_to.new_window('tab')
                        browser.get(BASE_URL + detail_url)
                        fran_fee, edu_fee, deposit_fee, etc_fee, interior_fee = get_detail_info(browser)
                        browser.close()
                        browser.switch_to.window(browser.window_handles[0])
                        if len(fran_fee) + len(edu_fee) + len(deposit_fee) + len(etc_fee) + len(interior_fee) > 0:
                            insert_frnc([id, category, fran_fee, edu_fee, deposit_fee, etc_fee, interior_fee])
                else:
                    hasNew = False
                    break

            if hasNew:
                goNext = go_to_next(browser)
            else :
                goNext = False

    except Exception as e:
        print("crawl_frnc.py 오류")
        print(e)
    finally:
        browser.quit()
        print("crawl_frnc.py 종료")