# -*- coding: utf-8 -*-
"""
Created 2015

@author: H. Rotzinger, MP Pfirrmann, M Wildermuth


"""
import logging
import h5py
import numpy as np
import qkit
from qkit.storage.hdf_constants import ds_types
from distutils.version import LooseVersion

file_kwargs = dict()
if LooseVersion(h5py.__version__) >= LooseVersion("3.5.0"): # new file locking
    file_kwargs = dict(locking=False)
elif LooseVersion(h5py.__version__) >= LooseVersion("3.0.0"): # intermediate
    logging.error("Qkit HDF file handling: In h5py between 3.0 and 3.5, there are problems with file locking handling. Please update to h5py==3.5.0")

class H5_file(object):
    """Base hdf5 class intended for qkit.
    
    hdf5 based Data class as compatible as possible to the standard data class. 
    It is in many respects more restricted to the hdf5_data.py class, 
    it e.g. does only create one group in the HDF5 file, etc.
    
    The class itself contans only the interface to the hdf5 file and 
    can be used also standalone.
    Here we again wrap the create_dataset() fctn and the append() fct does the
    trick of placing added data in the correct position in the dataset.
    """    
    
    def __init__(self,output_file, mode,**kw):
        """Inits the H5_file at the path 'output_file' with the access mode
        'mode'
        """
        self.create_file(output_file, mode)
        self.newfile = False
        
        if self.hf.attrs.get("qt-file",None) or self.hf.attrs.get("qkit",None):
            "File existed before and was created by qkit."
            self.setup_required_groups()
        else:
            "new file or none qkit file"
            self.newfile = True
            self.set_base_attributes()
        
            # set all standard attributes
            for k in kw:
                self.grp.attrs[k] = kw[k]
        
    def create_file(self,output_file, mode):
        self.hf = h5py.File(output_file, mode,**file_kwargs )

    def set_base_attributes(self):
        "stores some attributes and creates the default data group"
        # store version of the file format
        self.hf.attrs.create("qkit", "1.0".encode())  # qkit version
        # make the structure compatible with the nexus format
        # maybe some day the data can by analyzed by the software supporting nexus
        # first the entry group
        self.hf.attrs.create("NeXus_version","4.3.0".encode())
        
        self.entry = self.hf.require_group("entry")
        self.entry.attrs.create("NX_class","NXentry".encode())
        self.entry.attrs.create("data_latest",0)
        self.entry.attrs.create("analysis_latest",0)
        self.entry.attrs.create("updating",True)
        # create a nexus data group        
        self.dgrp = self.entry.require_group("data0")
        self.agrp = self.entry.require_group("analysis0")
        self.vgrp = self.entry.require_group("views")
        self.dgrp.attrs.create("NX_class","NXdata".encode())
        self.dgrp.attrs.create("NX_class","NXdata".encode())
    
    def setup_required_groups(self):
        # make the structure compatible with the nexus format
        # maybe some day the data can by analyzed by the software supporting nexus
        # first the entry group
        self.entry = self.hf.require_group("entry")
        # create a nexus data group        
        self.dgrp = self.entry.require_group("data0")
        self.agrp = self.entry.require_group("analysis0")
        self.vgrp = self.entry.require_group("views")
        
    def create_dataset(self,name, tracelength, ds_type = ds_types['vector'],
                       folder = "data", dim = 1, **kwargs):
        """Dataset for one, two, and three dimensional data
        
            Args:
                
                'tracelength'
            
                'dim'
                    is 1 for a single data point in a 1D scan (array of scalars)
                    is the length of the first trace in 2D scan (array of vectors)
                    For 2D scans the traces have to have the same tracelength
                    and are simply appended to the trace array
            
                'folder' is a optional group relative to the default group
            
                'kwargs' are appended as attributes to the dataset
        """

        self.ds_type = ds_type
        
        if dim == 1:
            shape    = (0,)
            maxshape = (None,)
            chunks=True
            
        elif dim == 2:
            shape    = (0,0)
            maxshape = (None,None)
            chunks=(5, tracelength)
            
        elif dim == 3:
            shape    = (0,0,0)
            maxshape = (None,None,None)
            chunks=(5, 5, tracelength)
            
        else:
            logging.error("Create datasets: '%s' is wrong number of dims." %(dim))
            raise ValueError

        if folder == "data":
            self.grp = self.dgrp
        elif folder == "analysis":
            self.grp = self.agrp
        elif folder == "views":
            self.grp = self.vgrp

        else:
            logging.error("please specify either: folder = 'data' , folder = 'analysis' or folder ='view' ")
            raise ValueError
            
        if name in self.grp.keys():
            logging.info("Item '%s' already exists in data set." % (name))
            #return False        
            
        # by default we create float datasets        
        dtype = kwargs.get('dtype','f')
        
        # we store text as unicode; this seems somewhat non-standard for hdf
        if ds_type == ds_types['txt']:
            try:
                dtype = h5py.special_dtype(vlen=unicode) # python 2
            except NameError:
                dtype = h5py.special_dtype(vlen=str) # python 3
        #create the dataset ...;  delete it first if it exists, unless it is data
        if name in self.grp.keys(): 
            if folder == "data":
                logging.error("Dataset '%s' in 'data' already exists. Cannot overwrite datasets in 'data'!" % (name))
                raise ValueError
            else:
                del self.grp[name]
                # comment: The above line does remove the reference to the dataset but does not free the space aquired
                # fixme if possible ...


        # 'scaleoffset' is an optional parameter for lossy compression of floating-point data,  retaining a specified number of bits post-decimal. 
        # It is used to compress dataset elements by reducing the precision of the data. Defaults to None, implying no compression.
        scaleoffset = kwargs.get('scaleoffset',None)

        if ds_type == ds_types['txt']:
            ds = self.grp.create_dataset(name, shape, maxshape=maxshape, chunks = chunks, dtype=dtype, scaleoffset = scaleoffset)
        else:
            ds = self.grp.create_dataset(name, shape, maxshape=maxshape, chunks = chunks, dtype=dtype, fillvalue = np.nan, scaleoffset = scaleoffset)
        
        ds.attrs.create("name",name.encode())
        ds.attrs.create("ds_type", ds_type)
        if ds_type == ds_types['matrix'] or ds_type == ds_types['box']:
            ## fill value only needed for >1D datasets
            ds.attrs.create("fill", [0,0,0])
        # add attibutes
        for a in kwargs:
            if not a == "scaleoffset":
                ds.attrs.create(a,(kwargs[a]).encode())
             
        self.flush()
        return ds
        
    def append(self,ds,data, next_matrix=False, reset=False, pointwise=False):
        """Method for appending hdf5 data. 
        
        A simple append method for data traces.
        Reshapes the array and updates the attributes.
        The optional 'next_matrix' atrribute arranges the incoming data in a 
        value_box correctly.
        
        Args:
            hdf_dataset 'ds'
            numpy array 'data'
            boolean 'next_matrix'
            pointwise (Boolean): if True, the data is appended pointwise, i.e. to the innermost dimension
        Returns:
            The function operates on the given variables.
        """
        # it gets a little ugly with all the different user-cases here ...
        if len(ds.shape) == 1:
            ## 1dim dataset (text, coordinate, vector)
            ## multiple inputs: text, scalar (not needed?), list/np.array with one or multiple entries
            if self.ds_type == ds_types['txt']:
                ## text
                dim1 = ds.shape[0]+1
                ds.resize((dim1,))
                ds[dim1-1] = data
                """
                ## This should not be needed anymore as there are non-user typecasts to np arrays before calling this fct.
                elif len(data.shape) == 0:              
                    ## scalar input; this is more or less useless, all non-text data gets cast
                    ## into np.array prior to calling this function.
                    dim1 = ds.shape[0]+1
                    fill[0] += 1
                    ds.resize((dim1,))
                    ds[fill[0]-1] = data
                """
            elif len(data.shape) == 1:
                ## np array (or list)
                if len(data) == 1:                  
                    ## single entry
                    dim1 = ds.shape[0]+1
                    ds.resize((dim1,))
                    ds[dim1-1] = data
                else:                               
                    ## list of entries               
                    if reset:
                        ## here the data gets not appended but overwritten!
                        ds.resize((len(data),))
                        ds[:] = data
                    else:
                        ## data append
                        dim1 = ds.shape[0] 
                        ds.resize((dim1+len(data),))
                        ds[dim1:] = data

        if len(ds.shape) == 2:       
            ## 2 dim dataset: matrix
            ## multiple inputs: list/np.array with one or multiple entries
            fill = ds.attrs.get('fill')
            dim1 = ds.shape[1]
            if len(data) == 1 and pointwise:
                dim0 = max(1, ds.shape[0])
                ## single entry; sorting like in the 'len(ds.shape) == 3' case
                if next_matrix:
                    dim0 += 1
                    fill[0] += 1
                    fill[1] = 0
                if dim0 == 1: # very first slice
                    fill[0] = 1
                    dim1 += 1
                ds.resize((dim0,dim1))
                fill[1] += 1
                ds[fill[0]-1,fill[1]-1] = data
            else: 
                ## list of entries, sort the data 'slice by slice'
                dim0 = ds.shape[0]
                fill[1] = len(data)
                if reset:
                    ds[dim0-1,:] = data  # reset overwrites last data series (last row matrix)
                else:  # standard reset = False
                    fill[0] += 1
                    ds.resize((dim0+1,len(data)))
                    ds[dim0,:] = data
            ds.attrs.modify('fill', fill)

        if len(ds.shape) == 3:      
            ## 3 dim dataset: box
            ## input: np.array with multiple entries
            dim0 = max(1, ds.shape[0])
            dim1 = ds.shape[1]
            fill = ds.attrs.get('fill')
            if next_matrix:
                dim0 += 1
                fill[0] += 1
                fill[1] = 0
            if dim0 == 1:
                fill[0] = 1
                dim1 += 1
            if not reset:  # standard reset = False
                ds.resize((dim0,dim1,len(data))) # Update array size
                fill[1] += 1 # Update write position
            ds[fill[0]-1,fill[1]-1] = data # Our indices start with one.
            ds.attrs.modify("fill", fill)

        self.flush()
        
    def flush(self):
        self.hf.flush()
        
    def close_file(self):
        # delegate close
        if self.newfile:
            self.entry.attrs["updating"] = False
        self.hf.close()
        
    def __getitem__(self,s):
        return self.hf[s]
