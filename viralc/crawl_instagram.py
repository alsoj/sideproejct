from selenium.webdriver.common.by import By

from time import sleep
import json

import viralc_config
import viralc_common
from viralc_common import log_debug, log_info, log_error

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
        return '잘못된 비밀번호입니다.'
    elif '입력한 사용자 이름' in browser.page_source:
        return '잘못된 사용자 ID입니다.'
    elif '문제가 발생' in browser.page_source:
        return '일시적인 문제가 발생하였습니다.'
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
                    break

    except Exception as e:
        log_error("get_api_url 실행 중 오류 발생 : " + str(e))
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
        log_error("get_data 실행 중 오류 발생 : " + str(e))
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
    log_info(f"ID={post_id}, LIKE={like_count}, COMMENT={comment_count}, FOLLOWER={follower_count}")

    return like_count, comment_count, follower_count

def get_instagram_content_id(url):
    """
    인스타그램 게시물 ID 추출
    :param url: 게시글 주소
    :return: 게시물 code
    """
    return url.split('/')[4]


if __name__ == "__main__":
    log_debug("crawl_instagram.py 실행")

    # DB 연결
    con = viralc_common.get_db_connection()

    # 대상 조회(DB)
    url_list = viralc_common.get_crawling_target(con, "I")
    log_info(f"인스타그램 크롤링 대상 : {len(url_list)}건")

    browser = viralc_common.get_selenium_wire()
    browser_login = viralc_common.get_selenium()
    try:
        login_id = viralc_config.INSTAGRAM_CONFIG['LOGIN_ID']
        login_reuslt = login_instagram(browser_login, login_id, viralc_config.INSTAGRAM_CONFIG['LOGIN_PW'])
        if login_reuslt != "OK":
            log_error(f"인스타그램 로그인에 실패했습니다. 계정 : {login_id}, 결과 : {login_reuslt}")
            # exit()
        else:
            log_info(f"인스타그램 로그인에 성공했습니다. 계정 : {login_id}")

        for url in url_list:
            result = viralc_common.get_reuslt_dict()
            result['content_url'] = url
            result['sns_type'] = "I"

            post_id = get_instagram_content_id(url)
            # post_id = viralc_common.get_content_id(url)

            # 크롤링 진행
            like_count, comment_count, follower_count = get_instagram_info(browser, browser_login, post_id)
            result['empathy'] = like_count
            result['comment'] = comment_count
            result['followers'] = follower_count

            # 대상 업데이트(DB)
            viralc_common.merge_crawl_result(con, result)
    except Exception as e:
        log_error("main 실행 중 오류 발생 : " + str(e))
    finally:
        browser.quit()
        browser_login.quit()

    # DB 연결 해제
    con.close()
    log_debug("crawl_youtube.py 종료")
