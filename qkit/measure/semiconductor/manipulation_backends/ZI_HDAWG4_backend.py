# -*- coding: utf-8 -*-
"""
Created on Mon Sep 13 15:40:38 2021

@author: Thomas
"""

from MA_backend_base import MA_backend_base

class ZI_HDAWG4_backend(MA_backend_base):
    def __init__(self, instrument, wave_data):
        self.register_channel("Ch1")
        self.register_channel("Ch2")
        self.register_channel("Ch3")
        self.register_channel("Ch4")
        
        self.register_channel("Trig1")
        self.register_channel("Trig2")
        self.register_channel("Trig3")
        self.register_channel("Trig4")
        
        self.hartwig = instrument
        
        self.wave_data = wave_data
    
    def get_sample_rate(self):
        rate = self.hartwig.get_sampling_clock()
        return rate
    
    def run(self):
        self.hartwig.start_playback()

    def stop(self):
        self.hartwig.stop_playback()
        
    def load_waveform(self):
        self.hartwig.zdict_to_CSV(self.wave_data)
        self.hartwig.zcreate_sequence_program(0)
        self.hartwig.upload_to_device()
    