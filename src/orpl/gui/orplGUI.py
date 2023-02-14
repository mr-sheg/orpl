import logging
import os
import sys
from time import strftime
from typing import List

import pyperclip  # module to copy text to clipboard (ctrl + c | ctrl + v)
import qtmodern.styles
from PyQt5 import QtGui
from PyQt5.QtWidgets import (
    QApplication,
    QErrorMessage,
    QFileDialog,
    QFileSystemModel,
    QMainWindow,
    QStyle,
)

from orpl.calibration import autogenx, compute_irf
from orpl.datatypes import Spectrum
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


class main_window(Ui_mainWindow, QMainWindow):
    def __init__(self):
        super().__init__()

        # Internal references
        self.data_dir: str = None
        self.raw_spectra: List[Spectrum]
        self.processed_spectra = None
        self.xaxis: Spectrum = None
        self.irf: Spectrum = None
        self.auto_update_processing: bool = False
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

        pixmapi = getattr(QStyle, "SP_TrashIcon")
        trash_icon = self.style().standardIcon(pixmapi)
        self.buttonDropSpectra.setIcon(trash_icon)
        self.buttonDropXref.setIcon(trash_icon)
        self.buttonDropYref.setIcon(trash_icon)

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
        self.buttonSelectSpectra.clicked.connect(self.select_data)
        self.treeViewFiles.selectionModel().selectionChanged.connect(
            self.selected_file_changed
        )
        self.buttonSelectXref.clicked.connect(self.select_xref)
        self.buttonSelectYref.clicked.connect(self.select_yref)
        self.buttonDropSpectra.clicked.connect(self.drop_data)
        self.buttonDropXref.clicked.connect(self.drop_xref)
        self.buttonDropYref.clicked.connect(self.drop_yref)

        # Processing tab
        self.buttonUpdate.clicked.connect(self.update_processing)
        self.spinBoxLeftCrop.valueChanged.connect(self.left_crop_changed)
        self.spinBoxRightCrop.valueChanged.connect(self.right_crop_changed)

        # Log tab
        self.buttonCopyLog.clicked.connect(self.copy_log)

        logger.info("connected GUI slots")

    # Callbacks

    # Tab File IO

    def selected_file_changed(self):
        files = self.get_selected_files()
        if len(files) == 0:
            return

        logger.info("Selected files - %s", files)
        lastfile = files[-1]

        # Load file
        spectrum = file_io.load_file(lastfile)

        # Update metadata
        self.plainTextMetadata.setPlainText(spectrum.metadata.details)

        # Plot data
        ax = self.currentSpectrumPlot.canvas.axes
        ax.clear()
        ax.plot(spectrum.accumulations.T)
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

    def select_data(self):
        # Load selected data
        self.raw_spectra = []
        for file in self.get_selected_files():
            spectrum = file_io.load_file(file)
            self.raw_spectra.append(spectrum)
            logger.info("Loaded data file - %s", file)

        # Update processing controls
        spectrum_length = self.raw_spectra[0].nbins
        self.spinBoxLeftCrop.setValue(0)
        self.spinBoxLeftCrop.setMaximum(spectrum_length)
        self.spinBoxRightCrop.setValue(spectrum_length)
        self.spinBoxRightCrop.setMaximum(spectrum_length)

        # Update plots
        self.plot_loaded_data()
        self.plot_raw_spectra()

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
        xref = file_io.load_file(selected_file[0])

        # Compute xaxis from x-ref
        if self.radioButtonTylenol.isChecked():
            xaxis = autogenx(xref.mean_spectrum, preset="tylenol")
        elif self.radioButtonNylon.isChecked():
            xaxis = autogenx(xref.mean_spectrum, preset="nylon")
        self.xaxis = xaxis

        self.plot_xref(xref)

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
        nist = file_io.load_file(selected_file[0]).mean_spectrum

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

        self.plot_irf()

    def drop_data(self):
        logger.info("Dropping loaded data")
        self.raw_spectra = []

        self.plot_raw_spectra()
        self.plot_loaded_data()

    def drop_xref(self):
        logger.info("Dropping xref and xaxis")
        self.xaxis = None

        self.plot_xref(None)

    def drop_yref(self):
        logger.info("Dropping yref and IRF")
        self.irf = None

        self.plot_irf()

    def plot_loaded_data(self):
        logger.info("Plotting loaded data")
        # Update Spectra graph (in File IO tab)
        ax = self.loadedDataPlot.canvas.axes
        ax.clear()

        for s in self.raw_spectra:
            ax.plot(s.mean_spectrum)
        ax.set_xlabel("Camera pixel [au]")
        ax.set_ylabel("Intensity [counts]")
        ax.figure.tight_layout()
        ax.figure.canvas.draw()
        logger.info("Updated Spectra plot")

    def plot_xref(self, xref):
        logger.info("Plotting (xaxis, xref)")
        # Update X-ref plot
        ax = self.xrefPlot.canvas.axes
        ax.clear()
        if self.xaxis is not None:
            ax.plot(self.xaxis, xref.mean_spectrum)
        ax.set_xlabel(r"Raman Shifts [cm$^{-1}$]")
        ax.set_ylabel("Intensity [counts]")
        ax.figure.tight_layout()
        ax.figure.canvas.draw()
        logger.info("Updated X-ref plot")

    def plot_irf(self):
        logger.info("Plotting Instrument Response Function")
        # Update Y-ref plot
        ax = self.yrefPlot.canvas.axes
        ax.clear()
        if self.irf is not None:
            if self.xaxis is not None:
                ax.plot(self.irf)
            else:
                ax.plot(self.xaxis, self.irf)
        ax.set_xlabel("Camera pixel [au]")
        ax.set_ylabel("Intensity [counts]")
        ax.figure.tight_layout()
        ax.figure.canvas.draw()
        logger.info("Updated Y-ref plot")

    # Tab Processing

    def update_processing(self):
        logger.info("Updating Processing")
        self.process_spectra()
        logger.info("Updating ")

    def left_crop_changed(self):
        return

    def right_crop_changed(self):
        return

    def plot_raw_spectra(self):
        # Update Spectra graph (in Processing tab)
        ax = self.rawDataPlot.canvas.axes
        ax.clear()

        for s in self.raw_spectra:
            ax.plot(s.mean_spectrum)
        ax.set_xlabel("Camera pixel [au]")
        ax.set_ylabel("Intensity [counts]")
        ax.figure.tight_layout()
        ax.figure.canvas.draw()
        logger.info("Updated Raw Spectra plot")

    # Tab Log

    def copy_log(self):
        pyperclip.copy(self.plainTextLog.toPlainText())
        logger.info("copied log text")

    # Backend

    def get_selected_files(self) -> list:
        # Get files from selection
        indexes = self.treeViewFiles.selectedIndexes()
        files = [index.model().filePath(index) for index in indexes]
        files = set(files)
        files = [file for file in files if os.path.isfile(file)]  # Remove directory
        # Remove unsupported files
        files = [f for f in files if file_io.is_file_supported(f)]

        return files

    def process_spectra(self):
        xaxis = self.xaxis
        raw_spectra = self.raw_spectra
        irf = self.irf

        # Truncating
        left_cutoff = self.spinBoxLeftCrop.value()
        right_cutoff = self.spinBoxRightCrop.value()
        print(left_cutoff, right_cutoff)
        # Removing cosmic rays

        # Removing baselines

        #


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
