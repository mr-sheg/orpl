"""
Cosmic Ray
================

Provides Raman spectrum cosmic ray removal tools.
"""
import numpy as np
from scipy.ndimage import binary_dilation


def crfilter_single(
    signal: np.ndarray, width: int = 3, std_factor: float = 5
) -> np.ndarray:
    """
    crfilter_single Cosmic Ray filter for a single spectrum/accumulation.

    signal_filtered = crfilter_single(signal, width=3, std_factor=3)

    Parameters
    ----------
    signal : np.ndarray
        The signal to filter.
    width : float, optional
        The filter width, by default 3
    std_factor : float, optional
        The adaptative threshold standard deviation factor.
        Smaller value gives more sensitive filter, by default 3

    Returns
    -------
    signal_filtered : np.ndarray
        The filtered signal.
    """

    # normalize spectrum
    origin = signal.min()
    scale = signal.max()
    signal_normalized = signal - origin
    signal_normalized = signal_normalized / scale

    # find cosmic rays
    # second derivative of spectrum
    diff2 = np.diff(signal_normalized, n=2) ** 2
    threshold = diff2.mean() + std_factor * diff2.std()
    cosmic_ray = np.array([False for i in range(len(signal_normalized))])

    # boolean vector (true if CR)
    cosmic_ray[1:-1] = np.abs(diff2) > threshold

    # include nearest neighbors on each sides
    cosmic_ray = binary_dilation(cosmic_ray, structure=width * [1])

    # removes cosmic rays with linear interpolation
    xaxis = np.arange(len(signal_normalized))
    xaxis_no_cr = xaxis[np.invert(cosmic_ray)]
    spectrum_no_cr = signal_normalized[np.invert(cosmic_ray)]
    signal_filtered = np.interp(xaxis, xaxis_no_cr, spectrum_no_cr)

    # undo normalization
    signal_filtered = scale * signal_filtered
    signal_filtered = signal_filtered + origin

    return signal_filtered


def crfilter_multi(
    signals: np.ndarray, width: int = 3, disparity_threshold: float = 0.1
) -> np.ndarray:
    """
    crfilter_multi Cosmic Ray filter for a multi signal/accumulation acquisition.
    Uses deviation between related signals and find outliers for each wavelengths.
    Filters flagged cosmic rays with linear interpolation.

    signals_filtered = crfilter_multi(signals, width, std_factor)

    Parameters
    ----------
    signals : np.ndarray
        an array of signals (MxN), M are the individual signal and N are wavelengths
    width : float, optional
        filter window width, by default 3
    disparity_threshold : float, optional
        disparity threshold used for detection. Smaller value means
        more sensitive filter. disparity_threshold of 0.1 means a disparity of ~10%
        from singals' mean, by default 0.1

    Returns
    -------
    signals_filtered : np.ndarray
        The filtered signals
    """

    signals_filtered = signals.copy()
    xaxis = np.arange(signals.shape[1])
    mean = signals.mean(0)
    mean_normalized = mean / mean.sum()

    for i, signal in enumerate(signals_filtered):
        # Finding cosmic rays
        disparity = (
            np.abs(signal / signal.sum() - mean_normalized) / mean_normalized.max()
        )
        flagged_cr = disparity > disparity_threshold

        if flagged_cr.sum() == 0:
            # No detected cosmic rays
            continue

        # Widening detection with width parameter
        flagged_cr = binary_dilation(flagged_cr, structure=width * [1])

        # Removing cosmic rays with interpolation
        signal_filtered = np.interp(
            xaxis, xaxis[np.invert(flagged_cr)], signal[np.invert(flagged_cr)]
        )

        # Updating spectrum in spectra_
        signals_filtered[i, :] = signal_filtered

    return signals_filtered


class CRFilter:
    """
    Cosmic ray Filter removal utility.
    """
