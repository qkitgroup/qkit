#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 14 18:38:42 2021

@author: lr1740
"""
from time import sleep
from random import random
import numpy as np

class RO_backend:
    def __init__(self):
        #These parts are to be removed later, they are for testing purposes only
        self._M1_sampling_rate = 2e9
        self._M1_measurement_count = 256
        self._M1_sample_count = 1
        self._M1_averages = 6
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
        self._M1_sampling_rate = value
    
    @property
    def M1_measurement_count(self):
        return self._M1_measurement_count   
    @M1_measurement_count.setter
    def M1_measurement_count(self, value):
        if type(value) != int:
            raise TypeError("Number of measurements must be an interger number.")
        self._M1_measurement_count = value
    
    @property
    def M1_sample_count(self):
        return self._M1_sample_count    
    @M1_sample_count.setter
    def M1_sample_count(self, value):
        if type(value) != int:
            raise TypeError("Number of samples must be an interger number.")
        self._M1_sample_count = value
    
    @property
    def M1_active(self):
        return self._M1_active
    @M1_active.setter
    def M1_active(self, value):
        if type(value) != bool:
            raise TypeError("Measurement activity must be a bool.")
        self._M1_active = value
    
    @property
    def M1_averages(self):
        return self._M1_averages
    @M1_averages.setter
    def M1_averages(self, value):
        if type(value) != int:
            raise TypeError("Number of measurements must be an interger number.")
        self._M1_averages = value
    
    def arm(self):
        avgs = []
        for measurement in self.measurement_settings.keys():
            if self.measurement_settings[measurement]["active"]:
                avgs.append(self.measurement_settings[measurement]["averages"])
        
        self.max_counter = sum(avgs)
        self.counter = 0
        self.is_finished = False
    
    def _roll_dice(self):
        choice = random()
        if choice <= 0.33:
            self._return_length = 1
        elif 0.33 < choice <= 0.66: 
            self._return_length = 2
        else:
            self._return_length = 3
    
    def read(self): #Will be called repeatedly during the measurement, and shall only return the data the was captured since the last call of read
        #sleep(0.05)
        data = {}
        for measurement in self.measurement_settings.keys():
            if self.measurement_settings[measurement]["active"]:
                self._roll_dice()
                print("_return_length: ", self._return_length)
                print("coutner: ", self.counter)
                if self.counter + self._return_length > self.max_counter:
                    self._return_length = self.max_counter - self.counter
                self.counter += self._return_length
                data[measurement] = {}
                arr = np.empty((self._return_length, 
                                self.measurement_settings[measurement]["measurement_count"], 
                                self.measurement_settings[measurement]["sample_count"]))                
                
                for node in self.measurement_settings[measurement]["data_nodes"]:                    
                    for avgs in range(len(arr)):
                        for iterator in range(len(arr[0][1])):
                            meas = np.sin(np.linspace(0, np.pi, self.measurement_settings[measurement]["measurement_count"]))
                            noise1 = np.random.normal(0, 5, self.measurement_settings[measurement]["measurement_count"])
                            arr[avgs, :, iterator] = meas + noise1                
                    data[measurement][node] = arr        
        return data

    
    def finished(self):
        if self.counter >= self.max_counter: 
            self.counter = 0
            self.is_finished = True
        
        return self.is_finished
    
    def stop(self):        
        self.is_finished = True
        self.counter = 0
        
if __name__ == "__main__":
    print("Hellol")
    test_backend = RO_backend()
    
    while not test_backend.finished():
        print("I run even though I don't run?")
        
    test_backend.arm()
    print(test_backend.max_counter)
    
    while not test_backend.finished():
        test_backend.read()
        print(test_backend.counter)
    print(test_backend.read())
