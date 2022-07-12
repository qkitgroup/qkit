#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 14 18:38:42 2021

@author: lr1740
"""
from qkit.measure.semiconductor.readout_backends.RO_backend_base import RO_backend_base
from time import sleep
from random import random
import numpy as np

class RO_backend(RO_backend_base):
    def __init__(self):
        super().__init__()
        #This dictionary acts as if it was the machine
        self.measurement_settings = {"M4":{"sampling_rate" : 10e9,
                               "measurement_count" : 256,
                               "sample_count" : 3,
                               "averages" : 30,
                               "data_nodes" : ["a", "b", "c"],
                               "unit" : "V",
                               "active" : True
                               },
                                    "M1":{"sampling_rate" : 10e9,
                               "measurement_count" : 256,
                               "sample_count" : 3,
                               "averages" : 30,
                               "data_nodes" : ["x", "y", "z"],
                               "unit" : "V",
                               "active" : True
                               },
                                    "M2":{"sampling_rate" : 10e9,
                               "measurement_count" : 256,
                               "sample_count" : 3,
                               "averages" : 30,
                               "data_nodes" : ["d", "e", "f"],
                               "unit" : "V",
                               "active" : True}
                                }
    
        
    #These parts are to be removed later, they are for testing purposes only
        self.is_finished = True
        self.max_counter = {}
        self.counter = {}
        self.return_length = {}
        self.register_measurement("M4", "V", ["a", "b", "c"])
        self.register_measurement("M1", "V", ["x", "y", "z"])
        self.register_measurement("M2", "V", ["d", "e", "f"])
    
    def M4_get_sample_rate(self):
        rate = self.measurement_settings["M4"]["sampling_rate"]
        print(f"M4 sampling rate: {rate}")
        return rate    
    def M4_set_measurement_count(self, new_meas):
        print(f"Setting M4 measurement_count to {new_meas}")
        self.measurement_settings["M4"]["measurement_count"] = new_meas
    def M4_set_sample_count(self, new_samp):
        print(f"Setting M4 sample_count to {new_samp}")
        self.measurement_settings["M4"]["sample_count"] = new_samp
    def M4_set_averages(self, new_avgs):
        print(f"Setting M4 averages to {new_avgs}")
        self.measurement_settings["M4"]["averages"] = new_avgs
    def M4_activate(self):
        print("Measurement M4 activated")
        self.measurement_settings["M4"]["active"] = True
    def M4_deactivate(self):
        print("Measurement M4 deactivated")
        self.measurement_settings["M4"]["active"] = False
        
    def M1_get_sample_rate(self):
        rate = self.measurement_settings["M1"]["sampling_rate"]
        print(f"M1 sampling rate: {rate}")
        return rate    
    def M1_set_measurement_count(self, new_meas):
        print(f"Setting M1 measurement_count to {new_meas}")
        self.measurement_settings["M1"]["measurement_count"] = new_meas
    def M1_set_sample_count(self, new_samp):
        print(f"Setting M1 sample_count to {new_samp}")
        self.measurement_settings["M1"]["sample_count"] = new_samp
    def M1_set_averages(self, new_avgs):
        print(f"Setting M1 averages to {new_avgs}")
        self.measurement_settings["M1"]["averages"] = new_avgs
    def M1_activate(self):
        print("Measurement M1 activated")
        self.measurement_settings["M1"]["active"] = True
    def M1_deactivate(self):
        print("Measurement M1 deactivated")
        self.measurement_settings["M1"]["active"] = False
    
    def M2_get_sample_rate(self):
        rate = self.measurement_settings["M2"]["sampling_rate"]
        print(f"M2 sampling rate: {rate}")
        return rate    
    def M2_set_measurement_count(self, new_meas):
        print(f"Setting M2 measurement_count to {new_meas}")
        self.measurement_settings["M2"]["measurement_count"] = new_meas
    def M2_set_sample_count(self, new_samp):
        print(f"Setting M2 sample_count to {new_samp}")
        self.measurement_settings["M2"]["sample_count"] = new_samp
    def M2_set_averages(self, new_avgs):
        print(f"Setting M2 averages to {new_avgs}")
        self.measurement_settings["M2"]["averages"] = new_avgs
    def M2_activate(self):
        print("Measurement M2 activated")
        self.measurement_settings["M2"]["active"] = True
    def M2_deactivate(self):
        print("Measurement M2 deactivated")
        self.measurement_settings["M2"]["active"] = False
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
                
                for node in self.measurement_settings[measurement]["data_nodes"]:
                    arr = np.empty((self._return_length, 
                                   self.measurement_settings[measurement]["measurement_count"],
                                   self.measurement_settings[measurement]["sample_count"]))
                    for avg in range(self._return_length):
                        for i in range(self.measurement_settings[measurement]["sample_count"]):
                                cosine = np.cos(np.linspace(0, np.pi, self.measurement_settings[measurement]["measurement_count"]))
                                noise = np.random.normal(0, 5, self.measurement_settings[measurement]["measurement_count"])
                                arr[avg, :, i] = cosine + noise                    
                    data[measurement][node] = arr
        return data
        
    def finished(self):
        done = 0
        for measurement in self.measurement_settings.keys():
            if self.counter[measurement] >= self.max_counter[measurement]:                
                done += 1
        if done == self.all_done:
            self.all_done = 0
            print("Readout backend here, all done!")
            self.is_finished = True
        return self.is_finished
    
    def stop(self):
        self.all_done = 0
        self.is_finished = True
        for measurement in self.measurement_settings.keys():
            self.counter[measurement] = 0
        
if __name__ == "__main__":
    test_backend = RO_backend()
    print(issubclass(test_backend.__class__, RO_backend_base))
    #while not test_backend.finished():
    #    print("I run even though I don't run?")
        
    test_backend.arm()
    i = 0
    while not test_backend.finished():
        a = test_backend.read()
        i += 1
        print(i)
    print(a.keys())
    for key in a.keys():
        print(key, a[key].keys())
    print(a)
    print(test_backend.read())
