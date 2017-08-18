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
from qkit.config.environment import cfg

alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

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
            self._unix_timestamp = int(time.time())
            self._uuid = self._create_uuid()
            self._localtime = time.localtime(self._unix_timestamp)
            self._timestamp = time.asctime(self._localtime)
            self._timemark = time.strftime('%H%M%S', self._localtime)
            self._datemark = time.strftime('%Y%m%d', self._localtime)
            self._filepath =  self._filename_generator.new_filename(self)
            self._relpath = os.path.relpath(self._filepath, cfg['datadir'])

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
        
    def _create_uuid(self):
        return self.encode_uuid()
    
    def encode_uuid(self,value=None):
        if not value: value = self._unix_timestamp
        output = ''
        la = len(alphabet)
        while(value):
            output += alphabet[value%la]
            value = value/la
        return output[::-1]

    def decode_uuid(self,string=''):
        if not string: string = self._uuid
        output = 0
        multiplier = 1
        string = string[::-1].upper()
        la = len(alphabet)
        while(string != ''):
            f = alphabet.find(string[0])
            if f == -1:
                raise ValueError("Can not decode this: %s<--"%string[::-1])
            output += f*multiplier
            multiplier*=la
            string = string[1:]
        return output