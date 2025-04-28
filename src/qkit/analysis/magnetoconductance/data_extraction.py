import h5py
import logging as log
import numpy as np

from qkit.storage.hdf_constants import ds_types
from qkit.measure.json_handler import QkitJSONEncoder, QkitJSONDecoder

class HDFData:
    ''' This class serves as a wrapper for .h/hdf5 files generated
    by qkit for easier data readout and saving analysis data.

        *Required keywords:
            -path:  File path of .h/hdf5 file
    '''
    def __init__(self, path):
        self._path = path
        self._h5file = h5py.File(path, mode="a")
        self._data_dir = self._h5file['entry/data0']
        self._data = {}
        self._analysis_dir = self._h5file['entry/analysis0']
        self._analysis = {}

    def create_analysis_ds(self, data, ds_name, prefix='', index=-1, suffix='', **kwargs):
        ''' create new dataset for analysis data'''
        name = f"{prefix}{ds_name}{suffix}"
        if index >= 0:
            name = f"{prefix}{ds_name}_{index}{suffix}"
        log.info(f'Create new dataset with name {name}.')
        # create dataset in analysis folder with name {name} and ds_type analysis
        ds = self._analysis_dir.create_dataset(name=name,data=data)
        if not ds.attrs.get('name',None):
            ds.attrs.create('name',name)
        ds.attrs.create('ds_type',ds_types['analysis'])
        # add metadata to new dataset
        self.set_metadata(ds,**kwargs)
        log.info(f'Dataset {name} was created successfully!')

    def set_metadata(self, ds:h5py.Dataset,**kwargs):
        ''' setter func fot metadata'''
        for key,val in kwargs.items():
            if not key in ds.attrs.keys():
                if isinstance(val, str):
                    ds.attrs.create(key,val.encode())
                elif isinstance(val,tuple):
                    ds.attrs.create(key,str(val))
                elif val is None:
                    pass
                else:
                    ds.attrs.create(key,str(val))
        self._h5file.flush()

    def get_metadata(self, ds:h5py.Dataset, var=None):
        ''' getter function for metadata of dataset, var can be either string or list of strings
        if no var for metadata is used, all metadata of ds will be returned'''
        metadata = {}
        if var:
            if isinstance(var, str):
                metadata[var] = ds.attrs.get(var,None)
            elif isinstance(var, list):
                for val in var:
                    metadata[val] = ds.attrs.get(val,None)
            else:
                log.error(f'{type(var)} is no valid type for var!')
        else:
            for key, val in ds.attrs.items():
                metadata[key] = val
        return metadata

    def get_ds_data(self, ds:h5py.Dataset, dtype=np.float32):
        ''' getter func for dataset as numpy array'''
        return np.array(ds, dtype)

    def get_dataset(self, ds_url:str):
        ''' getter func for single dataset as h5py Dataset object'''
        return self._h5file.get(ds_url)

    def get_xy_datasets(self, ds:h5py.Dataset):
        ''' getter func for x and y parameter dataset of ds'''
        return self.find_xy_ds(ds, ds.parent)

    def find_xy_ds(self, ds:h5py.Dataset, folder):
        ''' search for x and y datasets'''
        x_ds_url = ds.attrs.get("x_ds_url","")
        y_ds_url = ds.attrs.get("y_ds_url","")
        x, y = None, None
        if x_ds_url and y_ds_url:
            if len(ds.shape) == 2:
                x = folder[x_ds_url]
                y = folder[y_ds_url]
            else:
                assert ReferenceError(f"Shape {ds.shape} of dataset, does not match with references!")
        elif x_ds_url:
            if len(ds.shape) == 1:
                x = folder[x_ds_url]
            else:
                assert ReferenceError(f"Shape {ds.shape} of dataset, does not match with references!")
        elif y_ds_url:
            if len(ds.shape) == 1:
                x = folder[y_ds_url]
            else:
                assert ReferenceError(f"Shape {ds.shape} of dataset, does not match with references!")
        else:
            assert ReferenceError("There is no reference for a vector/coordinate in dataset!")
        return x, y

    def get_measure_data(self, prefix='', ds_name:list=[]):
        ''' getter func for multiple measure datasets in .h/hdf5 file data0 folder
        x and y parameter of measurement datasets will be searched and returned automatically
        if no dataset name is given, readout and return all measurement datasets'''
        if ds_name:
            # export all datasets in ds_name list from data folder
            for key in ds_name:
                data = None
                if key not in self._data.items():
                    try:
                        data = self._data_dir[prefix+key]
                    except KeyError:
                        log.error(f"Dataset {key} does not exist in 'entry/data0/'!")
                        continue
                # search for connected x/y datasets
                if isinstance(data,h5py.Dataset):
                    if not self._data.get("x_data") or not self._data.get("y_data"):
                        x, y = self.find_xy_ds(data, self._data_dir)
                        if isinstance(x,h5py.Dataset):
                            self._data["x_data"] = x
                        if isinstance(x,h5py.Dataset):
                            self._data["y_data"] = y
                    self._data[prefix+key] = data
        else:
            # export all datasets from data folder
            for key, val in self._data_dir.items():
                if key not in self._data.items():
                    if val.attrs.get("x_ds_url","") or val.attrs.get("y_ds_url",""):
                        if isinstance(val,h5py.Dataset):
                            if not self._data.get("x_data") or not self._data.get("y_data"):
                                x, y = self.find_xy_ds(val, self._data_dir)
                                if isinstance(x,h5py.Dataset):
                                    self._data["x_data"] = x
                                if isinstance(x,h5py.Dataset):
                                    self._data["y_data"] = y
                            self._data[key] = val
        return self._data

    def get_analysis_data(self, prefix='', ds_name:list=[], suffix=''):
        ''' getter func for multiple analysis datasets in .h/hdf5 file analysis0 folder
        x and y parameter of analysis datasets will be searched and returned automatically
        no dataset name is given -> readout and return all analysis datasets'''
        self._analysis = {}
        if ds_name:
            # export all datasets with 'ds_name' in analysis folder
            for key in ds_name:
                # create default dataset name without index
                name = f"{prefix}{key}{suffix}"
                index=-1
                analysis = None
                while True:
                    if index >= 0:
                        # create dataset name with additional index
                        name = f"{prefix}{key}_{index}{suffix}"
                    if name not in self._analysis.items():
                        # search for dataset 'name' in analysis folder
                        try:
                            analysis = self._analysis_dir[name]
                            index+=1
                        except KeyError:
                            if index == -1:
                                break
                            # save highest index of analysis datasets
                            self._analysis[f"{prefix}{key}{suffix}__imax"] = index
                            break
                        # search for connected x/y datasets
                        if isinstance(analysis,h5py.Dataset):
                            x, y = self.find_xy_ds(analysis, self._analysis_dir)
                            if isinstance(x,h5py.Dataset):
                                self._analysis[f"{x.attrs.get('name','')}"] = x
                            if isinstance(y,h5py.Dataset):
                                self._analysis[f"{y.attrs.get('name','')}"] = y
                            self._analysis[name] = analysis
                        else:
                            assert KeyError(f"{name} is no Dataset!")
                    else:
                        break
        else:
            # export all datasets in analysis folder
            for key, val in self._analysis_dir.items():
                analysis = None
                if key not in self._analysis.items():
                    if isinstance(val,h5py.Dataset):
                        x, y = self.find_xy_ds(val, self._analysis_dir)
                        if isinstance(x,h5py.Dataset):
                            self._analysis[f"{x.attrs.get('name','')}"] = x
                        if isinstance(y,h5py.Dataset):
                            self._analysis[f"{y.attrs.get('name','')}"] = y
                        self._analysis[key] = val
        return self._analysis