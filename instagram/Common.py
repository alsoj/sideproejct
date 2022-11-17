from selenium import webdriver
import platform
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import re

# 브라우저 실행
def execute_browser():
    options = webdriver.ChromeOptions()
    # options.add_argument("headless")

    if 'macOS' in platform.platform():
        browser = webdriver.Chrome(executable_path='/Users/alsoj/Workspace/kmong/ipynb/chromedriver_mac', options=options)
    else:
        browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    return browser

# 인스타그램 app id 추출
def get_app_id(res_text):
    prog = re.compile('"\d{15}"')
    result = prog.findall(res_text)
    return result[0].replace('"','')

# 게시글 URL에서 코드 추출
def get_short_code(target_url):
    short_code = ''
    try:
        short_code = target_url.split("/")[4]
    except Exception as e:
        short_code = ''
    finally:
        return short_code