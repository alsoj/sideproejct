import googleapiclient.discovery
import googleapiclient.errors

import pymysql
import config

YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def get_crawling_target():
    con = pymysql.connect(host=config.DATABASE_CONFIG['host'],
                          user=config.DATABASE_CONFIG['user'],
                          password=config.DATABASE_CONFIG['password'],
                          db=config.DATABASE_CONFIG['dbname'],
                          charset='utf8')

    cur = con.cursor()
    sql = "SELECT content_url FROM tb_content_keyword"
    cur.execute(sql)
    rows = cur.fetchall()
    return rows


def get_youtube_info():
    youtube = googleapiclient.discovery.build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,developerKey=config.YOUTUBE_API_CONFIG['DEVELOPER_KEY'])

    request = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        id="tQ19OKaMNBo"
    )
    response = request.execute()
    return response


if __name__ == "__main__":
    print("crawl_youtube.py 실행")
    # 대상 조회(DB)
    test = get_crawling_target()
    print(test)

    # 크롤링 진행

    # 대상 업데이트(DB)
