# ORPL

ORPL (read _orpel_) is the Open Raman Processing Library. It provides tools for the processing of Raman spectrum including;

1. System calibration (x-axis and system's response)
2. Cosmic Ray removal
3. Baseline removal
4. Spectrum analysis (peak finding, ...)
5. Synthetic spectrum generation (for testing and benchmarking)

## Installation

Until official release (at which point a simple `pip install orpl` should do the trick), you need to download the project and grab the wheel file (example with the 0.0.2 release : `orpl-X.X.X.whl`). To install the library, run

(example for `orpl-0.0.2.whl`)

```
pip install /PATH/TO/orpl-0.0.2.whl
```

If you have a virtual environment configured, don't forget to first activate the environment.

You can verify the installation by doing a `pip list`.

## Processing Raman spectra

The following section presents guidelines and recommendations from the the LRO (https://lroinnovation.com/). This process was optimized for spectra acquired on biological tissues or tissue mimicking phantoms.

The recommended steps are

1. Importing and formating raw spectrum data
2. Cropping spectra
3. Removal of cosmic rays
4. Correction for system response
5. Baseline removal
6. Normalization
7. Exporting processed spectrum data

Each steps are detailed in its respective jupyter notebook and the complete processing workflow is presented in `demo7_complete_workflow`.

---

### Contributors

- **Guillaume Sheehy** | guillaume.sheehy@polymtl.ca
- **Frédérick Dallaire**
- **Fabien Picot**
