from dataclasses import dataclass, field
from pathlib import Path
from typing import Type

from numpy import expand_dims, ndarray


@dataclass(frozen=True)
class Acquisition_info:
    exposure_time: float  # [ms]
    n_accumulations: int
    laser_power: float
    power_units: str


@dataclass(frozen=True)
class Rdf_metadata:
    # timestamp: int  # epoch [s]
    filepath: Type[Path]
    exposure_time: float  # [ms]
    source_power: float  # [mw]
    details: dict
    comment: str


@dataclass(frozen=True)
class Spectrum:
    metadata: Rdf_metadata
    accumulations: ndarray
    background: ndarray
    nbins: int = field(init=False)
    naccumulations: int = field(init=False)
    mean_spectrum: ndarray = field(init=False)

    def __post_init__(self):
        if self.accumulations.ndim < 2:
            object.__setattr__(
                self, "accumulations", expand_dims(self.accumulations, axis=1)
            )

        object.__setattr__(self, "naccumulations", self.accumulations.shape[1])
        object.__setattr__(self, "mean_spectrum", self.accumulations.mean(axis=1))
        object.__setattr__(self, "nbins", self.accumulations.shape[0])
