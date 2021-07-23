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
        self._M1_measurement_count = 128
        self._M1_sample_count = 256
        self._M1_active = True
        #These are not to be removed later
        self.measurement_settings = {"M1":{"sampling_rate" : self.M1_sampling_rate,
                               "measurement_count" : self.M1_measurement_count,
                               "sample_count" : self.M1_sample_count,
                               "data_nodes" : ["x", "y", "r"],
                               "unit" : "V",
                               "active" : self.M1_active
                               }}
        #These parts are to be removed later, they are for testing purposes only

        self.is_finished = True
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
        
    def arm(self):
        self.counter = 0
        self.is_finished = False
        
    def read(self): #Will be called repeatedly during the measurement, and shall only return the data the was captured since the last call of read
        sleep(0.05)
        a = {"M1" : {"x" : [], "y" : [], "r" : []}}
        for node in self.measurement_settings["M1"]["data_nodes"]:
            data = np.sin(np.linspace(0, np.pi, self.measurement_settings["M1"]["sample_count"]))
            noise1 = np.random.normal(0, 1, self.measurement_settings["M1"]["sample_count"])
            noise2 = np.random.normal(0, 1, self.measurement_settings["M1"]["sample_count"])
            a["M1"][node] = np.array([data + noise1, data + noise2])
        return a
    
    def finished(self):
        #sleep(0.1)
        self.counter += 1
        if self.counter >= self.measurement_settings["M1"]["measurement_count"] / 2: # since the read function always returns 2 timetraces
            self.counter = 0
            self.is_finished = True
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