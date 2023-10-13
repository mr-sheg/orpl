"""
System Response Correction
================

Provides Raman spectrum instrument/system response correction tools and xaxis calibration.
"""
import itertools

import numpy as np
from scipy.signal import find_peaks

# Unit conversion utilities


def nm2icm(nm: float, nm0: float = 785) -> float:
    """
    nm2icm Converts wavelenghts from nanometers to cm-1 Raman shift

    Usage
    -----
    icm = nm2icm(nm, nm0=785)

    Parameters
    ----------
    nm : float
        wavelength in [nm]
    nm0 : float, optional
        wavelenght of the excitation [nm]

    Returns
    -------
    float
    icm : Raman shift in [cm-1]
    """
    nm = np.array(nm)
    icm = (1 / nm0 - 1 / nm) * 1e7
    return icm


def icm2nm(icm: float, nm0: float = 785) -> float:
    """
    icm2nm Converts an Raman shift [cm-1] into a wavelength [nm].

    Usage
    -----

    nm = icm2nm(icm, nm0=785)

    Parameters
    ----------
    icm : float
        Raman shift in [cm-1]
    nm0 : float, optional
        wavelenght of excitation in [nm], by default 785

    Returns
    -------
    float
    nm : wavelength in [nm]
    """
    icm = np.array(icm)
    nm = 1 / (1 / nm0 - icm * 1e-7)
    return nm


# Xaxis tools
def truncate(signal: np.ndarray, start: int = None, stop: int = None) -> np.ndarray:
    """
    truncate the input signal between start and stop points

    Parameters
    ----------
    signal : np.ndarray
        an input signal, can be a vector or an array. If array, make sure spectra are aligned
        vertically in the array.
    start : int, optional
        start point of the truncation, by default 0
    stop : int, optional
        stop point of the truncation, by default signal.shape[0]

    Returns
    -------
    np.ndarray
        the truncated signal
    """

    # Defaults
    if start is None:
        start = 0
    if stop is None:
        stop = signal.shape[0]

    # Truncate
    if signal.ndim > 1:
        signal = signal[start:stop, :]
    else:
        signal = signal[start:stop]

    return signal


def find_npeaks(
    signal: np.ndarray, ntarget: int, metric: str = "prominence"
) -> np.ndarray:
    """
    find_npeaks finds ntarget peaks in a signal by automatically adjusting
    the threshold of scipy's find_peaks function with a bisection method.

    Usage
    -----
    peak_locations = find_npeaks(signal, ntarget, metric)

    Parameters
    ----------
    spectrum : np.ndarray
        input signal
    ntarget : int
        number of peak to find
    metric : str, optional
        metric used for peak detection, by default "prominence"
        possible metric are ['prominence', 'height']

    Returns
    -------
    peak_locations : np.ndarray
        the index locations of the peaks found in the input signal

    """
    # check if metric is supported
    supported = ["prominence", "height"]
    if metric not in supported:
        raise ValueError("Unsupported metric. Possible metric are " + str(supported))

    # Normalize signal
    spectrum_ = signal / signal.max()
    threshold = 1

    npeakfound = 0
    while npeakfound is not ntarget:
        if metric == "prominence":
            peak_locations, _ = find_peaks(spectrum_, prominence=threshold)
        elif metric == "height":
            peak_locations, _ = find_peaks(spectrum_, height=threshold)

        npeakfound = peak_locations.size

        # Ajust threshold with bisection method
        if npeakfound > ntarget:
            threshold = 1.5 * threshold
        else:
            threshold = 0.5 * threshold

    return peak_locations


def xaxis_from_ref(
    signal: np.ndarray, refx: np.ndarray, refy: np.ndarray, npks: int, deg: int = 2
) -> np.ndarray:
    """
    xaxis_from_ref generates an xaxis for a spectrum based on a reference
    Experimental spectrum peaks are compared with reference spectrum peaks and its
    reference xaxis to generate the xaxis of the experimental spectrum.

    Usage
    -----

    xaxis = xaxis_from_ref(signal, refx, refy, npks, deg)

    Parameters
    ----------
    signal : np.ndarray
        input measured signal
    refx : np.ndarray
        reference signal (y)
    refy : np.ndarray
        reference xaxis
    npks : int
        number of peaks to use. Peaks are identified with find_npeaks()
    deg : int, optional
        the degree of the xaxis polynomial model, by default 2

    Returns
    -------
    xaxis : np.ndarray
        the generated xaxis
    """
    # Normalization of spectrum
    expy = signal / signal.max()
    refy = refy / refy.max()

    # Find peaks
    exp_pid = find_npeaks(expy, npks)
    ref_pid = find_npeaks(refy, npks)

    ref_p = refx[ref_pid]

    coefs = np.polyfit(exp_pid, ref_p, deg=deg)
    xaxis = np.polynomial.polynomial.polyval(np.arange(expy.size), coefs[::-1])
    return xaxis


def xaxis_from_peaks(
    signal: np.ndarray, peaks: np.ndarray, deg: int = 2
) -> (np.ndarray, float):
    """
    xaxis_from_peaks generates an xaxis for a signal based on a list of peak
    positions (nm, cm-1, ...).

    The output is heavily dependent on the find_npeaks peak finder.

    Usage
    -----
    xaxis, residual = xaxis_from_peaks(signal, peaks, deg)

    Parameters
    ----------
    signal : np.ndarray
        input signal
    peaks : np.ndarray
        list of peak positions.
    deg : int, optional
        the degree of the xaxis polynomial model, by default 2, by default 2

    Returns
    -------
    xaxis : np.ndarray
        the generated xaxis

    residual : float
        the polynomial fit residual between the signal's detected peaks and the provided
        peaks.
    """
    # Normalization of spectrum
    expy = signal / signal.max()

    # Find peaks
    npks = len(peaks)
    exp_pid = find_npeaks(expy, npks)

    coefs, residual, _, _, _ = np.polyfit(exp_pid, peaks, deg=deg, full=True)
    residual = float(residual)

    xaxis = np.polynomial.polynomial.polyval(np.arange(expy.size), coefs[::-1])

    return xaxis, residual


def autogenx(signal: np.ndarray, preset: str = "tylenol", deg: int = 2) -> np.ndarray:
    """
    autogenx automatic xaxis generation from preset.

    Usage
    ------
    xaxis = autogenx(spectrum, preset, deg)

    Parameters
    ----------
    signal : np.ndarray
        sample measured spectrum. Raman peaks should be easily visible for
        better results.
    preset : str, optional
        name of a preset to use.
                    choose from ['tylenol', 'nylon'], by default "tylenol"
    deg : int, optional
        _description_, by default 2

    Returns
    -------
    xaxis : np.ndarray
        the generated xaxis [cm-1]
    """
    preset_pks_pos = {
        "tylenol": [797, 858, 1169, 1237, 1324, 1609, 1648],
        "nylon": [956, 1064, 1132, 1235, 1299, 1443, 1632],
    }

    if preset not in preset_pks_pos:
        raise ValueError(f"Invalid preset. Choose from {preset_pks_pos}")

    # Compute xaxis for npeaks combinations in preset peak lists
    # Selecting 5 peaks among the preset's 7 seems good for now, might need to change
    # for something more systematic later... #TODO?
    npeaks = 5
    axises = []
    residuals = []
    for peaks in itertools.combinations(preset_pks_pos[preset], r=npeaks):
        xaxis, residual = xaxis_from_peaks(signal, peaks)
        axises.append(xaxis)
        residuals.append(residual)

    # Get best xaxis from attempts based on best residual
    xaxis = axises[np.argmin(residuals)]

    return xaxis


# Intensity calibrations (y-axis)

# NIST correction
NIST_COEFS = [
    9.71937e-02,
    2.28325e-04,
    -5.86762e-08,
    2.16023e-10,
    -9.77171e-14,
    1.15596e-17,
]


def compute_irf(measured_nist: np.ndarray, xaxis: np.ndarray = None) -> np.ndarray:
    """
    compute_irf computes an Instrument Response Function (IRF) from a measured
    NIST raman spectrum. The IRF can be used to perform a relative intensity
    correction of a measured spectrum;

    corrected_spectrum = measured_spectrum / IRF

    Usage
    ------
        IRF = getCorrectionCurve(measured_nist, xaxis=None)

    Parameters
    ----------
    measured_nist : np.ndarray
        Measured NIST standard spectrum
    xaxis : np.ndarray, optional
        xaxis of the system in cm-1 (should match size of measured_nist).
        If None, the computation will be made in camera pixels and will not be
        accurate as the NIST coefficients are given in cm-1 units.
        by default None

    Returns
    -------
    IRF : np.ndarray
        The system instrument response
    """
    # computing theoretical NIST response for a system's WL range
    if xaxis is None:
        xaxis = np.array(range(0, len(measured_nist)))

    nist_theoretical = np.zeros(xaxis.shape)
    for i, coef in enumerate(NIST_COEFS):
        nist_theoretical += coef * xaxis**i

    # Computing correction curve
    # measured_nist = measured_nist / measured_nist.max()
    instrument_response = measured_nist / nist_theoretical
    instrument_response = instrument_response / instrument_response.max()

    return instrument_response
