# -*- coding: utf-8 -*-
"""
Created Sep 2022

@author: Thomas and Daniel
"""
import time
from qkit.measure.semiconductor.manipulation_backends.MA_backend_base import MA_backend_base

class ZI_HDAWG4_ADwin_Pro2_backend_waveform(MA_backend_base):
    def __init__(self, HDAWG4, ADwinPro2):
        self.register_channel("Ch1", "V")
        self.register_channel("Ch2", "V")
        self.register_channel("Ch3", "V")
        self.register_channel("Ch4", "V")
        
        self.register_channel("Trig1", "V")
        self.register_channel("Trig2", "V")
        self.register_channel("Trig3", "V")
        self.register_channel("Trig4", "V")
        
        self.hartwig = HDAWG4
        self.bill = ADwinPro2
        
    def Ch1_get_sample_rate(self):
        rate = self.hartwig.get_sampling_rate()*1e-9
        return rate
    
    def Ch2_get_sample_rate(self):
        rate = self.hartwig.get_sampling_rate()*1e-9
        return rate
    
    def Ch3_get_sample_rate(self):
        rate = self.hartwig.get_sampling_rate()*1e-9
        return rate
    
    def Ch4_get_sample_rate(self):
        rate = self.hartwig.get_sampling_rate()*1e-9
        return rate
    
    def Trig1_get_sample_rate(self):
        rate = self.hartwig.get_sampling_rate()*1e-9
        return rate

    def Trig2_get_sample_rate(self):
        rate = self.hartwig.get_sampling_rate()*1e-9
        return rate

    def Trig3_get_sample_rate(self):
        rate = self.hartwig.get_sampling_rate()*1e-9
        return rate

    def Trig4_get_sample_rate(self):
        rate = self.hartwig.get_sampling_rate()*1e-9
        return rate

    def run(self):
        self.hartwig.start_playback()
        time.sleep(1)
        self.bill.start_triggered_readout()

    def stop(self):
        self.bill.stop_triggered_readout()
        self.hartwig.stop_playback()
        
    def load_waveform(self, wave_data):
        self.hartwig.external_trigger = True

        # Assign the array (the first item of the 'samples' list) directly to the outer key
        wave_dict = {}
        for key, value in wave_data.items():
            wave_dict[key] = value['samples'][0]

        # Assign channels for the first core
        awg_core = 0
        channels_core0 = {"Ch1", "Ch2", "Trig1", "Trig2"}
        dict_core0 = {k: wave_dict.get(k) for k in channels_core0 if k in wave_dict}

        if dict_core0:
            # Upload waveform to to the first core
            self.hartwig.upload_waveform(awg_core, dict_core0)
        else:
            print("No waveform provided for the first core.")

        # Assign channels for the second core
        awg_core = 1
        channels_core1 = {"Ch3", "Ch4", "Trig3", "Trig4"}
        dict_core1 = {k: wave_dict.get(k) for k in channels_core1 if k in wave_dict}

        if dict_core1:
            # Assign new key arguments for the second core
            if "Ch3" in dict_core1.keys():
                dict_core1["Ch1"] = dict_core1.pop('Ch3')
            if "Ch4" in dict_core1.keys():
                dict_core1["Ch2"] = dict_core1.pop('Ch4')
            if "Trig3" in dict_core1.keys():
                dict_core1["Trig1"] = dict_core1.pop('Trig3')
            if "Trig4" in dict_core1.keys():
                dict_core1["Trig2"] = dict_core1.pop('Trig4')
            # Upload waveform to the second core
            self.hartwig.upload_waveform(awg_core, dict_core1)
        else:
            print("No waveform provided for the second core.")