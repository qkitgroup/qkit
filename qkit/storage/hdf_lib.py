# -*- coding: utf-8 -*-
"""
Created 2015

@author: hrotzing
"""
import logging
import h5py
import numpy
#import gobject
import os
import time


#import data

#from lib.config import get_config
#config = get_config()
#in_qtlab = config.get('qtlab', False)
#from lib.network.object_sharer import SharedGObject, cache_result

#if in_qtlab:
#    import qt
config = {}
config['datadir'] = '/Users/hrotzing/pik/devel/python/qkit/measure/storage'

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
            # create a nexus data group        
            self.grp = self.entry.create_group("data")
            self.grp.attrs.create("NX_class","NXdata")
        else:
            self.grp = self.create_group("data0")
            
    def add_default_datasets(self):
        # add a empty string dataset to the group -> used by add_data
        self.create_dataset(name='datasets',tracelength=0, dtype='S32')
        
    def create_dataset(self,name,tracelength,**kwargs):
        """ handles one and two dimensional data
        
            tracelength: 
                is 0 for a single data point in a 1D scan (array of scalars)
                is the length of the first trace in 2D scan (array of vectors)
            For 2D scans the traces have to have the same tracelength
            and are simply appended to the trace array
            
            kwargs are appended as attributes to the dataset
        """
        if tracelength:
            shape    = (100,tracelength)
            maxshape = (None,tracelength)
        else:
            shape     = (100,)
            maxshape  = (None,)
        
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
            simple append method for data traces
            reshapes the array and updates the fill attribute
            
        """
        fill = ds.attrs.get("fill")
        try:
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

class Data(object):
    "this is basically the hdf5 class from hdf5_data adopted to our needs"
    #_data_list = data.Data._data_list
    _filename_generator = DateTimeGenerator()

    def __init__(self, *args, **kwargs):
        """
        Creates an empty data set including the file, for which the currently
        set file name generator is used.

        kwargs:
            name (string) : default is 'data'
        """
        
        name = kwargs.pop('name', 'data')
             
        self.generate_file_name(name, **kwargs)
            
        self.hf = H5_file(self._filepath)
        
        self.hf.flush()
        
        
    def generate_file_name(self, name, **kwargs):
        # for now just a copy from the origial file
        # Fixme: I would like to see this as a library function
    
        #name = data.Data._data_list.new_item_name(self, name)
        #print args

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
    """
    def create_dataset(self, *args, **kwargs):
        return self._file.create_dataset(*args, **kwargs)

    def create_group(self, *args, **kwargs):
        '''Create a raw HDF5 group in the file.'''
        return self._file.create_group(*args, **kwargs)

    def create_data_group(self, name, **kwargs):
        '''Create a DataGroup object.'''
        return DataGroup(name, self, **kwargs)
    """
    # from HDF5_data.py
    def _add_dimension(self, name, dim_type, **meta):
        '''
        Add a dimension to the data group.
        dim_type is not restricted, but 'coordinate' and 'value' should be
        used to specify what the dimension represents.
        Extra keywords are added as meta data.
        '''

        if name in self.hf.grp.keys():
            logging.error("Dimension '%s' already exists in data set '%s'" \
                    % (name, self.name))
            return False

        """for the (compatible) function 'add data point' we have to maintain a ordered list containing
        the names of the dataests"""
        self.hf.append('datasets',name)
        
        
        _tracelength = meta.get('tracelength',None)
        data = meta.get('data',None)
        meta['dim_type'] = dim_type
        
        
        if _tracelength is not None:
            tracelength = _tracelength
                    
        if data is not None:
            _tracelength = len(data)
            if tracelength == _tracelength:
                pass
            else:
                logging.error("Tracelength 'data'/'tracelength' does not match for '%s'."\
                    % name)
                tracelength = _tracelength
                
        if not tracelength:
            logging.info("HDF: No tracelength: postpone creation of hdf dataset for %s." %name)
            logging.info("HDF: Please specify tracelength for %s." %name)
            return
            
        # create the dataset
        ds = self.hf.create_dataset(name,tracelength,meta)
        

        if data is not None:
            self.hf.append(ds,data)
        return True

    def _add_value_dimension(self, name, type, **meta):
        '''
        Add a dimension to the data group.
        dim_type is not restricted, but 'coordinate' and 'value' should be
        used to specify what the dimension represents.
        Extra keywords are added as meta data.
        '''

        if name in self.hf.grp.keys():
            logging.error("Dimension '%s' already exists in data set '%s'" \
                    % (name, self.name))
            return False

        """for the (compatible) function 'add data point' we have to maintain a ordered list containing
        the names of the dataests"""
        self.hf.append('datasets',name)
        
        
        _tracelength = meta.get('tracelength',None)
        #data = meta.get('data',None)
        meta['dim_type'] = dim_type
        
        
            
        # create the dataset
        ds = self.hf.create_dataset(name,tracelength,meta)
        

        if data is not None:
            self.hf.append(ds,data)
        return True
        

    def add_coordinate(self, name, data=None, **meta):
        '''
        Add a coordinate dimension, optionally with known data.
        Extra keywords are added as meta data.
        '''
        return self._add_dimension(name, 'coordinate', data, **meta)

    def add_scalar_value(self, name, data=None, type="scalar", **meta):
        '''
        Add a value dimension, optionally with known data.
        Extra keywords are added as meta data.
        '''
        return self._add_dimension(name, 'value', data, **meta)
        
    def add_vector_value(self, name, data=None, type="vector", **meta):
        '''
        Add a value dimension, optionally with known data.
        Extra keywords are added as meta data.
        '''
        return self._add_dimension(name, 'value', data, **meta)
        
    
    def add_data(self,**kwargs):
        '''
        Append data to the hdf dataset.
        
        The kwargs should contain pairs of
        dimension/value name = data 
        e.g,
        field = 0
        frequencies = [10,20,30]
        
        The hdf list 'datasets' contains the list of valid dimensions/values        
        Extra keywords are ignored.
        '''
        datasets = self.hf['datasets'][:self.hf['datasets'].attrs['fill']]
        for ds in datasets:
            if ds in kwargs:
                if ds not in self.hf.grp:
                    # if the creation of the dataset has been postponed...
                    tracelength = len(kwargs.get(ds))
                    ds = self.hf.create_dataset(ds,tracelength)
                    
        for ds in kwargs:
            if ds in datasets:
                # append the data
                self.hf.append(ds,kwargs.get(ds))
        
        self.hf.flush()
        
        
    def add_data_point(self, *args, **kwargs):
        '''

        Add new data point(s) to the data set (in memory and/or on disk).
        Note that one data point can consist of multiple coordinates and values.

        provide 1 data point
            - N numbers: d.add_data_points(1, 2, 3)

        OR

        provide >1 data points.
            - a single MxN 2d array: d.add_data_point(arraydata)
            - N 1d arrays of length M: d.add_data_points(a1, a2, a3)

        Notes:
        If providing >1 argument, all vectors should have same shape.
        String data is not compatible with 'inmem'.

        Input:
            *args:
                n column values or a 2d array
            **kwargs:
                newblock (boolean): marks a new 'block' starts after this point

        Output:
            None
        '''

        # Check what type of data is being added
        shapes = [numpy.shape(i) for i in args]
        dims = numpy.array([len(i) for i in shapes])

        if len(args) == 0:
            logging.warning('add_data_point(): no data specified')
            return
        elif len(args) == 1:
            if dims[0] == 2:
                ncols = shapes[0][1]
                npoints = shapes[0][0]
                args = args[0]
            elif dims[0] == 1:
                ncols = 1
                npoints = shapes[0][0]
                args = args[0]
            elif dims[0] == 0:
                ncols = 1
                npoints = 1
            else:
                logging.warning('add_data_point(): adding >2d data not supported')
                return
        else:
            # Check if all arguments have same shape
            for i in range(1, len(args)):
                if shapes[i] != shapes[i-1]:
                    logging.warning('add_data_point(): not all provided data arguments have same shape')
                    return

            if sum(dims!=1) == 0:
                ncols = len(args)
                npoints = shapes[0][0]
                # Transpose args to a single 2-d list
                args = zip(*args)
            elif sum(dims!=0) == 0:
                ncols = len(args)
                npoints = 1
            else:
                logging.warning('add_data_point(): addint >2d data not supported')
                return

        # Check if the number of columns is correct.
        # If the number of columns is not yet specified, then it will be done
        # (only the first time) according to the data

        if len(self._dimensions) == 0:
            logging.warning('add_data_point(): no dimensions specified, adding according to data')
            self._add_missing_dimensions(ncols)

        if ncols < len(self._dimensions):
            logging.warning('add_data_point(): missing columns (%d < %d)' % \
                (ncols, len(self._dimensions)))
            return
        elif ncols > len(self._dimensions):
            logging.warning('add_data_point(): too many columns (%d > %d)' % \
                (ncols, len(self._dimensions)))
            return

        # At this point 'args' is either:
        #   - a 1d tuple of numbers, for adding a single data point
        #   - a 2d tuple/list/array, for adding >1 data points
        

        if self._infile:
            if npoints == 1:
                self._write_data_line(args)
            elif npoints > 1:
                for i in range(npoints):
                    self._write_data_line(args[i])

        self._npoints += npoints
        self._npoints_last_block += npoints
        if self._npoints_last_block > self._npoints_max_block:
            self._npoints_max_block = self._npoints_last_block

        if 'newblock' in kwargs and kwargs['newblock']:
            self.new_block()
        else:
            self.emit('new-data-point')
            

    def new_block(self):
        "Fortunately there is no need for this function with a hdf file"
        self.emit('new-data-block')

    def flush(self):
        self.hf.flush()

    def close(self):
        self._file.close()
        