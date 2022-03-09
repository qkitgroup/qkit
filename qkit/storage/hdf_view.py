# -*- coding: utf-8 -*-
"""
Created 2015

@author: hrotzing
"""
import qkit
from qkit.storage.hdf_constants import ds_types, view_types
import json
from qkit.core.lib.misc import str3
class dataset_view(object):
    """This class describes a view on one or two datasets.        
    
    Views do not contain any data but only ds_url information about the datasets
    that should  be displayed. The attributes 'overlays' and 'xy_i' hold the 
    information about how many plots are created over one another and which
    datasets are plotted against each other.
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
            raise ValueError(__name__ + ": Error creating view '{!s}' in file {!s}: x or y axis not given.".format(name, hdf_file.hf.attrs['_filepath']))
        self.x_object = str3(x.ds_url)
        self.y_object = str3(y.ds_url)
        self.error_object = None
        if error:
            self.error_object = str3(error.ds_url)
        
        self.ds = self.hf.create_dataset(self.name,0,folder=self.folder,dim=1)
        self.view_params = json.dumps(view_params)
        self.view_num = 0
        self._setup_metadata()
        self.hf.flush()

        
    def add(self,x=None, y=None, error=None, pyfilter = None):
        """Adds one y vs x overlay plot to the dataset_view object.        
    
        Args:
            x, y, error: hdf_datasets; y over x gets plotted with error being 
                the y-error data.
        """
        if x:
            self.x_object = str3(x.ds_url)
        self.y_object = str3(y.ds_url)
        self.error_object = None
        if error:
            self.error_object = str3(error.ds_url)
        self.filter = pyfilter
        self._setup_metadata(init = False)
        
    def _setup_metadata(self,init=True):
        ds = self.ds
        if init:
            ds.attrs.create("view_type",view_types['1D-V'])
            ds.attrs.create('ds_type',self.ds_type)
            ds.attrs.create('view_params',self.view_params.encode())
        ds.attrs.create("xy_"+str(self.view_num),(str(self.x_object)+":"+str(self.y_object)).encode())
        if self.error_object:
            ds.attrs.create("xy_"+str(self.view_num)+"_error",str(self.error_object).encode())
        ds.attrs.create("overlays",self.view_num)
        ds.attrs.create("xy_"+str(self.view_num)+"_filter",str(self.filter).encode())

        self.view_num += 1
        
    def _exec_filter(self,view_num):
        """
        FIXME: this does not work!
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
        except SyntaxError as e:
            print("The filter code has to be proper python code! %s "% e)
        """
        pass
