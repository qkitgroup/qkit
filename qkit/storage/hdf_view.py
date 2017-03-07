# -*- coding: utf-8 -*-
"""
Created 2015

@author: hrotzing
"""
import logging
from hdf_constants import ds_types
import json
class dataset_view(object):

    """
    This class describes a view on one or two datasets.        
    
    """
    
    def __init__(self, hdf_file, name, x=None, y=None, error=None, filter = None,
                 ds_type =  ds_types['view'], folder = 'views', view_params={}):
        
        self.hf = hdf_file
        self.name = name
        self.folder = folder
        self.ds_url = "/entry/" + folder + "/" + name
        self.ds_type = ds_type
        self.filter = filter
        if not x or not y: 
            logging.ERROR("View: Please supply a x and y dataset.")
        self.x_object = str(x.ds_url)
        self.y_object = str(y.ds_url)
        self.error_object = None
        if error:
            self.error_object = str(error.ds_url)
        
        self.view_types =  {'1D':0,'1D-V':1, '2D':2, '3D':3, 'table':4, 'txt':5}
        self.ds = self.hf.create_dataset(self.name,0,folder=self.folder,dim=1)
        self.view_params = json.dumps(view_params)
        self.view_num = 0
        self._setup_metadata()
        self.hf.flush()

        
    def add(self,x=None, y=None, error=None, pyfilter = None):
            if x:
                self.x_object = str(x.ds_url)
            self.y_object = str(y.ds_url)
            self.error_object = None
            if error:
                self.error_object = str(error.ds_url)
            self.filter = pyfilter
            self._setup_metadata(init = False)
        
    def _setup_metadata(self,init=True):
        ds = self.ds
        if init:
            ds.attrs.create("view_type",self.view_types['1D-V'])
            ds.attrs.create('ds_type',self.ds_type)
            ds.attrs.create('view_params',self.view_params)
        ds.attrs.create("xy_"+str(self.view_num),str(self.x_object)+":"+str(self.y_object))
        if self.error_object:
            ds.attrs.create("xy_"+str(self.view_num)+"_error",str(self.error_object))
        ds.attrs.create("overlays",self.view_num)
        ds.attrs.create("xy_"+str(self.view_num)+"_filter",str(self.filter))

        self.view_num += 1
        
    def _exec_filter(self,view_num):
        # this is a somewhat dangerous function, since it allows to modify the 
        # hdf file while it is being updated by another program
        # as usual, power comes with responsibility...
    
        # prepare filter
        x_ds_url,y_ds_url = self.ds.attrs.get("xy_" + str(view_num)).split(':')
        print x_ds_url,y_ds_url
        
        locs = { 'x' : x_ds_url,
                  'y' : y_ds_url }
        head = "from qkit.config.environment import *\n"
        flt = head + self.filter
        
        try:
            exec(flt, globals(), locs)
            #exec(self.filter,locs)
        except SyntaxError,e:
            print "The filter code has to be proper python code!", e
        