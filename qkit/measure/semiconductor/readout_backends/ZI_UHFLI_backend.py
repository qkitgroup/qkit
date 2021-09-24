#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep  7 17:57:44 2021

@author: lr1740
"""
import numpy as np
from qkit.measure.semiconductor.readout_backends.RO_backend_base import RO_backend_base

class ZI_UHFLI_backend(RO_backend_base):
    def __init__(self, UHFLI):
        super().__init__()
        self.UHFLI = UHFLI
        self.register_measurement("demod1", "V", ["x", "y", "r", "theta"])
        
        self.grid_settings = {"demod1" : {"trig_type" : "HW_trigger",
                      "trig_demod_index" : 0,
                      "trig_channel" : 1,
                      "trig_edge" : "rising",
                      "trig_holdoff_count" : 0,
                      "trig_software_delay" : 0,                              
                      "mode" : "exact",
                      "direction" : "forward",
                      "demod_index" : 0,
                      "active" : False}
                      }
        self.name_to_index = {"demod1" : "0",
                              "demod2" : "1"}
        self.setup_grid()

    def setup_grid(self):
        #Set up the trigger
        self.UHFLI.daqM1.set_daqM_trigger_mode(self.grid_settings["demod1"]["trig_type"])
        self.UHFLI.daqM1.set_daqM_trigger_path("/{:s}/demods/{!s}/sample.TRIGIN{!s}".format(self.UHFLI._device_id,
                                                                                             self.grid_settings["demod1"]["demod_index"],
                                                                                             self.grid_settings["demod1"]["trig_channel"]))
        self.UHFLI.daqM1.set_daqM_trigger_edge(self.grid_settings["demod1"]["trig_edge"])
        self.UHFLI.daqM1.set_daqM_trigger_holdoff_count(self.grid_settings["demod1"]["trig_holdoff_count"])
        self.UHFLI.daqM1.set_daqM_trigger_delay(self.grid_settings["demod1"]["trig_software_delay"])
        
        #setting up the grid
        self.UHFLI.daqM1.set_daqM_grid_mode(self.grid_settings["demod1"]["mode"])
        self.UHFLI.daqM1.set_daqM_grid_direction(self.grid_settings["demod1"]["direction"])
        
        #setting up the sample path
        self.UHFLI.daqM1.set_daqM_sample_path(["/%s/demods/%d/sample.%s" % (self.UHFLI._device_id, self.grid_settings["demod1"]["demod_index"], "r"),
                                         "/%s/demods/%d/sample.%s" % (self.UHFLI._device_id, self.grid_settings["demod1"]["demod_index"], "theta"),
                                         "/%s/demods/%d/sample.%s" % (self.UHFLI._device_id, self.grid_settings["demod1"]["demod_index"], "x"),
                                         "/%s/demods/%d/sample.%s" % (self.UHFLI._device_id, self.grid_settings["demod1"]["demod_index"], "y")])
        
    def demod1_get_sample_rate(self):
        return self.UHFLI.get_dem1_sample_rate() # is returned in Hz
        
    def demod1_set_measurement_count(self, meas_num):
        self.UHFLI.daqM1.set_daqM_grid_num_measurements(meas_num)
    
    def demod1_set_sample_count(self, sample_num):
        #we set this here because it is at this point that the system knows how long a trigger event will be
        trigger_duration = sample_num / self.UHFLI.get_dem1_sample_rate()
        self.UHFLI.daqM1.set_daqM_trigger_holdoff_time(trigger_duration)
        self.UHFLI.daqM1.set_daqM_grid_num_samples(sample_num)        
    
    def demod1_set_averages(self, grid_num):
        self.UHFLI.daqM1.set_daqM_grid_num(grid_num)
    
    def demod1_activate(self):
        self.UHFLI.set_dem1_demod_enable(True)
        self.grid_settings["demod1"]["active"] = True
    
    def demod1_deactivate(self):
        self.UHFLI.set_dem1_demod_enable(False)
        self.grid_settings["demod1"]["active"] = False
    
    def arm(self):
        if self.grid_settings["demod1"]["active"]: self.UHFLI.daqM1.execute()
        #TODO if self.grid2_settings["active"]: ...
    
    def finished(self):
        finished = True
        if self.grid_settings["demod1"]["active"]: finished &= self.UHFLI.daqM1.finished()
        #TODO if self.grid2_settings["active"]: finished &= ... 
        return finished
    
    def read(self):
        data = {}
        demod = "demod1"
        if self.grid_settings[demod]["active"]:
            raw_data = self.UHFLI.daqM1.read()
            data[demod] = {}
            for node in self._registered_measurements[demod]["data_nodes"]:
                data[demod][node] = []
                path = f'/{self.UHFLI._device_id}/demods/{self.name_to_index[demod]}/sample.{node}'          
                if path in raw_data.keys():                    
                    for grid in range(len(raw_data[path])):
                        if raw_data[path][grid]["header"]["flags"] & 1:
                            data[demod][node].append(raw_data[path][grid]["value"])
        return data
    
    def stop(self):
        if self.grid_settings["demod1"]["active"]: self.UHFLI.daqM1.stop()
    
#%%
if __name__ == "__main__":
    from time import sleep
    import qkit
    qkit.start()
    UHFLI = qkit.instruments.create("UHFLI", "ZI_UHFLI_SemiCon", device_id = "dev2587")
    backend = ZI_UHFLI_backend(UHFLI)
    print(backend.demod1_get_sample_rate())
    backend.demod1_set_measurement_count(50)
    backend.demod1_set_sample_count(75)
    backend.demod1_set_averages(10)
    print("The number of samples to acquire by the daq module: ", UHFLI.daqM1.get_daqM_grid_num_samples())
    print("The number of measurements to acquire by the daq module: ", UHFLI.daqM1.get_daqM_grid_num_measurements())
    print("The number of grids to acquire by the daq module: ", UHFLI.daqM1.get_daqM_grid_num())
    #%%
    backend.demod1_activate()
    backend.arm()
    while not backend.finished():
        sleep(0.1)
        data = backend.read()
        print(data)
    print(data["demod1"]["x"].ndim)