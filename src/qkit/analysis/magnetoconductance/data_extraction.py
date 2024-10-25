import h5py
import logging as log
import numpy as np
# import qkit
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
        print(name)
        if index >= 0:
            name = f"{prefix}{ds_name}_{index}{suffix}"
        # try:
        ds = self._analysis_dir.create_dataset(name=name,data=data)
        if not ds.attrs.get('name',None):
            ds.attrs.create('name',name)
        ds.attrs.create('ds_type',ds_types['analysis'])
        self.set_metadata(ds,**kwargs)
        print(ds)
        # except ValueError:
        #     print("Error")
        #     self.create_analysis_ds(data=data, ds_name=ds_name, prefix=prefix, index=index+1, suffix=suffix, **kwargs)

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
            for val in var:
                metadata[val] = ds.attrs.get(val,None)
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

    def get_measure_data(self, prefix='', ds_name=[]):
        ''' getter func for multiple measure datasets in .h/hdf5 file data0 folder
        x and y parameter of measurement datasets will be searched and returned automatically
        if no dataset name is given, readout and return all measurement datasets'''
        if ds_name:
            for key in ds_name:
                data = None
                if key not in self._data.keys():
                    try:
                        data = self._data_dir[prefix+key]
                    except KeyError:
                        print((f"Dataset {key} does not exist in 'entry/data0/'!"))
                        continue
                    if isinstance(data,h5py.Dataset):
                        if not self._data.get("x_data") or not self._data.get("y_data"):
                            x, y = self.find_xy_ds(data, self._data_dir)
                            if isinstance(x,h5py.Dataset):
                                self._data["x_data"] = x
                            if isinstance(x,h5py.Dataset):
                                self._data["y_data"] = y
                        self._data[prefix+key] = data
        else:
            for key in self._data_dir.keys():
                data = None
                if key not in self._data.keys():
                    try:
                        data = self._data_dir[key]
                    except KeyError(f"Dataset {key} does not exist in 'entry/data0/'!"):
                        continue
                    if data.attrs.get("x_ds_url","") or data.attrs.get("y_ds_url",""):
                        if isinstance(data,h5py.Dataset):
                            if not self._data.get("x_data") or not self._data.get("y_data"):
                                x, y = self.find_xy_ds(data, self._data_dir)
                                if isinstance(x,h5py.Dataset):
                                    self._data["x_data"] = x
                                if isinstance(x,h5py.Dataset):
                                    self._data["y_data"] = y
                            self._data[key] = data
        return self._data

    def get_analysis_data(self, prefix='', ds_name:list=[], suffix=''):
        ''' getter func for multiple analysis datasets in .h/hdf5 file analysis0 folder
        x and y parameter of analysis datasets will be searched and returned automatically
        no dataset name is given -> readout and return all analysis datasets'''
        self._analysis = {}
        if ds_name:
            for key in ds_name:
                name = f"{prefix}{key}{suffix}"
                index=-1
                analysis = None
                while True:
                    if index >= 0:
                        name = f"{prefix}{key}_{index}{suffix}"
                    print(name)
                    if name not in self._analysis.keys():
                        try:
                            print(name)
                            analysis = self._analysis_dir[name]
                            index+=1
                        except:
                            if index == -1:
                                break
                            print(f"Dataset {name} can't be found")
                            self._analysis[f"{prefix}{key}{suffix}__imax"] = index
                            break
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
            for key in self._analysis_dir.keys():
                analysis = None
                group = None
                if key not in self._analysis.keys():
                    try:
                        analysis = self._analysis_dir[key]
                    except KeyError(f"Dataset {key} does not exist in 'entry/analysis0/'!"):
                        continue
                    if isinstance(analysis,h5py.Dataset):
                        x, y = self.find_xy_ds(analysis, self._analysis_dir)
                        if isinstance(x,h5py.Dataset):
                            self._analysis[f"{x.attrs.get('name','')}"] = x
                        if isinstance(y,h5py.Dataset):
                            self._analysis[f"{y.attrs.get('name','')}"] = y
                        self._analysis[key] = analysis
        return self._analysis


# path = "C:/Users/joshu/OneDrive/Desktop/Bachelorarbeit/qkit/src/qkit/analysis/SG3V8F_2D_psi_vd.h5"
# x=HDFData(path=path)
# # print(x.get_measure_data())
# print(x.get_analysis_data(ds_name=["test_dataset","test.metadata"]))
# y= np.random.randint(low=0,high=12,size=(5,7))
# metadata = {"namesy":"metadata","nothing":42, "ds_type":ds_types['analysis']}
# x.create_analysis_ds(data=y,ds_name="test_dataset")
# # x.create_analysis_ds("np.float32a",y,**metadata)

# # x.create_analysis_ds("np.float32a",y,**metadata)
# # x._h5file.close()
# # print(x.get_analysis_data())