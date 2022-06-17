import h5py
import numpy as np
from pathlib import Path
import urllib
from smb.SMBHandler import SMBHandler

from qkit.analysis.semiconductor.main.interfaces import LoaderInterface


class Loaderh5_julian(LoaderInterface):
    def __init__(self) :
        self.file_paths = []

    def set_filepath(self, paths:list):
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
        """Loads the data of a .h5 file. Analysis and views are not loaded. Is able to interprete smb connection to nanospin@phi-ndus"
        """
        
        path = settings['file_info']['filepath']
        
        if "smb:" in path:
            mod_path = path.replace("smb://nanospin@phi-ndus", "smb://nanospin:Hadamard_gate@phi-ndus")
            opener = urllib.request.build_opener(SMBHandler)
            fh = opener.open(mod_path)
            data = h5py.File(fh,"r")["entry"]["data0"]
        else:
            data = h5py.File(path,'r')["entry"]["data0"]
            
        self.data_dict = {}
        print("Done loading file, formatting now...")
        for key in data.keys():
            self.data_dict[key] = np.array(data.get(u'/entry/data0/' + key)[()])
        return self.data_dict


class H5filemerger():
    """Sonjas first class -whoop-whoop- merges data from several .h5 files with the same nodes and returns them as dict
    See accumulation_many_files.py in the scripts folder for an application
    """
    def __init__(self):
        self.paths = []
        
    def add_paths(self, paths):
        if type(paths) != list:
            raise TypeError("Your input type is dumb. Must be list, silly human.")
        self.paths.extend(paths)
            
    def merge(self): 
        data1 = h5py.File(Path(self.paths[0]),'r')["entry"]["data0"]
        dictmerged = {key : np.array([]) for key in data1.keys()}
        for element in self.paths:
            data = h5py.File(Path(element),'r')["entry"]["data0"]
            for key in dictmerged.keys():
                data_dict = {}
                data_dict[key] = np.array(data[key])
                dictmerged[key] = np.concatenate( (dictmerged[key], data_dict[key]))

        return dictmerged

