import datetime
import requests
from itertools import product
import psycopg2
import crawl_config
from bs4 import BeautifulSoup

# DB Connection
def get_db_conn():
    conn = psycopg2.connect(host=crawl_config.DATABASE_CONFIG['host'],
                            dbname=crawl_config.DATABASE_CONFIG['dbname'],
                            user=crawl_config.DATABASE_CONFIG['user'],
                            password=crawl_config.DATABASE_CONFIG['password'],
                            port=crawl_config.DATABASE_CONFIG['port'])
    return conn

# 최신일자 조회
def get_max_date():
    sql = """
                select MAX(reg_dt) 
                from tb_crawling_sup_intrf
                ;
                """
    conn = None
    max_date = 0

    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(sql)
        max_date = cur.fetchone()[0]

    except (Exception, psycopg2.DatabaseError) as error:
        log_error(error)
    finally:
        if conn is not None:
            conn.close()
    return max_date

# 크롤링 데이터 입력
def insert_sup(params):

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
        conn = get_db_conn()
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

# 크롤링 로그 입력
def insert_crawl_log(params):

    insert_sql = """
                INSERT INTO tb_crawling_log
                (id, status, reg_dtm, tab, keyword)
                VALUES
                (nextval('seq_crawling_log'), %s, now(), %s, %s)
                ;
                """
    conn = None

    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(insert_sql, params)
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        log_error("insert_crawl_log() ERROR : " + str(error))
    finally:
        if conn is not None:
            conn.close()

def select_insert():

    insert_sql = """
                    INSERT INTO tb_crawling_data (id, title, contents, reg_dt, category, url, crawling_gb, crawling_dt)
                    SELECT 
                        NEXTVAL('crawling_seq'), 
                        title, 
                        contents, 
                        replace(reg_dt, '.','-'), 
                        gb, 
                        replace(url, 'http://211.252.121.132:18882/', 'https://www.sbiz.or.kr/'),
                        '01', 
                        interface_dt 
                    FROM tb_crawling_sup_intrf 
                    WHERE to_char(interface_dt, 'yyyymmdd') = to_char(NOW(), 'yyyymmdd');
                """

    conn = None
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(insert_sql)

        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        log_error("select_insert() ERROR : " + str(error))
    finally:
        if conn is not None:
            conn.close()

# debug 로그
def log_debug(text):
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [DEBUG] {text}")

# info 로그
def log_info(text):
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO ] {text}")

# error 로그
def log_error(text):
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] {text}")

# 날짜 파라미터 변환
def trans_date(max_date):
    return max_date[0:4] + "." + max_date[4:6] + "." + max_date[6:8]

# HTML 태그 제거
def get_text_from_tag(contents):
    return BeautifulSoup(contents, 'html.parser').text.strip().replace(u'\xa0', u'')

# 리스트 조회
def get_list(keyword, section, max_date):
    # search_url = 'https://www.sbiz.or.kr/sup/search/search.do'  # 개발
    search_url = 'http://211.252.121.132:18882/sup/search/search.do'  # 운영

    data = {
        'query': keyword,
        'reQuery': '0',
        'realQuery': '',
        'startCount': '0',
        'collection': section,
        'sort': 'DATE/ASC',
        'startDate': max_date,
        'endDate': '',
        'listCount': '100',
        'searchField': ''
    }
    res = requests.post(search_url, json=data)

    res_json = res.json()
    docs = res_json['collections'][section + '_list']['document']
    return docs

def get_detail(doc_id, section_sn):
    # detail_url = 'https://www.sbiz.or.kr/sup/bbs/getObj.do'  # 개발
    detail_url = 'http://211.252.121.132:18882/sup/bbs/getObj.do'  # 운영

    data = {
        'bbsSn': doc_id,
        'bbsMngSn': section_sn,
        'inqYn': 'N'
    }

    res = requests.post(detail_url, data=data)
    res_json = res.json()

    title = res_json['data']['bbs']['bbsTtl']
    contents = get_text_from_tag(res_json['data']['bbs']['bbsCn'])

    return title, contents


if __name__ == "__main__":
    log_debug("crawl_sup.py START")

    keyword_list = ['정책', '창업', '대출']
    section_list = ['사업정보', '오늘의뉴스', '공지사항']
    query_list = list(product(keyword_list, section_list))
    keyword_category = {
        '정책': 'policy',
        '창업': 'startup',
        '대출': 'loans'
    }

    section_category = {
        '사업정보': 'supportmeasures',
        '오늘의뉴스': 'businessinfo',
        '공지사항': 'notice'
    }

    section_sn = {
        '사업정보': '10',
        '오늘의뉴스': '2',
        '공지사항': '1'
    }

    max_date = get_max_date()
    # max_date = '2023.03.21'
    log_debug(f'max_date : {max_date}')

    for query in query_list:
        try:
            keyword, section = query
            log_debug(keyword + ' / ' + section + ' START')

            # 리스트 조회
            docs_list = get_list(keyword, section_category[section], max_date)

            if len(docs_list) > 0:
                for doc in docs_list:

                    # 상세 조회
                    title, contents = get_detail(doc['DOCID'], section_sn[section])
                    params = [title, contents, keyword_category[keyword], doc['SOURCE_STR'], doc['Date'], doc['URL']]

                    insert_sup(params)
                    log_info('Insert Data : ' + title)

                insert_crawl_log(['S', section_category[section], keyword])  # 크롤링 로그 : 수집 성공
                select_insert()
            else:
                log_info('No Data : ' + keyword + ' / ' + section)
                insert_crawl_log(['N', section_category[section], keyword])  # 크롤링 로그 : 데이터 없음

        except requests.exceptions.RequestException as req_err:
            log_error("requests.exceptions.RequestException ERROR ")
            log_error(str(req_err))
            insert_crawl_log(['F', query[1], query[0]])  # 크롤링 로그 : 커넥션 오류
        except Exception as e:
            log_error("crawl_sup.py ERROR")
            log_error(str(e))
            insert_crawl_log(['C', query[1], query[0]])  # 크롤링 로그 : 자체 오류

    log_debug("crawl_sup.py FINISH")
