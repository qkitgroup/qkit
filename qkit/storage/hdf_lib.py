# -*- coding: utf-8 -*-
"""
Library to ease the use of the file format hdf5 for datastorage
It can be used with or without the qtlab environment.

@author: hannes.rotzinger@kit.edu 2015
@version: 0.1
"""
import logging


import os
import time

from hdf_file import H5_file
from hdf_dataset import hdf_dataset
from hdf_view import dataset_view
from hdf_DateTimeGenerator import DateTimeGenerator

try:
    from lib.config import get_config
    config = get_config()
    in_qtlab = config.get('qtlab', False)

    if in_qtlab:
        import qt
except ImportError:
    import tempfile
    #print 'executing apparently not in the qt environment, set data root to:'+tempfile.gettempdir()
    config = {}
    config['datadir'] = tempfile.gettempdir()





class Data(object):
    "this is a basic hdf5 class adopted to our needs"
   

    def __init__(self, *args, **kwargs):
        """
        Creates an empty data set including the file, for which the currently
        set file name generator is used.

        kwargs:
            name (string) : default is 'data'
        """
        
        name = kwargs.pop('name', 'data')
        
        "if path was omitted, a new filepath will be created"        
        path = kwargs.pop('path',None)        
        self._filename_generator = DateTimeGenerator()
        self.generate_file_name(name, filepath = path, **kwargs)
        
        "setup the  file"
        self.hf = H5_file(self._filepath)
        
        self.hf.flush()
        
        
    def generate_file_name(self, name, **kwargs):
        # for now just a copy from the origial file
        

        self._name = name

        filepath = kwargs.get('filepath', None)
        if filepath:
            self._filepath = filepath
        else:
            self._localtime = time.localtime()
            self._timestamp = time.asctime(self._localtime)
            self._timemark = time.strftime('%H%M%S', self._localtime)
            self._datemark = time.strftime('%Y%m%d', self._localtime)
            self._filepath =  self._filename_generator.new_filename(self)

        self._folder, self._filename = os.path.split(self._filepath)
        if self._folder and not os.path.isdir(self._folder):
            os.makedirs(self._folder)
        

    def __getitem__(self, name):
        return self.hf[name]

    def __setitem__(self, name, val):
        self.hf[name] = val

    def __repr__(self):
        ret = "HDF5Data '%s', filename '%s'" % (self._name, self._filename)
        return ret

    def get_filepath(self):
        return self._filepath

    def get_folder(self):
        return self._folder
    
    def add_comment(self,comment, folder = "data" ):
        if folder == "data":
            self.hf.dgrp.attrs.create("comment",comment)
        if folder == "analysis":
            self.hf.agrp.attrs.create("comment",comment)
            
    def add_coordinate(self,  name, unit = "", comment = "",folder="data",**meta):
        ds =  hdf_dataset(self.hf,name,unit=unit,comment= comment, folder=folder)
        return ds
    
    def add_value_vector(self, name, x = None, unit = "", comment = "",folder="data",**meta):
        ds =  hdf_dataset(self.hf,name, x=x, unit=unit, comment=comment, folder=folder)
        return ds

    def add_value_matrix(self, name, x = None , y = None, unit = "", comment = "",folder="data",**meta):
        ds =  hdf_dataset(self.hf,name, x=x, y=y, unit=unit, comment=comment, folder=folder)
        return ds
 
    def add_value_box(self, name, x = None , y = None, z = None, unit = "", comment = "",folder="data",**meta):
        #ds =  hdf_dataset(self.hf,name, x=x, y=y, z=z, unit=unit, comment=comment, folder=folder)
        pass
    
    
    
    def add_view(self,name,x = None, y = None, filter  = None, comment = ""):
        """a view is a way to display plot x-y data.
            x, y are the datasets to display, e.g. 
            x = "data0/temperature"
            y = "analysis0/frequency_fit"
            (if "folder/" is omitted "data0" is assumed)
            filter is a string of reguar python code, which 
            accesses the x,y dataset returns arrays of (x,y) 
            (Fixme: not jet implemented)                                     
        """
        ds =  dataset_view(self.hf,name, x=x, y=y, comment=comment)
        return ds
        
        pass        
    
    def get_dataset(self,ds_url):
        return hdf_dataset(self.hf,ds_url = ds_url)
        
    def save_finished():
        pass
    
    def flush(self):
        self.hf.flush()
    
    def close_file(self):
        self.hf.close_file()
    def close(self):
        self.hf.close_file()