#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep  3 19:50:44 2021

@author: lr1740
"""
from abc import ABC, abstractmethod

class MA_backend_base(ABC):
    
    @abstractmethod
    def run():
        pass
    
    @abstractmethod
    def stop():
        pass