"""
file_io modules provide file handling capabilities for the ORPL GUI.
"""

import pathlib

import numpy as np
import pandas as pd
import sif_parser

SUPPORTED_EXTENSIONS = [".sif"]


def is_file_supported(filepath):
    filetype = pathlib.Path(filepath).suffix
    return filetype in SUPPORTED_EXTENSIONS


def load_file(filepath: str) -> tuple([np.ndarray, str]):

    if not is_file_supported(filepath):
        raise TypeError(f"{filepath} is not supported as a spectrum file.")

    if filepath.endswith(".sif"):
        data, meta = sif_parser.np_open(filepath)
        data = np.squeeze(data)
        meta = pd.DataFrame([dict(meta)]).iloc[0].to_json(indent=2)

    return data, meta


if __name__ == "__main__":
    _, meta = load_file(
        "/home/gsheehy/Desktop/blue silicone 1s 25mw p5314 100 mic slit.sif"
    )
    print(meta)
