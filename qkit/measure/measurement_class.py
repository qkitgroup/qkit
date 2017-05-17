 # MP, AS @ KIT 05/2017
# Class to collect all information about a single measurement

import time
import json
import logging
import os, copy, types
import numpy as np
from qkit.measure.samples_class import QkitJSONEncoder
               
class Measurement(object):
    '''
    Measurement Class to define general information about the specific measurement
    '''
    def __init__(self):
        self._experimentalist = 'fluxon'
        self._name = ''
        self._setup = ''
        self._uuid = int(time.time())
        self._hdf_filename = ''
        self._web_visible = True
        self._rating = 3
        self._analyzed = False
        self._measurement_type = ''
        self._measurement_func = ''
        self._x_axis = ''
        self._y_axis = ''
        self._z_axis = ''
        
    ####
    # GETTER / SETTER
    ####
        
    def get_experimentalist(self):
        return self._experimentalist
        
    def set_experimentalist(self, exp):
        self._experimentalist = exp

    def get_name(self):
        return self._name
        
    def set_name(self, name):
        self._name = name

    def get_setup(self):
        return self._setup
        
    def set_setup(self, setup):
        self._setup = setup
        
    def get_uuid(self):
        return self._uuid
        
    def set_uuid(self, uuid):
        self._uuid = uuid
        
    def get_hdf_filename(self):
        return self._hdf_filename
        
    def set_hdf_filename(self, hdf_filename):
        self._hdf_filename = hdf_filename
        
    def get_web_visible(self):
        return self._web_visible
        
    def set_web_visible(self, web_visible):
        self._web_visible = web_visible
        
    def get_rating(self):
        return self._rating
        
    def set_rating(self, rating):
        self._rating = rating
        
    def get_analyzed(self):
        return self._analyzed
        
    def set_analyzed(self, analyzed):
        self._analyzed = analyzed
        
    def get_measurement_type(self):
        return self._measurement_type
        
    def set_measurement_type(self, measurement_type):
        self._measurement_type = measurement_type
        
    def get_measurement_func(self):
        return self._measurement_func
        
    def set_measurement_func(self, measurement_func):
        self._measurement_func = measurement_func
        
    def get_x_axis(self):
        return self._x_axis
        
    def set_x_axis(self, x_axis):
        self._x_axis = x_axis
        
    def get_y_axis(self):
        return self._y_axis
        
    def set_y_axis(self, y_axis):
        self._y_axis = y_axis
        
    def get_z_axis(self):
        return self._z_axis
        
    def set_z_axis(self, z_axis):
        self._z_axis = z_axis        