# Keithley 2636A class, to perform the communication between the Wrapper and the device
# Hannes Rotzinger, hannes.rotzinger@kit.edu 2010
#
# based on the work by
# Pieter de Groot <pieterdegroot@gmail.com>, 2008
# Martijn Schaafsma <qtlab@mcschaafsma.nl>, 2008
#
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from instrument import Instrument
import visa
import time
import logging
import numpy
from sympy.functions.special.delta_functions import Heaviside

class Keithley(Instrument):
    '''
    This is the driver for the Keithley 2636A Source Meter

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Keithley_2636A', address='<GBIP address>, reset=<bool>')
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the Keithley_2636A, and communicates with the wrapper.

        Input:
          name (string)    : name of the instrument
          address (string) : GPIB address
          reset (bool)     : resets to default values, default=False
        '''
        logging.info(__name__ + ' : Initializing instrument Keithley_2636A')
        Instrument.__init__(self, name, tags=['physical'])

        # Add some global constants
        self._address = address
        self._visainstrument = visa.instrument(self._address)
        #self._visainstrument.write('beeper.beep(0.5,1000)')
        
        self._mode_types   = {0:'curr', 1:'volt', 2:'res', 3:'pow'}
        self._smu_function = {'volt':'v', 'curr':'i'}
        self._units = {'curr':'A', 'volt':'V'}
        self._measurement_modes = ['2-wire', '4-wire', 'calibration']
        self._avg_types = ['moving average', 'repeat average', 'median']
        
        self._dAdV = 1
        self._dVdA = 1
        self._amp = 1
        
        
        if (reset):
            self.reset()
        #else:
        #    self.get_all()

    
    
    
    def _write(self, msg):
        '''
        Sends a visa command <msg> using pyvisa
        
        Input:
            msg (str)
        Output:
            None
        '''
        return self._visainstrument.write(msg)
    
    
    def _ask(self, msg):
        '''
        Sends a visa command <msg> and returns the read answer <output> using pyvisa
        
        Input:
            msg (str)
        Output:
            answer (str)
        '''
        return self._visainstrument.ask('print(%s)' % msg).strip()
    
    
    def set_dAdV(self, val=1):
        '''
        Sets voltage-current conversion of external current source used for current bias to <val> (in A/V)
        
        Input:
            val (float):
        Output:
            None
        '''
        self._dAdV = val
    
    
    def get_dAdV(self):
        '''
        Gets voltage-current conversion of external current source used for current bias (in A/V)
        
        Input:
            None
        Output:
            val (float)
        '''
        return(self._dAdV)
    
    
    def set_dVdA(self, val=1):
        '''
        Sets current-voltage conversion of external voltage source used for voltage bias to <val> (in V/A)
        
        Input:
            val (float):
        Output:
            None
        '''
        self._dVdA = val
    
    
    def get_dVdA(self):
        '''
        Gets current-voltage conversion of external voltage source used for voltage bias (in V/A)
        
        Input:
            None
        Output:
            val (float)
        '''
        return(self._dVdA)
    
    
    def set_amp(self, val=1):
        '''
        Sets apmlification factor of external measurement setup to <val>
        
        Input:
            val (float)
        Output:
            None
        '''
        self._amp = val
    
    
    def get_amp(self):
        '''
        Gets apmlification factor of external measurement setup
        
        Input:
            None
        Output:
            val (float)
        '''
        return(self._amp)
    
    
    def set_measurement_mode(self, val, channel=1):
        '''
        Sets measurement mode (wiring system) of channel <channel> to <val>
        
        Input:
            channel (int) : 1 (default) | 2
            val (int)     : 0 (2-wire) | 1 (4-wire) | 3 (calibration)
        Output:
            None
        '''
        # Corresponding Command: smuX.sense = senseMode
        try:
            logging.debug(__name__ + ' : set measurement mode of channel %s to %i' % (chr(64+channel), val))
            self._write('smu%s.sense = %i' % (chr(96+channel), val))
        except AttributeError:
            logging.error(__name__ + ': invalid input: cannot set measurement mode of channel %s to %f' % (chr(64+channel), val))
    
    
    def get_measurement_mode(self, channel=1):
        '''
        Gets measurement mode (wiring system) of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            val (int)     : 0 (2-wire) | 1 (4-wire) | 3 (calibration)
        '''
        # Corresponding Command: senseMode= smuX.sense
        try:
            logging.debug(__name__ + ': get measurement mode of channel %s' % chr(64+channel))
            return int(float(self._ask('smu%s.sense' % chr(96+channel))))
        except ValueError:
            logging.error(__name__ + ': Measurement mode of channel %s not specified:' % chr(64+channel))
    
    
    def set_bias_mode(self, mode, channel=1):
        '''
        Sets bias mode of channel <channel> to <mode> regime.
        
        Input:
            mode (str)    : 'curr' | 'volt'
            channel (int) : 1 | 2
        Output:
            None
        '''
        # Corresponding Command: smuX.source.func = 0|1|smuX.OUTPUT_DCAMPS|smuX.OUTPUT_DCVOLTS
        mode = self._mode_types.keys()[self._mode_types.values().index(mode)]
        try:
            logging.debug(__name__ + ': Set bias mode of channel %s to %s' % (chr(64+channel), mode))
            self._write('smu%s.source.func = %s' % (chr(96+channel), mode))
        except AttributeError:
            logging.error(__name__ + ': invalid input: cannot set bias mode of channel %s to %s' % (chr(64+channel), mode))
    
    
    def get_bias_mode(self, channel=1):
        '''
        Gets bias mode <output> of channel <channel>
        
        Input:
            channel (int) : 1 | 2
        Output:
            mode (int)    : 'curr' | 'volt'
        '''
        # Corresponding Command: 0|1|smuX.OUTPUT_DCAMPS|smuX.OUTPUT_DCVOLTS = smuX.source.func
        try:
            logging.debug(__name__ + ': Get bias mode of channel %s' % chr(64+channel))
            return self._mode_types[int(float(self._ask('smu%s.source.func' % chr(96+channel))))]
        except ValueError:
            logging.error(__name__ + ': Bias mode of channel %s not specified:' % chr(64+channel))
    
    
    def set_sense_mode(self, mode, channel=1):
        '''
        Sets sense mode of channel <channel> to <mode> regime.
        
        Input:
            mode (str)    : 'curr' | 'volt' | 'res' | 'pow'
            channel (int) : 1 | 2
        Output:
            None
        '''
        # Corresponding Command: display.smuX.measure.func = 0|1|2|3|display.MEASURE_DCAMPS|display.MEASURE_DCVOLTS|display.MEASURE_OHMS|display.MEASURE_WATTS
        mode = self._mode_types.keys()[self._mode_types.values().index(mode)]
        try:
            logging.debug(__name__ + ': Set sense mode of channel %s to %s' % (chr(64+channel), mode))
            self._write('display.smu%s.measure.func = %s' % (chr(96+channel), mode))
        except AttributeError:
            logging.error(__name__ + ': invalid input: cannot set sense mode of channel %s to %s' % (chr(64+channel), mode))
    
    
    def get_sense_mode(self, channel=1):
        '''
        Gets sense mode <output> of channel <channel>
        
        Input:
            channel (int) : 1 | 2
        Output:
            mode (str)    : 'curr' | 'volt' | 'res' | 'pow'
        '''
        # Corresponding Command: 0|1|2|3|display.MEASURE_DCAMPS|display.MEASURE_DCVOLTS|display.MEASURE_OHMS|display.MEASURE_WATTS = display.smuX.measure.func
        try:
            logging.debug(__name__ + ': Get bias mode of channel %s' % chr(64+channel))
            return self._mode_types[int(float(self._ask('display.smu%s.measure.func' % chr(96+channel))))]
        except ValueError:
            logging.error(__name__ + ': Bias mode of channel %s not specified:' % chr(64+channel))
    
    
    def set_bias_range(self, val, channel=1):
        '''
        Sets bias range of channel <channel> to <val>
        
        Input:
            val (float)   : auto | 200mV | 2V | 20V | 200V | 100pA | 1nA | 10nA |100nA | 1uA | 10uA | 100uA | 1mA | 10mA | 100mA | 1 A | 1.5A
            channel (int) : 1 | 2
        Output:
            None
        '''
        # Corresponding Command: smuX.source.rangeY = rangeValue
        # FIXME: need to do highC mode option? --> **val_auto (p. 510 <-> 7-195)
        try:
            logging.debug(__name__ + ': Set bias range of channel %s to %f' % (chr(64+channel), val))
            if val == 'auto':
                self._write('smu%s.source.autorange%s = 1' % (chr(96+channel), self._smu_function[self.get_bias_mode(channel=channel)], val))
            else:
                self._write('smu%s.source.range%s = %f' % (chr(96+channel), self._smu_function[self.get_bias_mode(channel=channel)], val))
        except AttributeError:
            logging.error(__name__ + ': invalid input: cannot set bias range of channel %s to %f' % (chr(64+channel), val))
    
    
    def get_bias_range(self, channel=1):
        '''
        Gets bias mode <output> of channel <channel>
        
        Input:
            channel (int) : 1 | 2
        Output:
            val (float)   : 200mV | 2V | 20V | 200V | 100pA | 1nA | 10nA |100nA | 1uA | 10uA | 100uA | 1mA | 10mA | 100mA | 1 A | 1.5A
        '''
        # Corresponding Command: rangeValue = smuX.source.rangeY
        try:
            logging.debug(__name__ + ': Get bias range of channel %s' % chr(64+channel))
            return float(self._ask('smu%s.source.range%s' % (chr(96+channel), self._smu_function[self.get_bias_mode(channel=channel)])))
        except ValueError:
            logging.error(__name__ + ': Bias range of channel %s not specified:' % chr(64+channel))
    
    
    def set_sense_range(self, val, channel=1):
        '''
        Sets sense range of channel <channel> to <val>
        
        Input:
            val (float)   : auto | 200mV | 2V | 20V | 200V | 100pA | 1nA | 10nA |100nA | 1uA | 10uA | 100uA | 1mA | 10mA | 100mA | 1 A | 1.5A
            channel (int) : 1 | 2
        Output:
            None
        '''
        # Corresponding Command: smuX.measure.rangeY = rangeValue
        try:
            logging.debug(__name__ + ': Set sense range of channel %s to %f' % (chr(64+channel), val))
            if val == 'auto':
                self._write('smu%s.measure.autorange%s = 1' % (chr(96+channel), self._smu_function[self.get_sense_mode(channel=channel)], val))
            else:
                self._write('smu%s.measure.range%s = %f' % (chr(96+channel), self._smu_function[self.get_sense_mode(channel=channel)], val))
        except AttributeError:
            logging.error(__name__ + ': invalid input: cannot set sense range of channel %s to %f' % (chr(64+channel), val))
    
    
    def get_sense_range(self, channel=1):
        '''
        Gets sense mode <output> of channel <channel>
        
        Input:
            channel (int) : 1 | 2
        Output:
            val (float)   : 200mV | 2V | 20V | 200V | 100pA | 1nA | 10nA |100nA | 1uA | 10uA | 100uA | 1mA | 10mA | 100mA | 1 A | 1.5A
        '''
        # Corresponding Command: rangeValue = smuX.measure.rangeY
        try:
            logging.debug(__name__ + ': Get sense range of channel %s' % chr(64+channel))
            return float(self._ask('smu%s.measure.range%s' % (chr(96+channel), self._smu_function[self.get_sense_mode(channel=channel)])))
        except ValueError:
            logging.error(__name__ + ': Sense range of channel %s not specified:' % chr(64+channel))
    
    
    def set_bias_delay(self, val, channel=1):
        '''
        Sets bias delay of channel <channel> to <val>
        
        Input:
            val (float)   : -1 (auto) | 0 (off) | positive number
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        # Corresponding Command: smuX.source.delay = sDelay
        try:
            logging.debug(__name__ + ': Set bias delay of channel %s to %f' % (chr(64+channel), val))
            self._write('smu%s.source.delay = %f' % (chr(96+channel), val))
        except AttributeError:
            logging.error(__name__ + ': invalid input: cannot set bias delay of channel %s to %f' % (chr(64+channel), val))
    
    
    def get_bias_delay(self, channel=1):
        '''
        Gets bias delay of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            val (float)
        '''
        # Corresponding Command: sDelay= smuX.source.delay
        try:
            logging.debug(__name__ + ': Get bias delay of channel %s' % chr(64+channel))
            return float(self._ask('smu%s.source.delay' % chr(96+channel)))
        except ValueError:
            logging.error(__name__ + ': Bias delay of channel %s not specified:' % chr(64+channel))
    
    
    def set_sense_delay(self, val, factor=1, channel=1):
        '''
        Sets sense delay of channel <channel> to <val>
        
        Input:
            val (float)   : -1 (auto) | 0 (off) | positive number
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        # Corresponding Command: smuX.measure.delay = mDelay
        # Corresponding Command: smuX.measure.delayfactor = delayFactor
        try:
            logging.debug(__name__ + ': Set sense delay of channel %s to %f' % (chr(64+channel), val))
            self._write('smu%s.measure.delay = %f' % (chr(96+channel), val))
            if val == -1: self._write('smu%s.measure.delayfactor = %f' % (chr(96+channel), factor))
        except AttributeError:
            logging.error(__name__ + ': invalid input: cannot set sense delay of channel %s to %f' % (chr(64+channel), val))
    
    
    def get_sense_delay(self, channel=1):
        '''
        Gets sense delay of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            val (float)
        '''
        # Corresponding Command: mDelay= smuX.measure.delay
        try:
            logging.debug(__name__ + ': Get sense delay of channel %s' % chr(64+channel))
            return float(self._ask('smu%s.measure.delay' % chr(96+channel)))
        except ValueError:
            logging.error(__name__ + ': Sense delay of channel %s not specified:' % chr(64+channel))
    
    
    def set_sense_average(self, val, mode=0, channel=1):
        '''
        Sets sense average of channel <channel> to <val>
        
        Input:
            val (int)     : [1, 100]
            mode (str)    : 0 (moving average) (default) | 1 (repeat average) | 2 (median)
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        # Corresponding Command: smuX.measure.filter.count = filterCount
        # Corresponding Command: smuX.measure.filter.enable = filterState
        # Corresponding Command: smuX.measure.filter.type = filterType
        try:
            logging.debug(__name__ + ': Set sense average of channel %s to %i and mode %s' % (chr(64+channel), val, self._avg_types[mode]))
            status = bool(Heaviside(val-1-1e-10))
            self._write('smu%s.measure.filter.enable = %i' % (chr(96+channel), status))
            if status:
                self._write('smu%s.measure.filter.count = %i' % (chr(96+channel), val))
                self._write('smu%s.measure.filter.type = %i' % (chr(96+channel), mode))
        except AttributeError:
            logging.error(__name__ + ': invalid input: cannot set sense average of channel %s to %i and mode %s' % (chr(64+channel), val, self._avg_types[mode]))
    
    
    def get_sense_average(self, channel=1):
        '''
        Gets sense average of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            status (bool)
            val (int)
            mode (int)
        '''
        # Corresponding Command: filterCount = smuX.measure.filter.count
        # Corresponding Command: filterState = smuX.measure.filter.enable
        # Corresponding Command: filterType = smuX.measure.filter.type
        try:
            logging.debug(__name__ + ': Get sense average of channel %s' % chr(64+channel))
            status = bool(int(float(self._ask('smu%s.measure.filter.enable' % chr(96+channel)))))
            val = int(float(self._ask('smu%s.measure.filter.count' % chr(96+channel))))
            mode = int(float(self._ask('smu%s.measure.filter.type' % chr(96+channel))))
            return status, val, mode
        except ValueError:
            logging.error(__name__ + ': Sense average of channel %s not specified:' % chr(64+channel))
    
    
    def set_sense_nplc(self, val, channel=1):
        '''
        Sets sense integrarion time of channel <channel> with the <val>-fold of one power line cycle
        
        Input:
            channel (int) : 1 (default) | 2
            val (float)   : [0.001, 25]
        Output:
            None
        '''
        # Corresponding Command: smuX.measure.nplc = nplc
        try:
            logging.debug(__name__ + ': Set sense integrarion time of channel %s to %f PLC' % (chr(64+channel), val))
            self._write('smu%s.measure.nplc =  %f' % (chr(96+channel), val))
        except ValueError:
            logging.error(__name__ + ': Number of PLC of channel %s not specified:' % chr(64+channel))
    
    
    def get_sense_nplc(self, channel=1):
        '''
        Gets sense integrarion time of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            val (int)
        '''
        # Corresponding Command: nplc = smuX.measure.nplc
        try:
            logging.debug(__name__ + ': Get sense integrarion time of channel %s' % chr(64+channel))
            return float(self._ask('smu%s.measure.nplc' % chr(96+channel)))
        except ValueError:
            logging.error(__name__ + ': Number of PLC of channel %s not specified:' % chr(64+channel))
    
    
    def set_status(self, status, channel=1):
        '''
        Sets output status of channel <channel> to <status>
        
        Input:
            status (int)  : 0 (off) | 1 (on) | 2 (high Z)
            channel (int) : 1 | 2
        Output:
            None
        '''
        # Corresponding Command: smuX.source.output = sourceOutput
        try:
            logging.debug(__name__ + ': Set output status of channel %s to %i' % (chr(64+channel), status))
            self._write('smu%s.source.output = %i' % (chr(96+channel), status))
        except AttributeError:
            logging.error(__name__ + ': invalid input: cannot set output status of channel %s to %r' % (chr(64+channel), status))
    
    
    def get_status(self, channel=1):
        '''
        Gets output status of channel <channel>
        
        Input:
            channel (int) : 1 | 2
        Output:
            status (int)  : 0 (off) | 1 (on) | 2 (high Z)
        '''
        # Corresponding Command: sourceOutput = smuX.source.output
        try:
            logging.debug(__name__ + ': Get status of channel %s' % chr(64+channel))
            return int(float(self._ask('smu%s.source.output' % chr(96+channel))))
        except ValueError:
            logging.error(__name__ + ': Status of channel %s not specified:' % chr(64+channel))
    
    
    def set_bias_value(self, val, channel=1):
        '''
        Sets bias value of channel <channel> to value >val>
        
        Input:
            val (float)
            channel (int) : 1 | 2
        Output:
            None
        '''
        # Corresponding Command: smuX.source.levelY = sourceLevel
        try:
            logging.debug(__name__ + ' : Set bias value of channel %s to %f' % (chr(64+channel), val))
            self._write('smu%s.source.level%s = %f' % (chr(96+channel), self._smu_function[self.get_bias_mode(channel=channel)], val))
        except AttributeError:
            logging.error(__name__ + ': invalid input: cannot set bias value of channel %s to %f' % (chr(64+channel), val))
    
    
    def get_bias_value(self, channel=1):
        '''
        Gets bias value of channel <channel>
        
        Input:
            channel (int) : 1 | 2
        Output:
            val (float)
        '''
        # Corresponding Command: sourceLevel = smuX.source.levelY
        try:
            logging.debug(__name__ + ' : Get bias value of channel %s' % chr(64+channel))
            return float(self._ask('smu%s.source.level%s' % (chr(96+channel), self._smu_function[self.get_bias_mode(channel=channel)])))
        except ValueError:
            logging.error(__name__ + ': Cannot get bias value of channel %s:' % chr(64+channel))
    
    
    def get_sense_value(self, channel=1):
        '''
        Gets sense value of channel <channel>
        
        Input:
            channel (int) : 1 | 2
        Output:
            val (float)
        '''
        # Corresponding Command: reading= smuX.measure.Y()
        try:
            logging.debug(__name__ + ' : Get sense value of channel %s' % chr(64+channel))
            return float(self._ask('smu%s.measure.%s()' % (chr(96+channel), self._smu_function[self.get_sense_mode(channel=channel)])))
        except ValueError:
            logging.error(__name__ + ': Cannot get sense value of channel %s:' % chr(64+channel))
    
    
    def get_sense_value_iv(self, channel=1):
        '''
        Gets both current and voltage sense value of channel <channel>
        
        Input:
            channel (int) : 1 | 2
        Output:
            i_val (float)
            v_val (float)
        '''
        # Corresponding Command: iReading, vReading= smuX.measure.iv()
        try:
            logging.debug(__name__ + ' : Get current and voltage sense value of channel %s' % chr(64+channel))
            return numpy.array([float(val) for val in self._ask('smu%s.measure.iv()' % chr(96+channel)).split('\t')])
        except ValueError:
            logging.error(__name__ + ': Cannot get current and voltage sense value of channel %s:' % chr(64+channel))
    
    
    def set_voltage(self, val, channel=1):
        '''
        Sets voltage value of channel <channel> to <val>
        
        Input:
            val (float)
            channel (int) : 1 | 2
        Output:
            None
        '''
        # Corresponding Command: smuX.source.levelY = sourceLevel
        try:
            logging.debug(__name__ + ' : set voltage of channel %s to %s' % (channel, str(val)))
            self._write('smu%s.source.levelv = %s' % (chr(96+channel), val))
        except AttributeError:
            logging.error('invalid input: cannot set voltage of channel %s to %f' % (channel, val))
    
    
    def get_voltage(self, channel=1):
        '''
        Gets voltage value of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            val (float)
        '''
        # Corresponding Command: reading= smuX.measure.Y()
        try:
            logging.debug(__name__ + ' : get voltage of channel %s' % chr(64+channel))
            return float(self._ask('smu%s.measure.v()' % chr(96+channel)))
        except ValueError:
            logging.error('Cannot get voltage of channel %s:' % chr(64+channel))
    
    
    def set_current(self, val, channel=1):
        '''
        Sets current value of channel <channel> to <val>
        
        Input:
            val (float): arb.
            channel (int): 1 | 2
        Output:
            None
        '''
        # Corresponding Command: smuX.source.levelY = sourceLevel
        try:
            logging.debug(__name__ + ' : set current of channel %s to %s' % (channel, str(val)))
            self._write('smu%s.source.leveli = %s' % (chr(96+channel), val))
        except AttributeError:
            logging.error('invalid input: cannot set current of channel %s to %f' % (channel, val))
    
    
    def get_current(self, channel=1):
        '''
        Gets current value of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            val (float)
        '''
        # Corresponding Command: reading= smuX.measure.Y()
        try:
            logging.debug(__name__ + ' : get current of channel %s' % chr(64+channel))
            return float(self._ask('smu%s.measure.i()' % chr(96+channel)))
        except ValueError:
            logging.error('Cannot get current of channel %s:' % chr(64+channel))
    
    
    def ramp_bias(self, stop, step, step_time=0.1, channel=2):
        '''
        Ramps current of channel <channel> from recent value to <stop>
        
        Input:
            stop (float)
            step (float)
            step_time (float)
            channel (int)     : 1 | 2 (default)
        Output:
            None
        '''
        start = self.get_bias_value(channel=channel)
        if (stop < start): step = -step
        for I in numpy.arange(start, stop, step)+step:
            self.set_bias_value(I, channel=channel)
            time.sleep(step_time)
    
    
    def set_sweep_parameters(self, sweep, channel=1):
        '''
        Sets sweep parameters <sweep> and prepares yoko
        
        Input:
            sweep obj(float): start, stop, step
            channel (int): 1 | 2
        Output:
        '''
        # TODO what to do?
        print('need to do: set sweep parameters')
    
    
    def take_IV(self, channel=1):
        # TODO reading explained on page 525
    
        # Corresponding Command: smuX.trigger.initiate()
        # Corresponding Command: waitcomplete()
        # example: smua.source.limitv = 1
        #          SweepILinMeasureV(smua, 1e-3, 10e-3, 0.1, 10)
        #          printbuffer(1, 10, smua.nvbuffer1.readings)
    
        print('need to do: take IV')
    
    
    
    
    
    
    def is_end_of_sweep(self, channel=1):
        '''
        Gets event "Sweep Complete" of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            val (bool)    : True | False
        '''
        # Corresponding Command: eventID = smuX.trigger.SWEEP_COMPLETE_EVENT_ID
        try:
            logging.debug(__name__ + ': Get event "Sweep Complete" of channel %s' % chr(64+channel))
            return bool(int(self._ask('smu%s.trigger.SWEEP_COMPLETE_EVENT_ID' % chr(96+channel))))
        except ValueError:
            logging.error(__name__ + ': Event "Sweep Complete" of channel %s not specified:' % chr(64+channel))
    
    
    def _wait_for_end_of_sweep(self, channel=1):
        '''
        Waits until the event "Sweep Complete" of channel <channel> occurs
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        while not (self.is_end_of_sweep(channel=channel)):
            time.sleep(100e-3)
    
    
    def is_end_of_measure(self, channel=1):
        '''
        Gets event "Measure Complete" of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            val (bool)    : True | False
        '''
        # Corresponding Command: eventID = smuX.trigger.MEASURE_COMPLETE_EVENT_ID
        try:
            logging.debug(__name__ + ': Get event "Measure Complete" of channel %s' % chr(64+channel))
            return bool(int(self._ask('smu%s.trigger.MEASURE_COMPLETE_EVENT_ID' % chr(96+channel))))
        except ValueError:
            logging.error(__name__ + ': Event "Measure Complete" of channel %s not specified:' % chr(64+channel))
    
    
    def _wait_for_end_of_measure(self, channel=1):
        '''
        Waits until the event "Measure Complete" of channel <channel> occurs
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        while not (self.is_end_of_measure(channel=channel)):
            time.sleep(100e-3)
    
    
    
    
    
    
    
    
    
    
    def set_defaults(self, channel=1):
        '''
        Sets default settings
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        # Corresponding Command: display.locallockout = lockout
        # Corresponding Command: beeper.enable = state
        self._channel = 1
        self._write('display.locallockout = 0')
        self._write('beeper.enable = 0')
        self.set_measurement_mode(val=1, channel=channel)
        self.set_bias_mode(mode='curr', channel=channel)
        self.set_sense_mode(mode='volt', channel=channel)
        self.set_bias_range(val=200e-6, channel=channel)
        self.set_sense_range(val=-1, channel=channel)
        self.set_bias_delay(val=15e-6, channel=channel)
        self.set_sense_delay(val=15e-6, channel=channel)
        self.set_bias_value(val=0, channel=channel)
    
    
    def get_all(self, channel=1):
        '''
        Prints all settings of channel <channel>
        
        Input:
            channel (int) : 1 | 2
        Output:
            None
        '''
        logging.info(__name__ + ' : get all')
        print('dAdV               = %eA/V' % self.get_dAdV())
        print('dVdA               = %eV/A' % self.get_dVdA())
        print('amplification      = %e'    % self.get_amp())
        #print('synchronization    = %r'    % self.get_sync())
        print('measurement mode   = %s'    % self._measurement_modes[self.get_measurement_mode(channel=channel)])
        print('bias mode          = %s'    % self.get_bias_mode(channel=channel))
        print('sense mode         = %s'    % self.get_sense_mode(channel=channel))
        print('bias range         = %e%s'  % (self.get_bias_range(channel=channel), self._units[self.get_bias_mode(channel=channel)]))
        print('sense range        = %e%s'  % (self.get_sense_range(channel=channel), self._units[self.get_sense_mode(channel=channel)]))
        #print('bias trigger       = %s'    % self.get_bias_trigger(channel=channel))
        #print('sense trigger      = %s'    % self.get_sense_trigger(channel=channel))
        print('bias delay         = %es'   % self.get_bias_delay(channel=channel))
        print('sense delay        = %es'   % self.get_sense_delay(channel=channel))
        print('sense average      = %i'    % self.get_sense_average(channel=channel)[1])
        print('sense average type = %s'    % self._avg_types[self.get_sense_average(channel=channel)[2]])
        #print('plc                = %fHz'  % self.get_plc())
        print('sense nplc         = %i'    % self.get_sense_nplc(channel=channel))
        #print('get sense int time = %fs'   % self.get_sense_integration_time(channel=channel))
        print('status             = %r'    % self.get_status(channel=channel))
        print('bias value         = %f%s'  % (self.get_bias_value(channel=channel), self._units[self.get_bias_mode(channel=channel)]))
        print('sense value        = %f%s'  % (self.get_sense_value(channel=channel), self._units[self.get_sense_mode(channel=channel)]))
        #print('sweep start        = %f%s'  % (self.get_sweep_start(channel=channel), self._units[self.get_bias_mode(channel=channel)]))
        #print('sweep stop         = %f%s'  % (self.get_sweep_stop(channel=channel), self._units[self.get_bias_mode(channel=channel)]))
        #print('sweep step         = %f%s'  % (self.get_sweep_step(channel=channel), self._units[self.get_bias_mode(channel=channel)]))
        #print('sweep step time    = %fs'   % self.get_sweep_step_time(channel=channel))
        #print('nop                = %i'    % self.get_sweep_nop(channel=channel))
        #print('sweep time         = %fs'   % self.get_sweep_time(channel=channel))
    
    
    def reset(self, channel=None):
        '''
        Resets the instrument or a single channel to factory settings
        
        Input:
            channel (int): None | 1 | 2
        Output:
            None
        '''
        # Corresponding Command: reset()
        # Corresponding Command: smuX.reset()
        if channel is None:
            logging.info(__name__ + ': resetting instrument')
            self._write('reset()')
            #self.get_all()
        else:
            try:
                logging.info(__name__ + ': resetting channel %s' % chr(64+channel))
                self._write('smu%s.reset()' % chr(96+channel))
            except AttributeError:
                logging.error(__name__ + ': invalid input: cannot reset channel %s' % chr(64+channel))
    
    
    def abort(self, channel=1):
        '''
        Aborts the running command of channel <channel>
        
        Input:
            channel (int): None | 1 | 2
        Output:
            None
        '''
        # Corresponding Command: smuX.abort()
        try:
            logging.debug(__name__ + ': Abort running command of channel %s' % chr(64+channel))
            return self._write('smu%s.abort()' % chr(96+channel))
        except ValueError:
            logging.error(__name__ + ': Cannot abort running command of channel %s' % chr(64+channel))
    
    
    def get_error(self):
        '''
        Gets error of instrument
        
        Input:
            None
        Output:
            error (str)
        '''
        # Corresponding Command: errorCount = errorqueue.count
        # Corresponding Command: errorCode, message, severity, errorNode = errorqueue.next() 
        try:
            logging.debug(__name__ + ': Get errors')
            return [str(self._ask('errorqueue.next()')[1]) for i in range(self._ask('errorqueue.count'))]
        except ValueError:
            logging.error(__name__ + ': Error not specified:')
    
    
    def clear_error(self):
        '''
        Clears error of instrument
        
        Input:
            None
        Output:
            None
        '''
        # Corresponding Command: errorqueue.clear()
        try:
            logging.debug(__name__ + ': Clear error')
            self._write('errorqueue.clear()')
        except AttributeError:
            logging.error(__name__ + ': invalid input: cannot clear error')
    