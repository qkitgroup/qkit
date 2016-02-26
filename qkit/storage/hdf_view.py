# -*- coding: utf-8 -*-
"""
Created 2015

@author: hrotzing
"""
import logging
from hdf_constants import ds_types
class dataset_view(object):

    """
    This class describes a view on one or two datasets.        
    
    """
    
    def __init__(self, hdf_file, name, x=None, y=None, x_axis=0, y_axis=0, filter = None,
                 label = "", ds_type =  ds_types['view'],
                 comment="", folder = 'views'):
        
        self.hf = hdf_file
        self.name = name
        self.folder = folder
        self.ds_url = "/entry/" + folder + "/" + name
        self.ds_type = ds_type
        self.comment = comment
        self.filter = filter
        if not x or not y: 
            logging.ERROR("View: Please supply a x and y dataset.")
        self.x_object = str(x.ds_url)
        self.y_object = str(y.ds_url)
        self.x_axis = x_axis
        self.y_axis = y_axis
        
        self.view_types = {'1D':0,'1D-V':1, '2D':2, '3D':3}
        self.ds = self.hf.create_dataset(self.name,0,folder=self.folder,dim=1)
        #print self.hf
        self.view_num = 0
        self._setup_metadata()
        self.hf.flush()

        
    def add(self,x, y, x_axis=0, y_axis=0, pyfilter = None, label=""):
            self.x_object = str(x.ds_url)
            self.y_object = str(y.ds_url)
            self.x_axis = x_axis
            self.y_axis = y_axis
            self.filter = pyfilter
            self._setup_metadata(init = False)
        
    def _setup_metadata(self,init=True):
        ds = self.ds
        if init:
            ds.attrs.create("view_type",self.view_types['1D-V'])
            ds.attrs.create('ds_type',self.ds_type)
        ds.attrs.create("xy_"+str(self.view_num),str(self.x_object)+":"+str(self.y_object))
        ds.attrs.create("xy_"+str(self.view_num)+"_axis",str(self.x_axis)+":"+str(self.y_axis))
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
        