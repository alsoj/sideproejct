import sys
from PyQt6.QtWidgets import *
from PyQt6 import uic

# 어플리케이션 패키지
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from openpyxl import Workbook, load_workbook

form_class = uic.loadUiType("crawl_instagram.ui")[0]

class INSTA_Window(QMainWindow, form_class):
  def __init__(self):
    super().__init__()
    self.setupUi(self)
    self.btn_start.clicked.connect(self.btn_start_clicked)

  def btn_start_clicked(self):
    self.setLogText("#######################################")
    self.setLogText("크롤링 작업을 시작합니다.")

    if self.check_input_valid() is not True:
      return False

    options = webdriver.ChromeOptions()
    # options.add_argument("headless")
    browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    try:
      login_instagram(input_id, input_pw):

    except Exception as e:
      self.setLogText("크롤링 작업 중 오류가 발생 했습니다.")
      self.setLogText(str(e))
      self.setLogText("#######################################")
    finally:
      browser.quit()
      self.setLogText("크롤링 작업이 종료되었습니다.")
      self.setLogText("#######################################")

  def check_input_valid(self):
    input_id = self.edit_id.text()
    input_pw = self.edit_pw.text()
    input_url = self.edit_url.text()

    if len(input_id) == 0 or len(input_pw) == 0 or len(input_url) == 0:
      self.setLogText("필수 입력 값이 입력되지 않았습니다.")
      self.setLogText("ID, PW, URL을 확인해주세요.")
      return False
    else:
      return True

  def clearLog(self):
    self.logBrowser.clear()

  def setLogText(self, text):
    self.logBrowser.append(text)
    QApplication.processEvents()


if __name__ == "__main__":
  app = QApplication(sys.argv)
  INSTA = INSTA_Window()
  INSTA.show()
  app.exec()