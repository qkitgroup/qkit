from qkit.core.instrument_base import Instrument
import numpy as np

class virtual_voltage_source(Instrument):

    def __init__(self, name):
        Instrument.__init__(self, name, tags=['virtual'])
        
        self.add_parameter('attenuation', type=float,
            flags=self.FLAG_GETSET, units='dB')
        
        self.add_parameter('output_voltage_in_V', type=float,
            flags=self.FLAG_GETSET,
            channels=(1,200), channel_prefix='gate%d_',
            minval=-10, maxval=10, units='V',
            tags=['sweep'])
        
        self._attn = 0
        self._gate_votlages = np.zeros(200)

    def _do_set_attenuation(self, attn):
        self._attn = attn

    def _do_get_attenuation(self):
        return self._attn
    
    def _do_set_output_voltage_in_V(self, newV, channel):
        self._gate_votlages[channel-1] = newV
    
    def _do_get_output_voltage_in_V(self, channel):
        return self._gate_votlages[channel-1]

if __name__ == "__main__":
    import qkit
    qkit.start()
    vsource = qkit.instruments.create("vsource", "virtual_voltage_source")
    vsource.set_attenuation(2)