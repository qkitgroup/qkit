# -*- coding: utf-8 -*-
"""
Library to ease the use of the file format hdf5 for datastorage
It can be used with or without the qtlab environment.

@author: hannes.rotzinger@kit.edu 2015
@version: 0.1
"""
import logging
import h5py
import numpy

import os
import time


try:
    from lib.config import get_config
    config = get_config()
    in_qtlab = config.get('qtlab', False)

    if in_qtlab:
        import qt
except ImportError:
    import tempfile
    print 'executing apparently not in the qt environment, set data root to:'+tempfile.gettempdir()
    config = {}
    config['datadir'] = tempfile.gettempdir()

class H5_file(object):
    """ This base hdf5 class ist intended for QTlab as a base class for a 
    hdf5 based Data class as compatible as possible to the standard data class. 
    It is in many respects more restricted to the hdf5_data.py class, 
    it e.g. does only create one group in the HDF5 file, etc.
    
    The class itself contans only the interface to the hdf5 file and 
    can be used also standalone.
    
    """    
    
    def __init__(self,output_file,**kw):
        
        self.create_file(output_file)
        self.set_base_attributes()
        
        # set all standard attributes
        for k in kw:
            self.grp.attrs[k] = kw[k]
            
    def create_file(self,output_file):
        self.hf = h5py.File(output_file,'a')
        
    def set_base_attributes(self,nexus=True):
        "stores some attributes and creates the default data group"
        # store version of the file format
        self.hf.attrs.create("qt-file","1.0") # qtlab file version
        self.hf.attrs.create("qtlab", "1.0")  # qtlab version
        if nexus:
            # make the structure compatible with the nexus format
            # maybe some day the data can by analyzed by the software supporting nexus
            # first the entry group
            self.hf.attrs.create("NeXus_version","4.3.0")
            self.entry = self.hf.create_group("entry")
            self.entry.attrs.create("NX_class","NXentry")
            self.entry.attrs.create("data_latest",0)
            self.entry.attrs.create("analysis_latest",0)
            # create a nexus data group        
            self.grp = self.entry.create_group("data0")
            self.grp.attrs.create("NX_class","NXdata")
        else:
            self.grp = self.create_group("data0")
            
    def add_default_datasets(self):
        # add a empty string dataset to the group -> used by add_data
        self.create_dataset(name='datasets',tracelength=0, dtype='S32')
        
    def add_string_datasets(self):
        # add a empty string dataset to the group -> used by add_data
        self.create_dataset(name='datasets',tracelength=0, dtype='S32')
        
    def create_dataset(self,name,tracelength, group = None,**kwargs):
        """ handles one and two dimensional data
        
            tracelength: 
                is 0 for a single data point in a 1D scan (array of scalars)
                is the length of the first trace in 2D scan (array of vectors)
            For 2D scans the traces have to have the same tracelength
            and are simply appended to the trace array
            
            'group' is a optional group relative to the default group
            
            kwargs are appended as attributes to the dataset
        """
        if tracelength:
            shape    = (100,tracelength)
            maxshape = (None,tracelength)
        else:
            shape     = (100,)
            maxshape  = (None,)
        if group:
                self.grp = self.grp.require_group(group)
                
        if name in self.grp.keys():
            logging.error("Item '%s' already exists in data set '%s'" \
                    % (name, self.name))
            return False        

        # by default we create float datasets        
        dtype = kwargs.get('dtype','f')

        #create the dataset            
        ds = self.grp.create_dataset(name, shape, maxshape=maxshape,dtype=dtype)
        
        # keep track of the actual fill of an array.
        ds.attrs.create("fill",0)
        
        ds.attrs.create("name",name)
        # add attibutes
        for a in kwargs:
             ds.attrs.create(a,kwargs[a])
        return ds
        
    def append(self,ds,data, extend_step = 100):
        """ Append method for hdf5 data. 
            A simple append method for data traces
            reshapes the array and updates the fill attribute
            
        """
        fill = ds.attrs.get("fill")
        try:
            if len(ds.shape) == 1:
                if type(data) == float:
                    ds[fill] = data
                    ds.attrs.modify("fill",fill+1)
                elif len(data.shape) == 1:
                    ds.resize(len(data),axis = 0)
                    ds.attrs.modify("fill",len(data))
                    ds[:] = data
            else:
                ds[fill] = data
                ds.attrs.modify("fill",fill+1)
            
        except ValueError:
            # array full...
            new_size = (ds.shape[0]) + extend_step
            ds.resize(new_size, axis=0)
            #print "resized at fill:", fill
            
            ds[fill] = data
            ds.attrs.modify("fill",fill+1)
            
    def flush(self):
        self.hf.flush()
        
    def close_file(self):
        # before closing the file, reduce all arrays in the group 
        # to their "fill" length
        for ds in self.grp.itervalues():
                fill  = ds.attrs.get("fill")
                if fill > 0:
                    ds.resize(fill,axis=0)
              
        self.hf.close()

# Filename generator classes (taken from qtlab.source.data)
class DateTimeGenerator(object):
    '''
    Class to generate filenames / directories based on the date and time.
    Date (YYYYMMDD) -> Time (HHMMSS) -> data
    '''

    def __init__(self):
        pass

    def create_data_dir(self, datadir, name=None, ts=None, datesubdir=True, timesubdir=True):
        '''
        Create and return a new data directory.

        Input:
            datadir (string): base directory
            name (string): optional name of measurement
            ts (time.localtime()): timestamp which will be used if timesubdir=True
            datesubdir (bool): whether to create a subdirectory for the date
            timesubdir (bool): whether to create a subdirectory for the time

        Output:
            The directory to place the new file in
        '''

        path = datadir
        if ts is None:
            ts = time.localtime()
        if datesubdir:
            path = os.path.join(path, time.strftime('%Y%m%d', ts))
        if timesubdir:
            tsd = time.strftime('%H%M%S', ts)
            if name is not None:
                tsd += '_' + name
            path = os.path.join(path, tsd)

        return path

    def new_filename(self, data_obj):
        '''Return a new filename, based on name and timestamp.'''

        dir = self.create_data_dir(config['datadir'], name=data_obj._name,
                ts=data_obj._localtime)
        tstr = time.strftime('%H%M%S', data_obj._localtime)
        filename = '%s_%s.h5' % (tstr, data_obj._name)

        return os.path.join(dir, filename)

class hdf_dataset(object):
        """
        This class represents the dataset in python.        
        
        this is also a helper class to postpone the creation of the datasets.
        The main issue here is that until the first data is aquired, 
        some dimensions and items are unknown.
        To keep the userinterface simple, we choose to postpone the creation 
        of the datasets and derive all the unknown values from the real data.
        """
        
        def __init__(self, hdf_file, name, x=None, y=None, unit= "" ,comment="", **meta):
            self.hf = hdf_file
            self.name = name
            self.unit = unit
            self.comment = comment
            self.meta = meta
            self.x_object = x
            self.y_object = y            
            
            # the first dataset is used to extract a few attributes
            self.first = True
            
            # 1d/2d attributes
            self.x_name = name
            self.x_unit = unit
            self.x0 = 0.0
            self.dx = 1.0
            
            self.y_name = ""
            self.y_unit = ""            
            self.y0 = 0.0
            self.dy = 1.0
                        
            self.z_name = name
            self.z_unit = unit
            
        def _setup_metadata(self):
            ds = self.ds
            # 2d/matrix 
            if self.x_object:
                ds.attrs.create("x0",self.x_object.x0)
                ds.attrs.create("dx",self.x_object.dx)
                ds.attrs.create("x_unit",self.x_object.x_unit)
                ds.attrs.create("x_name",self.x_object.x_name)
            else:
                ds.attrs.create("x0",self.x0)
                ds.attrs.create("dx",self.dx)
                ds.attrs.create("x_unit",self.x_unit)
                ds.attrs.create("x_name",self.x_name)
            if self.y_object:
                ds.attrs.create("y0",self.y_object.x0)
                ds.attrs.create("dy",self.y_object.dx)
                ds.attrs.create("y_unit",self.y_object.x_unit)
                ds.attrs.create("y_name",self.y_object.x_name)
                
                ds.attrs.create("z_unit",self.z_unit)
                ds.attrs.create("z_name",self.z_name)
            else:
                ds.attrs.create("y0",self.y0)
                ds.attrs.create("dy",self.dy)
                ds.attrs.create("y_unit",self.y_unit)
                ds.attrs.create("y_name",self.y_name)
                
                #ds.attrs.create("z_unit",self.z_unit)
                #ds.attrs.create("z_name",self.z_name)
                

            
        def append(self,data):
            """
            The add method is used to save a growing 2-Dim matrix to the hdf file, 
            one line/vector at a time.
            For example, data can be a frequency scan of a 1D scan.
            """
            # at this point the reference data should be around
            if self.first:
                self.first = False
                #print self.name, data.shape
                if type(data) == numpy.ndarray:
                    tracelength = len(data)
                else:
                    tracelength = 0
                # create the dataset
                self.ds = self.hf.create_dataset(self.name,tracelength,**self.meta)
                self._setup_metadata()
                
            if data is not None:
                self.hf.append(self.ds,data)
            self.hf.flush()
                
                
        def add(self,data):
            """
            The add method is used to save a 1-Dim vector to the hdf file once.
            For example, this can be a coordinate of a 1D scan.

            """
           
            if self.y_object:
                logging.info("add is only for 1-Dim data. Please use append 2-Dim data.")
                return False
                
            if self.first:
                self.first = False
                #print self.name, data.shape
                tracelength = 0
                # create the dataset
                self.ds = self.hf.create_dataset(self.name,tracelength,**self.meta)
                ds = self.ds
                if not self.x_object:
                    # value data
                    if len(data) > 2:                
                        self.x0 = data[0]
                        self.dx = data[1]-data[0]
                
                    ds.attrs.create("x0",self.x0)
                    ds.attrs.create("dx",self.dx)
                else:
                    # coordinate vector
                    self.x0 = self.x_object.x0
                    self.dx = self.x_object.dx
                
                    ds.attrs.create("x0",self.x0)
                    ds.attrs.create("dx",self.dx)
                    
                ds.attrs.create("x_unit",self.x_unit)
                ds.attrs.create("x_name",self.x_name)
                
                
            if data is not None:
                #print "hf  #: ",self.hf, self.ds
                self.hf.append(self.ds,data)
            self.hf.flush()
            

        """
        def __getitem__(self, name):
            return self.hf[name]

        def __setitem__(self, name, val):
            self.hf[name] = val
        """
        def __repr__(self):
            ret = "HDF5Data '%s', filename '%s'" % (self._name, self._filename)
            return ret

        

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
        
        "setup the new file"
        self.hf = H5_file(self._filepath)
        
        self.hf.flush()
        
        
    def generate_file_name(self, name, **kwargs):
        # for now just a copy from the origial file
        # Fixme: I would like to see this as a library function


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
        if not os.path.isdir(self._folder):
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
         
    def add_coordinate(self,  name, unit = "", comment = "",**meta):
        ds =  hdf_dataset(self.hf,name,unit=unit,comment= comment)
        return ds
    
    def add_value_vector(self, name, x = None, unit = "", comment = "",**meta):
        ds =  hdf_dataset(self.hf,name, x=x, unit=unit, comment= comment)
        return ds

    def add_value_matrix(self, name, x = None , y = None, unit = "", comment = "",**meta):
        ds =  hdf_dataset(self.hf,name, x=x, y=y, unit=unit, comment= comment)
        return ds
 
    def flush(self):
        self.hf.flush()

    def close(self):
        self.hf.close_file()