from dataclasses import dataclass, field
import time
from pathlib import Path
from typing import Optional

import numpy as np

import qkit
import qkit.storage.thin_hdf
from qkit.storage import thin_hdf


@dataclass(frozen=True)
class MeasurementFilePath:
    """
    Derive measurement file path and name from metadata.

    Replaces hdf_DateTimeGenerator
    """
    measurement_name: str # Derived from the measurement class
    additional_path_info: list[str] = field(default_factory=list)
    user: str = field(default_factory=lambda: qkit.cfg.get('user', 'John_Doe'), init=False)
    run_id: str = field(default_factory=lambda: qkit.cfg.get('run_id', 'NO_RUN'), init=False)
    timestamp: int = field(default_factory=time.time, init=False)

    @property
    def uuid(self) -> str:
        """
        Base 36 encoded timestamp. Unique enough identifier for each measurement.
        """
        return np.base_repr(self.timestamp, base=36)

    @property
    def folder_name(self) -> str:
        """
        Folder name for measurements based on the UUID and the name of the measurement.
        """
        return self.uuid + '_' + self.measurement_name

    @property
    def file_name(self) -> str:
        """
        The file name for the measurement. This is the same as the folder name but with an extension.
        """
        return self.folder_name + '.h5'

    @property
    def rel_path(self) -> Path:
        path = Path(_sanitize(self.run_id.upper())) / _sanitize(self.user)
        for folder in self.additional_path_info:
            path /= folder
        path /= self.folder_name
        path /= self.file_name
        return path

    def into_path(self, base_path: str | Path = qkit.cfg['datadir']) -> Path:
        return Path(base_path) / self.rel_path

    def mkdirs(self, base_path: str | Path = qkit.cfg['datadir']):
        full_path = self.into_path(base_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)

    def into_h5_file(self, base_path: str | Path = qkit.cfg['datadir']) -> thin_hdf.HDF5:
        self.mkdirs(base_path)
        return thin_hdf.HDF5(str(self.into_path(base_path)), mode='w')

def _sanitize(name: str) -> str:
    """
    Remove spaces from paths, makes it easier to use in the terminal.
    """
    return name.replace(' ', '_')

def decode_uuid(string: str) -> int:
    """
    Invert encode_uuid.
    """
    return int(string, 36)