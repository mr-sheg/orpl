import logging
import os
import sys
from time import strftime

import pyperclip  # module to copy text to clipboard (ctrl + c | ctrl + v)
import qtmodern.styles
from PyQt5 import QtGui
from PyQt5.QtWidgets import (
    QApplication,
    QErrorMessage,
    QFileDialog,
    QFileSystemModel,
    QMainWindow,
)

from orpl.calibration import autogenx, compute_irf
from orpl.gui import file_io
from orpl.gui.mplcanvas import PlotWidget
from orpl.gui.uis.ui_mainWindow import Ui_mainWindow

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
# disables matplotlib font msgs
logging.getLogger("matplotlib.font_manager").disabled = True


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

        # Internal references
        self.data_dir = None
        self.raw_spectra = None
        self.metadatas = None
        self.processed_spectra = None
        self.xaxis = None
        self.irf = None
        self.file_system_model = QFileSystemModel()

        # Plot windows
        self.currentSpectrumPlot = PlotWidget()
        self.loadedDataPlot = PlotWidget()
        self.xrefPlot = PlotWidget()
        self.yrefPlot = PlotWidget()
        self.rawDataPlot = PlotWidget()
        self.processedDataPlot = PlotWidget()

        # Window Setup
        self.setupUi(self)
        self.linkLogger()

        self.defaultSetup()
        self.connectSlots()
        self.setupPlots()

    def linkLogger(self):
        logger.addHandler(qlogHandler(self.plainTextLog))
        logger.setLevel(logging.DEBUG)
        logger.info("linked Logger with logWidget")

    def defaultSetup(self):
        # File IO
        self.file_system_model.setRootPath("/")
        self.treeViewFiles.setModel(self.file_system_model)
        self.treeViewFiles.setRootIndex(self.file_system_model.index(HOME_DIR))
        self.textEditDataDir.setText(HOME_DIR)

        # Log
        self.labelLogPath.setText(LOG_PATH)
        logger.info("setted default logTab setup")

    def setupPlots(self):
        self.boxDataSelection.setLayout(self.currentSpectrumPlot.createLayout())
        self.boxDataPlot.setLayout(self.loadedDataPlot.createLayout())
        self.boxXrefPlot.setLayout(self.xrefPlot.createLayout())
        self.boxYrefPlot.setLayout(self.yrefPlot.createLayout())
        self.boxRawSignal.setLayout(self.rawDataPlot.createLayout())
        self.boxProcessedSignal.setLayout(self.processedDataPlot.createLayout())

    def connectSlots(self):
        # File IO tab
        self.buttonSelectDirectory.clicked.connect(self.select_working_directory)
        self.buttonSelectSpectra.clicked.connect(self.select_spectra)
        self.treeViewFiles.selectionModel().selectionChanged.connect(self.select_file)
        self.buttonSelectXref.clicked.connect(self.select_xref)
        self.buttonSelectYref.clicked.connect(self.select_yref)
        # Processing tab

        # Log tab
        self.buttonCopyLog.clicked.connect(self.copyLogButtonPushed)

        logger.info("connected GUI slots")

    # Callbacks

    # Tab File IO

    def select_file(self):
        files = self.get_selected_files()
        if len(files) == 0:
            return

        logger.info("Selected files - %s", files)
        lastfile = files[-1]

        # Load file
        data, meta = file_io.load_file(lastfile)

        # Update metadata
        self.plainTextMetadata.setPlainText(meta)

        # Plot data
        ax = self.currentSpectrumPlot.canvas.axes
        ax.clear()
        ax.plot(data)
        ax.set_xlabel("Camera pixel [au]")
        ax.set_ylabel("Intensity [counts]")
        ax.figure.tight_layout()
        ax.figure.canvas.draw()
        logger.info("Updated currentSpectrum plot")

    def select_working_directory(self):
        options = QFileDialog.Options()
        new_dir = QFileDialog.getExistingDirectory(
            self, options=options, directory=HOME_DIR
        )

        if new_dir:
            self.data_dir = new_dir

        self.treeViewFiles.setRootIndex(self.file_system_model.index(new_dir))
        self.textEditDataDir.setText(new_dir)

        logger.info("Changed data directory - %s", new_dir)

    def select_spectra(self):
        # Load selected data
        self.raw_spectra = []
        self.metadatas = []
        for file in self.get_selected_files():
            data, meta = file_io.load_file(file)
            self.raw_spectra.append(data)
            self.metadatas.append(meta)
            logger.info("Loaded data file - %s", file)

        # Update Spectra graph (in File IO tab)
        ax = self.loadedDataPlot.canvas.axes
        ax.clear()
        for spectrum in self.raw_spectra:
            ax.plot(spectrum)
        ax.set_xlabel("Camera pixel [au]")
        ax.set_ylabel("Intensity [counts]")
        ax.figure.tight_layout()
        ax.figure.canvas.draw()
        logger.info("Updated Spectra plot")

        # Update Spectra graph (in Processing tab)
        ax = self.rawDataPlot.canvas.axes
        ax.clear()
        for spectrum in self.raw_spectra:
            ax.plot(spectrum)
        ax.set_xlabel("Camera pixel [au]")
        ax.set_ylabel("Intensity [counts]")
        ax.figure.tight_layout()
        ax.figure.canvas.draw()
        logger.info("Updated Raw Spectra plot")

    def select_xref(self):
        selected_file = self.get_selected_files()

        if len(selected_file) == 0:
            return
        elif len(selected_file) > 1:
            error_dialog = QErrorMessage()
            error_dialog.showMessage(
                "Please select only ONE file to be used for x-axis calibration."
            )
            error_dialog.exec()
            return

        # Load X-ref
        data, _ = file_io.load_file(selected_file[0])
        if data.ndim > 1:
            data = data.mean(axis=0)

        # Compute xaxis from x-ref
        if self.radioButtonTylenol.isChecked():
            xaxis = autogenx(data, preset="tylenol")
        elif self.radioButtonNylon.isChecked():
            xaxis = autogenx(data, preset="nylon")
        self.xaxis = xaxis

        # Update X-ref plot
        ax = self.xrefPlot.canvas.axes
        ax.clear()
        ax.plot(xaxis, data)
        ax.set_xlabel("Camera pixel [au]")
        ax.set_ylabel("Intensity [counts]")
        ax.figure.tight_layout()
        ax.figure.canvas.draw()
        logger.info("Updated X-ref plot")

    def select_yref(self):
        selected_file = self.get_selected_files()

        if len(selected_file) == 0:
            return
        elif len(selected_file) > 1:
            error_dialog = QErrorMessage()
            error_dialog.showMessage(
                "Please select only ONE file to be used for y-axis calibration."
            )
            error_dialog.exec()
            return

        # Load Y-ref
        nist, _ = file_io.load_file(selected_file[0])
        if nist.ndim > 1:
            nist = nist.mean(axis=0)

        # Compute IRF from y-ref
        if self.xaxis is None:
            logger.info("Computing y-ref %s without xaxis", nist.shape)
            irf = compute_irf(nist)
        else:
            logger.info(
                "Computing y-ref %s with xaxis %s", nist.shape, self.xaxis.shape
            )
            irf = compute_irf(nist, xaxis=self.xaxis)

        self.irf = irf

        # Update Y-ref plot
        ax = self.yrefPlot.canvas.axes
        ax.clear()
        if self.xaxis is None:
            ax.plot(self.irf)
        else:
            ax.plot(self.xaxis, self.irf)
        ax.set_xlabel("Camera pixel [au]")
        ax.set_ylabel("Intensity [counts]")
        ax.figure.tight_layout()
        ax.figure.canvas.draw()
        logger.info("Updated Y-ref plot")

    # Tab Log

    def copyLogButtonPushed(self):
        pyperclip.copy(self.plainTextLog.toPlainText())
        logger.info("copied log text")

    # Backend

    def get_selected_files(self) -> list:
        # Get files from selection
        indexes = self.treeViewFiles.selectedIndexes()
        files = [index.model().filePath(index) for index in indexes]
        files = set(files)
        files = [file for file in files if os.path.isfile(file)]  # Remove directory
        files = [
            file for file in files if file_io.is_file_supported(file)
        ]  # keep only supported file types

        return files


def launch_gui():
    logger.info("Starting ORPL GUI")

    app = QApplication(sys.argv)
    # app.setAttribute(Qt.AA_DisableHighDpiScaling, True)

    logger.info("Created application")

    # Changing Theme
    qtmodern.styles.light(app)
    logger.info("Setting Theme")

    window = main_window()
    window.showMaximized()

    app.exec_()


if __name__ == "__main__":

    launch_gui()
