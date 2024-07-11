# -*- coding: utf-8 -*-

import qkit
import json

class dataset_config(object):
    """This class describes a specific data analysis plots,
    like polar plot and hystogramms.        
    
    Analysis do not contain any data but only ds_url information about the datasets
    that should  be displayed. The attributes 'ds_type' and 'xyz' hold the 
    information about what type of plots are created and which
    datasets are plotted against each other.
    """

    def __init__(self, hdf_file, name, folder = 'data', **cfg):
        ''' init config dataset'''
        self.hf = hdf_file
        self.name = name
        self.folder = folder
        self.ds_url = "/entry/" + folder + "/" + name

        self.ds = self.hf.create_dataset(self.name,0,folder=self.folder,dim=1)
        # self._setup_metadata(**cfg)
        self.hf.flush()

    def add(self,name,value):
        ''' add attribute to config dataset'''
        self.ds.attrs.create(name,json.dumps(value))
        self.hf.flush()