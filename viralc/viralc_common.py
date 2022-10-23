import pymysql
import viralc_config

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from seleniumwire import webdriver as webdriver_wire

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By


def get_db_connection():
    """
    MySQL DB connect
    :return: DB connection
    """
    return pymysql.connect(
        host=viralc_config.DATABASE_CONFIG['host'],
        user=viralc_config.DATABASE_CONFIG['user'],
        password=viralc_config.DATABASE_CONFIG['password'],
        db=viralc_config.DATABASE_CONFIG['dbname'],
        charset='utf8')

def get_crawling_target(con, type):
    """
    크롤링 대상 조회
    :param DB Connection
    :param SNS type(Y:유튜브, I:인스타그램, N:네이버)
    :return: 대상 URL 리스트
    """

    param = {'base_url': ''}
    if type == "Y":
        param['base_url'] = viralc_config.BASE_URL['YOUTUBE']
    elif type == "I":
        param['base_url'] = viralc_config.BASE_URL['INSTAGRAM']
    elif type == "N":
        param['base_url'] = viralc_config.BASE_URL['NAVER']

    cur = con.cursor()
    sql = \
        """
        SELECT content_url
        FROM tb_content_keyword
        WHERE content_url LIKE concat(%(base_url)s, '%%');
        """
    cur.execute(sql, param)
    rows = cur.fetchall()

    url_list = []
    for row in rows:
        url_list.append(row[0])
    return url_list


def get_reuslt_dict():
    result = {
        'content_url': '',
        'sns_type': '',
        'empathy': '',
        'comment': '',
        'followers': '',
        'pc_view_cnt': '',
        'mo_view_cnt': ''
    }
    return result


def merge_crawl_result(con, result):
    cur = con.cursor()
    sql = \
        """
        INSERT INTO tb_content_crawling
        (content_url, sns_type, empathy, comment, followers, pc_view_cnt, mo_view_cnt, insert_datetime) 
        VALUES
        (%(content_url)s, %(sns_type)s, %(empathy)s, %(comment)s, %(followers)s, %(pc_view_cnt)s, %(mo_view_cnt)s, now())
        ON DUPLICATE KEY UPDATE
        empathy = %(empathy)s,
        comment = %(comment)s,
        followers = %(followers)s,
        pc_view_cnt = %(pc_view_cnt)s,
        mo_view_cnt = %(mo_view_cnt)s,
        update_datetime = now()
        """

    cur.execute(sql, result)
    con.commit()

def get_content_id(content_url):
    """
    URL에서 각 플랫폼별 content ID 추출
    :param content_url: content 주소
    :return: content ID
    """
    if content_url.strip()[-1] == "/":
        content_url = content_url[:-1]
    return content_url.split("/")[-1]


def get_selenium_wire():
    """
    셀레니움 와이어 실행
    :return: 크롬 브라우저
    """
    options = webdriver_wire.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--single-process")
    options.add_argument("--disable-dev-shm-usage")
    browser = webdriver_wire.Chrome(service=Service(ChromeDriverManager().install()), options=options)  # PROD
    # browser = webdriver_wire.Chrome(executable_path='/Users/alsoj/Workspace/kmong/ipynb/chromedriver_mac', options=options)  # LOCAL
    return browser

def get_selenium():
    """
    셀레니움 실행
    :return: 크롬 브라우저
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--single-process")
    options.add_argument("--disable-dev-shm-usage")
    browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)  # PROD
    # browser = webdriver.Chrome(executable_path='/Users/alsoj/Workspace/kmong/ipynb/chromedriver_mac', options=options)  # LOCAL
    return browser