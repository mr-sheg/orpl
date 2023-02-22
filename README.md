# ORPL

ORPL (read _orpel_) is the Open Raman Processing Library. It provides tools for the processing of Raman spectrum including;

1. System calibration (x-axis and system response)
2. Cosmic Ray removal
3. Baseline removal (autofluorescence)
4. Spectrum analysis (peak finding, ...)
5. Synthetic spectrum generation (for testing and benchmarking)

## Installation

ORPL is hosted and distributed through the python package index (https://pypi.org/project/orplib/) and can be installed with pip.

```
pip install orplib
```

If you have a virtual environment configured, don't forget to first activate the environment.

You can verify the installation by doing a `pip list`.

### Building from source

This is the command you need to run if you want to build the .whl from the source code yourself (make sure you run it from orpl's project root directory):

```
python -m build
```

and to update the build on pypi (this is a reminder for me, it wont do anything if you do this),

```
python -m twine upload --repository pypi dist/*
```

## Baseline removal

### BubbleFill

Bubblefill is a morphological processing algorithm designed for the removal of baselines in spectroscopic signal. It was created and optimized specifically to remove autofluorescence baselines in Raman spectra measured on biological samples.

![Bubblefill in action](documentation/bacon_100.gif)

The tuning parameter of Bubblefill is the size of the smallest bubble allowed to grow. In general, the smallest bubble width should be chosen to be larger than the widest Raman peak present in the signal. Otherwise, the baseline fit will _grow_ inside the peaks and the output Raman signal will have under expressed peaks.

**Note** : Bubbles can become arbitrarily small if they are growing along the leftmost or rightmost edge of the signal.

![Bubblefill with bubbles that are too small](documentation/bacon_30.gif)

Different smallest bubble widths can be specified for different regions of the spectrum. This enables nearly infinite tuninig of the algorithm and can be used to removed peaks that are known artifacts (for instance). In this example, the smallest bubble width for detector pixels 400 to 650 was set to 1 and to 100 for the rest of the x-axis.

![Bubblefill with multiple smallest bubble widths](documentation/bacon_multi.gif)

## How to cite this work

Guillaume Sheehy, Fabien Picot, Frédérick Dallaire, Katherine Ember, Tien Nguyen, Kevin Petrecca, Dominique Trudel, and Frédéric Leblond "Open-sourced Raman spectroscopy data processing package implementing a baseline removal algorithm validated from multiple datasets acquired in human tissue and biofluids," Journal of Biomedical Optics 28(2), 025002 (21 February 2023). https://doi.org/10.1117/1.JBO.28.2.025002

### BibTex (.bib)

```
@article{10.1117/1.JBO.28.2.025002,
author = {Guillaume Sheehy and Fabien Picot and Fr{\'e}d{\'e}rick Dallaire and Katherine Ember and Tien Nguyen and Kevin Petrecca and Dominique Trudel and Fr{\'e}d{\'e}ric Leblond},
title = {{Open-sourced Raman spectroscopy data processing package implementing a baseline removal algorithm validated from multiple datasets acquired in human tissue and biofluids}},
volume = {28},
journal = {Journal of Biomedical Optics},
number = {2},
publisher = {SPIE},
pages = {025002},
keywords = {Raman spectroscopy, fluorescence, tissue optics, open-sourced software, machine learning, optics, Raman spectroscopy, Data processing, Bubbles, Equipment, Tissues, Biological samples, Raman scattering, Fluorescence, Aluminum, Spectroscopy},
year = {2023},
doi = {10.1117/1.JBO.28.2.025002},
URL = {https://doi.org/10.1117/1.JBO.28.2.025002}
}
```

### EndNote (.enw)

```
%0 Journal Article
%A Sheehy, Guillaume
%A Picot, Fabien
%A Dallaire, Frédérick
%A Ember, Katherine
%A Nguyen, Tien
%A Petrecca, Kevin
%A Trudel, Dominique
%A Leblond, Frédéric
%T Open-sourced Raman spectroscopy data processing package implementing a baseline removal algorithm validated from multiple datasets acquired in human tissue and biofluids
%V 28
%J Journal of Biomedical Optics
%N 2
%P 025002
%D 2023
%U https://doi.org/10.1117/1.JBO.28.2.025002
%DOI 10.1117/1.JBO.28.2.025002
%I SPIE
```

### Contributors

- **Guillaume Sheehy** | guillaume.sheehy@polymtl.ca
- **Frédérick Dallaire**
- **Fabien Picot**
