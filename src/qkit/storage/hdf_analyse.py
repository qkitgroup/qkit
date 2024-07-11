# -*- coding: utf-8 -*-

import qkit
from qkit.storage.hdf_constants import ds_types
from qkit.core.lib.misc import str3
class dataset_analysis(object):
    """This class describes a specific data analysis plots,
    like polar plot and hystogramms.        
    
    Analysis do not contain any data but only ds_url information about the datasets
    that should  be displayed. The attributes 'ds_type' and 'xyz' hold the 
    information about what type of plots are created and which
    datasets are plotted against each other.
    """

    def __init__(self, hdf_file, name, x=None, y=None, z=None,
                 ds_type =  ds_types['analysis'], folder = 'analysis'):

        self.hf = hdf_file
        self.name = name
        self.folder = folder
        self.ds_url = "/entry/" + folder + "/" + name
        self.ds_type = ds_type
        self.filter = filter

        if ds_type != ds_types['analysis']:
            raise TypeError(__name__ + ": Dataset contains wrong ds_type")

        if not x or not y or not z:
            raise ValueError(__name__ + ": Error creating view '{!s}' in file {!s}: x or y axis not given.".format(name, hdf_file.hf.attrs['_filepath']))
        self.x_object = str3(x.ds_url)
        self.y_object = str3(y.ds_url)
        self.z_object = str3(z.ds_url)

        self.ds = self.hf.create_dataset(self.name,0,folder=self.folder,dim=1)
        self._setup_metadata()
        self.hf.flush()

    def _setup_metadata(self,init=True):
        ds = self.ds
        if init:
            ds.attrs.create('ds_type',self.ds_type)
        ds.attrs.create("xyz",(str(self.x_object)+":"+str(self.y_object)+":"+str(self.z_object)).encode())
        ds.attrs.create("step_var",str(self.x_object))
        ds.attrs.create("sweep_var",str(self.y_object))