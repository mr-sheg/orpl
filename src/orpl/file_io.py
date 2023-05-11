"""
file_io modules provide file handling capabilities for the ORPL GUI.
"""

import json
from pathlib import Path
from typing import Type

import numpy as np
import sif_parser
from renishawWiRE import WDFReader
from ruamel import yaml

from orpl.datatypes import Metadata, Spectrum

SUPPORTED_EXTENSIONS = [".sif", ".json", ".wdf"]


def is_file_supported(file_path: Path) -> bool:
    return file_path.suffix in SUPPORTED_EXTENSIONS


def load_file(file_name: str) -> Spectrum:
    file_path = Path(file_name)
    if not is_file_supported(file_path):
        raise TypeError(f"{file_path} is not supported as a spectrum file.")

    load_function = {".sif": load_sif, ".json": load_json, ".wdf": load_wdf}
    spectrum = load_function[file_path.suffix](file_path)

    return spectrum


def load_sif(sif_file: Path) -> Spectrum:
    data_array, meta_dict = sif_parser.np_open(sif_file)
    data_array = np.squeeze(data_array)

    # cleaning up string metadata
    for k, v in meta_dict.items():
        if isinstance(v, bytes):
            meta_dict[k] = v.decode(encoding="utf8", errors="replace")
        if isinstance(v, str):
            meta_dict[k] = v.strip()

    metadata = Metadata(
        filepath=sif_file,
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

    metadata = Metadata(
        filepath=wdf_path,
        comment=wdf.title,
        exposure_time=None,
        source_power=None,
        details=details,
    )
    spectrum = Spectrum(accumulations=accumulations, background=None, metadata=metadata)
    return spectrum


class SDF:
    pass


class RDF:
    metadata: Type[Metadata]
    xaxis: Type[np.ndarray]
    raman: Type[np.ndarray]
    baseline: Type[np.ndarray]

    def get_metadata_block(self) -> str:
        return "###\n" + yaml.dump(self.metadata, Dumper=yaml.RoundTripDumper) + "###\n"

    def get_data_block(self) -> str:
        data_array = np.stack((self.xaxis, self.baseline, self.raman), axis=1)
        data_str = ""
        for line in data_array:
            data_str += ",".join(map(str, line)) + "\n"
        return data_str

    def get_column_block(self) -> str:
        return "xaxis,baseline,raman\n"

    def save(self, filepath: str) -> None:
        blocks = (
            self.get_metadata_block(),
            self.get_column_block(),
            self.get_data_block(),
        )
        with open(filepath, "w", encoding="utf8") as file:
            for block in blocks:
                file.write(block)


if __name__ == "__main__":
    wdf_file = Path().home() / "Desktop/orpl_testing/nylon_objx5_0.wdf"
    s = load_file(wdf_file)

    print(yaml.dump(s.metadata.details, Dumper=yaml.RoundTripDumper))
