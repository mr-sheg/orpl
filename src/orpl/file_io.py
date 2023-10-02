"""
file_io modules provide file handling capabilities for the ORPL GUI.
"""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Type

import numpy as np
import pandas as pd
import sif_parser
from renishawWiRE import WDFReader
from ruamel import yaml

from orpl.datatypes import Acquisition_info, Rdf_metadata, Spectrum

## File specific load functions


def load_sif(sif_file: Path) -> Spectrum:
    data_array, meta_dict = sif_parser.np_open(sif_file)
    data_array = np.squeeze(data_array).T
    if data_array.ndim > 1:
        data_array = np.flip(data_array, axis=0)

    # cleaning up string metadata
    for k, v in meta_dict.items():
        if isinstance(v, bytes):
            meta_dict[k] = v.decode(encoding="utf8", errors="replace")
        if isinstance(v, str):
            meta_dict[k] = v.strip()

    metadata = Rdf_metadata(
        filepath=sif_file,
        source_power=None,
        exposure_time=meta_dict["CycleTime"],
        details=dict(meta_dict),
        comment="",
    )
    spectrum = Spectrum(accumulations=data_array, background=None, metadata=metadata)

    return spectrum


def load_json(json_file: Path) -> Spectrum:
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

    metadata = Rdf_metadata(
        filepath=json_file,
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


def load_wdf(wdf_path: Path):
    wdf = WDFReader(wdf_path)

    accumulations = np.flip(wdf.spectra)
    details = {
        "software": f"{wdf.application_name} {'.'.join(str(i) for i in wdf.application_version)}",
        "accumulation_count": wdf.accumulation_count,
        "laser_length": wdf.laser_length,
        "measurement_type": str(wdf.measurement_type),
        "point_per_spectrum": wdf.point_per_spectrum,
        "scan_type": str(wdf.scan_type),
        "spectral_unit": str(wdf.spectral_unit),
        "username": wdf.username,
        "xlist_length": wdf.xlist_length,
        "xlist_type": str(wdf.xlist_type),
        "xlist_unit": str(wdf.xlist_unit),
        "ylist_length": wdf.ylist_length,
        "ylist_type": str(wdf.ylist_type),
        "ylist_unit": str(wdf.ylist_unit),
    }

    metadata = Rdf_metadata(
        filepath=wdf_path,
        comment=wdf.title,
        exposure_time=None,
        source_power=None,
        details=details,
    )
    spectrum = Spectrum(accumulations=accumulations, background=None, metadata=metadata)
    return spectrum


def load_sdf(sdf_file: Path) -> Spectrum:
    sdf = SDF()
    sdf.load(sdf_file)

    # Unpacking data
    accumulations = sdf.accumulations
    background = sdf.background
    metadata = Rdf_metadata(
        filepath=sdf_file,
        exposure_time=sdf.acquisition_info.exposure_time,
        source_power=sdf.acquisition_info.exposure_time,
        details=sdf.get_metadata_dict(),
        comment=sdf.comment,
    )

    spectrum = Spectrum(
        accumulations=accumulations, background=background, metadata=metadata
    )
    return spectrum


def check_header_valid(header_keys: list):
    # Checks that all keys are valid
    valid_keys = ["xaxis", "background"]
    for key in header_keys:
        if key in valid_keys:
            pass
        elif key.startswith("accumulation_"):
            pass
        else:
            raise KeyError(f"Key '{key}' is not a valid header key.")

    # Checks that all required keys are present
    required_keys = ["background", "accumulation_"]
    for required_key in required_keys:
        if not any(header_key.startswith(required_key) for header_key in header_keys):
            raise KeyError(f"Key '{required_key}' is missing from header.")


def load_txt(txt_file: Path) -> Spectrum:
    data = pd.read_csv(txt_file)

    # Checking header validity
    check_header_valid(data.keys())

    # Loading data from file with pandas
    xaxis = data["xaxis"].to_numpy()
    background = data["background"].to_numpy()
    background[np.isnan(background)] = 0
    accumulations = data[
        [key for key in data.keys() if key.startswith("accumulation_")]
    ].to_numpy()

    # Loading metadata from file
    metadata = Rdf_metadata(
        filepath=txt_file,
        exposure_time=None,
        source_power=None,
        details={},
        comment=None,
    )

    # Building spectrum object
    spectrum = Spectrum(
        accumulations=accumulations, background=background, metadata=metadata
    )

    return spectrum


LOAD_FUNCTIONS = {
    ".sif": load_sif,
    ".json": load_json,
    ".wdf": load_wdf,
    ".sdf": load_sdf,
    ".csv": load_txt,
    ".txt": load_txt,
}


def is_file_supported(file_path: Path) -> bool:
    return file_path.suffix in LOAD_FUNCTIONS.keys()


def load_file(file_name: str) -> Spectrum:
    file_path = Path(file_name)
    if not is_file_supported(file_path):
        raise TypeError(f"{file_path} is not supported as a spectrum file.")

    spectrum = LOAD_FUNCTIONS[file_path.suffix](file_path)

    return spectrum


class RDF:
    metadata: Type[Rdf_metadata]
    xaxis: Type[np.ndarray]
    raman: Type[np.ndarray]
    baseline: Type[np.ndarray]

    def get_metadata_string(self) -> str:
        return "###\n" + yaml.dump(self.metadata, Dumper=yaml.RoundTripDumper) + "###\n"

    def get_data_string(self) -> str:
        data_array = np.column_stack((self.xaxis, self.baseline, self.raman))
        data_str = ""
        for line in data_array:
            data_str += ",".join(map(str, line)) + "\n"
        return data_str

    def get_column_string(self) -> str:
        return "xaxis,baseline,raman\n"

    def save(self, filepath: str) -> None:
        blocks = (
            self.get_metadata_string(),
            self.get_column_string(),
            self.get_data_string(),
        )
        with open(filepath, "w", encoding="utf8") as file:
            for block in blocks:
                file.write(block)


class SDF:
    # Data attributes
    xaxis: np.ndarray = None
    background: np.ndarray = None
    accumulations: np.ndarray = None
    # Metadata attributes
    epoch: float = None
    comment: str = ""
    oras_version: str = None
    camera_info: dict = None
    laser_info: dict = None
    acquisition_info: Acquisition_info = None

    def __data_attrs__(self) -> list:
        data_attrs = ["xaxis", "background", "accumulations"]
        return data_attrs

    def __meta_attrs__(self) -> list:
        meta_attrs = [
            key
            for key in self.__annotations__.keys()
            if key not in self.__data_attrs__()
        ]
        return meta_attrs

    def __repr__(self) -> str:
        return self.get_metadata_string()

    def get_metadata_dict(self) -> dict:
        metadata_dict = {
            "oras_version": self.oras_version,
            "epoch": self.epoch,
            "comment": self.comment,
            "acquisition_info": asdict(self.acquisition_info),
            "laser_info": self.laser_info,
            "camera_info": self.camera_info,
        }
        return metadata_dict

    def get_metadata_string(self) -> str:
        metadata_block = (
            "###\n"
            + yaml.dump(self.get_metadata_dict(), Dumper=yaml.RoundTripDumper)
            + "###\n"
        )

        return metadata_block

    def get_column_block(self) -> str:
        column_str = "xaxis,background"
        if self.accumulations.ndim > 1:
            n_accumulations = self.accumulations.shape[1]
        else:
            n_accumulations = 1
        for i in range(n_accumulations):
            column_str += f",accumulation_{i}"
        column_str += "\n"
        return column_str

    def get_data_block(self) -> str:
        data_array = np.column_stack((self.xaxis, self.background, self.accumulations))
        data_str = ""
        for line in data_array:
            data_str += ",".join(map(str, line)) + "\n"
        return data_str

    def save(self, filepath: str):
        blocks = (
            self.get_metadata_string(),
            self.get_column_block(),
            self.get_data_block(),
        )
        with open(filepath, "w", encoding="utf8") as file:
            for block in blocks:
                file.write(block)

    def load(self, filepath: str) -> pd.DataFrame:
        with open(filepath, encoding="utf8") as file:
            filecontent = file.readlines()

        file_str = "".join(filecontent)

        # Metadata
        metadata_str = file_str.split("###")[1].strip()
        metadata_dict = yaml.load(metadata_str, Loader=yaml.RoundTripLoader)
        for k, v in metadata_dict.items():
            if k == "acquisition_info":
                self.acquisition_info = Acquisition_info(
                    exposure_time=v["exposure_time"],
                    n_accumulations=v["n_accumulations"],
                    laser_power=v["laser_power"],
                    power_units=v["power_units"],
                )
            else:
                setattr(self, k, v)

        # Data
        data_str = "\n".join(file_str.split("###")[2].split()[1:])
        data_block = np.array(
            [[float(j) for j in i.split(",")] for i in data_str.splitlines()]
        )
        self.xaxis = data_block[:, 0]
        self.background = data_block[:, 1]
        self.accumulations = data_block[:, 2:]

    def to_pandas(self) -> pd.Series:
        data = {
            k: self.__dict__[k] for k in self.__meta_attrs__() + self.__data_attrs__()
        }

        return pd.Series(data)


if __name__ == "__main__":
    file2load = Path().cwd() / "sample data/Generic txt files/collagen.csv"
    # file2load = Path().cwd() / "sample data/neon_averaged_01.csv"
    file2load = Path().cwd() / "neon_averaged_01.csv"
    print(file2load)

    s = load_file(file2load)
    print(s.accumulations)
