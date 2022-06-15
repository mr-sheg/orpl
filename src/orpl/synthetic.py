"""
Tools to create synthetic raman spectra for benchmarking processing algorithms.
"""

import json
from math import log, sqrt
from importlib import resources

# Dependencies
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import savgol_filter

# loads synthetic presets
with resources.open_text(
    "orpl.data", "synthetic_presets.json", encoding="utf8"
) as preset_path:
    SYNTHETIC_PRESETS = json.load(preset_path)


def gen_raman(
    peak_centers: list,
    peak_heights: list,
    peak_fwhms: list,
    xaxis=None,
    normalize=True,
    plotting=False,
):
    """
    Generates a synthetic Raman spectrum and returns it in a vector (raman_).

        Inputs:
            - x=np.arange(0,1000) [NDARRAY]
                x axis of the spectrum [integers]

            - peak_centers=[265, 500] [list]
                list that contains the raman peak center positions.

            - peak_heights=[0.5, 0.7] [list]
                list that contains the raman peak heights.

            - peak_fwhms=[5, 15] [list]
                list that contains the raman peak full width at half maximum.

            - normalize=True
                if true, the raman spectra will be normalized raman_.max()=1

            - plotting=False
                if true, the function will plot the peaks as they are generated

        Output:

            - raman_ [NDARRAY]
                the total synthetic raman spectrum
    """
    # set default values
    if xaxis is None:
        xaxis = np.arange(1000).astype(float)

    # Generating raman spectrum
    raman_ = np.zeros(xaxis.shape)

    for peak_height, peak_center, fwhm in zip(peak_heights, peak_centers, peak_fwhms):
        c = fwhm / 2 / sqrt(2 * log(2))
        raman_peak = peak_height * np.exp(-((xaxis - peak_center) ** 2) / 2 / c**2)
        raman_ += raman_peak
        if plotting:
            plt.plot(raman_peak)

    if normalize:
        raman_ = raman_ / raman_.max()

    return raman_


def gen_baseline(coefficients, xaxis=None, normalize=True):
    """
    Generates a parametric baseline signal as a polynomial of
    deg=len(coefficients).

        Inputs:

            - coefficients [list]
                list of the coefficients of the polynomial [c0, c1, c2, ...]

            - x=np.arange(1000) [NDARRAY]
                numpy array that contains the x axis used for the polynomial

            - normalize
    """
    # set default values
    if xaxis is None:
        xaxis = np.arange(1000).astype(float)

    # Generating baseline spectrum
    baseline = np.zeros(xaxis.shape)
    for i, coef in enumerate(coefficients):
        if i == 0:
            baseline += coef
        else:
            sign = coef / abs(coef)
            coef = pow(abs(coef), 1 / i)
            baseline += sign * (coef * xaxis) ** i

    if normalize:
        baseline = baseline / baseline.max()
    return baseline


def gen_synthetic_spectrum(
    preset, rb_ratio=1, noise_std=0, baseline_preset=None, normalize=True, xaxis=None
):
    """
    Generates a synthetic raman spectrum from a pure raman, baseline and
    noise signal. The generation uses a specified preset from the presets.json
    file.
        spectrum, raman, baseline, noise = gen_synthetic_spectrum(...)

        Inputs:

            - preset [string]
                a string that contains the preset to be used for the
                generation. Note that the preset MUST be defined in preset.json

                Note: if baseline_preset is not specified [default:None], a
                parametric baseline for the specified preset will be used.
                Do not use this to test baseline removal algorithm!

            - rb_ratio=1 [float]
                Scalar ratio between max(baseline) and max(raman).
                Note that the synthetic spectra are normalized to min(spectrum) = 0
                and max(spectrum) = 1

            - noise_std=0 [float]
                the desired standard deviation of the noise spectrum.
                The noise signal follows a normal distribution.

            - baseline_preset=None [string]
                Experimental baseline signals (WITHOUT RAMAN) are available in
                the preset file. These baselines can be used instead of
                parametric ones to test baseline removal algorithms. Currently,
                the available baseline_presets are ['aluminium', 'nigrosin'].

            - normalize=True [Bool]
                if true, the outputed spectrum will be normalized (max=1)

            - x=None [NDARRAY]
                the desired xaxis [camera pixel] for the generated spectrum. By
                default, x=0,1,2,...,998,999.

        Outputs:

            - spectrum [NDARRAY]
                a synthetic spectrum = baseline + rb_ratio * Raman +
                noise

            - raman [NDARRAY]
                the pure raman spectrum

            - baseline [NDARRAY]
                the pure baseline spectrum

            - noise [NDARRAY]
                the pure noise spectrum

    """
    # set default values
    if xaxis is None:
        xaxis = np.arange(1000).astype(float)

    # check if preset exists
    available_presets = SYNTHETIC_PRESETS.keys()
    if preset not in available_presets:
        raise ValueError(f"preset not available. Choose from {available_presets}")

    # Generation of Raman
    raman = gen_raman(
        peak_centers=SYNTHETIC_PRESETS[preset]["peak_centers"],
        peak_heights=SYNTHETIC_PRESETS[preset]["peak_heights"],
        peak_fwhms=SYNTHETIC_PRESETS[preset]["peak_fwhms"],
    )
    raman = rb_ratio * raman

    # Generation of baseline
    if baseline_preset is None:
        baseline = gen_baseline(
            coefficients=SYNTHETIC_PRESETS[preset]["baseline_coefs"]
        )
    else:
        # check for baseline_preset in presets.json
        available_baselines = SYNTHETIC_PRESETS["baselines"].keys()
        if baseline_preset not in available_baselines:
            raise ValueError(
                f"baseline preset not available. Choose from {available_baselines}"
            )
        # load baseline from presets.json
        baseline = SYNTHETIC_PRESETS["baselines"][baseline_preset]
        # interpolation of baseline to match xaxis
        baseline = np.interp(xaxis, np.arange(len(baseline)).astype(float), baseline)
        # smooth baseline
        baseline = savgol_filter(baseline, window_length=31, polyorder=3)

    # Normalization of baseline
    baseline = baseline - baseline.min()
    baseline = baseline / baseline.max()

    # Generation of noise
    noise = np.random.normal(loc=0, scale=noise_std, size=len(raman))
    # noise = noise - noise.min()

    # Combining everything
    spectrum = baseline + raman + noise

    # Normalization (max=1)
    if normalize:
        scale = 1 / spectrum.max()
        raman = scale * raman
        baseline = scale * baseline
        spectrum = scale * spectrum

    return spectrum, raman, baseline, noise
