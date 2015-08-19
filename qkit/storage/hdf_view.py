# -*- coding: utf-8 -*-
"""
Created 2015

@author: hrotzing
"""
import logging

class dataset_view(object):

    """
    This class describes a view on one or two datasets.        
    
    """
    
    def __init__(self, hdf_file, name, x=None, y=None, x_axis=0, y_axis=0, filter = None ,comment="",folder = 'views'):
        
        self.hf = hdf_file
        self.name = name
        self.folder = folder
        self.ds_url = "/entry/" + folder + "/" + name
        self.comment = comment
        self.filter = filter
        if not x or not y: 
            logging.ERROR("View: Please supply a x and y dataset.")
        self.x_object = str(x.ds_url)
        self.y_object = str(y.ds_url)
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.view_types = {'1D':0,'1D-V':1, '2D':2, '3D':3}
        self.ds = self.hf.create_dataset(self.name,0,folder=self.folder)
        print self.hf
        self.view_num = 0
        self._setup_metadata()
        self.hf.flush()

        
    def add(self,x, y, x_axis=0, y_axis=0,filter = None):
            self.x_object = str(x.ds_url)
            self.y_object = str(y.ds_url)
            self.x_axis = x_axis
            self.y_axis = y_axis
            self.filter = filter
            self._setup_metadata(init = False)
        
    def _setup_metadata(self,init=True):
        ds = self.ds
        if init:
            ds.attrs.create("view_type",self.view_types['1D-V'])
        ds.attrs.create("xy_"+str(self.view_num),str(self.x_object)+":"+str(self.y_object))
        ds.attrs.create("xy_"+str(self.view_num)+"_axis",str(self.x_axis)+":"+str(self.y_axis))
        ds.attrs.create("overlays",self.view_num)
        ds.attrs.create("xy_"+str(self.view_num)+"_filter",str(self.filter))
        self.view_num += 1
