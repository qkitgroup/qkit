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
from hdf_constants import ds_types
from hdf_view import dataset_view
from hdf_DateTimeGenerator import DateTimeGenerator
from qkit.config.environment import *

class Data(object):
    "this is a basic hdf5 class adopted to our needs"
    # a types
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
                          comment= comment, folder=folder,**meta)
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

    def add_view(self,name,x = None, y = None, x_axis=0, y_axis=0, filter  = None, comment = ""):
        """a view is a way to display plot x-y data.
            x, y are the datasets to display, e.g.
            x = "data0/temperature"
            y = "analysis0/frequency_fit"
            (if "folder/" is omitted "data0" is assumed)
            x_axis is the slice dimension on multidim arrays
            y_axis is the slice dimension on multidim arrays
            filter is a string of reguar python code, which
            accesses the x,y dataset returns arrays of (x,y)
            (Fixme: not jet implemented)
        """
        ds =  dataset_view(self.hf,name, x=x, y=y, x_axis=x_axis, y_axis=y_axis, ds_type = ds_types['view'],
                           comment=comment)
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