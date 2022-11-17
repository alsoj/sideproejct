import os
import sys

# program_dir = os.path.dirname(os.path.abspath(sys.executable))
###########################################################
# 파이참에서 실행할 경우 아래에 MAIN.py가 존재하는 디렉토리 경로 입력
program_dir = '/Users/alsoj/Workspace/kmong/coinpan'
###########################################################

BASE_URL = 'https://coinpan.com/'
LOGIN_URL = BASE_URL + 'index.php?mid=index&act=dispMemberLoginForm'
BOARD_URL = BASE_URL + 'index.php?mid=free&page=1'

API_URL = 'https://api.coinpan.com/default.json?ts='
API_EXCHANGE = ['bithumb', 'upbit', 'coinone', 'korbit', 'bitflyer', 'binance', 'bitfinex']
API_COIN = ['BTC', 'ETH', 'ETC', 'XRP', 'BCH', 'EOS', 'TRX', 'ADA', 'DOGE', 'SOL']

UI_DIR = program_dir + '/CoinpanCrawler.ui'
CHROME_DIR = program_dir + '/chromedriver_mac'
OUTPUT_DIR = program_dir + '/output/'
IMAGE_DIR = program_dir + '/image/'
PRICE_FILENAME = '_코인판 실시간 시세.xlsx'
PRICE_FILENAME_FOR_APPEND = '코인판 실시간 시세.xlsx'
BOARD_FILENAME = '_코인판 자유 게시판.xlsx'