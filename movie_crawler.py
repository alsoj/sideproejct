import os
import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc

import urllib
import atexit
import youtube_dl

# 결과물 파일 저장 경로
TEMP_MOVIE_SAVE_PATH = './output/'

############################################
# 브라우저 세팅
############################################
def set_chrome_driver(wired=False):
  chrome_options = webdriver.ChromeOptions()
  # chrome_options.add_argument("--headless")

  if wired:
    driver = uc.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
  else:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

  return driver


############################################
# 크롤러 브라우저 생성
############################################
def get_browser():
  options = webdriver.ChromeOptions()
  options.add_argument("headless")
  # browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), chrome_options=options)
  browser = set_chrome_driver(wired=True)
  return browser

############################################
# 입력 URL의 Depth 확인
############################################
def get_url_type(input_url):
  try:
    if '/anime-list' in input_url \
      or '/airing' in input_url \
      or '/pv' in input_url \
      or '/anime-list' in input_url \
      or '/ani' in input_url \
      or '/top16' in input_url:
      return 'PAGE'
    elif input_url.endswith('html'):
      return 'EP'
    else:
      return 'ANI'

  except Exception as e:
    print('입력된 URL의 유형을 파악하는 중 오류가 발생했습니다.')
    print(str(e)[:50])

############################################
# 루트에서 페이지 리스트 추출
############################################
def get_page_list(browser, root_site_url):
  try:
    browser.get(root_site_url)
    wp_page = browser.find_element(by=By.ID, value='wp_page')
    current = wp_page.find_element(by=By.CLASS_NAME, value='current').text
    pages = wp_page.find_elements(by=By.TAG_NAME, value='a')
    page_list = [root_site_url]

    for i in range(int(current) - 1, len(pages)):
      page_list.append(pages[i].get_attribute('href'))

    return page_list

  except Exception as e:
    print('페이지 리스트 추출 시 오류가 발생했습니다')
    print(str(e)[:50])

############################################
# 페이지에서 애니메이션 리스트 추출
############################################
def get_ani_list(browser, page_site_url):

  try:
    browser.get(page_site_url)
    ani_list = browser.find_elements(by=By.CLASS_NAME, value='myui-vodlist__detail')
    return ani_list
  except Exception as e:
    print('애니메이션 리스트 추출 시 오류가 발생했습니다')
    print(str(e)[:50])

############################################
# 파일 명으로 사용할 수 없는 특수 문자 치환
############################################
def replace_title(title):
  title = title.replace("₩", "-")
  title = title.replace("/", "-")
  title = title.replace(":", "-")
  title = title.replace("*", "-")
  title = title.replace("?", "-")
  title = title.replace("<", "-")
  title = title.replace(">", "-")
  title = title.replace("|", "-")
  title = title.replace('"', '-')

  return title

############################################
# 애니에서 에피소드 리스트 추출
############################################
def get_episode_list(browser, ani_site_url):
  try:
    browser.get(ani_site_url)
    eps = browser.find_elements(by=By.CLASS_NAME, value='ep')
    title = browser.find_element(by=By.TAG_NAME, value='article').find_element(by=By.TAG_NAME, value='strong').text
    title = replace_title(title)
    # title = browser.find_element(by=By.XPATH, value='//*[@id="body"]/div/div[1]/article/center/strong').text.replace(":", "-")
    episode_list = [ep.get_attribute('href') for ep in eps]
    return title, episode_list

  except Exception as e:
    print('에피소드 리스트 추출 시 오류가 발생했습니다')
    print(str(e)[:50])


############################################
# 영상 기본 정보 추출
############################################
def get_movie_info(browser, ep_site_url):
  try:
    browser.get(ep_site_url)
    movie_title = browser.title
    movie_title = movie_title.replace(":", "-")
    # option = browser.find_element(by=By.TAG_NAME, value='option')
    # movie_id = option.get_attribute('value').split('id=')[-1]
    movie_id = ep_site_url.split('/')[-2]
    print(movie_title, '/', movie_id)

    return movie_title, movie_id

  except Exception as e:
    print('영상 기본 정보 추출 시 오류가 발생 했습니다 : ', e)


############################################
# m3u8 형태 비디오 다운로드
############################################
def get_m3u8_url(browser, ep_site_url):
  try:
    browser.get(ep_site_url)
    option = browser.find_element(by=By.TAG_NAME, value='option')
    php_url = option.get_attribute('value')

    request_headers = {
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
                "content-type":"application/json",
                "referer": "https://kfani.me/",
              }

    php_res = requests.get(php_url, headers=request_headers)
    soup_php = BeautifulSoup(php_res.text, "html.parser")
    m3u8_url = soup_php.select_one('source').attrs['src']

    return m3u8_url

  except Exception as e:
    print('m3u8 주소 추출 중 오류가 발생 했습니다.')
    print(str(e)[:50])


############################################
# 영상 추출
############################################
def download_movie(browser, ep_site_url, movie_title, MOVIE_SAVE_PATH):
  try:

    print('#' * 100)
    print("영상 다운로드가 시작되었습니다 : ", f'{movie_title}.mp4')
    browser.get(ep_site_url)

    # browser.switch_to.frame('videoarea')
    iframes = browser.find_elements(by=By.TAG_NAME, value='iframe')
    player_idx = 0
    for idx, iframe in enumerate(iframes):
      if 'google' not in iframe.get_attribute('src'):
        player_idx = idx
    browser.switch_to.frame(player_idx)

    iframes = browser.find_elements(by=By.TAG_NAME, value='iframe')
    if len(iframes) > 0:
      browser.switch_to.frame(0)
    video = browser.find_element(by=By.TAG_NAME, value='video')
    video_url = video.get_attribute("src")

    if video_url.startswith('blob'):
      m3u8_url = get_m3u8_url(browser, ep_site_url)
      youtube_dl.utils.std_headers['Referer'] = "https://kfani.me/"
      ydl_opts = {'outtmpl': f'{MOVIE_SAVE_PATH + movie_title}.mp4' }

      with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([m3u8_url])

    else :
      retries = 3
      while(retries > 0 ):
        try:
          opener = urllib.request.build_opener()
          opener.addheaders = [('User-agent', 'Mozilla/5.0'), ("referer", "https://mobikf.ncctvgroup.com/")]
          urllib.request.install_opener(opener)

          urllib.request.urlretrieve(video_url, f'{MOVIE_SAVE_PATH + movie_title}.mp4')
          break
        except Exception as e:
          retries = retries - 1
          print("응답이 없어 재시도 합니다. 남은 재시도 회수 : ", retries)
          print(str(e)[:50])
          continue

    print("영상 다운로드 완료 : ", '{}.mp4'.format(movie_title))

  except Exception as e:
    print('영상 다운로드 시 오류가 발생했습니다 : ', '{}.mp4'.format(movie_title))
    print(str(e)[:50])
    print('#' * 100)


############################################
# 자막 다운로드
############################################
def download_caption(movie_id, movie_title, MOVIE_SAVE_PATH):
  try :
    url_caption = f'https://kfani.me/s/{movie_id}.vtt'

    request_headers = {
      "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
      "content-type": "application/json",
      "referer": "https://mobikf.ncctvgroup.com/",
    }

    html_caption = requests.get(url_caption, headers=request_headers)
    soup_caption = BeautifulSoup(html_caption.text.replace('\r\n','\n'), "html.parser")

    with open('{}.vtt'.format(MOVIE_SAVE_PATH + movie_title), 'w', encoding='utf-8') as f:
      f.write(f'{soup_caption.text}')

    print("자막 다운로드 완료 : ", '{}.vtt'.format(movie_title))
    print('#' * 100)

  except Exception as e:
    print('자막 다운로드 시 오류가 발생했습니다 : ', '{}.vtt'.format(movie_title))
    print(str(e)[:50])
    print('#' * 100)


############################################
# 페이지별 다운로드
############################################
def download_page(browser, page_site_url):
  try:
    ani_list = get_ani_list(browser, page_site_url)
    ani_site_list = []
    # print("ani_list : ", ani_list)
    for ani_site_url_element in ani_list:
      ani_site_list.append(ani_site_url_element.find_element(by=By.TAG_NAME, value='a').get_attribute('href'))

    for ani_site_url in ani_site_list:
      download_ani(browser, ani_site_url)

  except Exception as e:
    print('페이지별 다운로드 중 오류가 발생했습니다.')
    print(str(e)[:50])
    print('#' * 100)


############################################
# 에피소드별 다운로드
############################################
def download_episode(browser, ep_site_url, MOVIE_SAVE_PATH):
  try:
    movie_title, movie_id = get_movie_info(browser, ep_site_url)

    # 파일이 존재하지 않는 경우만 다운로드
    if not os.path.exists(MOVIE_SAVE_PATH + '{}.mp4'.format(movie_title)):
      download_movie(browser, ep_site_url, movie_title, MOVIE_SAVE_PATH)
      download_caption(movie_id, movie_title, MOVIE_SAVE_PATH)
    else:
      print('#' * 100)
      print('영상이 존재하여 SKIP 합니다 : ', '{}.mp4'.format(movie_title))
      print('#' * 100)

  except Exception as e:
    print('에피소드별 다운로드 중 오류가 발생했습니다.')
    print(str(e)[:50])
    print('#' * 100)


############################################
# 애니별 다운로드
############################################
def download_ani(browser, ani_site_url):
  try:
    title, episode_list = get_episode_list(browser, ani_site_url)
    episode_list.reverse()
    MOVIE_SAVE_PATH = TEMP_MOVIE_SAVE_PATH + title + '/'
    if not os.path.exists(MOVIE_SAVE_PATH):
      os.mkdir(MOVIE_SAVE_PATH)

    for ep_site_url in episode_list:
      download_episode(browser, ep_site_url, MOVIE_SAVE_PATH)

  except Exception as e:
    print('애니별 다운로드 중 오류가 발생했습니다.')
    print(str(e)[:50])
    print('#' * 100)


def quit_brower():
  print("프로그램이 종료되었습니다.")


if __name__ == '__main__':
  atexit.register(quit_brower)

  while(True):
    try:
      input_site_url = input("영상을 추출할 URL을 입력해주세요 : ")
      # print("입력된 사이트 :", input_site_url)
      input_site_url = input_site_url.strip()
      url_type = get_url_type(input_site_url)
      # print("url_type :", url_type)

      browser = get_browser()
      # print("브라우저 로드 완료")

    except EOFError as e:
      print(e)
      break
    except Exception as e:
      print(e)
      break

    try:
      # print("크롤링 시작")

      if url_type == 'PAGE':
        print("페이지에 존재하는 애니 리스트 전체 다운로드")

        page_list = get_page_list(browser, input_site_url)
        # print("page_list :", page_list)
        for page_url in page_list:
          download_page(browser, page_url)
      elif url_type == 'ANI':
        print("애니에 존재하는 에피소드 리스트 전체 다운로드")
        download_ani(browser, input_site_url)

    except Exception as e:
      print('작업 중 오류가 발생했습니다.')
      print(str(e)[:50])

    finally:
      browser.quit()