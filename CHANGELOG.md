# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.7] - 2023-06-21

### Added

- File compatibility with .txt and .csv. See example files in `ORPL sample data.zip` for examples of the structure to follow.

### Changed

- ORPL's starting working directory is not the specific terminal directory where it's launched from (`python -m orpl`).

## [1.0.6] - 2023-06-06

### Changed

- Naming convention : replaced word "Select" with "Load"
- Uniformized spectra load : now "accumulations" are always 2d Array even for a single accumulation.

### Fixed

- Fixed xaxis label in IRF plot when an xaxis is loaded
- Fixed processing Bug with .sdf

## [1.0.5] - 2023-06-05

### Added

- Acquisistion_info dataclass
  - this object contains 4 fields : "exposure_time", "n_accumulations","laser_power" and "power_units"
- .sdf file support

## [1.0.4] - 2023-05-11

### Added

- Sample files to test ORPL GUI

### Bugfix

- Fixed a bug when loading .sif files that had non-utf8 encoding
- Fixed dimensionality when loading .sif images

## [1.0.3] - 2023-03-16

### Changed

- Updated README with install instructions
- Updated README with demo footage
- Added back imports of module in orpl's `__init__`. Fixes module not found error when importing orpl (`import orpl`)

## [1.0.2] - 2023-03-15

### Added

- ORPL window now shows version

### Changed

- replaced uses of the `os` module with `pathlib` for path handling in the orplGUI module

### Bugfix

- windows bugs

## [1.0.1] - 2023-03-15

### Changed

- bugfix

## [1.0] - 2023-03-15

### Added

- `bubblegif` module to create animated gifs of the bubblefill algorithm
- ORPL GUI
  - you can launch it by running `python -m orpl` in terminal
- `file_io` module
  - support for import different file types (.sif, .json, .wdf)
  - support for export in .rdf (Raman Data File)
- `datatypes` module
  - definition for a `metadata` and `spectrum` class (more will follow next version)

### Changed

- Renamed the `ssdeviation()` function to `assi()` in the `metrics` module
- Updated Readme after manuscript publication

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
