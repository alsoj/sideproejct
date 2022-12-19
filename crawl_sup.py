import requests
import datetime
from itertools import product
import platform
import psycopg2
import crawl_config

from bs4 import BeautifulSoup

KEYWORD_LIST = ['정책','창업','대출']
TAB_LIST = ['supportmeasures','businessinfo','notice']  #지원시책, 사업정보, 알림정보
CRAWL_LIST = list(product(KEYWORD_LIST, TAB_LIST))
category = {
    '정책': 'policy',
    '창업': 'startup',
    '대출': 'loans'
}

if 'macOS' in platform.platform():
    BASE_URL = 'https://www.sbiz.or.kr/'  # 로컬
else:
    BASE_URL = 'http://211.252.121.132:18882/'  # 운영
    # BASE_URL = 'https://www.sbiz.or.kr/'  # 개발
SEARCH_URL = BASE_URL + 'sup/search/Search.do'

def get_max_date():
    """
    기존 크롤링 데이터 중 max date 추출
    :return:
    """
    sql = """
            select MAX(reg_dt) 
            from tb_crawling_sup_intrf;
            """
    conn = None
    max_date = 0

    try:
        conn = psycopg2.connect(host=crawl_config.DATABASE_CONFIG['host'],
                                dbname=crawl_config.DATABASE_CONFIG['dbname'],
                                user=crawl_config.DATABASE_CONFIG['user'],
                                password=crawl_config.DATABASE_CONFIG['password'],
                                port=crawl_config.DATABASE_CONFIG['port'])
        cur = conn.cursor()
        cur.execute(sql)
        max_date = cur.fetchone()[0]

    except (Exception, psycopg2.DatabaseError) as error:
        log_error(error)
    finally:
        if conn is not None:
            conn.close()
    return max_date


def insert_sup(params):
    """
    DB 입력
    :param params: 입력 값 리스트
    :return:
    """

    select_sql = """
                SELECT COUNT(*)
                FROM tb_crawling_sup_intrf
                WHERE url = %s
                ;
                """

    insert_sql = """INSERT INTO tb_crawling_sup_intrf(id, title, contents, gb, resource_from, reg_dt, url, interface_dt)
                VALUES((select coalesce(max(id),0)+1 from tb_crawling_sup_intrf), %s, %s, %s, %s, %s, %s, now());"""
    conn = None

    try:
        conn = psycopg2.connect(host=crawl_config.DATABASE_CONFIG['host'],
                                dbname=crawl_config.DATABASE_CONFIG['dbname'],
                                user=crawl_config.DATABASE_CONFIG['user'],
                                password=crawl_config.DATABASE_CONFIG['password'],
                                port=crawl_config.DATABASE_CONFIG['port'])
        cur = conn.cursor()
        cur.execute(select_sql, [params[-1]])
        count = cur.fetchone()[0]

        if count > 0:
            log_info("already data exists(pass) : " + params[-1])
        else:
            log_info("new data(insert) : " + params[-1])
            cur.execute(insert_sql, params)

        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        log_error("insert_sup() ERROR : " + str(error))
    finally:
        if conn is not None:
            conn.close()


def search_tab(keyword, tab, start_date):
    temp_row = []
    today = datetime.datetime.now().strftime("%Y.%m.%d")
    data = {
        'startCount': 0,
        'sort': 'DATE/DESC',
        'collection': tab,
        'range': 'A',
        'startDate': start_date,
        'endDate': today,
        'searchField': 'ALL',
        'reQuery': 2,
        'realQuery': keyword,
        'alignment': 'DATE/DESC',
        'area': 'ALL',
        'period': 'A'
        }
    res = requests.post(SEARCH_URL, data=data)
    soup = BeautifulSoup(res.text, 'html.parser')
    business_list = soup.find('div', attrs={"class": "business_list"})

    if business_list is not None:
        page_list = business_list.find_all('div', attrs={"class": "bl_r"})

        for page in page_list:
            a = page.find('a', attrs={"class": "bl_link"})
            source = page.find('span', attrs={"class": "bl_source"}).text.split(':')[1].strip()
            date = page.find('span', attrs={"class": "bl_date"}).text.split(':')[1].strip()
            href = a['href']

            if href.startswith('javascript'):
                url = BASE_URL + href.split('\'')[1]
            else:
                url = BASE_URL + href.split('sbiz.or.kr/')[-1]

            temp_dict = {}
            temp_dict['url'] = url
            temp_dict['source'] = source
            temp_dict['date'] = date
            temp_row.append(temp_dict)
    else:
        log_info(f"no target data. ({category[keyword]}, {tab})")

    return temp_row

def get_detail_info(detail_url, tab):
    title, content = '', ''
    res = requests.get(detail_url)
    soup = BeautifulSoup(res.text, 'html.parser')
    title = soup.find('div', attrs={"class": "fl_l"}).find('p').text
    if tab == 'supportmeasures':
        content = soup.find('div', attrs={"class": "bv_cp"}).text.strip()
    else:
        content = soup.find('div', attrs={"class": "bv_c"}).text.strip()

    return title, content

def log_debug(text):
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [DEBUG] {text}")

def log_info(text):
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO ] {text}")

def log_error(text):
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] {text}")


if __name__ == "__main__":
    log_debug("crawl_sup.py START")
    max_date = get_max_date()
    log_debug("max_date : " +  max_date)

    for task in CRAWL_LIST:
        keyword, tab = task
        log_debug("=================================")
        log_debug("KEYWORD :" + category[keyword] + " | TAB :" + tab)

        target_list = search_tab(keyword, tab, max_date)
        for target in target_list:
            title, content = get_detail_info(target['url'], tab)

            params = [title, content, category[keyword], target['source'], target['date'], target['url']]
            insert_sup(params)

    log_debug("crawl_sup.py FINISH")
