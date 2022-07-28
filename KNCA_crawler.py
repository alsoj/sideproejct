import sys
from PyQt6 import QtWidgets
from PyQt6 import uic

form_class = uic.loadUiType("KNCA_crawler.ui")[0]

class KNCA_Window(QtWidgets.QMainWindow, form_class):
  def __init__(self):
    super().__init__()
    self.setupUi(self)

if __name__ == "__main__":
  app = QtWidgets.QApplication(sys.argv)
  KNCA = KNCA_Window()
  KNCA.show()
  app.exec()