'''
Tools to create synthetic raman spectra for benchmarking processing algorithms.
'''

import json
import os
from math import log, sqrt

# Dependencies
import matplotlib.pyplot as plt
import numpy as np

# path to this file's directory
path = os.path.split(__file__)[0]


def gen_raman(x=None,
              peak_centers=[265, 500], peak_heights=[0.5, 0.7],
              peak_fwhms=[5, 15], normalize=True, plotting=False):
    '''
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
    '''
    # set default values
    if x is None:
        x = np.arange(1000)
    # Generating raman spectrum
    raman_ = np.zeros(x.shape)
    for a, b, fwhm in zip(peak_heights, peak_centers, peak_fwhms):
        c = fwhm / 2 / sqrt(2 * log(2))
        raman_peak = a * np.exp(-(x - b)**2 / 2 / c**2)
        raman_ += raman_peak
        if plotting:
            plt.plot(raman_peak)
    if normalize:
        raman_ = raman_ / raman_.max()
    return raman_


def gen_fluo(coefficients, x=None, normalize=True):
    '''
    Generates a fluorescence signal as a polynomial of deg=len(coefficients).

        Inputs:

            - coefficients [list]
                list of the coefficients of the polynomial [c0, c1, c2, ...]

            - x=np.arange(1000) [NDARRAY]
                numpy array that contains the x axis used for the polynomial

            - normalize
    '''
    # set default values
    if x is None:
        x = np.arange(1000)
    # Generating fluorescence spectrum
    fluo_ = np.zeros(x.shape)
    i = 0
    for c in coefficients:
        fluo_ += c * x**i
        i += 1
    if normalize:
        fluo_ = fluo_ / fluo_.max()
    return fluo_


def gen_synthetic_spectrum(preset,
                           raman_flu_ratio,
                           noise_level,
                           normalize=True,
                           x=None):
    '''
    Generates a synthetic raman spectrum from a pure raman, fluorescence and
    noise signal. The generation uses a specified preset from the presets.json
    file.
        spectrum, raman, fluo, noise = gen_synthetic_spectrum(...)

        Inputs:

            - preset [string]
                a string that contains the preset to be used for the
                generation. Note that the preset MUST be defined in preset.json

            - raman_fluo_ratio
                the desired scalar ratio between max(fluo) and max(raman). Note
                that the synthetic spectra are always normalized to 1.

            - noise_level
                the desired standard deviation of the noise spectrum. Note that
                the noise follows a normal distribution.

            - normalize=True:
                if true, the outputed spectrum will be normalized (max=1)

            - x=None
                the desired xaxis [camera pixel] for the generated spectrum. By
                default, x=0,1,2,...,998,999.

        Outputs:

            - spectrum [NDARRAY]
                a synthetic spectrum = fluo + raman_flu_ratio * Raman + noise

            - raman [NDARRAY]
                the pure raman spectrum

            - fluo [NDARRAY]
                the pure fluorescence spectrum

            - noise [NDARRAY]
                the pure noise spectrum

    '''
    # set default values
    if x is None:
        x = np.arange(1000)
    # load presets
    presets = json.load(open(path + '/presets.json'))
    # check if preset exists
    if preset not in presets.keys():
        raise ValueError(
            'preset not available. Choose from {}'.format(
                list(presets.keys())))
    # Generation of Raman
    raman = gen_raman(peak_centers=presets[preset]['peak_centers'],
                      peak_heights=presets[preset]['peak_heights'],
                      peak_fwhms=presets[preset]['peak_fwhms'])
    raman = raman_flu_ratio * raman
    # Generation of fluorescence
    fluo = gen_fluo(coefficients=presets[preset]['fluo_coefs'])
    # Generation of noise
    noise = np.random.normal(loc=0,
                             scale=noise_level,
                             size=len(raman))
    # Combining everything
    spectrum = fluo + raman
    # Normalization (max=1)
    if normalize:
        scale = 1 / spectrum.max()
        raman = scale * raman
        fluo = scale * fluo
        spectrum = scale * spectrum
    spectrum += noise

    return spectrum, raman, fluo, noise
