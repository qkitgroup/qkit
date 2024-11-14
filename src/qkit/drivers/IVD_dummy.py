# -*- coding: utf-8 -*-
# Micha Wildermuth, micha.wildermuth@kit.edu 2020

from qkit.core.instrument_base import Instrument
import numpy as np

def get_IVC_JJ(x, Ic, Rn, SNR):
    sign = np.sign(x[-1] - x[0])
    return Rn * x * np.heaviside(np.abs(x) - Ic, int(sign > 0)) \
           + (np.heaviside(x, int(sign > 0)) - np.heaviside(x + sign * Ic, 0)) * Ic * Rn \
           + Ic * Rn / SNR * np.random.rand(x.size)


class IVD_dummy(Instrument):
    '''
    This is a driver for a dummy IV-Device as used for transport measurements with qkit.measure.transport.transport.transport.

    Usage:
        Initialize with
        <name> = qkit.instruments.create('<name>', 'IVD_dummy')
    '''
    def __init__(self, name):
        self.__name__ = __name__
        Instrument.__init__(self, name, tags=['virtual'])
        self.func = get_IVC_JJ
        self.args = ()
        self.kwargs = {'Ic': 1e-06, 'Rn': 0.5, 'SNR': 1e2}
    
    def set_status(self, status, channel=1):
        return

    def get_sweep_mode(self):
        return 0

    def get_sweep_channels(self):
        return (1, 2)
    
    def get_sweep_bias(self):
        return 0

    def set_func(self, func, *args, **kwargs):
        self.func, self.args, self.kwargs = func, args, kwargs

    def take_IV(self, sweep):
        start, stop, step, _ = sweep
        x = np.array([np.sign(val)*round(np.abs(val), -int(np.floor(np.log10(np.abs(step))))+1) for val in np.linspace(start, stop, int(round(np.abs(start-stop)/step+1)))])  # round to overcome missing precision of np.linspace
        y = self.func(x, *self.args, **self.kwargs)
        return x, y
    
    def get_parameters(self):
        return {}
    
    def get(self, param, **kwargs):
        return
