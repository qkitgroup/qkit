# -*- coding: utf-8 -*-
# Micha Wildermuth, micha.wildermuth@kit.edu 2020

from qkit.core.instrument_base import Instrument


class mfc_dummy(Instrument):
    '''
    This is a driver for a dummy mass flow controller as used for sputter deposition monitoring qkit.services.qdepokit.sdi.

    Usage:
        Initialize with
        <name> = qkit.instruments.create('<name>', 'mfc_dummy')
    '''
    def __init__(self, name):
        self.__name__ = __name__
        Instrument.__init__(self, name, tags=['virtual'])
        self.predef_channels = {'Ar': 0,
                                'ArO': 0,
                                'N': 0,
                                'O': 0}
        self.add_function('get_pressure')
        self.add_function('get_flow')

    def get_pressure(self):
        return 1

    def get_flow(self, channel=1):
        return channel