BASE_URL = 'https://coinpan.com/'
LOGIN_URL = BASE_URL + 'index.php?mid=index&act=dispMemberLoginForm'
BOARD_URL = BASE_URL + 'free'

API_URL = 'https://api.coinpan.com/default.json?ts='
API_EXCHANGE = ['bithumb', 'upbit', 'coinone', 'korbit', 'bitflyer', 'binance', 'bitfinex']
API_COIN = ['BTC', 'ETH', 'ETC', 'XRP', 'BCH', 'EOS', 'TRX', 'ADA', 'DOGE', 'SOL']

OUTPUT_DIR = './output/'
IMAGE_DIR = './image/'
PRICE_FILENAME = '_코인판 실시간 시세.xlsx'
BOARD_FILENAME = '_코인판 자유 게시판.xlsx'