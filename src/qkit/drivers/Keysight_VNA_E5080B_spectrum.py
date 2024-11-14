

import qkit
from qkit.core.instrument_base import Instrument
from qkit import visa
import logging
import numpy as np
import Keysight_VNA_E5080B


class Keysight_VNA_E5080B_spectrum(Keysight_VNA_E5080B.Keysight_VNA_E5080B):
    def __init__(self, name, address, channel_index=1):
        super().__init__(name, address, channel_index)
        
        self.add_parameter('measurement_class', type=str,
            flags=Instrument.FLAG_GET)
        
        self.add_parameter('signal_format', type=int,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=1)
        self.signal_formats = {0: 'MLIN', 1: 'MLOG'}
        self.inv_signal_formats = {val.upper(): key for key, val in self.signal_formats.items()}
        
        self.add_parameter('signal_unit', type=int,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=3)
        self.lin_units = {0: 'W', 1: 'V', 2: 'A'}
        self.inv_lin_units = {val.upper(): key for key, val in self.lin_units.items()}
        self.log_units =  {0: 'dBm', 1: 'dBmV', 2: 'dBuV', 3: 'dBmA'}
        self.inv_log_units = {val.upper(): key for key, val in self.log_units.items()}
        
        # Implement functions
        self.add_function('get_trace_name')
        self.add_function('get_y_unit')
        self.add_function('get_active_traces')
        self.add_function('get_tracedata')
        
    
    def write(self, cmd):
        self._visainstrument.write(cmd)
    
    def query(self, cmd):
        return self._visainstrument.query(cmd).strip('\n')
    
    def do_get_measurement_class(self):
        # corresponding command: SENSe<cnum>:CLASs:NAME?
        return self._visainstrument.query('SENS:CLAS:NAME?').strip().strip('"')
    
    def do_set_signal_format(self, signal_format):
        """
        Sets the signal format
        
        signal_format: int
            0: linear amplitude
            1: logarithmic amplitude
        """
        self.write('CALC:MEAS:FORM {:s}'.format(self.signal_formats[signal_format]))
    
    def do_get_signal_format(self):
        """
        Gets the signal format
        
        signal_format: int
            0: linear amplitude
            1: logarithmic amplitude
        """
        ans = self.query('CALC:MEAS:FORM?').strip()
        return self.inv_signal_formats[ans]
    
    def do_set_signal_unit(self, unit, signal_format=None):
        """
        Sets the signal unit
        
        unit: int
            for linear format
                0: Watt
                1: Volt
                2: Ampere
            for logarithmic format
                0: dBm
                1: dBmV
                2: dBuV
                3: dBmA
        """
        if signal_format is None:
            signal_format = self.get_signal_format()
        else:
            self.set_signal_format(signal_format)
        self.write('CALC:MEAS:FORM:UNIT {:s}, {:s}'.format(self.signal_formats[signal_format], {0: self.lin_units, 1: self.log_units}[signal_format][unit]))
            
    def do_get_signal_unit(self):
        """
        Gets the signal unit
        
        unit: int
            for linear format
                0: Watt
                1: Volt
                2: Ampere
            for logarithmic format
                0: dBm
                1: dBmV
                2: dBuV
                3: dBmA
        """
        signal_format = self.get_signal_format()
        ans = self.query('CALC:MEAS:FORM:UNIT? {:s}'.format(self.signal_formats[signal_format]))
        return {0: self.inv_lin_units, 1: self.inv_log_units}[signal_format][ans]
    
    def get_trace_name(self, trace=1):
        # corresponding command: CALCulate<cnum>:MEASure<mnum>:FORMat:UNIT <dataFormat>, <units>
        return 'amplitude'
    
    def get_y_unit(self, trace=1):
        # corresponding command: CALCulate<cnum>:MEASure<mnum>:FORMat:UNIT <dataFormat>, <units>
        signal_format = self.get_signal_format()
        unit = self.get_signal_unit()
        return {0: self.lin_units, 1: self.log_units}[signal_format][unit]
    
    def get_active_traces(self):
        # corresponding command: CALCulate<cnum>:PARameter:COUNt <value>
        return int(self.query('CALC:PAR:COUN?'))
        
    def get_tracedata(self, trace=1):
        if self.get_measurement_class() == 'Spectrum Analyzer':
            self._visainstrument.write('FORM:DATA REAL,32')
            self._visainstrument.write('FORM:BORD SWAPPED') #SWAPPED
            data = self._visainstrument.query_binary_values('CALC%i:MEAS%i:DATA:SDAT?' %( self._ci, trace))
            return np.array(data)[::2]
        else:
            raise ValueError('Keysight_VNA_E5080B_spectrum: Set the measurement class to the spectrum analyzer mode.')
