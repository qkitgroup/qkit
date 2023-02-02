#This is a clone of the UHFLI driver that is being adapted to the MFLI, work under construcion

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 15 12:17:39 2021

@author: lr1740
"""
import qkit
import qkit.drivers.ZI_MFLI as lolvl

from warnings import warn
from typing import Dict
import numpy as np
import logging

class ZI_MFLI_SemiCon(lolvl.ZI_MFLI):
    
    def __init__(self, name, device_id):
        self._device_id = device_id
        super().__init__(name, self._device_id)
        self.daqM1 = qkit.instruments.create("MFLI_daqM1", "ZI_DAQ_module", unmanaged_daq_module = self.create_daq_module(), device_id = self._device_id)
        self.daqM2 = qkit.instruments.create("MFLI_daqM2", "ZI_DAQ_module", unmanaged_daq_module = self.create_daq_module(), device_id = self._device_id)

        self._FLAG_THROW = 0x0004
        self._FLAG_DETECT = 0x0008
        self.integration_time = 0.05 #in s
        self.timeout = 100 #in ms
        
        self.add_parameter("daq_sample_path", type = list,
                          flags = self.FLAG_SET | self.FLAG_SOFTGET)
        self.add_parameter("data_nodes", type = list,
                          flags = self.FLAG_SET | self.FLAG_SOFTGET)
        
        self.set_daq_sample_path([])
        self.set_data_nodes([])
        
        self._depr_warnings= {"sample_ch0" : True,
                              "sample_ch1" : True,
                              "sample_ch0and1" : True}
        
        self.add_function("create_daq_module")
        self.add_function("activate_ch0")
    #    self.add_function("activate_ch1")
        self.add_function("easy_sub")
        self.add_function("get_sample")
        self.add_function("continuous_acquisition")
        self.add_function("sample_averaged")
    
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
        
    def deactivate_ch0(self):
        self.set_dem0_demod_enable(False)
        self.set_ch0_output(False)
        new_path = ""
        
        if any([True for path in self.get_daq_sample_path() if "/demods/4" in path]):
            new_path = [f"/{self._device_id}/demods/4/sample"]
        self.set_daq_sample_path("")
        self.set_daq_sample_path(new_path)
    """    
    def activate_ch1(self):
        self.set_dem4_demod_enable(True)
        self.set_ch1_output(True)
        
        if any([True for path in self.get_daq_sample_path() if "/demods/0" in path]):
            self.set_daq_sample_path([f"/{self._device_id}/demods/0/sample",
                                      f"/{self._device_id}/demods/4/sample"])
        else: self.set_daq_sample_path([f"/{self._device_id}/demods/4/sample"])
        
        self.set_data_nodes(["x", "y", "timestamp"])
    
    def deactivate_ch1(self):
        self.set_dem1_demod_enable(False)
        self.set_ch1_output(False)
        new_path = ""
        
        if any([True for path in self.get_daq_sample_path() if "/demods/0" in path]):
            new_path = [f"/{self._device_id}/demods/0/sample"]
        self.set_daq_sample_path("")
        self.set_daq_sample_path(new_path)
    """    
    def sample_dem(self, channel : int) -> Dict[str, np.ndarray]:
        assert getattr(self, f"get_dem{channel}_demod_enable")(), f"{__name__}: Demod {channel} is not enabled."
                    
        raw = self.daq.getSample(f"/{self._device_id}/demods/{channel}/sample")
        nodes = self.get_data_nodes()
        gotten_sample = {}
        for node in nodes:
            gotten_sample[f"{node}{channel}"] = float(raw[node])
            
        if "x" in nodes and "y" in nodes:
            gotten_sample[f"r{channel}"] = np.sqrt(gotten_sample[f"x{channel}"]**2 + gotten_sample[f"y{channel}"]**2)
        return gotten_sample
        
# =============================================================================
#     def sample_ch0(self, wait_settle_time):
#         if self._depr_warnings["sample_ch0"]:
#             warn(f"{__name__}: sample_ch0 will deprecate with the next update. Use sample_dem(channel) instead.")
#             self._depr_warnings["sample_ch0"] = False
#         
#         assert self.get_dem0_demod_enable(), f"{__name__}: Demod 0 is not enabled."
#         
#         if wait_settle_time:
#             self.wait_settle_time(0)
#             
#         raw = self.daq.getSample(f"/{self._device_id}/demods/0/sample")
#         nodes = self.get_data_nodes()
#         gotten_sample = {}
#         for node in nodes:
#             gotten_sample[f"{node}0"] = float(raw[node])
#             
#         if "x" in nodes and "y" in nodes:
#             gotten_sample["r0"] = np.sqrt(gotten_sample["x0"]**2 + gotten_sample["y0"]**2)
#         return gotten_sample
#     
#     def sample_ch1(self, wait_settle_time):
#         if self._depr_warnings["sample_ch1"]:
#             warn(f"{__name__}: sample_ch1 will deprecate with the next update. Use sample_dem(channel) instead.")
#             self._depr_warnings["sample_ch1"] = False
#         
#         assert self.get_dem4_demod_enable(), f"{__name__}: Demod 4 is not enabled."
#         if wait_settle_time:
#             self.wait_settle_time(4)
#             
#         raw = self.daq.getSample(f"/{self._device_id}/demods/4/sample")
#         nodes = self.get_data_nodes()
#         gotten_sample = {}
#         for node in self.get_data_nodes():
#             gotten_sample[f"{node}4"] = float(raw[node])
#         
#         if "x" in nodes and "y" in nodes:
#             gotten_sample["r4"] = np.sqrt(gotten_sample["x4"]**2 + gotten_sample["y4"]**2)
#         return gotten_sample  
#         
#     def sample_ch0and1(self, wait_settle_time):
#         if self._depr_warnings["sample_ch0and1"]:
#             warn(f"{__name__}: sample_ch0and1 will deprecate with the next update. Use sample_dem(channel) instead.")
#             self._depr_warnings["sample_ch0and1"] = False
#         
#         assert self.get_dem0_demod_enable(), f"{__name__}: Demod 0 is not enabled."
#         assert self.get_dem4_demod_enable(), f"{__name__}: Demod 4 is not enabled."
#         if wait_settle_time:
#             self.wait_settle_time(4)
#             
#         raw0 = self.daq.getSample(f"/{self._device_id}/demods/0/sample")
#         raw1 = self.daq.getSample(f"/{self._device_id}/demods/4/sample")
#         nodes = self.get_data_nodes()
#         gotten_sample = {}
#         for node in self.get_data_nodes():
#             gotten_sample[f"{node}0"] = float(raw0[node])
#             gotten_sample[f"{node}4"] = float(raw1[node])
#         
#         if "x" in nodes and "y" in nodes:
#             gotten_sample["r0"] = np.sqrt(gotten_sample["x0"]**2 + gotten_sample["y0"]**2)
#             gotten_sample["r4"] = np.sqrt(gotten_sample["x4"]**2 + gotten_sample["y4"]**2)
#         return gotten_sample  
# =============================================================================
    
    
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
    
    def continuous_acquisition(self):
        """
        Polls samples for 50 ms.
        Intended to be used in a a loop which calls the function repeatedly.

        Parameters
        ----------
        None

        Returns
        -------
        result : dict(str : np.ndarray)
            Samples polled during the last interval of poll and the time in between two polls.
        
        Raises
        ------
        EOFerror
            If sample loss is detected.
        """
        measured = self.daq.poll(self.integration_time, self.timeout, self._FLAG_THROW | self._FLAG_DETECT, True)
        nodes = self.get_data_nodes()
        gotten_traces = {}
        for path in measured.keys():
            demod_index = path.split('demods/')[1][0]
            for node in nodes:
                gotten_traces[f"{node}{demod_index}"] = measured[path][node]
            if "x" in nodes and "y" in nodes:
                gotten_traces[f"r{demod_index}"] = np.sqrt(gotten_traces[f"x{demod_index}"]**2 + gotten_traces[f"y{demod_index}"]**2)
        return gotten_traces
                
    def sample_averaged(self, avgs):
        """
        Software averages samples before returning.

        Parameters
        ----------
        avgs : int

        Returns
        -------
        result : dict(str : np.float64)
            Samples polled during the last interval of poll and the time in between two polls.
        
        Raises
        ------
        EOFerror
            If sample loss is dected.
        """
        
        node_lengths = {}
        cumulated_avgs = {}
        self.daq.flush()
        
        measured = self.continuous_acquisition()
        for node, values in measured.items(): 
            count = len(values)
            if count >= avgs:
                values = values[:avgs]
                node_lengths[node] = avgs
            else:
                node_lengths[node] = count
            cumulated_avgs[node] = np.sum(values)
        
        while(not all(length >= avgs for length in node_lengths.values())):
            measured = self.continuous_acquisition()
            for node, values in measured.items():
                count = node_lengths[node] + len(values)
                if count >= avgs:
                    values = values[:avgs - node_lengths[node]]
                    node_lengths[node] = avgs
                else:
                    node_lengths[node] = count
                cumulated_avgs[node] += np.sum(values)
        result = {node: values/avgs for node, values in cumulated_avgs.items()}        
        return result            
    
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
        
#%%
if __name__ == "__main__":
    qkit.start()
    #%% Create the device
    MFLI = qkit.instruments.create("MFLI", "ZI_MFLI_SemiCon", device_id = "dev2587")
    #%% Lockin Settings   
# =============================================================================
#     MFLI.easy_sub([1])
#     MFLI.set_data_nodes(["x", "y"])
#     
#     MFLI.set_ch1_input_ac_coupling(True)
#     MFLI.set_ch1_input_50ohm(True)
#     MFLI.set_ch1_input_range(0.5)
#     
#     MFLI.set_dem1_demod_enable(True)
#     MFLI.set_dem1_sample_rate(14e6)
#     MFLI.set_dem1_filter_order(4)
#     MFLI.set_dem1_filter_timeconst(1e-3)
#     MFLI.set_dem1_demod_harmonic(1)
#     MFLI.set_dem1_trigger_mode("continuous")
# 
#     MFLI.set_ch1_carrier_freq(400e3)
#     MFLI.set_ch1_output(True)
#     MFLI.set_ch1_output_amp_enable(True)
#     MFLI.set_ch1_output_range(1.5)
#     MFLI.set_ch1_output_amplitude(0.25)
# =============================================================================
    #%% Get a sample
    MFLI.activate_ch0()
    MFLI.activate_ch1()
    MFLI.daq.flush()
    print(MFLI.sample_averaged(100)["x0"])
    #print(MFLI.find_slowest_demod())

    #%% Sample chx
    print(MFLI.sample_dem(4))
    #%% Time the sample_averaged command
    import timeit
    def avgs(num, wait):
        MFLI.sample_averaged(num)
    num_exec = 20
    print(timeit.timeit("avgs(100, True)", "from __main__ import avgs", number = num_exec)/num_exec)
    #%% Print and save the instrument settings
    #print(get_instrument_settings(r"C:\Users\Julian\Documents\Code")["daqM1"])
# =============================================================================
#     #%% Find the daq Triggerlevel
#     import time
#     MFLI.daqM1.daqM.set("findlevel", 1)
#     findlevel = 1
#     timeout = 10  # [s]
#     t0 = time.time()
#     while findlevel == 1:
#         time.sleep(0.05)
#         findlevel =   MFLI.daqM1.daqM.getInt("findlevel")
#         if time.time() - t0 > timeout:
#             MFLI.daqM1.daqM.finish()
#             raise RuntimeError("Data Acquisition Module didn't find trigger level after %.3f seconds." % timeout)
#     level =   MFLI.daqM1.daqM.getDouble("level")
#     hysteresis =   MFLI.daqM1.daqM.getDouble("hysteresis")
#     print(f"Data Acquisition Module found and set level: {level},", f"hysteresis: {hysteresis}.")
# =============================================================================
    #%% Test the daq module
# =============================================================================
#     sample_num = 2
#     meas_num = 16000
#     trig_duration = sample_num / MFLI.get_dem1_sample_rate()
#     MFLI._prep_grid(trig_duration, sample_num, meas_num)
#     MFLI.daqM1.execute()
#     
#     while not MFLI.daqM1.finished():
#         sleep(0.01)
#         print("Everyday I'm shuffelin'.")
#         data_read = MFLI.daqM1.read()
#         if '/dev2587/demods/0/sample.r' in data_read.keys():
#             timestamps = data_read[r'/dev2587/demods/0/sample.r'][0]["timestamp"]
#             print(len(timestamps[timestamps!=0])/2)
#     
#     finished_data = data_read
#     print(finished_data)
#     #%% Do a performance comparison between averages and separate multiple recordings
#     MFLI._prep_grid(2, 5000, 4, 5*10**-6, 10)
#     
#     def wait_for_daq():
#         MFLI.daqM1.execute()
#         while not MFLI.daqM1.finished():
#             pass
#     
#     num_exec = 1
#     print(timeit.timeit("wait_for_daq()", "from __main__ import wait_for_daq", number = num_exec)/num_exec)
#     #%% Information about the readout
#     for key in data_read.keys():
#         print(key)
#     #%% Other stuff
#     a = np.array([[1,2],[0,0]])
#     print(a[a!=1])
#     pass
# =============================================================================
