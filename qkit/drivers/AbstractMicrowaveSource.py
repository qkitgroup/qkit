import logging
from abc import ABCMeta, abstractmethod

from qkit.core.instrument_base import Instrument


class AbstractMicrowaveSource(Instrument, metaclass=ABCMeta):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Implement parameters
        self.add_parameter('power',
                           flags=Instrument.FLAG_GETSET, units='dBm', minval=-135, maxval=30, offset=True, type=float)
        # self.add_parameter('phase',
        #    flags=Instrument.FLAG_GETSET, units='rad', minval=-numpy.pi, maxval=numpy.pi, type=types.FloatType)
        self.add_parameter('frequency',
                           flags=Instrument.FLAG_GETSET, units='Hz', minval=9e3, maxval=20e9, type=float)
        self.add_parameter('status',
                           flags=Instrument.FLAG_GETSET, type=bool)

        self.add_function('reset')
        self.add_function('get_all')

    def get_all(self):
        '''
        Reads all implemented parameters from the instrument,
        and updates the wrapper.

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : get all')
        self.get_power()
        #self.get_phase()
        self.get_frequency()
        self.get_status()

    @abstractmethod
    def reset(self):
        '''
        Resets the instrument to default values

        Input:
            None

        Output:
            None
        '''
        pass

    @abstractmethod
    def do_get_power(self):
        '''
        Reads the power of the signal from the instrument

        Input:
            None

        Output:
            ampl (float) : power in dBm
        '''
        pass

    @abstractmethod
    def do_set_power(self, amp):
        '''
        Set the power of the signal

        Input:
            amp (float) : power in dBm

        Output:
            None
        '''
        pass

    @abstractmethod
    def do_get_frequency(self):
        '''
        Reads the frequency of the signal from the instrument

        Input:
            None

        Output:
            freq (float) : Frequency in Hz
        '''
        pass

    @abstractmethod
    def do_set_frequency(self, freq):
        '''
        Set the frequency of the instrument

        Input:
            freq (float) : Frequency in Hz

        Output:
            None
        '''
        pass

    @abstractmethod
    def do_get_status(self):
        '''
        Reads the output status from the instrument

        Input:
            None

        Output:
            status (string) : 'On' or 'Off'
        '''
        pass

    @abstractmethod
    def do_set_status(self, status):
        '''
        Set the output status of the instrument

        Input:
            status (bool) : True: 'On' or False: 'Off'

        Output:
            None
        '''
        pass

    def off(self):
        '''
        Set status to 'off'

        Input:
            None

        Output:
            None
        '''
        self.set_status(False)

    def on(self):
        '''
        Set status to 'on'

        Input:
            None

        Output:
            None
        '''
        self.set_status(True)
