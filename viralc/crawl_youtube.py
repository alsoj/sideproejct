import googleapiclient.discovery
import googleapiclient.errors


YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def get_youtube_info():
    youtube = googleapiclient.discovery.build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,developerKey=DEVELOPER_KEY)

    request = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        id="tQ19OKaMNBo"
    )
    response = request.execute()
    return response


if __name__ == "__main__":
    print("crawl_youtube.py 실행")
    # 대상 조회(DB)

    # 크롤링 진행

    # 대상 업데이트(DB)
