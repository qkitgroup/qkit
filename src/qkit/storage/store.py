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
import traceback

import qkit
from qkit.storage.hdf_file import H5_file
from qkit.storage.hdf_dataset import hdf_dataset
from qkit.storage.hdf_constants import ds_types
from qkit.storage.hdf_view import dataset_view
from qkit.storage.hdf_DateTimeGenerator import DateTimeGenerator



class Data(object):
    """Basic hdf5 class adopted to our needs.
    
    This class is the public API for the qkit users with the hdf5 file. It
    is based in its core on h5py as well as our own adaptions in hdf_view, 
    hdf_file, and hdf_dataset. Here mostly have wrapper that operate on the
    mentioned classes.
    """
    # a types
    def __init__(self, name = None, mode = 'r+', copy_file = False):
        """Creates an empty data set including the file, for which the currently
        set file name generator is used or opens the h5 file at location 'name'.

        Args:
            name (string):  filename or absolute filepath
            mode (string):  access mode to the hdf5 file, default: 'r+' (read+write).
                Other modes are 'a' (read, write, and create)
        """
        self._name = name
        if os.path.isfile(self._name):
            self._filepath = os.path.abspath(self._name)
            self._folder, self._filename = os.path.split(self._filepath)
        elif not os.path.isabs(self._name):
            self._generate_file_name()
            try:
                qkit.fid.add_h5_file(self._filepath)
            except Exception as e:
                logging.debug("Could not add newly generated h5 File '{}' to qkit.fid database: {}".format(name,e))
        else:
            self._filepath = os.path.abspath(self._name)
            self._folder,self._filename = os.path.split(self._filepath)
        "setup the  file"
        try:
            self.hf = H5_file(self._filepath, mode)
        except IOError:
            raise IOError('File does not exist. Use argument \"mode=\'a\'\" to create a new h5 file.')
        if self.hf.newfile:
            if self.__dict__.get('_uuid', False):
                tags = ["_unix_timestamp", "_localtime", "_timestamp", "_timemark", "_datemark", "_uuid", "_filename", "_folder", "_relpath", "_filepath"]
                self.hf.hf.attrs.update({a: self.__dict__.get(a) for a in tags})
            if "user" in qkit.cfg:
                self.hf.hf.attrs['_user'] = qkit.cfg.get('user')
            if "run_id" in qkit.cfg:
                self.hf.hf.attrs['_run_id'] = qkit.cfg.get('run_id').upper()
        self._mapH5PathToObject()
        self.hf.flush()
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.hf.newfile:
            try:
                if type is not None:
                    s = "During creation of this file, the following error ocurred:\n"
                    s += str(exc_type.__name__) + ": " + str(exc_val)+"\n"
                    s += "".join(traceback.format_tb(exc_tb))
                    self.hf.entry.attrs["error"] = s
            except:
                pass
        self.close()

    def _mapH5PathToObject(self):
        """Function for automated data readout at Data object creation.
        
        This function gets called during the init of a data object. Here we 
        translate the attributes of all datasets into attributs of the 
        dummy-class "group". These objects get added to the self.__dict__ what
        makes them tabbable in a notebook.
        We iterate over all atributes of all entries in analysis0 and data0 as
        well as the 'comment' entry on the respective group attributes.
        """
        class group(object):
            pass
        
        a = group()
        for n, o in self.hf.hf['/entry/analysis0'].items():
            n = n.replace(" ","_")
            a.__dict__[n] = o
            for nn, oo in o.attrs.items():
                o.__dict__[nn] = oo
        a.__dict__['comment'] = self.hf.agrp.attrs.get('comment', '')
        d = group()
        for n, o in self.hf.hf['/entry/data0'].items():
            n = n.replace(" ","_")
            d.__dict__[n] = o
            for nn, oo in o.attrs.items():
                o.__dict__[nn] = oo
        d.__dict__['comment'] = self.hf.dgrp.attrs.get('comment', '')
        self.__dict__.update({'analysis':a})
        self.__dict__.update({'data':d})
        v = {a: self.hf.hf.attrs.get(a) for a in self.hf.hf.attrs.keys()}
        del v['NeXus_version'], v['qkit']
        self.__dict__.update(v)

    def _generate_file_name(self):
        """Generate new file name using hdf_DateTimeGenerator.
        
        This sets:
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
        """
        dtg = DateTimeGenerator()
        self.__dict__.update(dtg.new_filename(self._name))
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
            self.hf.dgrp.attrs.create('comment',comment.encode())
        elif folder == "analysis":
            self.hf.agrp.attrs.create("comment",comment.encode())
        else: 
            logging.warning("Foler muset be either 'data' (default) or 'analysis': '%s' provided" % (folder))
            raise ValueError

    def add_textlist(self,name,comment = "" ,folder="data", **meta):
        """Adds a dataset containing only text to the h5 file.
        
        This function is a wrapper to create a hdf_dataset object with some 
        predefined arguments. name, comment, and folder are parsed to the hdf_dataset
        init and the ds_type is set. The dataset does not have any axes.
        
        Args:
            name: String to name the dataset.
            comment: Optional string to put in any comment.
            folder: Optional string ('data' or 'analysis').
        
        Returns:
            hdf_dataset object.
        """
        ds =  hdf_dataset(self.hf, name, comment = comment, folder=folder, ds_type = ds_types['txt'], dim=1, **meta)
        return ds
        
    def add_coordinate(self,  name, unit = "", comment = "",folder="data",**meta):
        """Adds a coordinate dataset to the h5 file.
        
        This function is a wrapper to create a hdf_dataset object with some 
        predefined arguments. name, unit, comment, and folder are parsed to the hdf_dataset
        init and the ds_type is set. The dataset does not have any axes. The data
        is specifically casted to 64bit float.
        
        Args:
            name: String to name the dataset.
            unit: Optional string.
            comment: Optional string to put in any comment.
            folder: Optional string ('data' or 'analysis').
        
        Returns:
            hdf_dataset object.
        """
        ds =  hdf_dataset(self.hf, name,unit=unit, ds_type = ds_types['coordinate'],
                          comment= comment, folder=folder, dtype='float64', dim = 1, **meta)
        return ds

    def add_value_vector(self, name, x, unit = "", comment = "",folder="data",**meta):
        """Adds a 1dim dataset to the h5 file.
        
        This function is a wrapper to create a hdf_dataset object with some 
        predefined arguments. name, x-axis, unit, comment, and folder are parsed
        to the hdf_dataset init and the ds_type is set.
        
        Args:
            name: String to name the dataset.
            x: Optional hdf_dataset representing the x-coordinate of the vector.
            unit: Optional string.
            comment: Optional string to put in any comment.
            folder: Optional string ('data' or 'analysis').
        
        Returns:
            hdf_dataset object.
        """
        ds =  hdf_dataset(self.hf, name, x=x, unit=unit, ds_type = ds_types['vector'],
                          comment=comment, folder=folder, dim = 1, **meta)
        return ds

    def add_value_matrix(self, name, x , y, unit = "", comment = "",folder="data",**meta):
        """Adds a 2dim dataset to the h5 file.
        
        This function is a wrapper to create a hdf_dataset object with some 
        predefined arguments. name, x-axis, y-axis, unit, comment, and folder 
        are parsed to the hdf_dataset init and the ds_type is set.
        Our convention here is: y-axis changes "faster" than the x-axis.
        
        Args:
            name: String to name the dataset.
            x: Optional hdf_dataset representing the x-coordinate of the matrix.
            y: Optional hdf_dataset representing the y-coordinato of the matrix.
            unit: Optional string.
            comment: Optional string to put in any comment.
            folder: Optional string ('data' or 'analysis').
        
        Returns:
            hdf_dataset object.
        """
        ds =  hdf_dataset(self.hf, name, x=x, y=y, unit=unit, ds_type = ds_types['matrix'],
                          comment=comment, folder=folder, dim = 2, **meta)
        return ds

    def add_value_box(self, name, x , y, z, unit = "", comment = "",folder="data",**meta):
        """Adds a 3dim dataset to the h5 file.
        
        This function is a wrapper to create a hdf_dataset object with some 
        predefined arguments. name, x-axis, y-axis, z-axis, unit, comment, and folder 
        are parsed to the hdf_dataset init and the ds_type is set.
        Our convention here is: y-axis changes "faster" than the x-axis.
        
        Args:
            name: String to name the dataset.
            x: Optional hdf_dataset representing the x-coordinate of the box.
            y: Optional hdf_dataset representing the y-coordinato of the box.
            z: Optional hdf_dataset representing the y-coordinato of the box.
            unit: Optional string.
            comment: Optional string to put in any comment.
            folder: Optional string ('data' or 'analysis').
        
        Returns:
            hdf_dataset object.
        """        
        ds =  hdf_dataset(self.hf,name, x=x, y=y, z=z, unit=unit, ds_type = ds_types['box'],
                          comment=comment, folder=folder, dim = 3, **meta)
        return ds

    def add_view(self,name,x = None, y = None, error = None, filter  = None, view_params = {}):
        """Adds a view to plot x-y data.
        
        This function is a wrapper to create a dataset_view.
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

    def add_fid_param(self, param, value):
        """Adds a parameter (and value) to be read out with the file info database class.
        
        This function adds an entry to the atrribute dict of the self.hf agrp-entry. By default
        this is set to the attribute0 folder. The dict may be read out by the file info database
        class and in the end the entries can be sorted by all params.

        Args:
            param: Parameter name
            value: Parameter value
        """
    
        self.hf.agrp.attrs[param] = value

    def get_dataset(self,ds_url):
        return hdf_dataset(self.hf,ds_url = ds_url)

    def save_finished(self):
        pass

    def flush(self):
        self.hf.flush()

    def close_file(self):
        self.hf.close_file()
    def close(self):
        self.hf.close_file()
