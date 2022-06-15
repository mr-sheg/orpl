"""
Normalization
================

Functions and algorithms to normalize signals
"""
import numpy as np


def minmax(signal: np.ndarray) -> np.ndarray:
    """
    minmax normalize a signal for

    min(signal_) = 0
    max(signal_) = 1

    Usage
    -----
    signal_ = minmax(signal)

    Parameters
    ----------
    signal : np.ndarray
        a signal in vector form to normalize

    Returns
    -------
    signal_ : np.ndarray
        the normalized signal
    """
    signal_ = signal - signal.min()
    signal_ = signal_ / signal_.max()
    return signal_


def maxband(signal: np.ndarray, band_ix: int) -> np.ndarray:
    """
    maxband normalize a signal for

    min(signal_) = 0
    signal_[band_ix] = 1

    Usage
    -----
    signal_ = maxband(signal, band_ix)

    Parameters
    ----------
    signal : np.ndarray
        a signal in vector form to normalize

    band_ix : int
        the index (vector position) of the Raman band to normalize to an intensity of 1.

    Returns
    -------
    signal_ : np.ndarray
        the normalized signal
    """
    signal_ = signal - signal.min()
    signal_ = signal_ / signal_[band_ix]
    return signal_


def snv(signal: np.ndarray) -> np.ndarray:
    """
    snv (Standard Normal Variate) normalize a signal for
    mean(signal_) = 0
    std(signal_) = 1

    Usage
    -----
    signal_ = minmax(signal)

    Parameters
    ----------
    signal : np.ndarray
        a signal in vector form to normalize

    Returns
    -------
    signal_ : np.ndarray
        the normalized signal
    """
    signal_ = signal - signal.mean()
    signal_ = signal_ / signal_.std()
    return signal_


def auc(signal: np.ndarray) -> np.ndarray:
    """
    auc (Area Under Curve) normalize a signal for
    min(signal_) = 0
    sum(signal_) = 1

    Usage
    -----
    signal_ = minmax(signal)

    Parameters
    ----------
    signal : np.ndarray
        a signal in vector form to normalize

    Returns
    -------
    signal_ : np.ndarray
        the normalized signal
    """
    signal_ = signal - signal.min()
    signal_ = signal_ / signal_.sum()
    return signal_
