from qkit.core.instrument_base import Instrument

class virtual_step_attenuator(Instrument):
    '''
        this is real hardware connected to the experiment
        add one of those to automatically note its value in the measurement files
    '''

    def __init__(self, name):
        Instrument.__init__(self, name, tags=['virtual'])
        
        self.add_parameter('attenuation', type=float,
            flags=Instrument.FLAG_SET, units='dB')

    def do_set_attenuation(self, attn):
        self._attn = attn

    def do_get_attenuation(self):
        return self._attn
