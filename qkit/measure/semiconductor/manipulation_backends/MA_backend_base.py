#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep  3 19:50:44 2021

@author: lr1740
"""
from abc import ABC, abstractmethod

class MA_backend_base(ABC):
    _registered_channels = {}
    
    @abstractmethod
    def run():
        pass
    
    @abstractmethod
    def stop():
        pass
    
    @abstractmethod
    def load_waveform():
        pass
    
    def register_channel(self, name, unit):
        if type(name) != str:
            raise TypeError(f"{name} is not a valid channel name. The channel name must be a string.")
        if type(unit) != str:
            raise TypeError(f"{unit} is not a valid unit. The unit must be a string.")
            
        not_implemented = ""
        if not getattr(self, f"{name}_get_sample_rate", None):
            not_implemented += f"{name}_get_sample_rate()"
            
        if not_implemented:
            raise NotImplementedError(f"{name} is missing the following methods:\n" + not_implemented)
    
        self._registered_measurements[name] = {"unit" : unit}

