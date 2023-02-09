#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep  1 13:33:53 2021

@author: lr1740
"""
from abc import ABC, abstractmethod

class RO_backend_base(ABC):
    
    @abstractmethod
    def __init__(self):
        self._registered_measurements = {}
        
    @abstractmethod
    def arm():
        pass
    
    @abstractmethod
    def finished():
        pass
    
    @abstractmethod
    def read():
        pass
    @abstractmethod
    def stop():
        pass
    
    def __str__(self):
        return f"{self.__class__.__name__}"
    
    def register_measurement(self, name, unit, nodes):
        if type(name) != str:
            raise TypeError(f"{name} is not a valid experiment name. The experiment name must be a string.")
        if type(unit) != str:
            raise TypeError(f"{unit} is not a valid unit. The unit must be a string.")
        if type(nodes) != list:
            raise TypeError(f"{nodes} are not valid data nodes. The data nodes must be a list of strings.")
        else:
            for node in nodes:
                if type(node) != str:
                    raise TypeError(f"{node} is not a valid data node. A data node must be a string.")
        
        not_implemented = ""
        if not getattr(self, f"{name}_get_sample_rate", None):
            not_implemented += f"{name}_get_sample_rate()"
            
        if not getattr(self, f"{name}_set_measurement_count", None):
            not_implemented += f"\n{name}_set_measurement_count()"
            
        if not getattr(self, f"{name}_set_sample_count", None):
            not_implemented += f"\n{name}_set_sample_count()"
        
        if not getattr(self, f"{name}_set_averages", None):
            not_implemented += f"\n{name}_set_averages()"
            
        if not getattr(self, f"{name}_activate", None):
            not_implemented += f"\n{name}_activate()"
            
        if not getattr(self, f"{name}_deactivate", None):
            not_implemented += f"\n{name}_deactivate()"
            
        if not_implemented:
            raise NotImplementedError(f"{name} if missing the following methods:\n" + not_implemented)
        
        self._registered_measurements[name] = {"unit" : unit}
        self._registered_measurements[name].update({"data_nodes" : nodes})
        
if __name__ == "__main__":
    class My_Backend(RO_backend_base):        
        def __init__(self):
            self.register_measurement("M1")
            
        def M1_get_sample_rate():
            pass
        def M1_set_measurement_count():
            pass
        def M1_set_sample_count():
            pass
        def M1_set_averages():
            pass
        def M1_set_data_nodes():
            pass
        def M1_activate():
            pass
        def M1_deactivate():
            pass
        def arm():
            pass
        def finished():
            pass
        def read():
            pass
        def stop():
            pass
    Backend = My_Backend()
            
        