import qkit
from qkit.core.instrument_base import Instrument
import numpy as np
from time import sleep

class virtual_yokomagnet(Instrument):

    def __init__(self, name, source=None, channel = 0, stepsize = 2e-9, stepdelay=1):
        '''
            virtual magnet built upon yokogawa source
        '''
        Instrument.__init__(self, name, tags=['virtual'])
        self._instruments = qkit.instruments.get_instruments()
        self._source= self._instruments.get(source)
        self._channel = channel        
        # Add parameters        
        self.add_parameter('current', type=float,
            flags=Instrument.FLAG_GETSET, units='A')
        self.add_parameter('stepsize', type=float,
            flags=Instrument.FLAG_GETSET, units='A')        
        self.add_parameter('range', type=float,
            flags=Instrument.FLAG_GETSET, units='A')        
        self.add_parameter('stepdelay', type=float,
            flags=Instrument.FLAG_GETSET, units='ms')

        self._stepsize = stepsize
        self._stepdelay = stepdelay
        getattr(self._source, 'set_ch%d_sweep_mode'%channel)('fix')
        getattr(self._source, 'set_ch%d_source_mode'%channel)('curr')
        getattr(self._source, 'set_ch%d_sense_mode'%channel)('curr')

        self.get_all()

    def get_all(self):
        self.get_current()
        self.get_stepsize()
        self.get_stepdelay()
        self.get_range()

    def do_get_current(self):
        self._old = getattr(self._source, 'get_ch%d_level'%(self._channel))()
        return self._old

    def do_set_current( self, cur):
        if np.abs(cur) > self._range:
            raise ValueError('set_current(): given value exeeds the range of %f' % self._range)
        old = self._old
        stepsize =  self.get_stepsize()
        stepdelay = self.get_stepdelay()

        if np.abs(old-cur) <= stepsize:
            steps = np.array([])
        elif old > cur:				
            steps = np.arange(old,cur-stepsize,-stepsize)
        else:
            steps = np.arange(old,cur+stepsize,stepsize)
        steps = np.append(steps, cur)

        for step in steps:
            getattr(self._source, 'set_ch%d_level'%(self._channel))(step)
            sleep(stepdelay*1e-3)
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
        self._range = getattr(self._source, 'get_ch%d_source_range'%self._channel)()
        return self._range
    def do_set_range(self, val):
        getattr(self._source, 'set_ch%d_source_range'%self._channel)(val)
        self._do_get_range()
