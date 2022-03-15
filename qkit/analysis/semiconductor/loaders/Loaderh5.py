from typing import List
import h5py
import numpy as np
from pathlib import Path
from interfaces import LoaderInterface

class Loader(LoaderInterface):
    def __init__(self) :
        self.file_paths = []

    def set_filepath(self, paths):
        for path in paths:
            if not path.endswith(".h5"):
                raise TypeError("Invalid data format. File must be of type h5.")
        self.file_paths = paths

    def load(self):
        """Loads the data0 entry of an h5 file.
        """
        data_dict = {}
        for element in self.file_paths:
            path = Path(element)
            data = h5py.File(path,'r')["entry"]["data0"]
            
            fname = path.stem
            data_dict[fname] = {}
            for key in data.keys():
                data_dict[fname][key] = np.array(data[key])

        return data_dict