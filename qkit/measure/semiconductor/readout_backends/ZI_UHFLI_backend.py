#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep  7 17:57:44 2021

@author: lr1740
"""
from RO_backend_base import RO_backend_base
from qkit.drivers import ZI_UHFLI_SemiCon

class ZI_UHFLI_backend(RO_backend_base):
    def arm():
        pass
    def finished():
        pass
    def read():
        pass
    def stop():
        pass
    

if __name__ == "__main__":
    backend = ZI_UHFLI_backend()
