# -*- coding: utf-8 -*-
# Micha Wildermuth, micha.wildermuth@kit.edu 2020

from qkit.core.instrument_base import Instrument
import time


class quartz_dummy(Instrument)::
    '''
    This is a driver for a dummy quartz oscillator as used for sputter deposition monitoring qkit.services.qdepokit.sdi.

    Usage:
        Initialize with
        <name> = qkit.instruments.create('<name>', 'mfc_dummy')
    '''
    def __init__(self, name):
        self.__name__ = __name__
        Instrument.__init__(self, name, tags=['virtual'])
        self.t0 = None
        self.add_function('get_rate')
        self.add_function('get_thickness')


    def get_rate(self, nm=True):
        rate = 1.
        return rate

    def get_thickness(self, nm=True):
        if self.t0 is None:
            self.t0 = time.time()
        return self.get_rate()*(time.time()-self.t0)