#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 14 18:38:42 2021

@author: lr1740
"""
from time import sleep
import numpy as np

class RO_backend:
    def __init__(self):
        #These parts are to be removed later, they are for testing purposes only
        self._M1_sampling_rate = 2e9
        self._M1_measurement_count = 256
        self._M1_sample_count = 5
        self._M1_averages = 1000
        self._M1_active = True
        #These are not to be removed later
        self.measurement_settings = {"M1":{"sampling_rate" : self.M1_sampling_rate,
                               "measurement_count" : self.M1_measurement_count,
                               "sample_count" : self.M1_sample_count,
                               "averages" : self.M1_averages,
                               "data_nodes" : ["x", "y", "r"],
                               "unit" : "V",
                               "active" : self.M1_active
                               },
                                    "M2":{"sampling_rate" : self.M1_sampling_rate,
                               "measurement_count" : 3,
                               "sample_count" : 1,
                               "averages" : 3,
                               "data_nodes" : ["a", "b", "c"],
                               "unit" : "V",
                               "active" : False
                               }}
        self._create_data_structure()
        #These parts are to be removed later, they are for testing purposes only
        self.is_finished = True
        self.max_counter = 0
        self.counter = 0
    
    @property
    def M1_sampling_rate(self):
        return self._M1_sampling_rate
    @M1_sampling_rate.setter
    def M1_sampling_rate(self, value):
        if type(value) != int:
            raise TypeError("Number of measurements must be an interger number.")
        if value not in self._range_meas_num:
            raise ValueError("Number of Measurements cannot be set, it is outside the instrument range.")
        self._M1_sampling_rate = value
    
    @property
    def M1_measurement_count(self):
        return self._M1_measurement_count   
    @M1_measurement_count.setter
    def M1_measurement_count(self, value):
        if type(value) != int:
            raise TypeError("Number of measurements must be an interger number.")
        if value not in self._range_meas_num:
            raise ValueError("Number of Measurements cannot be set, it is outside the instrument range.")
        self._M1_measurement_count = value
    
    @property
    def M1_sample_count(self):
        return self._M1_sample_count    
    @M1_sample_count.setter
    def M1_sample_count(self, value):
        if type(value) != int:
            raise TypeError("Number of samples must be an interger number.")
        if value not in self._range_meas_num:
            raise ValueError("Number of samples cannot be set, it is outside the instrument range.")
        self._M1_sample_count = value
    
    @property
    def M1_active(self):
        return self._M1_active
    @M1_active.setter
    def M1_active(self, value):
        if type(value) != int:
            raise TypeError("Number of averages must be an interger number.")
        if value not in self._range_avg_num:
            raise ValueError("Number of averages cannot be set, it is outside the instrument range.")
        self._M1_active = value
    
    @property
    def M1_averages(self):
        return self._M1_averages
    @M1_averages.setter
    def M1_averages(self, value):
        if type(value) != int:
            raise TypeError("Number of measurements must be an interger number.")
        if value not in self._range_meas_num:
            raise ValueError("Number of Measurements cannot be set, it is outside the instrument range.")
        self._M1_averages = value

    
    def _active_measurements(self, func):
        for measurement in self.measurement_settings.keys():
            if self.measurement_settings[measurement]["active"]:
                func(measurement)
                
    def _active_measurement_nodes(self, func):
        for measurement in self.measurement_settings.keys():
            if self.measurement_settings[measurement]["active"]:
                for node in self.measurement_settings[measurement]["data_nodes"]:
                    func(measurement, node)
    
    def _create_data_structure(self):
        datastructure = {}
        @self._active_measurements
        def create_tree(measurement):
            a = {}
            for node in self.measurement_settings[measurement]["data_nodes"]:
# =============================================================================
#                 empty_arr = np.empty(self.measurement_settings[measurement]["averages"],
#                                      self.measurement_settings[measurement]["measurement_count"],
#                                      self.measurement_settings[measurement]["sample_count"])
#                 empty_arr.fill(np.NaN)
# =============================================================================
                a.update({node : np.NaN})
            datastructure.update({measurement : a})
        return datastructure
    
    def arm(self):
        avgs = []
        @self._active_measurements
        def find_stop(measurement):
            nonlocal avgs
            avgs.append(self.measurement_settings[measurement]["averages"])
        self.max_counter = max(avgs)
        self.counter = 0
        self.is_finished = False
        
    def read(self): #Will be called repeatedly during the measurement, and shall only return the data the was captured since the last call of read
        #sleep(0.05)
        arr = None
        data = self._create_data_structure()
        @self._active_measurement_nodes
        def get_data(measurement, node):
            nonlocal arr, data
            arr = np.empty((1,
                            self.measurement_settings[measurement]["measurement_count"],
                            self.measurement_settings[measurement]["sample_count"]))
            for iterator in range(len(arr[0][1])):
                meas = np.sin(np.linspace(0, np.pi, self.measurement_settings[measurement]["measurement_count"]))
                noise1 = np.random.normal(0, 5, self.measurement_settings[measurement]["measurement_count"])
                arr[0, :, iterator] = meas + noise1
            data[measurement][node] = arr
        return data
    
    def finished(self):
        if self.counter == self.max_counter - 1: #since the first call is outside the main loop
            self.counter = 0
            self.is_finished = True
        self.counter += 1
        return self.is_finished
    
    def stop(self):
        self.counter = 0
        self.is_finished = True
        
if __name__ == "__main__":
    print("Hellol")
    test_backend = RO_backend()
    
    while not test_backend.finished():
        print("I run even though I don't run?")
        
    test_backend.arm()
    
    while not test_backend.finished():
        print("Running all day")
    print(test_backend.data)
    print(test_backend.read())