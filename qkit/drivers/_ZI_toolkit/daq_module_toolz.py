#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 15 12:17:39 2021

@author: lr1740
"""
import logging
from iterools import count

class daq_module_toolz(Instrument):
    _daq_ids = count(0)
    def __init__(self, dataAcquisitionModule, device_id):
        logging.info(__name__ + ' : Initializing daq tools')
        Instrument.__init__(self, name, tags=['virtual', "lock-in amplifier"])
        self.daqM = dataAcquisitionModule
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
        
        self.add_parameter("daqM_sample_path", type = str,
                           flags = self.FLAG_SET)
        
        self.add_parameter("daqM_grid_mode", type = str,
                           flags = self.FLAG_GETSET)
        
        self.add_parameter("daqM_grid_averages", type = int, #are called repetitions in ZI
                           flags = self.FLAG_GETSET,
                           minval = 1)
        
        self.add_parameter("daqM_grid_num_samples", type = int,
                           flags = self.FLAG_GETSET,
                           minval = 1)
        
        self.add_parameter("daqM_grid_num_measurements", type = int,
                          flags = self.FLAG_GETSET,
                          minval = 1)
        
        self.add_parameter("daqM_grid_direction", type = str,
                           flags = self.FLAG_GETSET)
        
        self.add_parameter("daqM_grid_num", type = int,
                           flags = self.FLAG_GETSET,
                           minval = 1)
        
        #Tell qkit which functions are intended for public use
        self.add_function("reset_daqM_signal_paths")
        
        #public use functions
    def reset_daqM_signal_paths(self):
        self.daqM.unsubscribe("*")
    
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
        logging.debug(__name__ + ' : setting sample path of the daqM to %s' % (newpath))
        self.daqM.subscribe(newpath)
    
    
    def _do_set_daqM_grid_mode(self, newmode):
        logging.debug(__name__ + ' : setting the grid mode of the daqM to %s' % (newmode))
        try:
            self.daqM.set('grid/mode', self._daqM_grid_mode_dict[newmode])
        except:
            logging.warning("You entered an invalid daqM-grid mode, puny human.")
    
    def _do_get_daqM_grid_mode(self):
        logging.debug(__name__ + ' : getting trigger mode of daqM')
        return self._inv_daqM_grid_mode_dict[self.daqM.getInt('grid/mode')]
    
    
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
    UHFLI_test = qkit.instruments.create("UHFLI_test", "ZI_UHFLI_SemiCon", device_id = "dev2587")
    #%%
    print("Trigger mode:")
    UHFLI_test.set_daqM_trigger_mode("HW_trigger")
    print(UHFLI_test.get_daqM_trigger_mode())
    
    print("Trigger path:")
    UHFLI_test.set_daqM_trigger_path("/dev2587/demods/0/sample.x")
    print(UHFLI_test.get_daqM_trigger_path())
    
    print("Trigger edge:")
    UHFLI_test.set_daqM_trigger_edge("falling")
    print(UHFLI_test.get_daqM_trigger_edge())
    
    print("Trigger duration:")
    UHFLI_test.set_daqM_trigger_duration(1e-3)
    print(UHFLI_test.get_daqM_trigger_duration())
    
    print("Trigger delay:")
    UHFLI_test.set_daqM_trigger_delay(-1e-3)
    print(UHFLI_test.get_daqM_trigger_delay())
    
    print("Holdoff time:")
    UHFLI_test.set_daqM_trigger_holdoff_time(1e-3)
    print(UHFLI_test.get_daqM_trigger_holdoff_time())
    
    print("Holdoff count:")
    UHFLI_test.set_daqM_trigger_holdoff_count(1)
    print(UHFLI_test.get_daqM_trigger_holdoff_count())
    
    UHFLI_test.set_daqM_sample_path("/dev2587/demods/0/sample.r")
    #print(UHFLI_test.get_daqM_sample_path()) #It seems there is no way to get this
    
    print("Grid mode:")
    UHFLI_test.set_daqM_grid_mode("exact")
    print(UHFLI_test.get_daqM_grid_mode())
    
    print("Grid averages:")
    UHFLI_test.set_daqM_grid_averages(666)
    print(UHFLI_test.get_daqM_grid_averages())
    
    print("Grid sample num:")
    UHFLI_test.set_daqM_grid_num_samples(69)
    print(UHFLI_test.get_daqM_grid_num_samples())
    
    print("Grid meas num:")
    UHFLI_test.set_daqM_grid_num_measurements(13)
    print(UHFLI_test.get_daqM_grid_num_measurements())
    
    print("Grid direction:")
    UHFLI_test.set_daqM_grid_direction("alternating")
    print(UHFLI_test.get_daqM_grid_direction())
    
    print("Grid num:")
    UHFLI_test.set_daqM_grid_num(1414)
    print(UHFLI_test.get_daqM_grid_num())
    
    UHFLI_test.reset_daqM_signal_paths()