from selenium.webdriver.common.by import By

from time import sleep
import json

import viralc_config
from viralc import viralc_common


def merge_crawl_result(con, result):
    cur = con.cursor()
    sql = \
        """
        INSERT INTO tb_content_crawling
        (content_url, sns_type, empathy, comment, followers, insert_datetime) 
        VALUES
        (%(content_url)s, 'I', %(like_count)s, %(comment_count)s, %(follower_count)s, now())
        ON DUPLICATE KEY UPDATE
        empathy = %(like_count)s,
        comment = %(comment_count)s,
        followers = %(follower_count)s,        
        update_datetime = now()
        """

    cur.execute(sql, result)
    con.commit()


def login_instagram(browser, id, password):
    """
    인스타그램 로그인
    :param browser: 웹 드라이버
    :param id: 사용자 ID
    :param password: 사용자 PW
    :return: 로그인 결과
    """
    browser.get(viralc_config.INSTAGRAM_CONFIG['LOGIN_URL'])
    sleep(5)
    inputs = browser.find_elements(by=By.TAG_NAME, value='input')
    inputs[0].clear()
    inputs[1].clear()
    inputs[0].send_keys(id)
    inputs[1].send_keys(password)
    inputs[1].submit()
    sleep(10)

    if '잘못된 비밀번호' in browser.page_source:
        return 'PWERR'
    elif '입력한 사용자 이름' in browser.page_source:
        return 'IDERR'
    else:
        return 'OK'

def get_api_url(browser, post_id):
    """
    게시물 정보 조회 API 주소 추출
    :param browser: 웹 드라이버
    :param post_id: 게시물 ID
    :return: API 주소
    """
    base_url = f'https://www.instagram.com/p/{post_id}/'
    api_url = ''
    try:
        browser.get(base_url)
        sleep(3)

        for request in browser.requests:
            if request.response:
                if 'query_hash=' in request.url and post_id in request.url:
                    api_url = request.url

    except Exception as e:
        print(str(e))
    finally:
        del browser.requests
        return api_url

def get_data(browser, api_url):
    """
    API 호출하여 게시물 정보 추출
    :param browser: 웹 드라이버
    :param api_url: API 주소
    :return: 좋아요 수, 댓글 수, 팔로워 수
    """
    like_cnt = ''
    comment_cnt = ''
    follower_cnt = ''

    try:
        browser.get(api_url)
        content = browser.find_element(by=By.TAG_NAME, value='pre').text
        data = json.loads(content)
        media = data['data']['shortcode_media']
        like_cnt = media['edge_media_preview_like']['count']  # 좋아요
        comment_cnt = media['edge_media_preview_comment']['count']  # 코멘트
        follower_cnt = media['owner']['edge_followed_by']['count']  # 팔로워
    except Exception as e:
        print(str(e))
    finally:
        return like_cnt, comment_cnt, follower_cnt

def get_instagram_info(browser, browser_login, post_id):
    """
    인스타그램 정보 조회(selenium)
    :param: 포스팅 ID
    :return: 좋아요, 댓글, 구독자, 조회 수
    """
    api_url = get_api_url(browser, post_id)
    like_count, comment_count, follower_count = get_data(browser_login, api_url)
    print(post_id, like_count, comment_count, follower_count)

    return like_count, comment_count, follower_count


if __name__ == "__main__":
    print("crawl_instagram.py 실행")

    # DB 연결
    con = viralc_common.get_db_connection()

    # 대상 조회(DB)
    url_list = viralc_common.get_crawling_target(con, "I")

    browser = viralc_common.get_selenium_wire()
    browser_login = viralc_common.get_selenium()
    try:
        login_reuslt = login_instagram(browser_login, viralc_config.INSTAGRAM_CONFIG['LOGIN_ID'], viralc_config.INSTAGRAM_CONFIG['LOGIN_PW'])
        if login_reuslt != "OK":
            print("인스타그램 로그인에 실패했습니다.")
            exit()

        for url in url_list:
            result = {'content_url': url}
            post_id = viralc_common.get_content_id(url)

            # 크롤링 진행
            like_count, comment_count, follower_count = get_instagram_info(browser, browser_login, post_id)
            result['like_count'] = like_count
            result['comment_count'] = comment_count
            result['follower_count'] = follower_count

            # 대상 업데이트(DB)
            merge_crawl_result(con, result)
    except Exception as e:
        print(e)
    finally:
        browser.quit()
        browser_login.quit()

    # DB 연결 해제
    con.close()
    print("crawl_youtube.py 종료")
