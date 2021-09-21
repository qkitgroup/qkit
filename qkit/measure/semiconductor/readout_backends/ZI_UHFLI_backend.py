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
        self.register_measurement("demod1", "V", ["x", "y", "r", "theta"])
        
    def _setup_grid1(self):
        self.UHFLI.daqM1.set_daqM_trigger_mode("HW_trigger")
        self.UHFLI.daqM1.set_daqM_trigger_path("/{self.UHFLI._decive_id}/demods/0/sample.TRIGIN1")
    def demod1_get_sample_rate(self):
        return self.UHFLI.get_dem1_sample_rate() # is returned in Hz
        
    def demod1_set_measurement_count(self, meas_num):
        self.UHFLI.daqM1.set_daqM_grid_num_measurements(meas_num)
    
    def demod1_set_sample_count(self, sample_num):
        self.UHFLI.daqM1.set_daqM_grid_num_samples(sample_num)
    
    def demod1_set_averages(self, grid_num):
        self.UHFLI.daqM1.set_daqM_grid_num(grid_num)
    
    def demod1_activate(self):
        pass
    def demod1_deactivate(self):
        pass
    def arm():
        pass
    def finished():
        pass
    def read():
        pass
    def stop():
        pass
    

if __name__ == "__main__":
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