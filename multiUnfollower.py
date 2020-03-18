import shutil
import main_ui
from PyQt5 import QtWidgets
import sys
import os

app = QtWidgets.QApplication(sys.argv)
window = main_ui.Login()
app.exec_()
shutil.rmtree("images/", ignore_errors=True)
os.mkdir("images")

