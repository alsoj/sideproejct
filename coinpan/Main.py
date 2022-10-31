import sys
from PyQt6.QtWidgets import *

from coinpan.CoinpanCrawler import CoinpanCrawler
from openpyxl import Workbook, load_workbook
from datetime import datetime

import Config


if __name__ == "__main__":
    app = QApplication(sys.argv)
    coinpan_crawelr = CoinpanCrawler()
    coinpan_crawelr.show()
    app.exec()