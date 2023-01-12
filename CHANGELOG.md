# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `bubblegif` module to create animated gifs of the bubblefill algorithm

### Changed

- Renamed the `ssdeviation()` function to `addi()` in the `metrics` module
- Updated Readme

## [0.1] - 2022-06-15

### First open sourced released version!!!

### Added

- imports statements for every modules in ORPL's `__init__` so you can now `import orpl` instead of needing `from orpl import ...`

## [0.0.4] - 2022-05-05

### Added

- `ssdeviation` in the `metrics` module
  - this function computes a new quality factor for a Raman spectrum.
  - the quality factor is based on the average signed square deviation of the spectrum to its mean

### Changed

- `crfilter_single` no longer uses binary opening to reject cosmic ray if not wide enough
- `crfilter_single` second derivative is squared. This fixed CR not being detected if d2 was negative
- `crfilter_single` std_factor was increased to reduce the effects of squaring the second derivative

### Removed

- removed import of `binary_opening` from the `cosmic_ray` as it is no longer used

## [0.0.3] - 2022-04-14

### Added

- Added `normalization` module with `minmax()`, `snv()` and `auc()` methods

### Changed

- `crfilter_multi` now uses area under curve normalisation instead of max values.
- `gen_synthetic_spectrum` now uses `noise_std` parameter instead of `noise_level`
- `gen_synthetic_spectrum` now uses `xaxis` parameter instead of `x`
- code formatting improvements in `synthetic` module
- code formatting improvements in `calibration` module
- renamed many variables and parameters in `calibration` module
- `xaxis_from_peaks()` now also returns `residual`. This is now used in `autogenx()` to find the best fit.

### Fixed

- Demo10 to work with `orpl`'s new structure
- changes in `crfilter_multi` fixes problems in detection of cosmic rays when the max intensity is from a raman peak instead of the baseline.
- fixed mislabeling of algorithm in `demo4_baseline_removal.ipynb`
- fixed parameter name changes in `demo9_synthetic_data.ipynb`
- fixed `autogenx()` failing in cases where the input signal's detected peaks did not exactly match the presets
  - The function now tries combinations of 5 peaks from the preset lists and finds the best fit
  - The new method should work as long as the input signal has AT LEAST 5 of the preset peaks
  - More testing needed

## [0.0.2] - 2022-02-02

First proper build

### Changed

- Readme and documentation
- `orpl.baseline_removal` docstrings

## [0.0.1] - 2022-02-02

Major refactor of the ramanTools project and the birth of _ORPL_. This first version was essentially a move from the `ramanTools.py` module into a proper package structure and everything that comes with it.

### Added

- Everything from `ramanTools.py`

### Changed

- Split ramanTools.py into:

  - `orpl.baseline_removal`
  - `orpl.calibration`
  - `orpl.cosmic_ray`
  - `orpl.metrics`
  - `orpl.synthetic`

- Moved Demo files to their own directory
- Updated demos to work with new `orpl` package:
