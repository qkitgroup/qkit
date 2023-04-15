# -*- coding: utf-8 -*-
"""
Created on Tue Apr 11 17:11:47 2023

@author: Thomas Koch
"""
import time
from qkit.measure.semiconductor.manipulation_backends.MA_backend_base import MA_backend_base

class Moku_Pro_backend(MA_backend_base):
    def __init__(self, instrument):
        self.register_channel("Ch1", "V")
        self.register_channel("Ch2", "V")
        self.register_channel("Ch3", "V")
        self.register_channel("Ch4", "V")
        
        self.register_channel("Trig1", "V")
        self.register_channel("Trig2", "V")
        self.register_channel("Trig3", "V")
        self.register_channel("Trig4", "V")
        
        self.moku = instrument
        
    def Ch1_get_sample_rate(self):
        rate = self.moku.get_sampling_rate()*1e-9
        return rate
    
    def Ch2_get_sample_rate(self):
        rate = self.moku.get_sampling_rate()*1e-9
        return rate
    
    def Ch3_get_sample_rate(self):
        rate = self.moku.get_sampling_rate()*1e-9
        return rate
    
    def Ch4_get_sample_rate(self):
        rate = self.moku.get_sampling_rate()*1e-9
        return rate
    
    def Trig1_get_sample_rate(self):
        rate = self.moku.get_sampling_rate()*1e-9
        return rate

    def Trig2_get_sample_rate(self):
        rate = self.moku.get_sampling_rate()*1e-9
        return rate

    def Trig3_get_sample_rate(self):
        rate = self.moku.get_sampling_rate()*1e-9
        return rate

    def Trig4_get_sample_rate(self):
        rate = self.moku.get_sampling_rate()*1e-9
        return rate

    def run(self):
        self.bill.start_triggered_readout()

    def stop(self):
        self.bill.stop_triggered_readout()
        
    def load_waveform(self, wave_data):
        self.moku.configure_outputs(wave_data, triggered = True)

    
    def decode_qupulse(self, pulse_obj, parameters):
        self.moku._seq_prog = pulse_obj.create_program(parameters = parameters)
        self.moku._frequency = 1/(int(self._seq_prog.duration)/1e9)