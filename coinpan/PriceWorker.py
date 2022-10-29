from PyQt6.QtCore import QThread

from datetime import datetime
from pandas import DataFrame
from time import time
import requests

import Config

class PriceWorker(QThread):
    """
    실시간 시세 크롤링 쓰레드
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def run(self):
        self.parent.btn_price.setEnabled(False)
        self.parent.info("실시간 시세 추출 시작")
        result = get_price()
        filename = export_excel(result)
        self.parent.debug("파일 저장 경로 : " + filename)
        self.parent.info("실시간 시세 추출 종료")
        self.parent.btn_price.setEnabled(True)

def get_price():
    """
    실시간 시세 API 호출
    :return: 실시간 시세 API
    """
    now = round(time())
    response = requests.get(Config.API_URL + str(now))
    data = response.json()

    prices = DataFrame(
        columns=['순번1', '순번2', '가상화폐', '거래소', '실시간시세(KRW)', '실시간시세(USD)', '24시간변동액', '24시간변동률', '한국프리미엄',
                 '한국프리미엄(%)', '거래량'])

    for i, exchange in enumerate(Config.API_EXCHANGE):
        if exchange in data['prices']:
            for j, coin in enumerate(Config.API_COIN):
                if coin in data['prices'][exchange]:
                    price = data['prices'][exchange][coin]
                    prices.loc[len(prices)] = [j, i, coin, exchange,
                                                round(float(price['now_price'] or 0), 2),
                                                round(float(price['now_price_usd'] or 0), 4),
                                                round(float(price['diff_24hr'] or 0), 2),
                                                round(float(price['diff_24hr_percent'] or 0), 2),
                                                round(float(price['korea_premium'] or 0), 2),
                                                round(float(price['korea_premium_percent'] or 0), 2),
                                                round(float(price['units_traded'] or 0), 2)]
    result = prices.sort_values(by=['순번1','순번2'])
    result = result.drop(['순번1','순번2'], axis=1)
    result = result.reset_index(drop=True)
    return result

def export_excel(result):
    """
    엑셀 export 함수
    :param result: 실시간 시세 Dataframe
    :return filename : 경로 및 파일명
    """
    filename = Config.OUTPUT_DIR + datetime.now().strftime('%Y%m%d%H%M%S') + Config.PRICE_FILENAME
    result.to_excel(filename, index=False)
    return filename