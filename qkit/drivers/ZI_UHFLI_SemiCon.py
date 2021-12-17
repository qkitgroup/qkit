#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 15 12:17:39 2021

@author: lr1740
"""
import qkit
import qkit.drivers.ZI_UHFLI as lolvl

from time import sleep
import numpy as np
import logging

class ZI_UHFLI_SemiCon(lolvl.ZI_UHFLI):
    
    def __init__(self, name, device_id):
        self._device_id = device_id
        super().__init__(name, self._device_id)
        self.daqM1 = qkit.instruments.create("UHFLI_daqM1", "ZI_DAQ_module", unmanaged_daq_module = self.create_daq_module(), device_id = self._device_id)
        self.daqM2 = qkit.instruments.create("UHFLI_daqM2", "ZI_DAQ_module", unmanaged_daq_module = self.create_daq_module(), device_id = self._device_id)

        self._FLAG_THROW = 0x0004
        self._FLAG_DETECT = 0x0008
        
        self.ch0_clearance = 0
        self.ch1_clearance = 0
        
        self.add_parameter("daq_sample_path", type = list,
                          flags = self.FLAG_SET | self.FLAG_SOFTGET)
        self.add_parameter("data_nodes", type = list,
                          flags = self.FLAG_SET | self.FLAG_SOFTGET)
        self.add_parameter("step_recovery", type = str,
                          flags = self.FLAG_SET | self.FLAG_SOFTGET)
        
        self.set_daq_sample_path([])
        self.set_data_nodes([])
        self.set_step_recovery(r"99%")
        
        self.add_function("create_daq_module")
        self.add_function("activate_ch0")
        self.add_function("activate_ch1")
        self.add_function("easy_sub")
        self.add_function("get_sample")
    
    def create_daq_module(self):
        return self.daq.dataAcquisitionModule()
    
    def activate_ch0(self):
        self.set_dem0_demod_enable(True)
        self.set_ch0_output(True)
        
        if any([True for path in self.get_daq_sample_path() if "/demods/4" in path]):
            self.set_daq_sample_path([f"/{self._device_id}/demods/0/sample",
                                      f"/{self._device_id}/demods/4/sample"])
        else: self.set_daq_sample_path([f"/{self._device_id}/demods/0/sample"])
        
        self.set_data_nodes(["x", "y", "timestamp"])
        
    def activate_ch1(self):
        self.set_dem4_demod_enable(True)
        self.set_ch1_output(True)
        
        if any([True for path in self.get_daq_sample_path() if "/demods/0" in path]):
            self.set_daq_sample_path([f"/{self._device_id}/demods/0/sample",
                                      f"/{self._device_id}/demods/4/sample"])
        else: self.set_daq_sample_path([f"/{self._device_id}/demods/4/sample"])
        
        self.set_data_nodes(["x", "y", "timestamp"])
        
    def sample_ch0(self, wait_settle_time):
        assert self.get_dem0_demod_enable(), f"{__name__}: Demod 0 is not enabled."
        if wait_settle_time:
            self.wait_settle_time(0, self.get_step_recovery())
            
        raw = self.daq.getSample(f"/{self._device_id}/demods/0/sample")
        nodes = self.get_data_nodes()
        gotten_sample = {}
        for node in nodes:
            gotten_sample[f"{node}0"] = float(raw[node])
            
        if "x" in nodes and "y" in nodes:
            gotten_sample["r0"] = np.sqrt(gotten_sample["x0"]**2 + gotten_sample["y0"]**2)
        return gotten_sample
    
    def sample_ch1(self, wait_settle_time):
        assert self.get_dem0_demod_enable(), f"{__name__}: Demod 4 is not enabled."
        if wait_settle_time:
            self.wait_settle_time(4, self.get_step_recovery())
            
        raw = self.daq.getSample(f"/{self._device_id}/demods/4/sample")
        nodes = self.get_data_nodes()
        gotten_sample = {}
        for node in self.get_data_nodes():
            gotten_sample[f"{node}4"] = float(raw[node])
        
        if "x" in nodes and "y" in nodes:
            gotten_sample["r4"] = np.sqrt(gotten_sample["x4"]**2 + gotten_sample["y4"]**2)
        return gotten_sample  
        
    def easy_sub(self, demod_index):
       sub_list = [] 
       for element in demod_index:
            if not isinstance(element, int):
                raise TypeError("%s: Cannot use %s to subscribe to the DAQ. Object must be an iterable of integers." % (__name__, demod_index))
            if element not in range(8):
                raise ValueError("%s: Cannot use %s to subscribe to the DAQ. Invalid demodulator number."% (__name__, demod_index))
            sub_list.append("/%s/demods/%d/sample" % (self._device_id, element))            
       self.set_daq_sample_path(sub_list)
    
    def get_sample(self):
        channels = {}
        
        sample_path = self.get_daq_sample_path()
        data_nodes = self.get_data_nodes()
        assert sample_path, f"{__name__}: No sample_path was specified. Use set_daq_sample_path(list(str)) before calling get_sample."
        assert data_nodes, f"{__name__}: No data_nodes were specified. Use set_data_nodes(list(str)) before calling get_sample."
        for path in sample_path:
            raw_data = self.daq.getSample(path)
            gotten_samples = {}
            for node in data_nodes:
                gotten_samples[node] = float(raw_data[node])
            
            channels[path] = gotten_samples
        
        return channels
                
    #These functions will deprecate soon
    def poll_samples(self, integration_time):
        #self.daq.flush()
        data = self.daq.poll(integration_time, 100, self._FLAG_DETECT | self._FLAG_THROW , True) #arguments: (Poll length in s, timeout in ms, flags, return flat dictionary)
       
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
        allowed_nodes = {"timestamp", "x", "y", "frequency", "phase", "dio", "trigger", "auxin0", "auxin1"}
        typerr = TypeError("%s: Cannot set %s as data_nodes. Object must be a list of strings." % (__name__, newnode))
        if not isinstance(newnode, list):
            raise typerr
        for element in newnode:
            if not isinstance(element, str):
                raise typerr         
            if element not in allowed_nodes:
                raise ValueError(f"{__name__}: {element} is not an allowed data_node. The allowed data_nodes are {allowed_nodes}.")
        logging.debug(__name__ + ' : setting data_nodes to %s' % (newnode))

    def _do_set_step_recovery(self, new_rec):
        allowed_recs = self._filter_settling_factors.keys()
        if new_rec not in allowed_recs:
            raise ValueError(f"{__name__}: {new_rec} is not a defined step recovery percentile. The allowed percentiles are {allowed_recs}.")
        logging.debug(__name__ + ' : setting step_recovery to %s' % (new_rec))
        
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
    pass
