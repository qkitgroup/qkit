# -*- coding: utf-8 -*-
"""
Created 2015

@author: hrotzing
"""


import logging
import numpy

class hdf_dataset(object):
        """
        This class represents the dataset in python.        
        
        this is also a helper class to postpone the creation of the datasets.
        The main issue here is that until the first data is aquired, 
        some dimensions and items are unknown.
        To keep the userinterface simple, we choose to postpone the creation 
        of the datasets and derive all the unknown values from the real data.
        """
        
        def __init__(self, hdf_file, name='', ds_url=None, x=None, y=None, z=None, unit= "" 
                ,comment="",folder = 'data', overwrite=False ,**meta):

            self.hf = hdf_file
            self.x_object = x
            self.y_object = y
            self.z_object = z
            if (name and ds_url) or (not name and not ds_url) :
                logging.ERROR("HDF_dataset: Please specify [only] one, 'name' or 'ds_url' ")
                raise NameError
            if name:
                # 1d/2d attributes
                self._new_ds_defaults(name,unit,folder=folder,comment=comment)
            elif ds_url:
                self._read_ds_from_hdf(ds_url)
        
        def _new_ds_defaults(self,name,unit,folder='data',comment=""):
            self.name = name
            self.folder = folder
            self.ds_url = "/entry/" + folder + "0/" + name
            self.unit = unit
            self.comment = comment
            # the first dataset is used to extract a few attributes
            self.first = True

            self.x_name = name
            self.x_unit = unit
            self.x0 = 0.0
            self.dx = 1.0
            
            self.y_name = ""
            self.y_unit = ""            
            self.y0 = 0.0
            self.dy = 1.0
            
            self.z_name = ""
            self.z_unit = ""            
            self.z0 = 0.0
            self.dz = 1.0
            # simple dimension check -- Fixme: too simple
            self.dim = 1
            if self.x_object:
                self.dim = 1    
            if self.y_object:
                self.dim = 2
            if self.z_object:
                self.dim = 3
                
        def _read_ds_from_hdf(self,ds_url):
            self.ds_url =  ds_url
            ds = self.hf[str(ds_url)]

            for attr in ds.attrs.keys():
                val = ds.attrs.get(attr)
                setattr(self,attr,val)
            
        def _setup_metadata(self):
            ds = self.ds
            ds.attrs.create('unit', self.unit)
            ds.attrs.create("comment",self.comment)
            # 2d/matrix 
            if self.x_object:
                ds.attrs.create("x0",self.x_object.x0)
                ds.attrs.create("dx",self.x_object.dx)
                ds.attrs.create("x_unit",self.x_object.x_unit)
                ds.attrs.create("x_name",self.x_object.x_name)
                ds.attrs.create("x_ds_url",self.x_object.ds_url)                
            else:
                ds.attrs.create("x0",self.x0)
                ds.attrs.create("dx",self.dx)
                ds.attrs.create("x_unit",self.x_unit)
                ds.attrs.create("x_name",self.x_name)
                ds.attrs.create("x_ds_url",self.ds_url)
            if self.y_object:
                ds.attrs.create("y0",self.y_object.x0)
                ds.attrs.create("dy",self.y_object.dx)
                ds.attrs.create("y_unit",self.y_object.x_unit)
                ds.attrs.create("y_name",self.y_object.x_name)
                ds.attrs.create("y_ds_url",self.y_object.ds_url) 
            if self.z_object:
                ds.attrs.create("z0",self.z_object.x0)
                ds.attrs.create("dz",self.z_object.dx)
                ds.attrs.create("z_unit",self.z_object.x_unit)
                ds.attrs.create("z_name",self.z_object.x_name)
                ds.attrs.create("z_ds_url",self.z_object.ds_url)


        def next_block(self):
            self.hf.next_block()
            
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
                self.ds = self.hf.create_dataset(self.name,tracelength,folder=self.folder,dim = self.dim)
                self._setup_metadata()
                
            if data is not None:
                # we cast everything to a float numpy array
                #data = numpy.array(data,dtype=float)
                self.hf.append(self.ds,data)
            self.hf.flush()
                
                
        def add(self,data):
            """
            The add method is used to save a 1-Dim vector to the hdf file once.
            For example, this can be a coordinate of a 1D scan.

            """
            # we cast everything to a float numpy array
            data = numpy.array(data,dtype=float)
            if self.y_object:
                logging.info("add is only for 1-Dim data. Please use append 2-Dim data.")
                return False
                
            if self.first:
                self.first = False
                #print self.name, data.shape
                tracelength = 0
                # create the dataset
                self.ds = self.hf.create_dataset(self.name,tracelength,folder=self.folder,dim = 1)

                if not self.x_object:
                    # value data
                    if len(data) > 2:                
                        self.x0 = data[0]
                        self.dx = data[1]-data[0]
                else:
                    # coordinate vector
                    self.x0 = self.x_object.x0
                    self.dx = self.x_object.dx
                self._setup_metadata()

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
            ret = "HDF5Data '%s'" % (self.name)
            return ret
