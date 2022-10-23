import googleapiclient.discovery
import googleapiclient.errors

import pymysql
import viralc_config
from viralc import viralc_common


def merge_crawl_result(con, result):
    cur = con.cursor()
    sql = \
        """
        INSERT INTO tb_content_crawling
        (content_url, sns_type, empathy, comment, followers, pc_view_cnt, insert_datetime) 
        VALUES
        (%(content_url)s, 'Y', %(like_count)s, %(comment_count)s, %(subscriber_count)s, %(view_count)s, now())
        ON DUPLICATE KEY UPDATE
        empathy = %(like_count)s,
        comment = %(comment_count)s,
        followers = %(subscriber_count)s,
        pc_view_cnt = %(view_count)s,
        update_datetime = now()
        """

    cur.execute(sql, result)
    con.commit()

def get_youtube_info(video_id):
    """
    YOUTUBE 정보 조회(API)
    :param: 비디오 ID
    :return: 좋아요, 댓글, 구독자, 조회 수
    """
    youtube = googleapiclient.discovery.build(viralc_config.YOUTUBE_API_CONFIG['NAME'], viralc_config.YOUTUBE_API_CONFIG['VERSION'],
                                              developerKey=viralc_config.YOUTUBE_API_CONFIG['KEY'])

    # 영상 정보 추출
    request = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        id=video_id
    )
    response = request.execute()
    statistics = response['items'][0]['statistics']
    view_count = statistics['viewCount']
    like_count = statistics['likeCount']
    comment_count = statistics['commentCount']

    # 채널 정보 추출
    channel_id = response['items'][0]['snippet']['channelId']
    request = youtube.channels().list(
        part="snippet,contentDetails,statistics",
        id=channel_id
    )
    response = request.execute()
    subscriber_count = response['items'][0]['statistics']['subscriberCount']

    return like_count, comment_count, subscriber_count, view_count


if __name__ == "__main__":
    print("crawl_youtube.py 실행")

    # DB 연결
    con = viralc_common.get_db_connection()

    # 대상 조회(DB)
    url_list = viralc_common.get_crawling_target(con, "Y")

    for url in url_list:
        result = {'content_url': url}
        video_id = viralc_common.get_content_id(url)

        # 크롤링 진행
        like_count, comment_count, subscriber_count, view_count = get_youtube_info(video_id)
        result['like_count'] = like_count
        result['comment_count'] = comment_count
        result['subscriber_count'] = subscriber_count
        result['view_count'] = view_count

        # 대상 업데이트(DB)
        merge_crawl_result(con, result)

    # DB 연결 해제
    con.close()
    print("crawl_youtube.py 종료")
