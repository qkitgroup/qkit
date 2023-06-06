# -*- coding: utf-8 -*-
# Micha Wildermuth, micha.wildermuth@kit.edu 2020

from qkit.core.instrument_base import Instrument
import time


class ohmmeter_dummy(Instrument)::
    '''
    This is a driver for a dummy ohmmeter as used for sputter deposition monitoring qkit.services.qdepokit.sdi.

    Usage:
        Initialize with
        <name> = qkit.instruments.create('<name>', 'mfc_dummy')
    '''
    def __init__(self, name):
        self.__name__ = __name__
        Instrument.__init__(self, name, tags=['virtual'])
        self.t0 = None
        self.add_parameter('measure_4W', type=bool,
            flags=Instrument.FLAG_GETSET)

    def do_set_measure_4W(self, status = False):
        pass

    def do_get_measure_4W(self):
        return None

    def get_resistance(self):
        if self.t0 is None:
            self.t0 = time.time()
        return 1.e9/(time.time() - self.t0 + 1e-20)