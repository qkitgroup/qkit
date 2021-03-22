#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 15 12:17:39 2021

@author: lr1740
"""
from _ZI_toolkit import daq_module_toolz as dtools
import ZI_UHFLI as lolvl

from time import sleep
import numpy as np
import logging

class ZI_UHFLI_SemiCon(lolvl.ZI_UHFLI):
    
    def __init__(self, name, device_id):
        lolvl.ZI_UHFLI.__init__(self, name, device_id)
        
        #Initialize two managed daqMs to run measurements in parallel
        self.daqM1 = dtools.daq_module_toolz(self.create_daq_module(), self._device_id)        
        self.daqM2 = dtools.daq_module_toolz(self.create_daq_module(), self._device_id)
        
        self.add_function("get_value")
        self.add_function("create_daq_module")
        
    def create_daq_module(self):
        return self.daq.dataAcquisitionModule()
    
        #Set and get functions for the qkit wrapper, not intended for public use
        '''
        signal ins
        '''
        
        
    def _prep_singleshot(self, daqM, averages):
        if averages == 1: # We have to do this since the min length of the grid mode is 2
            averages = 2  # We'll only use the first sample for return vals. I know this is ugly, plz don't hit me any more!
        daqM.set_daqM_grid_mode("exact")
        daqM.set_daqM_grid_num_samples(averages)
        daqM.set_daqM_grid_num_measurements(2)
        daqM.set_daqM_grid_direction("forward")
        daqM.set_daqM_grid_num(1)
    
    def get_value(self, averages, daqM = None):        
        #Use daqM1 as default
        if daqM is None:
            daqM = self.daqM1
        #Check wheter the device is rdy for measurement
        if not daqM.get_daqM_sample_path(): #Did the user specify which data to stream?
            logging.error("Humanling, you forgot AGAIN to add sample paths. You are not worthy of me.")
            return
        if not daqM.get_daqM_trigger_mode() == "continuous" and not daqM.get_daqM_trigger_path(): #The trigger should either be continuous or, in case of a not self-triggered measurement, a trigger path must be specified
            logging.error("You are waiting for a trigger signal which will never come. Hopeless. Set a trigger path to escape this purgatory.")
            return
        
        self._prep_singleshot(daqM, averages) #Setup the daqM parameters for a single shot                
        
        #Actual measurement routine:
        daqM.execute() #Arm the measurement
        while not daqM.finished(): #wait for completion
            sleep(0.1)        
        data = daqM.read() #Getting that sweet, sweet data, baby!
        
        meanval = []
        #Assert that the data has the correct structure. Build the return value while you're at it ;)
        assert data, "Datastream was empty, the daq couldn't return any values"
        for sample_path in daqM.get_daqM_sample_path():
            assert sample_path in data, "Datastream doesn't contain the subscribed data paths."
            assert len(data[sample_path]) == 1, "Datastream doesn't contain the desired amout of samples"
            if averages != 1:
                meanval.append(np.average(data[sample_path][0]["value"]))# ZI's data structure is quite intense...
            else:
                meanval.append(data[sample_path][0]["value"][0][0])
                
        return meanval, data #return the processed mean and the raw data dict, becuz why not?
    
    
#%%
if __name__ == "__main__":
    import qkit
    qkit.start()
    #%%
    UHFLI_test = qkit.instruments.create("UHFLI_test", "ZI_UHFLI_SemiCon", device_id = "dev2587")
    UHFLI_test.set_ch1_input_ac_coupling(True)
    UHFLI_test.set_ch1_input_50ohm(True)
    UHFLI_test.set_ch1_input_range(0.5)
    UHFLI_test.set_dem1_demod_enable(True)
    UHFLI_test.set_dem1_sample_rate(100e+03)
    UHFLI_test.set_dem1_filter_order(4)
    UHFLI_test.set_dem1_filter_timeconst(1e-3)
    UHFLI_test.set_dem1_demod_harmonic(1)
    UHFLI_test.set_ch1_carrier_freq(400e3)    
    UHFLI_test.set_ch1_output_amp_enable(True)
    UHFLI_test.set_ch1_output(True)
    UHFLI_test.set_ch1_output_range(1.5)
    UHFLI_test.set_ch1_output_amplitude(0.25)
    UHFLI_test.daqM1.set_daqM_trigger_mode("continuous")
    UHFLI_test.daqM1.set_daqM_trigger_edge("rising")
    UHFLI_test.daqM1.set_daqM_trigger_path("/dev2587/demods/0/sample.trigin4")
    print(UHFLI_test.daqM1.get_daqM_trigger_mode())
    print(UHFLI_test.daqM1.get_daqM_trigger_edge())
    UHFLI_test.daqM1.set_daqM_sample_path(["/dev2587/demods/0/sample.x", "/dev2587/demods/0/sample.y"])
    (meanval, _) = UHFLI_test.get_value(5000)
    print(meanval)
    print(UHFLI_test.daqM1.get_daqM_grid_num_samples())
    print(UHFLI_test.daqM1.get_daqM_grid_num_measurements())
