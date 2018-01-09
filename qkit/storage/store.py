# -*- coding: utf-8 -*-
"""
Library to ease the use of the file format hdf5 for datastorage
It can be used with or without the qtlab environment.

@author: hannes.rotzinger@kit.edu 2018
@author: marco.pfirrmann@kit.edu 2018
@version: 0.1
"""
import logging
import os

import qkit
from qkit.storage.hdf_file import H5_file
from qkit.storage.hdf_dataset import hdf_dataset
from qkit.storage.hdf_constants import ds_types
from qkit.storage.hdf_view import dataset_view
from qkit.storage.hdf_DateTimeGenerator import DateTimeGenerator



class Data(object):
    "this is a basic hdf5 class adopted to our needs"
    # a types
    def __init__(self, name = None, copy_file = False):
        """
        Creates an empty data set including the file, for which the currently
        set file name generator is used.

        name (string):  filename or absolute filepath
        """
        self._name = name

        if not os.path.isabs(self._name):
            self._generate_file_name()
        else:
            self._filepath = os.path.abspath(self._name)
            self._folder,self._filename = os.path.split(self._filepath)
        "setup the  file"
        self.hf = H5_file(self._filepath)
        self._mapH5PathToObject()
        self.hf.flush()

    def _mapH5PathToObject(self):
        class group(object):
            pass
        
        a = group()
        for n, o in self.hf.hf['/entry/analysis0'].iteritems():
            a.__dict__[n] = o
            for nn, oo in o.attrs.iteritems():
                o.__dict__[nn] = oo
        d = group()
        for n, o in self.hf.hf['/entry/data0'].iteritems():
            d.__dict__[n] = o
            for nn, oo in o.attrs.iteritems():
                o.__dict__[nn] = oo
        self.__dict__.update({'analysis':a})
        self.__dict__.update({'data':d})

    def _generate_file_name(self):
        dtg = DateTimeGenerator()
        self.__dict__.update(dtg.new_filename(self._name))
        '''
        this sets:
            _unix_timestamp
            _localtime    
            _timestamp
            _timemark
            _datemark
            _uuid
            _filename
            _folder
            _relpath
            _filepath        
        '''
        
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
            #existing_comment = self.hf.dgrp.attrs.get('comment',None)
            #if existing_comment:
            #    comment = existing_comment+\n+comment
            self.hf.dgrp.attrs.create('comment',comment)
        if folder == "analysis":
            #existing_comment = self.hf.agrp.attrs.get('comment',None)
            #if existing_comment:
            #    comment = existing_comment+\n+comment
            self.hf.agrp.attrs.create("comment",comment)
    def add_textlist(self,name,comment = "" ,folder="data", **meta):
        ds =  hdf_dataset(self.hf, name, comment = comment, folder=folder, ds_type = ds_types['txt'], dim=1, **meta)
        return ds
        
    def add_coordinate(self,  name, unit = "", comment = "",folder="data",**meta):
        ds =  hdf_dataset(self.hf, name,unit=unit, ds_type = ds_types['coordinate'],
                          comment= comment, folder=folder, dtype='float64', **meta)
        return ds

    def add_value_vector(self, name, x = None, unit = "", comment = "",folder="data",**meta):
        ds =  hdf_dataset(self.hf, name, x=x, unit=unit, ds_type = ds_types['vector'],
                          comment=comment, folder=folder,**meta)
        return ds

    def add_value_matrix(self, name, x = None , y = None, unit = "", comment = "",folder="data",**meta):
        ds =  hdf_dataset(self.hf, name, x=x, y=y, unit=unit, ds_type = ds_types['matrix'],
                          comment=comment, folder=folder,**meta)
        return ds

    def add_value_box(self, name, x = None , y = None, z = None, unit = "", comment = "",folder="data",**meta):
        ds =  hdf_dataset(self.hf,name, x=x, y=y, z=z, unit=unit, ds_type = ds_types['box'],
                          comment=comment, folder=folder,**meta)
        return ds

    def add_view(self,name,x = None, y = None, error = None, filter  = None, view_params = {}):
        """
        a view is a way to display plot x-y data.
        x, y with the corresponding error are the datasets to display, e.g.
        x = h5["/entry/data0/temperature"]
        y = h5["/entry/analysis0/frequency_fit"]
        error = h5["/entry/analysis0/frequency_fit_error"]
        filter is a string of reguar python code, which
        accesses the x,y dataset returns arrays of (x,y)
        (Fixme: not jet implemented)
        """
        ds =  dataset_view(self.hf,name, x=x, y=y, error=error, filter = filter, 
                           ds_type = ds_types['view'],view_params = view_params)
        return ds

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
