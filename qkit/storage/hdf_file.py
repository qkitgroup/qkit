# -*- coding: utf-8 -*-
"""
Created 2015

@author: hrotzing
"""
import logging

import h5py
import qkit
from qkit.storage.hdf_constants import ds_types


class H5_file(object):
    """ This base hdf5 class ist intended for QTlab as a base class for a 
    hdf5 based Data class as compatible as possible to the standard data class. 
    It is in many respects more restricted to the hdf5_data.py class, 
    it e.g. does only create one group in the HDF5 file, etc.
    
    The class itself contans only the interface to the hdf5 file and 
    can be used also standalone.
    
    """    
    
    def __init__(self,output_file, mode,**kw):
        
        self.create_file(output_file, mode)
        
        if self.hf.attrs.get("qt-file",None) or self.hf.attrs.get("qkit",None):
            "File existed before and was created by qkit."
            self.setup_required_groups()
        else:
            "new file or none qkit file"
            self.set_base_attributes()
        
            # set all standard attributes
            for k in kw:
                self.grp.attrs[k] = kw[k]
        

        
    def create_file(self,output_file, mode):
        self.hf = h5py.File(output_file, mode)

    def set_base_attributes(self,nexus=True):
        "stores some attributes and creates the default data group"
        # store version of the file format
        #self.hf.attrs.create("qt-file","1.0") # qtlab file version
        self.hf.attrs.create("qkit", "1.0")  # qtlab version
        if nexus:
            # make the structure compatible with the nexus format
            # maybe some day the data can by analyzed by the software supporting nexus
            # first the entry group
            self.hf.attrs.create("NeXus_version","4.3.0")
            
            self.entry = self.hf.require_group("entry")
            self.entry.attrs.create("NX_class","NXentry")
            self.entry.attrs.create("data_latest",0)
            self.entry.attrs.create("analysis_latest",0)
            # create a nexus data group        
            self.dgrp = self.entry.require_group("data0")
            self.agrp = self.entry.require_group("analysis0")
            self.vgrp = self.entry.require_group("views")
            self.dgrp.attrs.create("NX_class","NXdata")
            self.dgrp.attrs.create("NX_class","NXdata")
        else:
            self.dgrp = self.create_require_group("data0")
            self.agrp = self.create_require_group("analysis0")
            self.vgrp = self.create_require_group("views")
    
    def setup_required_groups(self,nexus=True):
        if nexus:
            # make the structure compatible with the nexus format
            # maybe some day the data can by analyzed by the software supporting nexus
            # first the entry group
            self.entry = self.hf.require_group("entry")
            # create a nexus data group        
            self.dgrp = self.entry.require_group("data0")
            self.agrp = self.entry.require_group("analysis0")
            self.vgrp = self.entry.require_group("views")

        else:
            self.dgrp = self.require_group("data0")
            self.agrp = self.require_group("analysis0")
            self.vgrp = self.require_group("views")
        

    def create_dataset(self,name, tracelength, ds_type = ds_types['vector'],
                       folder = "data", dim = 1,  **kwargs):
        """ handles one, two and three dimensional data
        
            tracelength:
            
            dim:
                is 1 for a single data point in a 1D scan (array of scalars)
                is the length of the first trace in 2D scan (array of vectors)
            For 2D scans the traces have to have the same tracelength
            and are simply appended to the trace array
            
            'folder' is a optional group relative to the default group
            
            kwargs are appended as attributes to the dataset
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
            logging.ERROR("Create datasets: wrong number of dims.")
            


        if folder == "data":
            self.grp = self.dgrp
        elif folder == "analysis":
            self.grp = self.agrp
#           self.grp = self.grp.require_group(group)
        elif folder == "views":
            self.grp = self.vgrp

        else:
            logging.error("please specify either no folder, folder = 'data' , folder = 'analysis' or folder ='view' ")
            raise
            
        if name in self.grp.keys():
            logging.info("Item '%s' already exists in data set." % (name))
            #return False        
            
        
        # by default we create float datasets        
        dtype = kwargs.get('dtype','f')
        
        # we store text as unicode; this seems somewhat non-standard for hdf
        if ds_type == ds_types['txt']:
            dtype = h5py.special_dtype(vlen=unicode)
        

        #create the dataset ...;  delete it first if it exists, unless it is data
        if name in self.grp.keys(): 
            if folder == "data":
                logging.error("Dataset '%s' in 'data' already exists. Cannot overwrite datasets in 'data'!" % (name))
                raise ValueError
            else:
                del self.grp[name]
                # comment: The above line does remove the reference to the dataset but does not free the space aquired
                # fixme if possible ...
                
        ds = self.grp.create_dataset(name, shape, maxshape=maxshape, chunks = chunks, dtype=dtype)
        
        
        ds.attrs.create("name",name)
        ds.attrs.create("fill", [0,0,0])
        # add attibutes
        for a in kwargs:
             ds.attrs.create(a,kwargs[a])
             
        self.flush()
        return ds
        
    def append(self,ds,data, next_matrix=False):
        """ 
        Append method for hdf5 data. 
        A simple append method for data traces
        reshapes the array and updates the attributes
        """
        # it gets a little ugly with all the different user-cases here ...
        
        if len(ds.shape) == 1:      # 1 dim dataset: coordinate/vector/text
            fill = ds.attrs.get('fill')
            if self.ds_type == ds_types['txt']:     #text
                dim1 = ds.shape[0]+1
                ds.resize((dim1,))
                ds[dim1-1] = data
            elif len(data.shape) == 0:              # scalar
                dim1 = ds.shape[0]+1
                fill[0] += 1
                ds.resize((dim1,))
                ds[fill[0]-1] = data
            elif len(data.shape) == 1:              # list or np array
                if len(data) == 1:                  # single entry
                    dim1 = ds.shape[0]+1
                    fill[0] += 1
                    ds.resize((dim1,))
                    ds[fill[0]-1] = data
                else:                               # multiple entries                  
                    ds.resize((len(data),))
                    fill[0] += len(data)
                    ds[:] = data
            ds.attrs.modify("fill", fill)
        
        if len(ds.shape) == 2:  # 2 dim dataset: matrix
            fill = ds.attrs.get('fill')
            if len(data.shape) == 1 and data.shape[0] == 1:  # appending data as single points on a 2D dataset
                if next_matrix:
                    ds.resize((ds.shape[0] + 1, ds.shape[1]))
                    fill[0] += 1
                    fill[1] = 1
                else:
                    ds.resize((max(1, ds.shape[0]), max(fill[1] + 1, ds.shape[1])))
                    fill[1] += 1
                ds[fill[0], max(0, fill[1] - 1)] = data[0]
            else:  # appending data as vectors on a 2D dataset
                dim1 = ds.shape[0] + 1
                ds.resize((dim1, len(data)))
                fill[0] += 1
                fill[1] = len(data)
                ds[fill[0] - 1, :] = data
            ds.attrs.modify('fill', fill)


        if len(ds.shape) == 3:      # 3 dim dataset: box
            dim1 = max(1, ds.shape[0])
            dim2 = ds.shape[1]
            fill = ds.attrs.get('fill')
            if next_matrix:
                dim1 += 1
                fill[0] += 1
                fill[1] = 0
                ds.resize((dim1,dim2,len(data)))
            if dim1 == 1:
                fill[0] = 1
                dim2 += 1
                ds.resize((dim1,dim2,len(data)))
            fill[1] += 1
            ds.attrs.modify("fill", fill)
            ds[fill[0]-1,fill[1]-1] = data

        self.flush()
        
    def flush(self):
        self.hf.flush()
        
    def close_file(self):
        # delegate close 
        self.hf.close()
        
    def __getitem__(self,s):
        return self.hf[s]
