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

        #These are not to be removed later
        self.measurement_settings = {"M1":{"sampling_rate" : 1.3e6,
                               "measurement_count" : 256,
                               "sample_count" : 3,
                               "averages" : 30,
                               "data_nodes" : ["x", "y", "r"],
                               "unit" : "V",
                               "active" : True
                               },
                                    "M2":{"sampling_rate" : 1.4e6,
                               "measurement_count" : 256,
                               "sample_count" : 3,
                               "averages" : 31,
                               "data_nodes" : ["a", "b", "c"],
                               "unit" : "V",
                               "active" : True
                               },
                                    "M3":{"sampling_rate" : 1.4e6,
                               "measurement_count" : 256,
                               "sample_count" : 3,
                               "averages" : 31,
                               "data_nodes" : ["hubbi"],
                               "unit" : "V",
                               "active" : True
                               }
                                }
        #These parts are to be removed later, they are for testing purposes only
        self.is_finished = True
        self.max_counter = {}
        self.counter = {}
        self.return_length = {}
    
    def arm(self):
        self.all_done = 0
        for measurement in self.measurement_settings.keys():
            if self.measurement_settings[measurement]["active"]:
                self.all_done += 1
            #self.measurement_settings[measurement]["active"] = True
            self.max_counter[measurement] = self.measurement_settings[measurement]["averages"]
            #print(type(self.counter))
            self.counter[measurement] = 0
        
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
            if self.measurement_settings[measurement]["active"] and self.counter[measurement] < self.measurement_settings[measurement]["averages"]:
                self._roll_dice()
                data[measurement] = {}
                if self.counter[measurement] + self._return_length > self.measurement_settings[measurement]["averages"]:
                    self._return_length = self.measurement_settings[measurement]["averages"] - self.counter[measurement]
                self.counter[measurement] += self._return_length
                
                arr = np.empty((self._return_length, 
                               self.measurement_settings[measurement]["measurement_count"],
                               self.measurement_settings[measurement]["sample_count"]))
                for node in self.measurement_settings[measurement]["data_nodes"]:
                    for avg in range(self._return_length):
                        for i in range(self.measurement_settings[measurement]["sample_count"]):
                                sine = np.sin(np.linspace(0, np.pi, self.measurement_settings[measurement]["measurement_count"]))
                                noise = np.random.normal(0, 5, self.measurement_settings[measurement]["measurement_count"])
                                arr[avg, :, i] = sine + noise                    
                    data[measurement][node] = arr         
        return data
        
    def finished(self):
        done = 0
        for measurement in self.measurement_settings.keys():
            if self.counter[measurement] >= self.max_counter[measurement]:                
                done += 1
        if done == self.all_done:
            self.all_done = 0
            self.is_finished = True
        return self.is_finished
    
    def stop(self):
        self.all_done = 0
        self.is_finished = True
        for measurement in self.measurement_settings.keys():
            self.counter[measurement] = 0
        
if __name__ == "__main__":
    test_backend = RO_backend()
    
    #while not test_backend.finished():
    #    print("I run even though I don't run?")
        
    test_backend.arm()
    i = 0
    while not test_backend.finished():
        a = test_backend.read()
        i += 1
        #print(i)
    #print(a.keys())
   # for key in a.keys():
        #print(key, a[key].keys())
    #print(test_backend.read())
