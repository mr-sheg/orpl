import logging
import os
import sys
import traceback
from pathlib import Path
from time import strftime
from typing import List, Tuple

import numpy as np
import pyperclip  # module to copy text to clipboard (ctrl + c | ctrl + v)
import qtmodern.styles
from matplotlib.cm import tab10
from PyQt5 import QtGui
from PyQt5.QtWidgets import (
    QApplication,
    QErrorMessage,
    QFileDialog,
    QFileSystemModel,
    QMainWindow,
    QStyle,
)

from orpl import file_io
from orpl.baseline_removal import bubblefill, imodpoly, morph_br
from orpl.calibration import autogenx, compute_irf
from orpl.cosmic_ray import crfilter_multi, crfilter_single
from orpl.datatypes import Spectrum
from orpl.gui.mplcanvas import PlotWidget
from orpl.gui.uis.ui_mainWindow import Ui_mainWindow
from orpl.normalization import auc, maxband, minmax, snv

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
        self.raw_spectra: List[np.ndarray] = []
        self.baseline_spectra: List[np.ndarray] = []
        self.irf_corrections: List[np.ndarray] = []
        self.raman_spectra = None
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
        self.baselineFitPlot = PlotWidget()
        self.irfCorrectionPlot = PlotWidget()

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
        # File IO tab
        self.file_system_model.setRootPath("/")
        self.treeViewFiles.setModel(self.file_system_model)
        self.treeViewFiles.setRootIndex(self.file_system_model.index(HOME_DIR))
        self.textEditDataDir.setText(HOME_DIR)

        pixmapi = getattr(QStyle, "SP_TrashIcon")
        trash_icon = self.style().standardIcon(pixmapi)
        self.buttonDropSpectra.setIcon(trash_icon)
        self.buttonDropXref.setIcon(trash_icon)
        self.buttonDropYref.setIcon(trash_icon)

        # Processing tab
        self.spinBoxMCRRWidth.setValue(3)
        self.spinBoxMCRRthreshold.setValue(0.1)
        self.spinBoxSCRRWidth.setValue(3)
        self.spinBoxSCRRstd.setValue(5)
        self.spinBoxPolyOrder.setValue(6)
        self.spinBoxHWS.setMaximum(1024)
        self.spinBoxHWS.setValue(100)
        self.spinBoxBubbleWidth.setMaximum(1024)
        self.spinBoxBubbleWidth.setValue(200)

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
        self.boxBaselineFit.setLayout(self.baselineFitPlot.createLayout())
        self.boxIRFCorrection.setLayout(self.irfCorrectionPlot.createLayout())

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
        self.spinBoxLeftCrop.valueChanged.connect(self.left_crop_changed)
        self.spinBoxRightCrop.valueChanged.connect(self.right_crop_changed)
        self.buttonUpdate.clicked.connect(self.process_spectra)
        self.checkBoxMultiCRR.clicked.connect(self.processing_changed)
        self.spinBoxMCRRWidth.valueChanged.connect(self.processing_changed)
        self.spinBoxMCRRthreshold.valueChanged.connect(self.processing_changed)
        self.checkBoxSingleCRR.clicked.connect(self.processing_changed)
        self.spinBoxSCRRWidth.valueChanged.connect(self.processing_changed)
        self.spinBoxSCRRstd.valueChanged.connect(self.processing_changed)
        self.comboBoxBRAlgorithm.currentTextChanged.connect(self.processing_changed)
        self.spinBoxPolyOrder.valueChanged.connect(self.processing_changed)
        self.spinBoxHWS.valueChanged.connect(self.processing_changed)
        self.spinBoxBubbleWidth.valueChanged.connect(self.processing_changed)
        self.radioButtonNoNorm.clicked.connect(self.processing_changed)
        self.radioButtonMinMax.clicked.connect(self.processing_changed)
        self.radioButtonAUC.clicked.connect(self.processing_changed)
        self.radioButtonSNV.clicked.connect(self.processing_changed)
        self.radioButtonMaxBand.clicked.connect(self.processing_changed)
        self.spinBoxNormBand.valueChanged.connect(self.processing_changed)

        # self.comboBox

        # Log tab
        self.buttonCopyLog.clicked.connect(self.copy_log)

        logger.info("connected GUI slots")

    # Callbacks

    # Tab File IO

    def selected_file_changed(self):
        logger.info("Updating currentSpectrum plot")
        files = self.get_selected_files()
        if len(files) == 0:
            return

        logger.info("Selected files - %s", files)
        lastfile = files[-1]

        # Load file
        try:
            spectrum = file_io.load_file(lastfile)
        except Exception:
            logger.error(traceback.format_exc())
            return

        # Update metadata
        self.plainTextMetadata.setPlainText(spectrum.metadata.details)

        # Plot data
        ax = self.currentSpectrumPlot.canvas.axes
        ax.clear()
        ax.plot(spectrum.accumulations)
        ax.set_xlabel("Camera pixel [au]")
        ax.set_ylabel("Intensity [counts]")
        ax.figure.tight_layout()
        ax.figure.canvas.draw()
        self.currentSpectrumPlot.toolbar.update()

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
            try:
                spectrum = file_io.load_file(file)
                self.raw_spectra.append(spectrum)
                logger.info("Loaded data file - %s", file)
            except Exception:
                logger.error(traceback.format_exc())

        if not self.raw_spectra:
            return

        # Update processing controls
        spectrum_length = self.raw_spectra[0].nbins
        self.spinBoxLeftCrop.setMaximum(spectrum_length)
        self.spinBoxLeftCrop.setValue(0)
        self.spinBoxRightCrop.setMaximum(spectrum_length)
        self.spinBoxRightCrop.setValue(spectrum_length)
        self.spinBoxBubbleWidth.setMaximum(spectrum_length)
        self.spinBoxHWS.setMaximum(spectrum_length)
        self.spinBoxNormBand.setMaximum(spectrum_length)

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

        # Update xaxis dependant control
        self.spinBoxNormBand.setMaximum(max(xaxis))

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
        self.loadedDataPlot.toolbar.update()

    def plot_xref(self, xref: Spectrum):
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
        self.xrefPlot.toolbar.update()

    def plot_irf(self):
        logger.info("Plotting Instrument Response Function")
        # Update Y-ref plot
        ax = self.yrefPlot.canvas.axes
        ax.clear()
        if self.irf is not None:
            if self.xaxis is None:
                ax.plot(self.irf)
            else:
                ax.plot(self.xaxis, self.irf)
        ax.set_xlabel("Camera pixel [au]")
        ax.set_ylabel("Intensity [counts]")
        ax.figure.tight_layout()
        ax.figure.canvas.draw()
        self.yrefPlot.toolbar.update()

    # Tab Processing

    def left_crop_changed(self):
        logger.info("Left crop changed to %s", self.spinBoxLeftCrop.value())

        self.spinBoxRightCrop.setMinimum(self.spinBoxLeftCrop.value() + 10)

        self.plot_raw_spectra()

        if self.checkBoxAutoUpdate.isChecked():
            self.process_spectra()

    def right_crop_changed(self):
        logger.info("Right crop chaneg to %s", self.spinBoxRightCrop.value())

        self.spinBoxLeftCrop.setMaximum(self.spinBoxRightCrop.value() - 10)

        self.plot_raw_spectra()

        if self.checkBoxAutoUpdate.isChecked():
            self.process_spectra()

    def processing_changed(self):
        logger.info("Processing update - %s - changed", self.sender().objectName())
        if self.checkBoxAutoUpdate.isChecked():
            self.process_spectra()

    def plot_raw_spectra(self):
        logger.info("Updating Raw Spectra plot")
        # Update Spectra graph (in Processing tab)
        ax = self.rawDataPlot.canvas.axes
        ax.clear()

        # Plot raw spectra
        for s in self.raw_spectra:
            ax.plot(s.mean_spectrum)

        # Plot crop lines
        lc = self.spinBoxLeftCrop.value()
        rc = self.spinBoxRightCrop.value()
        ylim = ax.get_ylim()
        ax.plot(
            [lc, lc],
            ylim,
            color="tab:red",
        )
        ax.plot(
            [rc, rc],
            ylim,
            color="tab:red",
        )

        ax.set_xlabel("Camera pixel [au]")
        ax.set_ylabel("Intensity [counts]")
        ax.set_ylim(ylim)
        ax.figure.tight_layout()
        ax.figure.canvas.draw()
        self.rawDataPlot.toolbar.update()

    def process_spectrum(
        self, spectrum: Spectrum
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:

        spectrum_ = spectrum.accumulations
        background_ = spectrum.background

        # Tuncation
        lbound = self.spinBoxLeftCrop.value()
        rbound = self.spinBoxRightCrop.value()
        if spectrum.naccumulations == 1:
            spectrum_ = spectrum_[lbound:rbound]
        else:
            spectrum_ = spectrum_[lbound:rbound, :]
        if background_ is not None:
            background_ = background_[lbound:rbound]

        # CRR filters
        if self.checkBoxMultiCRR.isChecked():
            width = self.spinBoxMCRRWidth.value()
            threshold = self.spinBoxMCRRthreshold.value()
            if spectrum_.ndim > 1:
                spectrum_ = crfilter_multi(
                    spectrum_, width=width, disparity_threshold=threshold
                )
        if self.checkBoxSingleCRR.isChecked():
            width = self.spinBoxSCRRWidth.value()
            std_factor = self.spinBoxSCRRstd.value()
            spectrum_ = crfilter_single(spectrum_, width=width, std_factor=std_factor)

        # Background removal
        if background_ is not None:
            background_ = crfilter_single(background_)
            if background_.ndim != spectrum_.ndim:
                spectrum_ = spectrum_ - np.expand_dims(background_, axis=1)
            else:
                spectrum_ = spectrum_ - background_

        # Combining accumulations
        if spectrum.naccumulations > 1:
            spectrum_ = spectrum_.mean(axis=1)

        # IRF correction
        if self.irf is not None:
            spectrum_ = spectrum_ / self.irf[lbound:rbound]
        irf_correction = spectrum_

        # Baseline removal
        method = self.comboBoxBRAlgorithm.currentText()
        if method == "BubbleFill":
            width = self.spinBoxBubbleWidth.value()
            raman, baseline = bubblefill(spectrum_, min_bubble_widths=width)
        elif method == "IModPoly":
            poly_order = self.spinBoxPolyOrder.value()
            raman, baseline = imodpoly(spectrum_, poly_order=poly_order)
        elif method == "MorphBR":
            hws = self.spinBoxHWS.value()
            raman, baseline = morph_br(spectrum_, hws=hws)
        else:
            raman = spectrum_
            baseline = np.zeros(raman.shape)

        # Normalization
        if self.radioButtonMinMax.isChecked():
            raman = minmax(raman)
        elif self.radioButtonAUC.isChecked():
            raman = auc(raman)
        elif self.radioButtonSNV.isChecked():
            raman = snv(raman)
        elif self.radioButtonMaxBand.isChecked():
            if self.xaxis is not None:
                band_ix = (
                    np.argmin((self.xaxis - self.spinBoxNormBand.value()) ** 2) - lbound
                )
            else:
                band_ix = int(self.spinBoxNormBand.value())
            raman = maxband(raman, band_ix=band_ix)

        return raman, baseline, irf_correction

    def process_spectra(self):
        logger.info("Processing spectra")
        self.raman_spectra = []
        self.baseline_spectra = []
        self.irf_corrections = []
        for s in self.raw_spectra:
            try:
                raman, baseline, irf_correction = self.process_spectrum(s)
                self.raman_spectra.append(raman)
                self.baseline_spectra.append(baseline)
                self.irf_corrections.append(irf_correction)
            except Exception:
                logger.error(traceback.format_exc())

        self.plot_irf_corrections()
        self.plot_baseline_fit()
        self.plot_processed_spectra()

    def plot_processed_spectra(self):
        logger.info("Plotting processed spectra")

        ax = self.processedDataPlot.canvas.axes
        ax.clear()

        for raman in self.raman_spectra:
            if self.xaxis is not None:
                lbound = self.spinBoxLeftCrop.value()
                rbound = self.spinBoxRightCrop.value()
                xaxis = self.xaxis[lbound:rbound]
                ax.plot(xaxis, raman)
                ax.set_xlabel(r"Raman shift [cm$^{-1}$]")
            else:
                ax.plot(raman)
                ax.set_xlabel("Camera pixel")

        ax.set_ylabel("Intensity [counts]")
        ax.figure.tight_layout()
        ax.figure.canvas.draw()
        self.processedDataPlot.toolbar.update()

    def plot_baseline_fit(self):
        logger.info("Plotting baseline fits")

        ax = self.baselineFitPlot.canvas.axes
        ax.clear()

        for i, (s_before_br, baseline) in enumerate(
            zip(self.irf_corrections, self.baseline_spectra)
        ):
            c = tab10(i % 10)
            lbound = self.spinBoxLeftCrop.value()
            rbound = self.spinBoxRightCrop.value()
            if self.xaxis is not None:
                xaxis = self.xaxis[lbound:rbound]
                ax.plot(xaxis, s_before_br, alpha=0.75, color=c)
                ax.plot(xaxis, baseline, linewidth=1, color=c)
                ax.set_xlabel(r"Raman shift [cm$^{-1}$]")
            else:
                ax.plot(s_before_br, alpha=0.75, color=c)
                ax.plot(baseline, linewidth=1, color=c)
                ax.set_xlabel("Camera pixel")

        ax.set_ylabel("Intensity [counts]")
        ax.figure.tight_layout()
        ax.figure.canvas.draw()
        self.baselineFitPlot.toolbar.update()

    def plot_irf_corrections(self):
        logger.info("Plotting spectra after irf corrections")

        ax = self.irfCorrectionPlot.canvas.axes
        ax.clear()

        for irf_correction in self.irf_corrections:
            ax.plot(irf_correction)

        ax.set_ylabel("Intensity [counts]")
        ax.figure.tight_layout()
        ax.figure.canvas.draw()
        self.irfCorrectionPlot.toolbar.update()

    # Tab Log

    def copy_log(self):
        pyperclip.copy(self.plainTextLog.toPlainText())
        logger.info("copied log text")

    # Backend

    def get_selected_files(self) -> list:
        # Get files from selection
        indexes = self.treeViewFiles.selectedIndexes()
        file_names = [index.model().filePath(index) for index in indexes]
        file_names = set(file_names)
        file_paths = [Path(f) for f in file_names]

        # Remove unsupported files
        file_paths = [f for f in file_paths if file_io.is_file_supported(f)]

        return file_paths


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
