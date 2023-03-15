from dataclasses import dataclass, field
from pathlib import Path
from typing import Type

from numpy import ndarray


@dataclass(frozen=True)
class Metadata:
    # timestamp: int  # epoch [s]
    filepath: Type[Path]
    exposure_time: float  # [ms]
    source_power: float  # [mw]
    details: dict
    comment: str


@dataclass(frozen=True)
class Spectrum:
    metadata: Metadata
    accumulations: ndarray
    background: ndarray
    nbins: int = field(init=False)
    naccumulations: int = field(init=False)
    mean_spectrum: ndarray = field(init=False)

    def __post_init__(self):
        if self.accumulations.ndim > 1:
            object.__setattr__(self, "naccumulations", self.accumulations.shape[1])
            object.__setattr__(self, "mean_spectrum", self.accumulations.mean(axis=1))
        else:
            object.__setattr__(self, "naccumulations", 1)
            object.__setattr__(self, "mean_spectrum", self.accumulations)

        object.__setattr__(self, "nbins", self.accumulations.shape[0])
