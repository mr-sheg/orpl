"""
Cosmic Ray
================

Provides Raman spectrum evaluation metrics.
"""
import numpy as np
from orpl.normalization import snv


def raman_snr(
    raman: np.array, baseline: np.array, exposure_time: float, laser_power: float
) -> np.array:
    """
    raman_snr computes the raman signal to noise ratio as described in Dallaire2020.

    snr = raman_snr(raman, baseline, exposure_time, laser_power)

    Parameters
    ----------
    raman : np.array
        An array of raman spectrum. Repeated measurements are along lines, wavelengths are
        along columns
    baseline : np.array
        An array of baseline spectrum. Same configuration as for raman.
    exposure_time : float
    laser_power : float

    Returns
    -------
    np.array
    snr : The computed snr spectrum
    """
    nb_spectrum = raman.shape[0]  # number of spectrum (aka nb of repeated measurements)
    average_raman = raman.mean(axis=1)
    average_baseline = baseline.mean(axis=1)
    snr = (
        np.sqrt(nb_spectrum * exposure_time * laser_power)
        * average_raman
        / np.sqrt(average_raman + average_baseline)
    )
    return snr


def ssdeviation(raman: np.ndarray) -> float:
    """
    ssdeviation computes the average signed squared deviation of a Raman spectrum to its mean
    to be used as a general purpose spectrum quality metric/factor.

    Usage
    -----
    quality = ssdeviation(raman)

    Parameters
    ----------
    raman : np.ndarray
        an input raman spectrum. Normalization has no effect.

    Returns
    -------
    quality : float
        the quality of the raman spectrum as computed by the signed squared deviation metric.
    """
    raman_ = snv(raman)
    deviation_sign = np.sign(raman_)
    deviation2 = (raman_) ** 2
    quality_factor = (deviation_sign * deviation2).mean()
    return quality_factor
