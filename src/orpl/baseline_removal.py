"""
Baseline Removal
================

Provides Raman spectrum baseline removal tools.
"""
from typing import Tuple

import numpy as np
from scipy.signal import savgol_filter


# njit decorator
def njit(*args, **kwargs):
    try:
        import numba

        return numba.njit(*args, **kwargs)

    except:
        warning_msg = "".join(
            [
                "Could not import numba. ",
                "Install numba to use JITed implementations of backend ",
                "functions for speed up of baseline removal algorithms",
            ]
        )

        from warnings import warn

        warn(warning_msg)

        def no_decorator(fn):
            return fn

        return no_decorator


# imodpoly


def imodpoly(
    spectrum: np.ndarray,
    poly_order: int = 6,
    precision: float = 0.005,
    max_iter: int = 1000,
    imod: bool = True,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    imodpoly splits a spectrum into it's raman and baseline components.
    Based on the IModPoly (or ModPoly if using imod=False) algorithm.

    Usage
    ------
    (raman, baseline) = imodpoly(spectrum,
                                 poly_order=6,
                                 precision=0.005,
                                 max_iter=1000,
                                 imod=True
                                 )

    Parameters
    ----------
    spectrum : np.ndarray
        the input spectrum
    poly_order : int, optional
        the polinomial fit's order, by default 6
    precision : float, optional
        the precision to reach. , by default 0.005
    max_iter : int, optional
        maximum number of iterations, by default 1000
    imod : bool, optional
        imod=True will use imodpoly
        imod=False will use modpoly, by default True

    Returns
    -------
    raman : np.ndarray
        the spectrum's raman component
    baseline : np.ndarray
        the spectrum's baseline component

    Reference
    ---------
    'Automated Autofluorescence Background Subtraction Algorithm for
    Biomedical Raman Spectroscopy'
    DOI : 10.1366/000370207782597003
    """

    i = 1
    converged = False
    raman_data = np.array(spectrum)
    xaxis = np.array(range(0, raman_data.shape[0]))
    std_dev = 0
    while not converged and i < max_iter:
        poly_fit = np.polyval(np.polyfit(xaxis, raman_data, poly_order), xaxis)
        residual = raman_data - poly_fit
        previous_std_dev = std_dev
        std_dev = np.std(residual)

        # if first iteration -> peak removal
        if imod:
            # IModPoly
            if i == 1:
                ind = np.where(raman_data > poly_fit + std_dev)[0]
                raman_data[ind] = poly_fit[ind] + std_dev

            ind = np.where(raman_data > poly_fit + std_dev)[0]
            raman_data[ind] = poly_fit[ind] + std_dev

        else:
            # ModPoly
            if i == 1:
                ind = np.where(raman_data > poly_fit)[0]
                raman_data[ind] = poly_fit[ind]

            ind = np.where(raman_data > poly_fit)[0]
            raman_data[ind] = poly_fit[ind]

        converged = np.abs((std_dev - previous_std_dev) / std_dev) < precision
        i = i + 1

    baseline = poly_fit
    raman = spectrum - baseline
    return raman, baseline


# Morphological transformations


@njit(cache=True)
def erosion(signal: list, hws: list) -> list:
    """
    erosion computes the morphological erosion of a singal using
    a plane structuring element window.

    Usage
    -----
    signal_ = erosion(signal, hws)

    Parameters
    ----------
    signal : list
        the input signal
    hws : list
        the Half Window Size

    Returns
    -------
    signal_ : list
        the eroded signal
    """
    eroded_f = []
    for i in range(len(signal)):
        left_bound = i - hws[i]  # left bound of window
        if left_bound < 0:
            left_bound = 0
        right_bound = i + hws[i] + 1  # right bound of window
        if right_bound > len(signal):
            right_bound = len(signal)
        eroded_f.append(min(signal[left_bound:right_bound]))
    return eroded_f


@njit(cache=True)
def dilation(signal: list, hws: list) -> list:
    """
    dilation computes the morphological dilation of a signal using
    a plane structuring element window.

    Usage
    -----
    signal_ = dilation(signal, hws)

    Parameters
    ----------
    signal : list
        the input signal
    hws : list
        the Half Window Size

    Returns
    -------
    signal_ : list
        the dilated signal
    """

    diladed_f = []
    for i in range(len(signal)):
        lbound = i - hws[i]  # left bound of window
        if lbound < 0:
            lbound = 0
        rbound = i + hws[i] + 1  # right bound of window
        if rbound > len(signal):
            rbound = len(signal)
        diladed_f.append(max(signal[lbound:rbound]))
    return diladed_f


@njit(cache=True)
def opening(signal: list, hws: list) -> list:
    """
    opening computes the morphological opening of a signal using
    a plane structuring element window.

    Usage
    -----
    signal_ = opening(signal, hws)

    Parameters
    ----------
    signal : list
        the input signal
    hws : list
        the Half Window Size

    Returns
    -------
    signal_ : list
        the opened signal

    Notes
    -----
    The morphological opening is the same as an erosion followed
    by a dilation : opening{X} = dilation{erosion{X}}
    """

    eroded_f = erosion(signal, hws)
    opened_f = dilation(eroded_f, hws)
    return opened_f


@njit(cache=True)
def bopening(signal: list, hws: list) -> list:
    """
    bopening computes the better opening (see reference) of a signal using
    a structuring element window.

    Usage
    -----
    signal_ = opening(signal, hws)

    Parameters
    ----------
    signal : list
        the input signal
    hws : list
        the the Half Window Size

    Returns
    -------
    signal_ : list
        the b-opened signal

    Reference
    ---------
    'Morphology-Based Automated Baseline Removal for Raman
    Spectra of Artistic Pigments'
    DOI:10.1366/000370210791414281
    """

    opened_f = opening(signal, hws)  # \gamma(f)
    dilated_opening = dilation(opened_f, hws)
    eroded_opening = erosion(opened_f, hws)
    opened_mod = [
        (dilated_opening[i] + eroded_opening[i]) / 2 for i in range(len(signal))
    ]  # \gamma'(f)
    bopened = [min([opened_mod[i], opened_f[i]]) for i in range(len(signal))]
    return bopened


# Morphology based baseline removal


def morph_br(spectrum: np.ndarray, hws: int) -> np.ndarray:
    """
    morph_br splits a spectrum into it's raman and baseline components

    Usage
    -----
    raman, baseline = morph_br(spectrum, hws)

    Parameters
    ----------
    spectrum : np.ndarray
        the input spectrum
    hws : int
        the Half Window Size

    Returns
    -------
    raman : np.ndarray
        the spectrum's raman component
    baseline : np.ndarray
        the spectrum's baseline component

    Reference
    ---------
    'Morphology-Based Automated Baseline Removal for Raman
    Spectra of Artistic Pigments'
    DOI:10.1366/000370210791414281
    """
    if isinstance(hws, int):
        if hws < 1:
            raise ValueError("Minimal hws is 1")
        hws = hws * np.ones(len(spectrum))
        hws = hws.astype(int)
    elif isinstance(hws, list):
        hws = np.array(hws).astype(int)
    elif isinstance(hws, np.ndarray):
        hws = hws.astype(int)
    else:
        raise TypeError("hws must be one of the following ; INT, LIST or NDARRAY")

    spectrum = np.array(spectrum)
    baseline = np.array(bopening(spectrum, hws))
    raman = np.array([spectrum[i] - baseline[i] for i in range(len(spectrum))])
    return raman, baseline


# Bubblefill


@njit(cache=True)
def grow_bubble(
    spectrum: np.ndarray, alignment: str = "center"
) -> Tuple[np.ndarray, int]:
    """
    grow_bubble grows a bubble until it touches a spectrum.

    Usage
    -----
    bubble, touching_point = grow_bubble(spectrum, alignment)

    Parameters
    ----------
    spectrum : np.ndarray
        the input spectrum
    alignment : str, optional
        the alignment of the bubble to be grown. Possible values are
        ['left', 'right' and 'center'].
        If 'left', the bubble will be centered in x=0 and will have a width
        of 2x len(spectrum)
        If 'right', the bubble will be centered in x=len(spectrum) and will
        have a width of 2x len(spectrum)
        If 'center', the bubble will be centered in x=len(spectrum)/2 and
        will have a width of len(spectrum)
        , by default "center"

    Returns
    -------
    bubble : np.ndarray
        the grown bubble
    touching_point : int
        the x-coordinate where it touched the spectrum and *popped*.
    """
    xaxis = np.arange(len(spectrum))

    # Ajusting bubble parameter based on alignment
    if alignment == "left":
        # half bubble right
        width = 2 * len(spectrum)
        middle = 0
    elif alignment == "right":
        # half bubble left
        width = 2 * len(spectrum)
        middle = len(spectrum)
    else:
        # Centered bubble
        width = len(spectrum)
        middle = len(spectrum) / 2

    squared_arc = (width / 2) ** 2 - (xaxis - middle) ** 2  # squared half circle
    # squared_arc[squared_arc < 0] = 0
    bubble = np.sqrt(squared_arc) - width
    # find new intersection
    touching_point = (spectrum - bubble).argmin()

    # grow bubble until touching
    bubble = bubble + (spectrum - bubble).min()

    return bubble, touching_point


@njit(cache=True)
def keep_largest(baseline: np.ndarray, bubble: np.ndarray) -> np.ndarray:
    """
    keep_largest selectively updates a baseline region with a bubble, depending
    on which has a greater y-value.

    Usage
    -----
    baseline_ = keep_largest(baseline, bubble)

    Parameters
    ----------
    baseline : np.ndarray
        an input baseline
    bubble : np.ndarray
        an input bubble (usually computed with grow_bubble())

    Returns
    -------
    baseline_ : np.ndarray
        the updated baseline
    """
    for i, _ in enumerate(baseline):
        if baseline[i] < bubble[i]:
            baseline[i] = bubble[i]
    return baseline


def bubbleloop(
    spectrum: np.ndarray, baseline: np.ndarray, min_bubble_widths: list
) -> np.ndarray:
    """
    bubbleloop itteratively updates a baseline estimate by growing bubbles under a spectrum.

    Usage
    -----
    baseline = bubbleloop(spectrum, baseline, min_bubble_widths)

    Parameters
    ----------
    spectrum : np.ndarray
        the input spectrum
    baseline : np.ndarray
        the initial baseline should be akin to np.zeros(spectrum.shape)
    min_bubble_widths : list
        the minimum bubble widths to use. Can be an array-like or int.
        if array-like -> must be the same length as spectrum and baseline. Useful to specify
        different bubble sizes based on x-coordinates.
        if int -> will use the same width for all x-coordinates.

    Returns
    -------
    baseline : np.ndarray
        the updated baseline
    """
    # initial range is always 0 -> len(s). aka the whole spectrum
    # bubblecue is a list of bubble x-coordinate span as
    # [[x0, x2]_0, [x0, x2]_1, ... [x0, x2]_n]
    # additional bubble regions are added as the loop runs.
    range_cue = [[0, len(spectrum)]]

    i = 0
    while i < len(range_cue):
        # Bubble parameter from bubblecue
        left_bound, right_bound = range_cue[i]
        i += 1

        if left_bound == right_bound:
            continue

        if isinstance(min_bubble_widths, int):
            min_bubble_width = min_bubble_widths
        else:
            min_bubble_width = min_bubble_widths[(left_bound + right_bound) // 2]

        if left_bound == 0 and right_bound != (len(spectrum)):
            # half bubble right
            alignment = "left"
        elif left_bound != 0 and right_bound == (len(spectrum)):
            alignment = "right"
            # half bubble left
        else:
            # Reached minimum bubble width
            if (right_bound - left_bound) < min_bubble_width:
                continue
            # centered bubble
            alignment = "center"

        # new bubble
        bubble, relative_touching_point = grow_bubble(
            spectrum[left_bound:right_bound], alignment
        )
        touching_point = relative_touching_point + left_bound

        # add bubble to baseline by keeping largest value
        baseline[left_bound:right_bound] = keep_largest(
            baseline[left_bound:right_bound], bubble
        )
        # Add new bubble(s) to bubblecue
        if touching_point == left_bound:
            range_cue.append([touching_point + 1, right_bound])
        elif touching_point == right_bound:
            range_cue.append([left_bound, touching_point - 1])
        else:
            range_cue.append([left_bound, touching_point])
            range_cue.append([touching_point, right_bound])

    return baseline


def bubblefill(
    spectrum: np.ndarray, min_bubble_widths: list = 50, fit_order: int = 1
) -> Tuple[np.ndarray, np.ndarray]:
    """
    bubblefill splits a spectrum into it's raman and baseline components.

    Usage
    -----
    raman, baseline = bubblefill(spectrum, bubblewidths, fitorder)

    Parameters
    ----------
    spectrum : np.ndarray
        the input spectrum
    min_bubble_widths: list or int
        is the smallest width allowed for bubbles. Smaller values will
        allow bubbles to penetrate further into peaks resulting
        in a more *aggressive* baseline removal. Larger values are more
        *concervative* and might the computed underestimate baseline.
        use list to specify a minimum width that depends on the
        x-coordinate of the bubble. Make sure len(bubblewidths) = len(spectrum).
        Otherwise if bubblewidths [int], the same width is used for all x-coordinates.
    fit_order : int
        the order of the polynomial fit used to remove the *overall* baseline slope.
        Recommendend value is 1 (for linear slope).
        Higher order will result in Runge's phenomena and
        potentially undesirable and unpredictable effects.
        fitorder = 0 is the same as not removing the overall baseline slope

    Returns
    -------
    raman : np.ndarray
        the spectrum's raman component
    baseline : np.ndarray
        the spectrum's baseline component

    Reference
    ---------
    Guillaume Sheehy 2021-01
    """
    xaxis = np.arange(len(spectrum))

    # Remove general slope
    poly_fit = np.poly1d(np.polyfit(xaxis, spectrum, fit_order))(xaxis)
    spectrum_ = spectrum - poly_fit

    # Normalization
    smin = spectrum_.min()  # value needed to return to the original scaling
    spectrum_ = spectrum_ - smin
    scale = spectrum_.max() / len(spectrum)
    spectrum_ = spectrum_ / scale  # Rescale spectrum to X:Y=1:1 (square aspect ratio)

    baseline = np.zeros(spectrum_.shape)

    # Bubble loop (this is the bulk of the algorithm)
    baseline = bubbleloop(spectrum_, baseline, min_bubble_widths)

    # Bringing baseline back in original scale
    baseline = baseline * scale + poly_fit + smin

    # Final smoothing of baseline (only if bubblewidth is not a list!!!)
    if not isinstance(min_bubble_widths, int):
        filter_width = max(min(min_bubble_widths), 10)
    else:
        filter_width = max(min_bubble_widths, 10)
    # print(filter_width)
    baseline = savgol_filter(baseline, int(2 * (filter_width // 4) + 3), 3)

    raman = spectrum - baseline

    return raman, baseline
