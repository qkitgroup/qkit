import h5py
import numpy as np
from pathlib import Path
from qkit.analysis.semiconductor.main.interfaces import LoaderInterface

class Loaderh5_julian(LoaderInterface):
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


class Loaderh5:
    """Extracts all data from .h5 files in this folder and returns it as a dict.
    """  
    def load(self, settings):
        """Loads the data of a .h5 file. Analysis and views are not loaded.
        """
        path = f"{settings['file_info']['absolute_path']}{settings['file_info']['date_stamp']}/{settings['file_info']['filename']}/{settings['file_info']['filename']}.h5"
        data = h5py.File(path,'r')["entry"]["data0"]
        self.data_dict = {}
        for key in data.keys():
            self.data_dict[key] = np.array(data.get(u'/entry/data0/' + key)[()])
        return self.data_dict