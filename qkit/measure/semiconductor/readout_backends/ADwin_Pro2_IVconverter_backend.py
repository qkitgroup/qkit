#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sept 2022

@author: oc0612
"""
from qkit.measure.semiconductor.readout_backends.RO_backend_base import RO_backend_base
from qkit.measure.semiconductor.readout_backends.ADwin_Pro2_backend import ADwin_Pro2_backend
import logging 
import sys 


class ADwin_Pro2_IVconverter_backend(RO_backend_base, ADwin_Pro2_backend):
    def __init__(self, ADwin_Pro2, IV_converter=1e8):
        super().__init__()
        self.register_measurement("input1", "A", ["amplitude"])
        self.IV_converter = IV_converter # in V/A


    def read(self):
        """This function is supposed to read out each average (full pulse train) so that spin-excite can show a live plot"""
        data = {}
        if self.ADwinPro2.check_error_triggered_readout():
                logging.error(__name__ + ': error flag thrown by ADwin.')
                sys.exit()
        elif self.finished_single_average():
            data["input1"] = {}
            data["input1"]["amplitude"] = self.ADwinPro2.read_triggered_readout() /self.IV_converter
        return data



