import logging
import os
import sys
from time import strftime

import pyperclip  # module to copy text to clipboard (ctrl + c | ctrl + v)
import qtmodern.styles
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QWidget

from orpl.GUI.uis.ui_mainWindow import Ui_mainWindow

# Set-up home directory for ORPL
HOME_DIR = os.environ["HOME"]
ORPL_DIR = os.path.join(HOME_DIR, "orpl")
if not os.path.isdir(ORPL_DIR):
    os.mkdir(ORPL_DIR)
LOG_DIR = os.path.join(ORPL_DIR, "logs")
if not os.path.isdir(LOG_DIR):
    os.mkdir(LOG_DIR)


# Logging
DEV_MODE = True

# Creates logger
LOG_FORMAT = (
    "%(asctime)s - %(levelname)s"
    "(%(filename)s:%(funcName)s)"
    "(%(filename)s:%(lineno)d) - "
    "%(message)s"
)

if DEV_MODE:
    LOG_PATH = os.path.join(LOG_DIR, "dev.log")
else:
    LOG_PATH = os.path.join(LOG_DIR, f"{strftime('%Y_%m_%d_%H_%M_%S')}.log")


logging.basicConfig(
    filename=LOG_PATH,
    level=logging.DEBUG,
    format=str(LOG_FORMAT),
    filemode="w",
)
logger = logging.getLogger()


class qlogHandler(logging.Handler):
    """
    qlogHandler is a custom logger class that links the QPlainTextEdit from the loggin tab
    with the root logger of the application.
    """

    def __init__(self, QPlainTextEdit):
        super().__init__()
        self.loggerTextEdit = QPlainTextEdit
        self.setFormatter(logging.Formatter(LOG_FORMAT))

        # Add current log lines to widget
        # Currently the log is created before it is linked to the widget
        # Not sure if there is a way to get around this, but it works
        with open(LOG_PATH, encoding="utf8") as file:
            log_thus_far = file.read()
        self.loggerTextEdit.setPlainText(log_thus_far.strip())

    def emit(self, record):
        msg = self.format(record)
        self.loggerTextEdit.appendPlainText(msg)
        self.loggerTextEdit.moveCursor(QtGui.QTextCursor.End)


class main_window(QMainWindow, Ui_mainWindow):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.setupUi(self)
        self.linkLogger()

        self.defaultSetup()
        self.connectSlots()

    def linkLogger(self):
        logger.addHandler(qlogHandler(self.plainTextLog))
        logger.setLevel(logging.DEBUG)
        logger.info("linked Logger with logWidget")

    def defaultSetup(self):
        self.labelLogPath.setText(LOG_PATH)
        logger.info("setted default logTab setup")

    def connectSlots(self):
        self.buttonCopyLog.clicked.connect(self.copyLogButtonPushed)
        logger.info("connected GUI slots")

    def copyLogButtonPushed(self):
        pyperclip.copy(self.plainTextLog.toPlainText())
        logger.info("copied log text")


def launch_gui():
    logger.info("Starting ORPL GUI")

    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DisableHighDpiScaling, True)

    logger.info("Created application")

    # Changing Theme
    qtmodern.styles.light(app)
    logger.info("Setting Theme")

    window = main_window()
    window.showMaximized()

    app.exec_()


if __name__ == "__main__":

    launch_gui()
