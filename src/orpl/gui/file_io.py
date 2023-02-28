"""
file_io modules provide file handling capabilities for the ORPL GUI.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import sif_parser

from orpl.datatypes import Metadata, Spectrum

SUPPORTED_EXTENSIONS = [".sif", ".json"]


def is_file_supported(file_path: Path) -> bool:
    return file_path.suffix in SUPPORTED_EXTENSIONS


def load_file(file_name: str) -> Spectrum:
    file_path = Path(file_name)
    if not is_file_supported(file_path):
        raise TypeError(f"{file_path} is not supported as a spectrum file.")

    load_function = {".sif": load_sif, ".json": load_json}
    spectrum = load_function[file_path.suffix](file_path)

    return spectrum


def load_sif(sif_file: Path) -> Spectrum:
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


def load_json(json_file: Path) -> Spectrum:
    with open(json_file) as f:
        json_data = json.load(f)

    return spectrum


def split_json(json_file: Path, new_dir: str = None):
    """
    split_json splits a .json file exported from ORAS into a directory of the same name containing
    a .json file for each indivudual acquisitions.

    Parameters
    ----------
    json_file : str
        the path of a .json file to split into multiple files in a new directory.
    new_dir : str, optional
        the name of the new directory that will contain new individual spectrum files,
        by default None
    """

    # Creating new directory where to split the json_file
    json_path = Path(json_file)
    if json_path.suffix != ".json":
        raise TypeError("json_file is not a .json")

    if new_dir is None:
        new_dir = json_path.resolve().parent / json_path.stem  # New dir Path
    else:
        new_dir = Path(new_dir).resolve()

    if not new_dir.exists():
        new_dir.mkdir()

    # Loading the json_file
    json_path = Path(json_file)

    if not json_path.exists():
        raise FileExistsError(f"{json_path} does not exists.")

    with open(json_path) as file:
        json_data = json.load(file)

    if not isinstance(json_data, list):
        raise TypeError("The loaded json does not contain a list.")

    for i, data in enumerate(json_data):
        new_file = new_dir / f"{i}.json"
        with open(new_file, "w", encoding="utf8") as f:
            json.dump(data, f)


if __name__ == "__main__":
    split_json("/home/gsheehy/Desktop/sharpie.json")
    # print(spectrum)
