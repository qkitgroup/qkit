import qkit
from qkit.core.instrument_base import Instrument
import numpy as np
from time import sleep

class virtual_magnet(Instrument):

    def __init__(self, name, source=None, channel = 0, stepsize = 2e-9, stepdelay=1, multiplier = 1, range = 1e-3, old = 0):
        Instrument.__init__(self, name, tags=['virtual'])
        self._instruments = qkit.instruments.get_instruments()
        self._source= self._instruments.get(source)
        self._channel = channel        
        # Add parameters        
        self.add_parameter('current', type=float,
            flags=Instrument.FLAG_SET, units='A')
        self.add_parameter('stepsize', type=float,
            flags=Instrument.FLAG_GETSET, units='A')        
        self.add_parameter('stepdelay', type=float,
            flags=Instrument.FLAG_GETSET, units='ms')
        self.add_parameter('multiplier', type=float,
            flags=Instrument.FLAG_GETSET, units='')
        self.add_parameter('range', type=float,
            flags=Instrument.FLAG_GETSET, units='A')            

        self._stepsize = stepsize
        self._stepdelay = stepdelay
        self._multiplier = multiplier
        self._range = range
        self._old = old;
        self.get_all()
    def get_all(self):
        self.get_stepsize()
        self.get_stepdelay()
        self.get_range()
        self.get_multiplier()

    def do_set_current( self, cur):
                if np.abs(cur) > 10*self._range:
                        raise ValueError('set_current(): given value exeeds the range of %f' % self._range)
        old = self._old
        stepsize =  self.get_stepsize()
        stepdelay = self.get_stepdelay()
        f = 1/(self._multiplier*self._range) #conversion factor from current to voltage
        if np.abs(old-cur) <= stepsize:
            steps = cur*f
        elif old > cur:                
            steps = np.arange(old*f,cur*f-stepsize*f,-stepsize*f)
        else:
            steps = np.arange(old*f,cur*f+stepsize*f,stepsize*f)
        if np.size(steps)>1:    
            for i in steps:
                self._source.set('ao%i' % self._channel, i )
                sleep(stepdelay*1e-3)
        self._source.set('ao%i' % self._channel,cur*f)    
        self._old = cur #Putting new value to the buffer        
        
    def do_get_stepsize(self):
        return self._stepsize
    def do_set_stepsize(self, val):
        self._stepsize = val
        
    def do_get_stepdelay(self):
        return self._stepdelay
    def do_set_stepdelay(self, val):
        self._stepdelay = val
        
    def do_get_range(self):
        return self._range
    def do_set_range(self, val):
        self._range = val     

    def do_get_multiplier(self):
        return self._multiplier
    def do_set_multiplier(self, val):
        self._multiplier = val              
