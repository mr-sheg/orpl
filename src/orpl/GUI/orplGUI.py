import sys

import qtmodern.styles
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QMainWindow

from orpl.GUI.uis.ui_mainWindow import Ui_mainWindow


import logging
import os
from time import strftime

import pyperclip  # module to copy text to clipboard (ctrl + c | ctrl + v)
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5 import QtGui

class main_window(QMainWindow, Ui_mainWindow):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.setupUi(self)
        
    def setup_logging(self):
        


def launch_gui():
    # logger.info("Starting ORAS")

    app = QApplication(sys.argv)
    # app.setAttribute(Qt.AA_DisableHighDpiScaling, True)

    # logger.info("Created application")

    # Changing Theme
    qtmodern.styles.light(app)
    # logger.info("Setting Theme")

    window = main_window()
    window.showMaximized()

    app.exec_()


if __name__ == "__main__":

    launch_gui()
