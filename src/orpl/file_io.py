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

    # cleaning up string metadata
    for k, v in meta_dict.items():
        if isinstance(v, bytes):
            meta_dict[k] = v.decode()
        if isinstance(v, str):
            meta_dict[k] = v.strip()

    metadata = Metadata(
        source_power=None,
        exposure_time=meta_dict["CycleTime"],
        details=dict(meta_dict),
        comment="",
    )
    spectrum = Spectrum(accumulations=data_array, metadata=metadata, background=None)

    return spectrum


def load_json(json_file: Path, dump_meta_spectra=True) -> Spectrum:
    with open(json_file, encoding="utf8") as f:
        json_data = json.load(f)

    if isinstance(json_data, list):
        if len(json_data) > 1:
            raise TypeError(
                f"It appears file '{json_file.name}' contains multiple acquisitions. "
                "Please split it into multiple files using the split_json() function."
            )
        else:
            json_data = json_data[0]

    accumulations = np.stack(json_data["RawSpectra"])
    background = np.stack(json_data["Background"])
    details = {
        k: v
        for k, v in json_data.items()
        if k not in ["RawSpectra", "Background", "aec", "asnr"]
    }

    metadata = Metadata(
        comment=json_data["Comment"],
        exposure_time=json_data["ExpTime"],
        source_power=json_data["Power"],
        details=details,
    )
    spectrum = Spectrum(
        accumulations=accumulations, background=background, metadata=metadata
    )
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

    with open(json_path, encoding="utf8") as file:
        json_data = json.load(file)

    if not isinstance(json_data, list):
        raise TypeError("The loaded json does not contain a list.")

    for i, data in enumerate(json_data):
        new_file = new_dir / f"{new_dir.stem}_{i}.json"
        with open(new_file, "w", encoding="utf8") as f:
            json.dump(data, f)


class SDF:
    pass


class RDF:
    pass


if __name__ == "__main__":
    p = Path.home() / "Desktop" / "blue silicone 1s 25mw p5314 100 mic slit.sif"
    data = load_sif(p)
    print(data.metadata.details)
