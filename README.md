# ORPL

ORPL (read _orpel_) is the Open Raman Processing Library. It provides tools for the processing of Raman spectrum, including;

1. System calibration (x-axis and system response)
2. Cosmic Ray removal
3. Baseline removal (autofluorescence)
4. Spectrum analysis (peak finding, ...)
5. Synthetic spectrum generation (for testing and benchmarking)

As of v1.0.0, ORPL also provides a Graphical User Interface. See demo below ;)

## Table of content

- [ORPL](#orpl)
  - [Table of content](#table-of-content)
  - [ORPL GUI in action](#orpl-gui-in-action)
  - [Installation](#installation)
    - [Windows Installation Guide](#windows-installation-guide)
    - [Already familiar with python and pip?](#already-familiar-with-python-and-pip)
    - [I'm new to python and this 'pip' thing?](#im-new-to-python-and-this-pip-thing)
      - [Content of the `orpl GUI.txt` file](#content-of-the-orpl-guitxt-file)
    - [Updating ORPL to the latest version](#updating-orpl-to-the-latest-version)
      - [If you have admin rights](#if-you-have-admin-rights)
      - [If you do not have admin rights](#if-you-do-not-have-admin-rights)
    - [Building from source](#building-from-source)
  - [Baseline removal](#baseline-removal)
    - [BubbleFill](#bubblefill)
  - [How to cite this work](#how-to-cite-this-work)
    - [BibTex (.bib)](#bibtex-bib)
    - [EndNote (.enw)](#endnote-enw)
    - [Contributors](#contributors)

## ORPL GUI in action

https://user-images.githubusercontent.com/27356351/225768644-56ebf40a-51d1-44a1-bba3-edb86f8b1fad.mp4

## Installation

At its core, ORPL is designed to be a processing library to use in your own processing workflow. Nevertheless, I also wrote a GUI to go with it if programming is not your jam. In either case, installation is made through **pip**.

### Windows Installation Guide

I wrote a detailed installation guide for windows complete with screenshots of all the steps, so do not worry if you are a python beginer and have no idea what I'm talking about here. You can access the guide on github ![here](/documentation/Installation%20guide%20-%20Windows.md) or download a ![PDF](/documentation/Installing%20ORPL%20-%20Windows.pdf) version.

### Already familiar with python and pip?

I recommend you create a virtual environment with [**venv**](https://docs.python.org/3/library/venv.html). Otherwise, just install **orplib** with pip.

```
pip install orplib
```

Using Anaconda?... dont... Jokes aside, if people ask me about this, I might write a guide for this. Otherwise, use pip.

### I'm new to python and this 'pip' thing?

I am working on a python tutorial repository, you can learn more about it ![here](https://github.com/mr-sheg/Python-Tutorials).

##### Content of the `orpl GUI.txt` file

```
python -m orpl
pause
```

### Updating ORPL to the latest version

If you want to update to the latest version of ORPL, run the following pip command,

#### If you have admin rights

```
pip install --upgrade orplib
```

#### If you do not have admin rights

```
pip install --upgrade --user orplib
```

### Building from source

This is the command you need to run if you want to build the .whl from the source code yourself (make sure you run it from orpl's project root directory):

```
python -m build
```

and to update the build on pypi (this is a reminder for me, it won't do anything if you do this),

```
python -m twine upload --repository pypi --skip-existing dist/*
```

## Baseline removal

### BubbleFill

Bubblefill is a morphological processing algorithm designed for the removal of baselines in spectroscopic signal. It was created and optimized specifically to remove autofluorescence baselines in Raman spectra measured on biological samples.

![Bubblefill in action](documentation/bacon_100.gif)

The tuning parameter of Bubblefill is the size of the smallest bubble allowed to grow. In general, the smallest bubble width should be chosen to be larger than the widest Raman peak present in the signal. Otherwise, the baseline fit will _grow_ inside the peaks and the output Raman signal will have under expressed peaks.

**Note** : Bubbles can become arbitrarily small if they are growing along the leftmost or rightmost edge of the signal.

![Bubblefill with bubbles that are too small](documentation/bacon_30.gif)

Different smallest bubble widths can be specified for different regions of the spectrum. This enables nearly infinite tuning of the algorithm and can be used to remove peaks that are known artifacts (for instance). In this example, the smallest bubble width for detector pixels 400 to 650 was set to 1 and to 100 for the rest of the x-axis.

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
