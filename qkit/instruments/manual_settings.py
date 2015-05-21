from instrument import Instrument
import types

class manual_settings(Instrument):

    def __init__(self, name):
        Instrument.__init__(self, name, tags=['virtual'])
        self.add_function('add_manual')

    def add_manual(self, name, type=types.FloatType, **kwargs):
        self.add_parameter(name, type=type,
                flags=Instrument.FLAG_SET|Instrument.FLAG_SOFTGET,
                set_func=lambda x: True,
                **kwargs)

