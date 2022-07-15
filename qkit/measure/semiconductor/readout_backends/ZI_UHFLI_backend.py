#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep  7 17:57:44 2021

@author: lr1740
"""
from qkit.measure.semiconductor.readout_backends.RO_backend_base import RO_backend_base

class ZI_UHFLI_backend(RO_backend_base):
    def __init__(self, UHFLI):
        super().__init__()
        self.UHFLI = UHFLI
        self._id = self.UHFLI._device_id
        self.register_measurement("demod0", "V", ["x", "y", "r", "theta"])
        self.register_measurement("demod4", "V", ["x", "y", "r", "theta"])
        
        self.settings = {"demod0" : {"trig_type" : "HW_trigger",
                                    "trig_channel" : 1,
                                    "trig_edge" : "rising",
                                    "trig_holdoff_count" : 0,
                                    "trig_software_delay" : 0,                              
                                    "mode" : "exact",
                                    "direction" : "forward",
                                    "demod_index" : 0,
                                    "active" : False,
                                    "daqM" : self.UHFLI.daqM1},
                         "demod4" : {"trig_type" : "HW_trigger",
                                    "trig_channel" : 2,
                                    "trig_edge" : "rising",
                                    "trig_holdoff_count" : 0,
                                    "trig_software_delay" : 0,                              
                                    "mode" : "exact",
                                    "direction" : "forward",
                                    "demod_index" : 4,
                                    "active" : False,
                                    "daqM" : self.UHFLI.daqM2}
                          }
        self.setup_grid()

    def setup_grid(self):
        for settings in self.settings.values():
            #Set up the trigger
            settings["daqM"].set_daqM_trigger_mode(settings["trig_type"])
            settings["daqM"].set_daqM_trigger_path(f"/{self._id}/demods/{settings['demod_index']}/sample.TRIGIN{settings['trig_channel']}")
            settings["daqM"].set_daqM_trigger_edge(settings["trig_edge"])
            settings["daqM"].set_daqM_trigger_holdoff_count(settings["trig_holdoff_count"])
            settings["daqM"].set_daqM_trigger_delay(settings["trig_software_delay"])
            
            #setting up the grid
            settings["daqM"].set_daqM_grid_mode(settings["mode"])
            settings["daqM"].set_daqM_grid_direction(settings["direction"])
            
            #setting up the sample path
            settings["daqM"].set_daqM_sample_path([f"/{self._id}/demods/{settings['demod_index']}/sample.r",
                                                   f"/{self._id}/demods/{settings['demod_index']}/sample.theta",
                                                   f"/{self._id}/demods/{settings['demod_index']}/sample.x",
                                                   f"/{self._id}/demods/{settings['demod_index']}/sample.y",])
        
    def demod0_get_sample_rate(self):
        return self.UHFLI.get_dem0_sample_rate() # is returned in Hz
        
    def demod0_set_measurement_count(self, meas_num):
        self.UHFLI.daqM1.set_daqM_grid_num_measurements(meas_num)
    
    def demod0_set_sample_count(self, sample_num):
        #we set this here because it is at this point that the system knows how long a trigger event will be
        trigger_duration = sample_num / self.UHFLI.get_dem0_sample_rate()
        self.UHFLI.daqM1.set_daqM_trigger_holdoff_time(trigger_duration)
        self.UHFLI.daqM1.set_daqM_grid_num_samples(sample_num)        
    
    def demod0_set_averages(self, grid_num):
        self.UHFLI.daqM1.set_daqM_grid_num(grid_num)
    
    def demod0_activate(self):
        self.UHFLI.set_dem0_demod_enable(True)
        self.settings["demod0"]["active"] = True
    
    def demod0_deactivate(self):
        self.UHFLI.set_dem0_demod_enable(False)
        self.settings["demod0"]["active"] = False
        
    def demod4_get_sample_rate(self):
        return self.UHFLI.get_dem4_sample_rate() # is returned in Hz
        
    def demod4_set_measurement_count(self, meas_num):
        self.UHFLI.daqM2.set_daqM_grid_num_measurements(meas_num)
    
    def demod4_set_sample_count(self, sample_num):
        #we set this here because it is at this point that the system knows how long a trigger event will be
        trigger_duration = sample_num / self.UHFLI.get_dem4_sample_rate()
        self.UHFLI.daqM2.set_daqM_trigger_holdoff_time(trigger_duration)
        self.UHFLI.daqM2.set_daqM_grid_num_samples(sample_num)        
    
    def demod4_set_averages(self, grid_num):
        self.UHFLI.daqM2.set_daqM_grid_num(grid_num)
    
    def demod4_activate(self):
        self.UHFLI.set_dem4_demod_enable(True)
        self.settings["demod4"]["active"] = True
    
    def demod4_deactivate(self):
        self.UHFLI.set_dem4_demod_enable(False)
        self.settings["demod4"]["active"] = False
    
    def arm(self):
        for settings in self.settings.values():
            if settings["active"]: settings["daqM"].execute()
    
    def finished(self):
        finished = True
        for settings in self.settings.values():            
            if settings["active"]: finished &= settings["daqM"].finished()
            
        return finished
    
    def read(self):
        data = {}
                            
        for demod, settings in self.settings.items():
            if settings["active"]:
                data[demod] = {}
                raw_data = settings["daqM"].read()
                for node in self._registered_measurements[demod]["data_nodes"]:
                    data[demod][node] = []
                    path = f"/{self._id}/demods/{settings['demod_index']}/sample.{node}"
                    if path in raw_data.keys():
                        for grid in range(len(raw_data[path])):
                            if raw_data[path][grid]["header"]["flags"] & 1:
                                data[demod][node].append(raw_data[path][grid]["value"])
                            
        return data
    
    def stop(self):
        for settings in self.settings.values():
            if settings["active"]: settings["daqM"].stop()
    
#%%
if __name__ == "__main__":
    from time import sleep
    import qkit
    qkit.start()
    UHFLI = qkit.instruments.create("UHFLI", "ZI_UHFLI_SemiCon", device_id = "dev2587")
    UHFLI.set_ch0_output(True)
    UHFLI.set_ch1_output(True)
    UHFLI.set_ch0_output_amp_enable(True)
    UHFLI.set_ch1_output_amp_enable(True)
    backend = ZI_UHFLI_backend(UHFLI)
    print(backend.demod0_get_sample_rate())
    backend.demod0_set_measurement_count(50)
    backend.demod0_set_sample_count(75)
    backend.demod0_set_averages(10)
    backend.demod4_set_measurement_count(50)
    backend.demod4_set_sample_count(75)
    backend.demod4_set_averages(10)
    print("The number of samples to acquire by the daq module: ", UHFLI.daqM1.get_daqM_grid_num_samples())
    print("The number of measurements to acquire by the daq module: ", UHFLI.daqM1.get_daqM_grid_num_measurements())
    print("The number of grids to acquire by the daq module: ", UHFLI.daqM1.get_daqM_grid_num())
    #%%
    backend.demod0_activate()
    backend.demod4_activate()
    backend.arm()
    while not backend.finished():
        sleep(0.1)
        data = backend.read()
        print(data)
    #%%
    print(UHFLI.daqM1.get_daqM_sample_path())
    print(UHFLI.daqM1.get_daqM_trigger_path())
    
    print(UHFLI.daqM2.get_daqM_sample_path())
    print(UHFLI.daqM2.get_daqM_trigger_path())
    print(backend.finished())
    #%%
    UHFLI.set_ch0_carrier_freq(400e3)
    UHFLI.set_ch1_carrier_freq(1e6)
    UHFLI.set_ch0_output_amplitude(250e-3)
    UHFLI.set_ch1_output_amplitude(100e-3)
    UHFLI.set_ch0_output(True)
    UHFLI.set_ch1_output(True)
    UHFLI.set_ch0_output_amp_enable(True)
    UHFLI.set_ch1_output_amp_enable(True)