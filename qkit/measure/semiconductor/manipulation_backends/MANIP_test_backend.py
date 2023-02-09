#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 14 18:42:00 2021

@author: lr1740
"""
from qkit.measure.semiconductor.manipulation_backends.MA_backend_base import MA_backend_base

class MA_test_backend(MA_backend_base):
    def __init__(self):
        self.machine_settings = {"Ch1" : {"sample_rate" : 1},
                                 "Ch2" : {"sample_rate" : 2.4}}
        self.register_channel("Ch1", "V")
        self.register_channel("Ch2", "V")
        
    def Ch1_get_sample_rate(self):
        print("Getting Ch1 sampling rate")
        return self.machine_settings["Ch1"]["sample_rate"]
    
    def Ch2_get_sample_rate(self):
        print("Getting Ch2 sampling rate")
        return self.machine_settings["Ch2"]["sample_rate"]
    
    def load_waveform(self, waves):
        print(f"Setting waveforms to {waves}")

    def stop(self):
        pass
    
    def run(self):
        pass
