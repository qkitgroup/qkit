#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 15 12:17:39 2021

@author: lr1740
"""
import qkit
import ZI_UHFLI as lolvl

from math import ceil
from time import sleep
import numpy as np
import logging

class ZI_UHFLI_SemiCon(lolvl.ZI_UHFLI):
    
    def __init__(self, name, device_id):
        self._device_id = device_id
        lolvl.ZI_UHFLI.__init__(self, name, self._device_id)
        self.daqM1 = qkit.instruments.create("daqM1", "ZI_DAQ_module", unmanaged_daq_module = self.create_daq_module(), device_id = self._device_id)
        
        self.grid_settings = {"trig_type" : "HW_trigger",
                              "trig_demod_index" : 0,
                              "trig_channel" : 4,
                              "trig_edge" : "rising",
                              "trig_holdoff_count" : 0,
                              "trig_software_delay" : 0,                              
                              "mode" : "exact",
                              "direction" : "forward",
                              "number_of_grids" : 1,
                              "demod_index" : 0
                              }
        
        self._last_poll = None
        self._FLAG_THROW = 0x0004
        self._FLAG_DETECT = 0x0008
        
        self.add_parameter("daq_sample_path", type = list,
                          flags = self.FLAG_SET | self.FLAG_SOFTGET)
        self.add_parameter("data_nodes", type = list,
                          flags = self.FLAG_SET | self.FLAG_SOFTGET)
        
        self.add_function("create_daq_module")
        self.add_function("get_value")
        self.add_function("easy_sub")
        self.add_function("get_sample")
        self.add_function("poll_samples")
        self.add_function("data_fetch")
    
    def create_daq_module(self):
        return self.daq.dataAcquisitionModule()   

    def easy_sub(self, demod_index):
        typerr = TypeError("%s: Cannot use %s to subscribe to the DAQ. Object must be a list of integers." % (__name__, demod_index))
        for element in demod_index:
            if not isinstance(element, int):
                raise typerr
            if element > 8:
                raise ValueError("%s: Cannot use %s to subscribe to the DAQ. Device only possesses 8 demodulators."% (__name__, demod_index))
        
        sub_list = []                
        for element in demod_index:
            sub_list.append("/%s/demods/%d/sample" % (self._device_id, element - 1))
            
        self.set_daq_sample_path(sub_list)
    
    def get_sample(self):
        channels = {}
        gotten_samples = []
        data_nodes = self.get_data_nodes()
        
        for path in self.get_daq_sample_path():
            raw_data = self.daq.getSample(path)
            
            for node in data_nodes:
                gotten_samples.append(float(raw_data[node]))
            
            channels[path] = gotten_samples
            gotten_samples = []
        
        return channels
    
    def _prep_grid(self, trigger_duration, sample_num, meas_num, num_averages = 1):
        #setting up the trigger
        self.daqM1.set_daqM_trigger_mode(self.grid_settings["trig_type"])
        self.daqM1.set_daqM_trigger_path("/%s/demods/%d/sample.TRIGIN%d" % (self._device_id, 
                                                                            self.grid_settings["trig_demod_index"], 
                                                                            self.grid_settings["trig_channel"]))
        self.daqM1.set_daqM_trigger_edge(self.grid_settings["trig_edge"])
        self.daqM1.set_daqM_trigger_duration(trigger_duration)
        self.daqM1.set_daqM_trigger_holdoff_time(trigger_duration)
        self.daqM1.set_daqM_trigger_holdoff_count(self.grid_settings["trig_holdoff_count"])
        self.daqM1.set_daqM_trigger_delay(self.grid_settings["trig_software_delay"])
        #setting up the grid
        self.daqM1.set_daqM_grid_mode(self.grid_settings["mode"])
        self.daqM1.set_daqM_grid_direction(self.grid_settings["direction"])
        self.daqM1.set_daqM_grid_num(self.grid_settings["number_of_grids"])
        self.daqM1.set_daqM_grid_num_samples(sample_num)
        self.daqM1.set_daqM_grid_num_measurements(meas_num)
        self.daqM1.set_daqM_grid_averages(num_averages)
        #setting up the sample path
        self.daqM1.set_daqM_sample_path(["/%s/demods/%d/sample.%s" % (self._device_id, self.grid_settings["demod_index"], "r"),
                                         "/%s/demods/%d/sample.%s" % (self._device_id, self.grid_settings["demod_index"], "theta"),
                                         "/%s/demods/%d/sample.%s" % (self._device_id, self.grid_settings["demod_index"], "x"),
                                         "/%s/demods/%d/sample.%s" % (self._device_id, self.grid_settings["demod_index"], "y")])
                
    #These functions will deprecate soon
    def poll_samples(self, integration_time):
        self.daq.flush()
        data = self.daq.poll(integration_time, 500, self._FLAG_DETECT | self._FLAG_THROW , True) #arguments: (Poll length in s, timeout in ms, flags, return flat dictionary)
       
        assert data, "Datastream was empty, the daq couldn't return any values"
        for sample_path in self.get_daq_sample_path():
            assert sample_path in data, "Data stream does not contain the subscribed data paths"
        
        self._last_poll = data

    def data_fetch(self, demod_index, data_node, average = True):
        assert self._last_poll, "No data has been polled yet"
        selected = self._last_poll["/%s/demods/%d/sample" % (self._device_id, demod_index)] [data_node]
        if average:
            return np.array([np.mean(selected)])
        else:
            return selected
    
    def _prep_singleshot(self, daqM, averages):
        num_samples = ceil(averages / 2)      
        if num_samples == 1:
            num_samples = 2    
        daqM.set_daqM_grid_mode("exact")
        daqM.set_daqM_grid_num_samples(num_samples)
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
                a = np.append(data[sample_path][0]["value"][0], data[sample_path][0]["value"][1])
                meanval.append(np.average(a))# ZI's data structure is quite intense...
            else:
                meanval.append(data[sample_path][0]["value"][0][0])
                
        return meanval, data # return the processed mean and the raw data dict, becuz why not?    
    
    def _do_set_daq_sample_path(self, newpath):
        typerr = TypeError("%s: Cannot set %s as daq_sample_path. Object must be a list of strings." % (__name__, newpath))
        for element in newpath:
            if not isinstance(element, str):
                raise typerr  
        logging.debug(__name__ + ' : setting sample path of the daq to %s' % (newpath))
        self.daq.unsubscribe("*")
        self.daq.flush()
        
        for element in newpath:
            self.daq.subscribe(element)
    
    def _do_set_data_nodes(self, newnode):
        typerr = TypeError("%s: Cannot set %s as data_nodes. Object must be a list of strings." % (__name__, newnode))
        for element in newnode:
            if not isinstance(element, str):
                raise typerr         
        
        logging.debug(__name__ + ' : setting data_nodes to %s' % (newnode))

#%%
if __name__ == "__main__":
    qkit.start()
    #%%
    from qkit.measure.write_additional_files import get_instrument_settings
    import timeit
    #%% Create the device
    UHFLI = qkit.instruments.create("UHFLI", "ZI_UHFLI_SemiCon", device_id = "dev2587")
    #%% Lockin Settings   
    UHFLI.easy_sub([1])
    UHFLI.set_data_nodes(["x", "y"])
    
    UHFLI.set_ch1_input_ac_coupling(True)
    UHFLI.set_ch1_input_50ohm(True)
    UHFLI.set_ch1_input_range(0.5)
    
    UHFLI.set_dem1_demod_enable(True)
    UHFLI.set_dem1_sample_rate(14e6)
    UHFLI.set_dem1_filter_order(4)
    UHFLI.set_dem1_filter_timeconst(1e-3)
    UHFLI.set_dem1_demod_harmonic(1)
    UHFLI.set_dem1_trigger_mode("in3_hi")

    UHFLI.set_ch1_carrier_freq(400e3)
    UHFLI.set_ch1_output(True)
    UHFLI.set_ch1_output_amp_enable(True)
    UHFLI.set_ch1_output_range(1.5)
    UHFLI.set_ch1_output_amplitude(0.25)
    #%% Get a sample
    try:
        print(UHFLI.get_sample())
    except(RuntimeError):
        print("Seems the demod is not triggered.")
    #%% Print and save the instrument settings
    print(get_instrument_settings(r"C:\Users\Julian\Documents\Code")["daqM1"])
# =============================================================================
#     #%% Find the daq Triggerlevel
#     import time
#     UHFLI.daqM1.daqM.set("findlevel", 1)
#     findlevel = 1
#     timeout = 10  # [s]
#     t0 = time.time()
#     while findlevel == 1:
#         time.sleep(0.05)
#         findlevel =   UHFLI.daqM1.daqM.getInt("findlevel")
#         if time.time() - t0 > timeout:
#             UHFLI.daqM1.daqM.finish()
#             raise RuntimeError("Data Acquisition Module didn't find trigger level after %.3f seconds." % timeout)
#     level =   UHFLI.daqM1.daqM.getDouble("level")
#     hysteresis =   UHFLI.daqM1.daqM.getDouble("hysteresis")
#     print(f"Data Acquisition Module found and set level: {level},", f"hysteresis: {hysteresis}.")
# =============================================================================
    #%% Test the daq module
    sample_num = 2
    meas_num = 16000
    trig_duration = sample_num / UHFLI.get_dem1_sample_rate()
    UHFLI._prep_grid(trig_duration, sample_num, meas_num)
    UHFLI.daqM1.execute()
    
    while not UHFLI.daqM1.finished():
        sleep(0.01)
        print("Everyday I'm shuffelin'.")
        data_read = UHFLI.daqM1.read()
        if '/dev2587/demods/0/sample.r' in data_read.keys():
            timestamps = data_read[r'/dev2587/demods/0/sample.r'][0]["timestamp"]
            print(len(timestamps[timestamps!=0])/2)
    
    finished_data = data_read
    print(finished_data)
    #%% Do a performance comparison between averages and separate multiple recordings
    UHFLI._prep_grid(2, 5000, 4, 5*10**-6, 10)
    
    def wait_for_daq():
        UHFLI.daqM1.execute()
        while not UHFLI.daqM1.finished():
            pass
    
    num_exec = 1
    print(timeit.timeit("wait_for_daq()", "from __main__ import wait_for_daq", number = num_exec)/num_exec)
    #%% Information about the readout
    for key in data_read.keys():
        print(key)
    #%% Other stuff
    a = np.array([[1,2],[0,0]])
    print(a[a!=1])