# -*- coding: utf-8 -*-
"""
Created 2015

@author: hrotzing
"""


import logging
import numpy
import time
import qkit
from qkit.storage.hdf_constants import ds_types
from qkit.measure.json_handler import QkitJSONEncoder, QkitJSONDecoder

class hdf_dataset(object):
    """Dataset representation in qkit.        
    
    Wrapper class around the native h5py.crate_dataset().
    This is also a helper class to postpone the creation of the datasets.
    The main issue here is that until the first data is aquired, 
    some dimensions and items are unknown.
    To keep the userinterface simple, we choose to postpone the creation 
    of the datasets and derive all the unknown values from the real data.
    The working horse here is the 'append()' or the 'add()' function. Before, 
    just an empty dataset is created and the metadata are set.
    """
    
    def __init__(self, hdf_file, name='', 
                 ds_url=None, 
                 x=None, 
                 y=None, 
                 z=None, 
                 unit= "", 
                 comment="",
                 folder = 'data', 
                 save_timestamp = False, 
                 overwrite=False,
                 ds_type = ds_types['vector'],
                 **meta):
        """Init the dataset object with case sensitive arguments"""
        name = name.lower().replace(" ","_")
        self.hf = hdf_file
        self.x_object = x
        self.y_object = y
        self.z_object = z
        self.meta = meta
        self.dim = self.meta.pop('dim', None)
        self.dtype = self.meta.pop('dtype','f')
        self.ds_type = ds_type
        self._next_matrix = False
        self._save_timestamp = save_timestamp
        
        ## only one information: either 'name' (for creation) or 'ds_url' (for readout)
        if (name and ds_url) or (not name and not ds_url) :
            logging.error("HDF_dataset: Please specify [only] one, 'name' or 'ds_url' ")
            raise NameError
        if name:
            self._new_ds_defaults(name, unit, folder, comment)
        elif ds_url:
            self._read_ds_from_hdf(ds_url)

    def _new_ds_defaults(self, name, unit, folder, comment):
        self.name = name
        self.folder = folder
        self.ds_url = "/entry/" + folder + "0/" + name
        self.unit = unit
        self.comment = comment
        # the first dataset is used to extract a few attributes
        self.first = True

    def _read_ds_from_hdf(self,ds_url):
        ds = self.hf[str(ds_url)]

        for attr in ds.attrs.keys():
            val = ds.attrs.get(attr)
            setattr(self,attr,val)
        
        self.ds_url =  ds_url
        
    def _setup_metadata(self):
        ds = self.ds
        ds.attrs.create('ds_type',self.ds_type)            
        ds.attrs.create("comment",self.comment.encode())
        ds.attrs.create('ds_url',self.ds_url.encode())
        if self.ds_type != ds_types['txt']:
            ds.attrs.create('unit', self.unit.encode())
            if self.x_object:
                ds.attrs.create("x_ds_url",self.x_object.ds_url.encode())
            if self.y_object:
                ds.attrs.create("y_ds_url",self.y_object.ds_url.encode())
            if self.z_object:
                ds.attrs.create("z_ds_url",self.z_object.ds_url.encode())


    def next_matrix(self):
        self._next_matrix = True
        self._y_pos = 0
        
    def append(self,data, reset=False, pointwise=False):
        """Function to save a growing measurement dataset to the hdf file.
        
        Data is added one datapoint (vector) or one dataline (matrix, box) at a
        time. The data is cast to numpy arrays if possible and appended to the
        existing dataset. A timestamp-dataset is also recorded here.

        Args:
            data: any data to be appended to the dataset
            reset (Boolean, optional); indicator for appending, or resetting the dataset
            pointwise (Boolean): if True, the data is appended pointwise, i.e. to the innermost dimension
        """
        if self.ds_type == ds_types['txt']:
            try:
                data = data.encode("utf-8")
            except AttributeError:
                import json
                data = json.dumps(data, cls=QkitJSONEncoder, indent = 4, sort_keys=True)
        else:
            ## we cast everything to a float numpy array
            data = numpy.atleast_1d(numpy.array(data,dtype=self.dtype))
        # at this point the reference data should be around
        if self.first:
            self.first = False
            if self.ds_type == ds_types['txt']:
                tracelength = 0
            else:
                tracelength = len(data)
            ## tracelength is used so far only for multi-dimensional datasets to chunk needed memory
            self.ds = self.hf.create_dataset(self.name,tracelength,
                                             folder=self.folder,
                                             dim = self.dim,
                                             ds_type = self.ds_type,
                                             dtype = self.dtype,
                                             **self.meta)
            self._setup_metadata()
            if self._save_timestamp:
                self._create_timestamp_ds()

        self.hf.append(self.ds, data, next_matrix=self._next_matrix, reset=reset, pointwise=pointwise)
        if self._save_timestamp:
            self.hf.append(self.ds_ts, numpy.array([time.time()]), next_matrix=self._next_matrix, reset=reset)
        if self._next_matrix:
            self._next_matrix = False

        self.hf.flush()
            
    def add(self,data):
        """Function to save a 1dim dataset once.
        
        The add method is used to add data to a coordinate dataset. The data is
        cast to a numpy array.
        """

        if self.ds_type == ds_types['coordinate'] or self.ds_type == ds_types['vector']:
            self.append(data, reset = True)
        else:
            logging.info("add is only for 1-Dim data. Please use append 2-Dim data.")
            return False
        
    def _create_timestamp_ds(self):
        """Create datasets containing timestamps assocciated with a measurement dataset.
        
        A dataset with the same name (+ suffix '_ts') and dimension-1 is created
        and unix timestamp added at each append() call.
        """
        ds_type = {
            ds_types['vector']: ds_types['vector'],
            ds_types['matrix']: ds_types['vector'],
            ds_types['box']: ds_types['matrix']
        }[self.ds_type]
        self.ds_ts = self.hf.create_dataset(self.name + '_ts', tracelength=1, folder=self.folder, dim=max(self.dim - 1, 1), dtype='float64', ds_type=ds_type)
        self.ds_ts.attrs.create('name', 'measurement_time'.encode())       
        self.ds_ts.attrs.create('unit', 's'.encode())
        if self.ds_type == ds_types['matrix']:
            self.ds_ts.attrs.create("x_ds_url",self.ds.attrs.get('x_ds_url', ''))
        if self.ds_type == ds_types['box']:
            self.ds_ts.attrs.create("x_ds_url",self.ds.attrs.get('x_ds_url', ''))
            self.ds_ts.attrs.create("y_ds_url",self.ds.attrs.get('y_ds_url', ''))
    """
    def __getitem__(self, name):
        return self.hf[name]

    def __setitem__(self, name, val):
        self.hf[name] = val
    """
    def __repr__(self):
        ret = "HDF5Data '%s'" % (self.name)
        return ret
