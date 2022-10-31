import os
import sys
from PyQt6.QtWidgets import *

from CoinpanCrawler import CoinpanCrawler

if __name__ == "__main__":
    app = QApplication(sys.argv)
    coinpan_crawelr = CoinpanCrawler()
    coinpan_crawelr.show()
    app.exec()