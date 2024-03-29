from selenium.webdriver.common.by import By
import viralc_common
from viralc_common import log_debug, log_info, log_error

from time import sleep

def get_naver_info(browser, url):
    like_count, comment_count, img_cnt, content_length = '', '', '', ''

    try:
        browser.get(url)
        sleep(1)
        browser.switch_to.frame('mainFrame')
        sleep(1)

        post_id = viralc_common.get_content_id(url)
        sympathy = browser.find_elements(by=By.ID, value='Sympathy'+post_id)
        if len(sympathy) > 0:
            like_count = sympathy[0].find_element(by=By.CLASS_NAME, value='u_cnt').text.strip()
        else:
            like_count = 0
        comment_count = browser.find_element(by=By.ID, value='commentCount').text.strip()
        comment_count = comment_count if len(comment_count) > 0 else 0

        main_container = browser.find_element(by=By.CLASS_NAME, value='se-main-container')
        img_cnt = len(main_container.find_elements(by=By.TAG_NAME, value='img'))
        content_length = len(main_container.text)

    except Exception as e:
        log_error(e)
    finally:
        return str(like_count), str(comment_count), str(img_cnt), str(content_length)


if __name__ == "__main__":
    log_debug("crawl_naver.py 실행")

    # DB 연결
    con = viralc_common.get_db_connection()

    # 대상 조회(DB)
    url_list = viralc_common.get_crawling_target(con, "N")
    log_info(f"네이버 크롤링 대상 : {len(url_list)}건")

    browser = viralc_common.get_selenium()
    try:
        for content_seq, url in url_list:
            result = viralc_common.get_reuslt_dict()
            result['content_url'] = url
            result['sns_type'] = "N"

            # 크롤링 진행
            like_count, comment_count, img_cnt, content_length = get_naver_info(browser, url)
            result['empathy'] = like_count
            result['comment'] = comment_count
            log_info(f"{url}, 공감 수 : {like_count}, 댓글 수 : {comment_count}, 이미지 수 : {img_cnt}, 글자 수 : {content_length}")

            # 대상 업데이트(DB)
            viralc_common.merge_crawl_result(con, result)

            # 이미지 수, 컨텐츠 길이 UPDATE
            update_result = {
                'img_cnt': img_cnt,
                'content_length': content_length,
                'content_seq': content_seq
            }
            viralc_common.update_naver_result(con, update_result)
    except Exception as e:
        log_error(e)
    finally:
        browser.quit()

    # DB 연결 해제
    con.close()
    log_debug("crawl_naver.py 종료")