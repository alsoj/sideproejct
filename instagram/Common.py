from datetime import datetime

from selenium import webdriver
import platform
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import re

# 브라우저 실행
def execute_browser():
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    if 'macOS' in platform.platform():
        browser = webdriver.Chrome(executable_path='/Users/alsoj/Workspace/kmong/ipynb/chromedriver_mac', options=options)
    else:
        browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
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