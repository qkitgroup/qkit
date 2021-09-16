#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep  3 19:50:44 2021

@author: lr1740
"""
from abc import ABC, abstractmethod

class MA_backend_base(ABC):
    _registered_channels = []
    
    @abstractmethod
    def run():
        pass
    
    @abstractmethod
    def stop():
        pass
    
    @abstractmethod
    def load_waveform():
        pass
    
    def register_channel(self, name):
        if type(name) != str:
            raise TypeError(f"{name} is not a valid channel name. The channel name must be a string.")
    
        self._registered_channels.append(name)
