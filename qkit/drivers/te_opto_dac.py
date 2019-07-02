from qkit.core.instrument_base import Instrument
import instruments
import types
import logging
import numpy as np
from time import sleep

class te_opto_dac(Instrument):
    '''
        This is the instrument driver for optically decoupled 
        Tunnelelektronik single- and triple channel DACs
    '''

    def __init__(self, name, source=None, channel = 0, dachannels = 1, inverted = False):
		Instrument.__init__(self, name, tags=['virtual'])
		self._instruments = instruments.get_instruments()
		self._source= self._instruments.get(source)
		self._channel = channel # channel = 'portn/linem'
		self._nchannels = dachannels
		self._values = np.zeros((dachannels))
		self._inverted = inverted
        
		# Add parameters        
		self.add_parameter('value', type=float,
			channels=(1, dachannels), channel_prefix = 'ch%d_',
			flags=Instrument.FLAG_SET, units='V')
		self.add_parameter('invert', type=bool,
			flags=Instrument.FLAG_SET, units='')
		#self.add_parameter('binary', type=int,
		#	flags=Instrument.FLAG_SET, units='')

    def get_all(self):
        pass
        
    def do_set_value(self, val, channel):
        ''' 
            output a float between -10. and 10. on the dac
        '''
        if((val > 10) || (val < -10)):
            raise ValueError('Valid outputs of TE DACs are be between -10V and +10V.')
        val = np.int16(min(2**15-1, max(-2**15, val/10*1**15)))
        self.do_set_binary(val, channel)
    def do_set_binary(self, val, channel):
        '''
            pass a 16bit signed integer sample to the dac
            
            format:
            000000000 --- (01x * 16 bits)) * nchannels --- 000000000
            where x are the inverted bits of the input
            
            original matlab code:
            disc_val=uint16(round(inp/10*65536));
            ofs=10
            a(2+ofs:3:16*3+ofs)=1-bitget(disc_val,16:-1:1); # split ~disc_val into bits
            a(1+ofs:3:16*3+ofs)=ones(1,16);
            a=[a zeros(1,9)];
        '''
        self._values[channel] = val

        # unpack bits
        bits = np.zeros((9), np.bool)
        for val in self._values:
            number_bits = [bool(np.int16(val) & 1<<n) for n in range(16, 0, -1)]
            code_bits = np.zeros(3*16, np.bool)
            code_bits[1:1+3*16:3] = np.ones((16), np.bool)
            code_bits[2:2+3*16:3] = number_bits
            bits = np.append(bits, code_bits)
        bits = np.append(bits, np.zeros((9), np.bool))
        if(self._inverted): bits = ~bits

        # push bits to device; matlab code outputs stream of bits at 19kS/s
        # variant 1: bit-bang
        # variant 2: hardware streaming
        self._source.digital_stream(self._channel, np.atleast_2d(bits).transpose(), rate = 19e3)
        #self._source.digital_out(self._channel, bla)
