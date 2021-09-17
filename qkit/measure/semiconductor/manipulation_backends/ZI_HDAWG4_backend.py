# -*- coding: utf-8 -*-
"""
Created on Mon Sep 13 15:40:38 2021

@author: Thomas
"""

from MA_backend_base import MA_backend_base

class ZI_HDAWG4_backend(MA_backend_base):
    def __init__(self, instrument):
        self.register_channel("Ch1", "V")
        self.register_channel("Ch2", "V")
        self.register_channel("Ch3", "V")
        self.register_channel("Ch4", "V")
        
        self.register_channel("Trig1", "V")
        self.register_channel("Trig2", "V")
        self.register_channel("Trig3", "V")
        self.register_channel("Trig4", "V")
        
        self.hartwig = instrument
        
    def Ch1_get_sample_rate(self):
        rate = self.hartwig.get_sampling_clock()*1e-9
        return rate
    
    def Ch2_get_sample_rate(self):
        rate = self.hartwig.get_sampling_clock()*1e-9
        return rate
    
    def Ch3_get_sample_rate(self):
        rate = self.hartwig.get_sampling_clock()*1e-9
        return rate
    
    def Ch4_get_sample_rate(self):
        rate = self.hartwig.get_sampling_clock()*1e-9
        return rate
    
    def Trig1_get_sample_rate(self):
        rate = self.hartwig.get_sampling_clock()*1e-9
        return rate

    def Trig2_get_sample_rate(self):
        rate = self.hartwig.get_sampling_clock()*1e-9
        return rate

    def Trig3_get_sample_rate(self):
        rate = self.hartwig.get_sampling_clock()*1e-9
        return rate

    def Trig4_get_sample_rate(self):
        rate = self.hartwig.get_sampling_clock()*1e-9
        return rate
    
    
    def run(self):
        self.hartwig.start_playback()

    def stop(self):
        self.hartwig.stop_playback()
        
    def load_waveform(self, wave_data):
        self.hartwig.zdict_to_CSV(wave_data)
        self.hartwig.zcreate_sequence_program(0)
        self.hartwig.upload_to_device()
        
        