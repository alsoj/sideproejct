from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import re
import requests
from io import BytesIO
from PIL import Image

# 브라우저 실행
def execute_browser(background=True):

    options = webdriver.ChromeOptions()
    if background:
        options.add_argument("headless")

    try:
        browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    except Exception as e:
        browser = webdriver.Chrome(executable_path='./chromedriver', options=options)
    finally:
        return browser

# 인스타그램 app id 추출
def get_app_id(res_text):
    prog = re.compile('"X-IG-App-ID":"\d{15}"')
    result = prog.findall(res_text)
    return result[0].replace('"','').replace("X-IG-App-ID:","")

# 게시글 URL에서 코드 추출
def get_short_code(target_url):
    short_code = ''
    try:
        short_code = target_url.split("/")[4]
    except Exception as e:
        short_code = ''
    finally:
        return short_code

# 미디어 ID 추출
def get_media_id(res_text):
    prog = re.compile('"media_id":"\d{19}"')
    result = prog.findall(res_text)
    return result[0].replace('"','').replace("media_id:","")

# 사용자 ID로 정보 조회
def get_user_by_user_id(user_id, headers):
    api_url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={user_id}"
    if user_id:
        try:
            res = requests.get(api_url, headers=headers)
            user_info = res.json()

        except Exception as e:
            print("getting user failed, due to '{}'".format(e.message))
    return user_info['data']

def download_img(url, file_path_name):
    try:
        res = requests.get(url)
        img = Image.open(BytesIO(res.content))
        img.save(f'{file_path_name}.jpeg', 'JPEG')
    except Exception as e:
        print("image download failed, url : '{}'".format(url))
        print("image download failed, due to '{}'".format(e.message))

# header 만들기
def get_headers(browser):
    res = browser.page_source
    app_id = get_app_id(res)
    csrftoken = browser.get_cookie("csrftoken")['value']

    cookies = browser.get_cookies()
    header_cookie = ''
    for cookie in cookies:
        header_cookie += f"{cookie['name']}={cookie['value']}; "

    # 헤더 세팅
    headers = {
        'referer': 'https://www.instagram.com/',
        'x-csrftoken': csrftoken,
        'cookie': header_cookie,
        'x-ig-app-id': app_id
    }
    return headers


# 유닉스 타임 -> 날짜형식 변환
def get_datetime(unixtimestamp):
    return datetime.utcfromtimestamp(int(unixtimestamp)).strftime('%Y-%m-%d %H:%M:%S')

# 디버그 로그 출력
def debug(log_browser, text):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_browser.append(f'<p>[{now}] {text}</p>')
    scroll_bar = log_browser.verticalScrollBar()
    scroll_bar.setValue(scroll_bar.maximum())

# 정보 로그 출력(초록색)
def info(log_browser, text):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_browser.append(f'<p style="color:green">[{now}] {text}</p>')
    scroll_bar = log_browser.verticalScrollBar()
    scroll_bar.setValue(scroll_bar.maximum())

# 에러 로그 출력(빨간색)
def error(log_browser, text):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_browser.append(f'<p style="color:red">[{now}] {text}</p>')
    scroll_bar = log_browser.verticalScrollBar()
    scroll_bar.setValue(scroll_bar.maximum())

# 입력 값 체크
def is_null(target):
    return target is None or len(target.strip()) == 0

# 해시 태그 추출
def get_hashtag(text):
    pattern = '#([0-9a-zA-Z가-힣]*)'
    hashtag_regex = re.compile(pattern)

    hashtag = hashtag_regex.findall(text)
    hashtag = ['#' + tag for tag in hashtag]
    return hashtag
