"""
file_io modules provide file handling capabilities for the ORPL GUI.
"""

import pathlib
from typing import Tuple

import numpy as np
import pandas as pd
import sif_parser

from orpl.datatypes import Metadata, Spectrum

SUPPORTED_EXTENSIONS = [".sif"]


def is_file_supported(filepath):
    filetype = pathlib.Path(filepath).suffix
    return filetype in SUPPORTED_EXTENSIONS


def load_file(filepath: str) -> Spectrum:

    if not is_file_supported(filepath):
        raise TypeError(f"{filepath} is not supported as a spectrum file.")

    if filepath.endswith(".sif"):
        spectrum = load_sif(filepath)

    return spectrum


def load_sif(sif_file: str) -> Spectrum:
    data_array, meta_dict = sif_parser.np_open(sif_file)
    data_array = np.squeeze(data_array)
    meta_str = pd.DataFrame([dict(meta_dict)]).iloc[0].to_json(indent=2)

    metadata = Metadata(
        source_power=None,
        exposure_time=meta_dict["CycleTime"],
        details=meta_str,
        comment="",
    )
    spectrum = Spectrum(accumulations=data_array, metadata=metadata, background=None)

    return spectrum


if __name__ == "__main__":
    spectrum = load_file(
        "/home/gsheehy/Desktop/blue silicone 1s 25mw p5314 100 mic slit.sif"
    )
    print(spectrum)
