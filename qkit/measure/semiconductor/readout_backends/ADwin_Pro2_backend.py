#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sept 2022

@author: oc0612
"""
from qkit.measure.semiconductor.readout_backends.RO_backend_base import RO_backend_base
import logging 


class ADwin_Pro2_backend(RO_backend_base):
    def __init__(self, ADwin_Pro2):
        super().__init__()
        self.ADwinPro2 = ADwin_Pro2
        self._id = 1
        self.register_measurement("input1", "V", ["amplitude"])



    def input1_activate(self):
        """dummy as there is nothing to activate."""
        pass

    def input1_deactivate(self):
        """dummy as there is nothing to deactivate."""
        pass

    def input1_set_sample_rate(self, sample_rate=4e6):
        self.ADwinPro2.set_input1_sample_rate_triggered_readout(sample_rate)

    def input1_get_sample_rate(self):
        return self.ADwinPro2.get_input1_sample_rate_triggered_readout()
        
    def input1_set_measurement_count(self, meas_num):
        """meas_num gives the number of sequences in a pulse train"""
        self.ADwinPro2.set_input1_measurement_count_triggered_readout(meas_num)
    
    def input1_set_sample_count(self, sample_num):
        """sample_num gives the measured data points for each trigger"""
        #we set this here because it is at this point that the system knows how long a trigger event will be
        self.ADwinPro2.set_input1_sample_count_triggered_readout(sample_num)
    
    def input1_set_averages(self, grid_num):
        self.ADwinPro2.set_input1_repeats_triggered_readout(grid_num)
    
    def arm(self):
        self.ADwinPro2.initialize_triggered_readout()

    def finished(self):
        """returns "True" if full measurment is done."""
        return self.ADwinPro2.check_finished_triggered_readout()

    def finished_single_average(self):
        """returns "True" if one full measurement_count is done, so one average."""
        return self.ADwinPro2.check_finished_one_average_triggered_readout()

    def read(self):
        """This function is supposed to read out each average (full pulse train) so that spin-excite can show a live plot"""
        data = {}
        if self.ADwinPro2.check_error_triggered_readout():
                logging.error(__name__ + ': error flag thrown by ADwin.')
                sys.extit()
        elif self.finished_single_average():
            data["input1"] = {}
            data["input1"]["amplitude"] = self.ADwinPro2.read_triggered_readout()
        return data
    
    def stop(self):
        """stop the measurement but leave it initialized with the current counts of the parameters.
        To restart better self.initialize_triggered_readout()"""
        self.ADwinPro2.stop_triggered_readout()
    

#%%
if __name__ == "__main__":
    from time import sleep
    import qkit
    qkit.start()
    ADwin = qkit.instruments.create("ADwinPro2", "ZI_UHFLI_SemiCon", device_id = "dev2587")
    backend = ADwin_Pro2_backend(ADwinPro2)
    print(backend.input1_get_sample_rate())
    backend.input1_set_measurement_count(50)
    backend.input1_set_sample_count(75)
    backend.input1_set_averages(10)

