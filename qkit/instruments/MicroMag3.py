#
# MicroMag3+mbed 3d fluxgate magnetometer
#

from qkit.core.instrument_base import Instrument
from time import time, sleep
from qkit import visa
import types
import logging

class MicroMag3(Instrument):
    '''
    This driver communicates with Markus's custom fluxgate magnetometer setup.

    Usage:
    Initialize with
    <name> = instruments.create('name', 'MicroMag3', address='<Instrument address>')
    <Instrument address> = ASRL3::INSTR

    '''

    def __init__(self, name, address):
        '''

        Input:
            name (string)    : name of the instrument
            address (string) : instrument (serial port) address

        Output:
            None
        '''
        logging.debug(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])


        self._address = address
        self._visainstrument = visa.SerialInstrument(self._address, delay = 30e-3)
        self._values = {}
        self._visainstrument.stop_bits = 1  # This works only using pyvisa 1.4
        self.reset()

        #Add parameters
        self.add_parameter('b_raw', type=int,
            flags=Instrument.FLAG_GET)
        self.add_parameter('counts', type=int,
            flags=Instrument.FLAG_GETSET)

        # Add functions
        self.add_function('get_all')
        self.get_all()

    def get_all(self):
        '''
        Reads all implemented parameters from the instrument,
        and updates the wrapper.

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : reading all settings from instrument')
        self.reset()
        self.get_b_raw()
        self.get_counts()


    # Functions
    def _execute(self, message):
        '''
        Write a command to the device

        Input:
            message (str) : write command for the device

        Output:
            None
        '''
        logging.info(__name__ + ' : Send the following command to the device: %s' % message)
        try:
            result = self._visainstrument.ask('@%s%s' % (self._number, message))
        except:
            self.reset()
            
        if result.find('?') >= 0:
            print "Error: Command %s not recognized" % message
        else:
            return result

    def reset(self):
        '''
        Clear serial input buffer from stale values
        '''
        self._visainstrument.clear()

    def do_get_b_raw(self):
        '''
            get uncalibrated magnetic field
        '''
        raw_mag_str = self._visainstrument.ask(':MAG:RAW?')
        raw_mag_vect = map(int, raw_mag_str.split(" "))
        return raw_mag_vect

    def do_set_counts(self, value):
        '''
            set number of measurement cycles
            number must be 2^n, n = 5..13
            larger count results in longer measurement time, higher accuracy and lower maximum field
        '''
        if not value in [32, 64, 128, 256, 512, 1024, 2048, 4096]:
            raise ValueError('Number of counts must be a power of 2 between 32 and 4096.')
        self._visainstrument.write(':MAG:COUNT %d'%value)

    def do_get_counts(self):
        '''
            get number of measurement cycles
        '''
        return self._visainstrument.ask(':MAG:COUNT?')
