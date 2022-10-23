import googleapiclient.discovery
import googleapiclient.errors

import viralc_config
import viralc_common


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
    print(f"유튜브 크롤링 대상 : {len(url_list)}건")

    for url in url_list:
        result = viralc_common.get_reuslt_dict()
        result['content_url'] = url
        result['sns_type'] = "Y"

        video_id = viralc_common.get_content_id(url)

        # 크롤링 진행
        like_count, comment_count, subscriber_count, view_count = get_youtube_info(video_id)
        result['empathy'] = like_count
        result['comment'] = comment_count
        result['followers'] = subscriber_count
        result['pc_view_cnt'] = view_count

        # 대상 업데이트(DB)
        viralc_common.merge_crawl_result(con, result)

    # DB 연결 해제
    con.close()
    print("crawl_youtube.py 종료")
