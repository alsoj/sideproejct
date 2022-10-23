from selenium.webdriver.common.by import By
import viralc_common

from time import sleep

def get_naver_info(browser, url):
    like_count = ''
    comment_count = ''
    try:
        browser.get(url)
        sleep(1)
        browser.switch_to.frame('mainFrame')
        sleep(1)

        post_id = viralc_common.get_content_id(url)
        sympathy = browser.find_element(by=By.ID, value='Sympathy'+post_id)
        like_count = sympathy.find_element(by=By.CLASS_NAME, value='u_cnt').text
        comment_count = browser.find_element(by=By.ID, value='commentCount').text
    except Exception as e:
        print(e)
    finally:
        return like_count, comment_count

if __name__ == "__main__":
    print("crawl_naver.py 실행")

    # DB 연결
    con = viralc_common.get_db_connection()

    # 대상 조회(DB)
    url_list = viralc_common.get_crawling_target(con, "N")
    print(f"네이버 크롤링 대상 : {len(url_list)}건")

    browser = viralc_common.get_selenium()
    try:
        for url in url_list:
            result = viralc_common.get_reuslt_dict()
            result['content_url'] = url
            result['sns_type'] = "N"

            # 크롤링 진행
            like_count, comment_count = get_naver_info(browser, url)
            result['empathy'] = like_count
            result['comment'] = comment_count
            print(url, like_count, comment_count)

            # 대상 업데이트(DB)
            viralc_common.merge_crawl_result(con, result)
    except Exception as e:
        print(e)
    finally:
        browser.quit()

    # DB 연결 해제
    con.close()
    print("crawl_naver.py 종료")