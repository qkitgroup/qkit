#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 15 12:17:39 2021

@author: lr1740
"""

import logging
from itertools import count
from qkit.core.instrument_base import Instrument

class ZI_DAQ_module(Instrument):
    _daqM_ids = count(0)
    def __init__(self, name, unmanaged_daq_module, device_id):
        self.daqM_id = next(self._daqM_ids)
        logging.info(__name__ + ' : Initializing daq tools for daqM %d of device %s ' % (self.daqM_id, device_id))
        Instrument.__init__(self, name, tags=['virtual', "data acquisition module"])
        
        self.daqM = unmanaged_daq_module
        self.daqM.set("device", device_id)
        
        self._daqM_trigger_mode_dict = {"continuous" : 0,
                                        "edge_trigger" : 1,
                                        "digital_trigger" : 2,
                                        "pulse_trigger" : 3,
                                        "tracking_trigger" : 4,
                                        "HW_trigger" : 6,
                                        "tracking_pulse_trigger" : 7,
                                        "event_count_trigger" : 8}
        
        self._inv_daqM_trigger_mode_dict = {v: k for k, v in self._daqM_trigger_mode_dict.items()}
        
        
        self._daqM_trigger_edge_dict = {"rising" : 1,
                                        "falling" : 2,
                                        "both" : 3}
        
        self._inv_daqM_trigger_edge_dict = {v: k for k, v in self._daqM_trigger_edge_dict.items()}
        
        
        self._daqM_grid_mode_dict = {"nearest" : 1,
                                     "linear" : 2,
                                     "exact" : 4}
        
        self._inv_daqM_grid_mode_dict = {v: k for k, v in self._daqM_grid_mode_dict.items()}
         
        
        self._daqM_grid_direction_dict = {"forward" : 0,
                                          "backward" : 1,
                                          "alternating" : 2}
        
        self._inv_daqM_grid_direction_dict = {v: k for k, v in self._daqM_grid_direction_dict.items()}
        
        
        
        self.add_parameter("daqM_trigger_mode", type = str,
                           flags = self.FLAG_GETSET)
        
        self.add_parameter("daqM_trigger_path", type = str,
                           flags = self.FLAG_GETSET)
        
        self.add_parameter("daqM_trigger_edge", type = str,
                           flags = self.FLAG_GETSET)
        
        self.add_parameter("daqM_trigger_duration", type = float,
                           flags = self.FLAG_GETSET,
                           minval = 0,
                           units = "s")
        
        self.add_parameter("daqM_trigger_delay", type = float,
                           flags = self.FLAG_GETSET,
                           units = "s")
        
        self.add_parameter("daqM_trigger_holdoff_time", type = float,
                           flags = self.FLAG_GETSET,
                           units = "s")
        
        self.add_parameter("daqM_trigger_holdoff_count", type = int,
                           flags = self.FLAG_GETSET,
                           minval = 0)
        
        self.add_parameter("daqM_sample_path", type = list,
                          flags = self.FLAG_SET | self.FLAG_SOFTGET)
        
        self.add_parameter("daqM_grid_mode", type = str,
                           flags = self.FLAG_GETSET)
        
        self.add_parameter("daqM_grid_averages", type = int, #are called repetitions in ZI
                           flags = self.FLAG_GETSET,
                           minval = 1)
        
        self.add_parameter("daqM_grid_num_samples", type = int,
                           flags = self.FLAG_GETSET,
                           minval = 2)
        
        self.add_parameter("daqM_grid_num_measurements", type = int,
                          flags = self.FLAG_GETSET,
                          minval = 2)
        
        self.add_parameter("daqM_grid_direction", type = str,
                           flags = self.FLAG_GETSET)
        
        self.add_parameter("daqM_grid_num", type = int,
                           flags = self.FLAG_GETSET,
                           minval = 1)
        
        #Tell qkit which functions are intended for public use
        self.add_function("read")
        self.add_function("execute")
        self.add_function("finished")
        self.add_function("stop")
        self.add_function("reset_daqM_sample_path")
        
        #public use functions       
    def read(self, return_flat_data_dict = True):
        return self.daqM.read(return_flat_data_dict)
    
    def execute(self):
        self.daqM.execute()
    
    def finished(self):
        return self.daqM.finished()
    
    def stop(self):
        self.daqM.finish()
    
    def reset_daqM_sample_path(self):
        logging.debug(__name__ + ' : removing all samples paths')
        self.daqM.unsubscribe("*")
    
        #sets and gets
    def _do_set_daqM_trigger_mode(self, newmode):
        logging.debug(__name__ + ' : setting trigger mode of the daqM to %s' % (newmode))
        try:
            self.daqM.set('type', self._daqM_trigger_mode_dict[newmode])
        except:
            logging.warning("You entered an invalid daqM-trigger mode, puny human.")
            
    def _do_get_daqM_trigger_mode(self):
        logging.debug(__name__ + ' : getting trigger mode of daqM')
        return self._inv_daqM_trigger_mode_dict[self.daqM.getInt('type')]
    
    
    def _do_set_daqM_trigger_path(self, newpath):
        logging.debug(__name__ + ' : setting trigger path of the daqM to %s' % (newpath))
        self.daqM.set("triggernode", newpath)
        
    def _do_get_daqM_trigger_path(self):
        logging.debug(__name__ + ' : getting trigger path of daqM')
        return self.daqM.get("triggernode")["triggernode"][0]
        
    
    def _do_set_daqM_trigger_edge(self, newmode):
        logging.debug(__name__ + ' : setting trigger edge of the daqM to %s' % (newmode))
        try:
            self.daqM.set('edge', self._daqM_trigger_edge_dict[newmode])
        except:
            logging.warning("You entered an invalid daqM-trigger edge, puny human.")
    
    def _do_get_daqM_trigger_edge(self):
        logging.debug(__name__ + ' : getting trigger mode of daqM')
        return self._inv_daqM_trigger_edge_dict[self.daqM.getInt('edge')]
    
    
    def _do_set_daqM_trigger_duration(self, newduration):
        logging.debug(__name__ + ' : setting trigger duration of the daqM to %s' % (newduration))
        self.daqM.set("duration", newduration)
        
    def _do_get_daqM_trigger_duration(self):
        logging.debug(__name__ + ' : getting trigger duration of the daqM')
        return self.daqM.getDouble("duration")
    
    
    def _do_set_daqM_trigger_delay(self, newduration):
        logging.debug(__name__ + ' : setting trigger delay of the daqM to %s' % (newduration))
        self.daqM.set("delay", newduration)
        
    def _do_get_daqM_trigger_delay(self):
        logging.debug(__name__ + ' : getting trigger delay of the daqM')
        return self.daqM.getDouble("delay")
    
    
    def _do_set_daqM_trigger_holdoff_time(self, newduration):
        logging.debug(__name__ + ' : setting trigger holdoff time of the daqM to %s' % (newduration))
        self.daqM.set("holdoff/time", newduration)
        
    def _do_get_daqM_trigger_holdoff_time(self):
        logging.debug(__name__ + ' : getting trigger holdoff time of the daqM')
        return self.daqM.getDouble("holdoff/time")
    
    
    def _do_set_daqM_trigger_holdoff_count(self, newcount):
        logging.debug(__name__ + ' : setting trigger holdoff count of the daqM to %s' % (newcount))
        self.daqM.set("holdoff/count", newcount)
        
    def _do_get_daqM_trigger_holdoff_count(self):
        logging.debug(__name__ + ' : getting trigger holdoff count of the daqM')
        return self.daqM.getInt("holdoff/count")
    
    
    def _do_set_daqM_sample_path(self, newpath):
        self.reset_daqM_sample_path()
        logging.debug(__name__ + ' : Adding the sample paths to %s' % (newpath))
        for element in newpath:
            self.daqM.subscribe(element)
    
    
    def _do_set_daqM_grid_mode(self, newmode):
        logging.debug(__name__ + ' : setting the grid mode of the daqM to %s' % (newmode))
        try:
            self.daqM.set('grid/mode', self._daqM_grid_mode_dict[newmode])
        except:
            logging.warning("You entered an invalid daqM-grid mode, puny human.")
    
    def _do_get_daqM_grid_mode(self):
        logging.debug(__name__ + ' : getting trigger mode of daqM')
        return self._inv_daqM_grid_mode_dict[self.daqM.getInt('grid/mode')]
    
    #u sure you are what you are? BUGFIX ME
    def _do_set_daqM_grid_averages(self, newavg):
        logging.debug(__name__ + ' : setting grid averages of the daqM to %s' % (newavg))
        self.daqM.set("grid/repetitions", newavg)
        
    def _do_get_daqM_grid_averages(self):
        logging.debug(__name__ + ' : getting the number of grid averages of the daqM')
        return self.daqM.getInt("grid/repetitions")
    
    
    def _do_set_daqM_grid_num_samples(self, newnum):
        logging.debug(__name__ + ' : setting the number of samples aqcuired during one trigger event of the daqM to %s' % (newnum))
        self.daqM.set("grid/cols", newnum)
        
    def _do_get_daqM_grid_num_samples(self):
        logging.debug(__name__ + ' : getting the number of samples aqcuired during one trigger event of the daqM')
        return self.daqM.getInt("grid/cols")
    

    def _do_set_daqM_grid_num_measurements(self, newnum):
        logging.debug(__name__ + ' : setting the number of trigger events to be acquired before the daqM finishes one grid to %s' % (newnum))
        self.daqM.set("grid/rows", newnum)
        
    def _do_get_daqM_grid_num_measurements(self):
        logging.debug(__name__ + ' : getting the number of trigger events to be acquired before the daqM finishes one grid')
        return self.daqM.getInt("grid/rows")
    
    
    def _do_set_daqM_grid_direction(self, newdir):
        logging.debug(__name__ + ' : setting grid direction of the daqM to %s' % (newdir))
        try:
            self.daqM.set('grid/direction', self._daqM_grid_direction_dict[newdir])
        except:
            logging.warning("You entered an invalid daqM-grid direction, puny human.")
            
    def _do_get_daqM_grid_direction(self):
        logging.debug(__name__ + ' : getting grid direction of the daqM')
        return self._inv_daqM_grid_direction_dict[self.daqM.getInt('grid/direction')]
    
    
    def _do_set_daqM_grid_num(self, newnum):
        logging.debug(__name__ + ' : setting the number of grids to acquire before the daqM finishes to %s' % (newnum))
        self.daqM.set("count", newnum)
        
    def _do_get_daqM_grid_num(self):
        logging.debug(__name__ + ' : getting the number of grids to acquire before the daqM finishes')
        return self.daqM.getInt("count")
#%%
if __name__ == "__main__":
    import qkit
    qkit.start()
    #%%
    UHFLI_test = qkit.instruments.create("UHFLI_test", "ZI_UHFLI", device_id = "dev2587")
    unmanaged_daq = UHFLI_test.create_daq_module()
    print(unmanaged_daq.getString("device"))
    daqM = qkit.instruments.create("name", "ZI_DAQ_module", unmanaged_daq_module = unmanaged_daq, device_id = "dev2587")
    #%%
    print("Trigger mode:")
    daqM.set_daqM_trigger_mode("HW_trigger")
    print(daqM.get_daqM_trigger_mode())
    
    print("Trigger path:")
    daqM.set_daqM_trigger_path("/dev2587/demods/0/sample.x")
    print(daqM.get_daqM_trigger_path())
    
    print("Trigger edge:")
    daqM.set_daqM_trigger_edge("falling")
    print(daqM.get_daqM_trigger_edge())
    
    print("Trigger duration:")
    daqM.set_daqM_trigger_duration(1e-3)
    print(daqM.get_daqM_trigger_duration())
    
    print("Trigger delay:")
    daqM.set_daqM_trigger_delay(-1e-3)
    print(daqM.get_daqM_trigger_delay())
    
    print("Holdoff time:")
    daqM.set_daqM_trigger_holdoff_time(1e-3)
    print(daqM.get_daqM_trigger_holdoff_time())
    
    print("Holdoff count:")
    daqM.set_daqM_trigger_holdoff_count(1)
    print(daqM.get_daqM_trigger_holdoff_count())
    
    daqM.set_daqM_sample_path(["/dev2587/demods/0/sample.r", "/dev2587/demods/0/sample.x"])
    print(daqM.get_daqM_sample_path())
    
    print("Grid mode:")
    daqM.set_daqM_grid_mode("exact")
    print(daqM.get_daqM_grid_mode())
    
    print("Grid averages:")
    daqM.set_daqM_grid_averages(666)
    print(daqM.get_daqM_grid_averages())
    
    print("Grid sample num:")
    daqM.set_daqM_grid_num_samples(69)
    print(daqM.get_daqM_grid_num_samples())
    
    print("Grid meas num:")
    daqM.set_daqM_grid_num_measurements(13)
    print(daqM.get_daqM_grid_num_measurements())
    
    print("Grid direction:")
    daqM.set_daqM_grid_direction("alternating")
    print(daqM.get_daqM_grid_direction())
    
    print("Grid num:")
    daqM.set_daqM_grid_num(1414)
    print(daqM.get_daqM_grid_num())
   
    daqM.reset_daqM_sample_path()
    print(daqM.read())