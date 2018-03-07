# Keithley.py driver for Keithley 2636A multi channel source measure unit
# Hannes Rotzinger, hannes.rotzinger@kit.edu 2010
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
from qkit import visa
import time
import logging
import numpy
from distutils.version import LooseVersion


class Keithley(Instrument):
    '''
    This is the driver for the Keithley 2636A Source Meter
    
    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Keithley', address='<GBIP address>', reset=<bool>)
    '''
    
    def __init__(self, name, address, reset=False):
        '''
        Initializes the Keithley_2636A, and communicates with the wrapper.
        
        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address
            reset (bool)     : resets to default values, default=False
        '''
        # Start VISA communication
        logging.info(__name__ + ': Initializing instrument Keithley_2636A')
        Instrument.__init__(self, name, tags=['physical'])
        self._address           = address
        self._visainstrument    = visa.instrument(self._address)
        # distinguish high level commands to query status bit for different pyvisa versions
        if  LooseVersion(visa.__version__) < LooseVersion('1.5.0'):        # pyvisa 1.4
            self._read_stb = lambda: visa.vpp43.read_stb(self._visainstrument.vi)
        else:                                                              # pyvisa 1.8
            self._read_stb = lambda: visa.visalib.read_stb(self._visainstrument.session)[0]
        
        # Global constants
        self._mode_types        = {0:'curr', 1:'volt', 2:'res', 3:'pow'}
        self._smu_command       = {0:'i', 1:'v'}
        self._IV_units          = {0:'A', 1:'V'}
        self._avg_types         = ['moving average', 'repeat average', 'median']
        self._measurement_modes = ['2-wire', '4-wire', 'calibration']
        
        # external measuremnt setup
        self._dAdV             = 1 # for external current qseudo_bias_mode
        self._dVdA             = 1 # for external voltage qseudo_bias_mode
        self._amp              = 1 # amplification
        self._sweep_mode       = 0 # VV-mode
        self._pseudo_bias_mode = 0 # current bias
        
        # Reset
        if reset: self.reset()
        else: self.get_all()
    
    
    
    def _write(self, cmd):
        '''
        Sends a visa command <cmd>
        
        Input:
            cmd (str)
        Output:
            None
        '''
        return self._visainstrument.write(cmd)
    
    
    def _ask(self, cmd):
        '''
        Sends a visa command <cmd> and returns the read answer <output>
        
        Input:
            cmd (str)
        Output:
            answer (str)
        '''
        return self._visainstrument.ask('print({:s})'.format(cmd)).strip()
    
    
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
        Sets amplification factor of external measurement setup to <val>
        
        Input:
            val (float)
        Output:
            None
        '''
        self._amp = val
    
    
    def get_amp(self):
        '''
        Gets amplification factor of external measurement setup
        
        Input:
            None
        Output:
            val (float)
        '''
        return(self._amp)
    
    
    def set_digio(self, line, status):
        '''
        Sets digital Input/Output line <line> to status <status> (0V | 5V)
        
        Input:
            line (int): [1,14]
            status (bool)
        Output:
            None
        '''
        # Corresponding Command: digio.writebit(N, data)
        try:
            logging.debug(__name__ + ': Set digial I/O of line {:s} to {:d}'.format(line, status))
            self._write('digio.writebit({:d}, {:d})'.format(line, status))
        except AttributeError:
            logging.error(__name__ + ': Invalid input: cannot set digital I/O of line {:s} to {:f}'.format(line, status))
    
    
    def get_digio(self, line):
        '''
        Gets digital Input/Output status of line <line> (0V | 5V)
        
        Input:
            line (int): [1,14]
        Output:
            status (bool)
        '''
        # Corresponding Command: data = digio.readbit(N)
        try:
            logging.debug(__name__ + ': Get digial I/O of line {:s}'.format(line))
            return bool(int(float(self._ask('digio.readbit({:d})'.format(line)))))
        except AttributeError as e:
            logging.error(__name__ + ': Invalid input: cannot get digital I/O of line {:s}: {:s}'.format(line, e))
    
    
    def set_sweep_mode(self, mode=0, **channels):
        '''
        Sets an internal variable to decide weather voltage is both applied and measured (default), current is applied and voltage is measured or voltage is applied and current is measured.
        VV-mode needs two different channels (bias channel <channel> and sense channel <channel2>), IV-mode and VI-mode only one (<channel>).
        
        Input:
            mode (int) : 0 (VV-mode) (default) | 1 (IV-mode) | 2 (VI-mode)
            **channels : channel  (int) : 1 (default) | 2
                         channel2 (int) : 1 | 2 (default)
        Output:
            None
        '''
        self._sweep_mode = mode
        self.set_defaults(channel=channels.get('channel', 1), channel2=channels.get('channel2', 2))
    
    
    def get_sweep_mode(self):
        '''
        Gets an internal variable to decide weather voltage is both applied and measured (default), current is applied and voltage is measured or voltage is applied and current is measured.
        
        Input:
            None
        Output:
            mode (int) : 0 (VV mode) | 1 (IV mode)
        '''
        return self._sweep_mode
    
    
    def set_pseudo_bias_mode(self, mode):
        '''
        Sets an internal variable to decide weather bias or sense values are converted to currents
        
        Input:
            mode (int) : 0 (current bias) (default) | 1 (voltage bias)
        Output:
            None
        '''
        self._pseudo_bias_mode = mode
    
    
    def get_pseudo_bias_mode(self):
        '''
        Gets an internal variable to decide weather bias or sense values are converted to currents
        
        Input:
            None
        Output:
            mode (int) : 0 (current bias) (default) | 1 (voltage bias)
        '''
        return self._pseudo_bias_mode
    
    
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
            logging.debug(__name__ + ': Set measurement mode of channel {:s} to {:d}'.format(chr(64+channel), val))
            self._write('smu{:s}.sense = {:d}'.format(chr(96+channel), val))
        except AttributeError as e:
            logging.error(__name__ + ': Invalid input: cannot set measurement mode of channel {:s} to {:f}: {:s}'.format(chr(64+channel), val, e))
    
    
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
            logging.debug(__name__ + ': Get measurement mode of channel {:s}'.format(chr(64+channel)))
            return int(float(self._ask('smu{:s}.sense'.format(chr(96+channel)))))
        except ValueError as e:
            logging.error(__name__ + ': Measurement mode of channel {:s} not specified: {s}'.format(chr(64+channel), e))
    
    
    def set_bias_mode(self, mode, channel=1):
        '''
        Sets bias mode of channel <channel> to <mode> regime.
        
        Input:
            mode (int)    : 0 (current) | 1 (voltage)
            channel (int) : 1 | 2
        Output:
            None
        '''
        # Corresponding Command: smuX.source.func = 0|1|smuX.OUTPUT_DCAMPS|smuX.OUTPUT_DCVOLTS
        try:
            logging.debug(__name__ + ': Set bias mode of channel {:s} to {:d}'.format(chr(64+channel), mode))
            self._write('smu{:s}.source.func = {:d}'.format(chr(96+channel), mode))
        except AttributeError as e:
            logging.error(__name__ + ': Invalid input: cannot set bias mode of channel {:s} to {:d}: {:s}'.format(chr(64+channel), mode, e))
    
    
    def get_bias_mode(self, channel=1):
        '''
        Gets bias mode <output> of channel <channel>
        
        Input:
            channel (int) : 1 | 2
        Output:
            mode (int)    : 0 (current) | 1 (voltage)
        '''
        # Corresponding Command: 0|1|smuX.OUTPUT_DCAMPS|smuX.OUTPUT_DCVOLTS = smuX.source.func
        try:
            logging.debug(__name__ + ': Get bias mode of channel {:s}'.format(chr(64+channel)))
            return int(float(self._ask('smu{:s}.source.func'.format(chr(96+channel)))))
        except ValueError as e:
            logging.error(__name__ + ': Bias mode of channel {:s} not specified: {:s}'.format(chr(64+channel), e))
    
    
    def set_sense_mode(self, mode, channel=1):
        '''
        Sets sense mode of channel <channel> to <mode> regime.
        
        Input:
            mode (str)    : 0 (current) | 1 (voltage) | 2 (resistance) | 3 (power)
            channel (int) : 1 | 2
        Output:
            None
        '''
        # Corresponding Command: display.smuX.measure.func = 0|1|2|3|display.MEASURE_DCAMPS|display.MEASURE_DCVOLTS|display.MEASURE_OHMS|display.MEASURE_WATTS
        try:
            logging.debug(__name__ + ': Set sense mode of channel {:s} to {:d}'.format(chr(64+channel), mode))
            self._write('display.smu{:s}.measure.func = {:d}'.format(chr(96+channel), mode))
        except AttributeError as e:
            logging.error(__name__ + ': Invalid input: cannot set sense mode of channel {:s} to {:d}: {:s}'.format(chr(64+channel), mode, e))
    
    
    def get_sense_mode(self, channel=1):
        '''
        Gets sense mode <output> of channel <channel>
        
        Input:
            channel (int) : 1 | 2
        Output:
            mode (str)    : 0 (current) | 1 (voltage) | 2 (resistance) | 3 (power)
        '''
        # Corresponding Command: 0|1|2|3|display.MEASURE_DCAMPS|display.MEASURE_DCVOLTS|display.MEASURE_OHMS|display.MEASURE_WATTS = display.smuX.measure.func
        try:
            logging.debug(__name__ + ': Get bias mode of channel {:s}'.format(chr(64+channel)))
            return int(float(self._ask('display.smu{:s}.measure.func'.format(chr(96+channel)))))
        except ValueError as e:
            logging.error(__name__ + ': Bias mode of channel {:s} not specified: {:s}'.format(chr(64+channel), e))
    
    
    def set_bias_range(self, val, channel=1):
        '''
        Sets bias range of channel <channel> to <val>
        
        Input:
            val (float)   : -1 (auto) | 200mV | 2V | 20V | 200V | 100pA | 1nA | 10nA |100nA | 1uA | 10uA | 100uA | 1mA | 10mA | 100mA | 1 A | 1.5A
            channel (int) : 1 | 2
        Output:
            None
        '''
        # Corresponding Command: smuX.source.rangeY = rangeValue
        # Corresponding Command: smuX.source.autorangeY = 0|1|smuX.AUTORANGE_OFF|smuX.AUTORANGE_ON
        try:
            logging.debug(__name__ + ': Set bias range of channel {:s} to {:f}'.format(chr(64+channel), val))
            if val == -1:
                self._write('smu{:s}.source.autorange{:s} = 1'.format(chr(96+channel), self._smu_command[self.get_bias_mode(channel=channel)]))
            else:
                self._write('smu{:s}.source.autorange{:s} = 0'.format(chr(96+channel), self._smu_command[self.get_bias_mode(channel=channel)]))
                self._write('smu{:s}.source.range{:s} = {:f}'.format(chr(96+channel), self._smu_command[self.get_bias_mode(channel=channel)], val))
        except AttributeError as e:
            logging.error(__name__ + ': Invalid input: cannot set bias range of channel {:s} to {:f}: {:s}'.format(chr(64+channel), val, e))
    
    
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
            logging.debug(__name__ + ': Get bias range of channel {:s}'.format(chr(64+channel)))
            return float(self._ask('smu{:s}.source.range{:s}'.format(chr(96+channel), self._smu_command[self.get_bias_mode(channel=channel)])))
        except ValueError as e:
            logging.error(__name__ + ': Bias range of channel {:s} not specified: {:s}'.format(chr(64+channel), e))
    
    
    def set_sense_range(self, val, channel=1):
        '''
        Sets sense range of channel <channel> to <val>
        
        Input:
            val (float)   : -1 (auto) | 200mV | 2V | 20V | 200V | 100pA | 1nA | 10nA |100nA | 1uA | 10uA | 100uA | 1mA | 10mA | 100mA | 1 A | 1.5A
            channel (int) : 1 | 2
        Output:
            None
        '''
        # Corresponding Command: smuX.measure.rangeY = rangeValue
        # Corresponding Command: smuX.measure.autorangeY = 0|1|2|smuX.AUTORANGE_OFF|smuX.AUTORANGE_ON|smuX.AUTORANGE_FOLLOW_LIMIT
        try:
            logging.debug(__name__ + ': Set sense range of channel {:s} to {:f}'.format(chr(64+channel), val))
            if val == -1:
                self._write('smu{:s}.measure.autorange{:s} = 1'.format(chr(96+channel), self._smu_command[self.get_sense_mode(channel=channel)]))
            else:
                self._write('smu{:s}.measure.autorange{:s} = 0'.format(chr(96+channel), self._smu_command[self.get_sense_mode(channel=channel)]))
                self._write('smu{:s}.measure.range{:s} = {:f}'.format(chr(96+channel), self._smu_command[self.get_sense_mode(channel=channel)], val))
        except AttributeError as e:
            logging.error(__name__ + ': Invalid input: cannot set sense range of channel {:s} to {:f}: {:s}'.format(chr(64+channel), val, e))
    
    
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
            logging.debug(__name__ + ': Get sense range of channel {:s}'.format(chr(64+channel)))
            return float(self._ask('smu{:s}.measure.range{:s}'.format(chr(96+channel), self._smu_command[self.get_sense_mode(channel=channel)])))
        except ValueError as e:
            logging.error(__name__ + ': Sense range of channel {:s} not specified: {:s}'.format(chr(64+channel), e))
    
    
    def set_bias_delay(self, val, channel=1):
        '''
        Sets bias delay of channel <channel> to <val>
        
        Input:
            val (float)   : -1 (auto) | 0 (off) | positive number
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        # Corresponding Command: smuX.source.delay = 0|1|smuX.DELAY_OFF|muX.DELAY_AUTO|sDelay
        try:
            logging.debug(__name__ + ': Set bias delay of channel {:s} to {:f}'.format(chr(64+channel), val))
            self._write('smu{:s}.source.delay = {:f}'.format(chr(96+channel), val))
        except AttributeError as e:
            logging.error(__name__ + ': Invalid input: cannot set bias delay of channel {:s} to {:f}: {:s}'.format(chr(64+channel), val, e))
    
    
    def get_bias_delay(self, channel=1):
        '''
        Gets bias delay of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            val (float)
        '''
        # Corresponding Command: 0|1|smuX.DELAY_OFF|muX.DELAY_AUTO|sDelay = smuX.source.delay
        try:
            logging.debug(__name__ + ': Get bias delay of channel {:s}'.format(chr(64+channel)))
            return float(self._ask('smu{:s}.source.delay'.format(chr(96+channel))))
        except ValueError as e:
            logging.error(__name__ + ': Bias delay of channel {:s} not specified: {:s}'.format(chr(64+channel), e))
    
    
    def set_sense_delay(self, val, factor=1, channel=1):
        '''
        Sets sense delay of channel <channel> to <val>
        
        Input:
            val (float)   : -1 (auto) | 0 (off) | positive number
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        # Corresponding Command: smuX.measure.delay = 0|1|smuX.DELAY_OFF|muX.DELAY_AUTO|mDelay
        # Corresponding Command: smuX.measure.delayfactor = delayFactor
        try:
            logging.debug(__name__ + ': Set sense delay of channel {:s} to {:f}'.format(chr(64+channel), val))
            self._write('smu{:s}.measure.delay = {:f}'.format(chr(96+channel), val))
            if val == -1: self._write('smu{:s}.measure.delayfactor = {:f}'.format(chr(96+channel), factor))
        except AttributeError as e:
            logging.error(__name__ + ': Invalid input: cannot set sense delay of channel {:s} to {:f}: {:s}'.format(chr(64+channel), val, e))
    
    
    def get_sense_delay(self, channel=1):
        '''
        Gets sense delay of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            val (float)
        '''
        # Corresponding Command: 0|1|smuX.DELAY_OFF|muX.DELAY_AUTO|mDelay= smuX.measure.delay
        try:
            logging.debug(__name__ + ': Get sense delay of channel {:s}'.format(chr(64+channel)))
            return float(self._ask('smu{:s}.measure.delay'.format(chr(96+channel))))
        except ValueError as e:
            logging.error(__name__ + ': Sense delay of channel {:s} not specified: {:s}'.format(chr(64+channel), e))
    
    
    def set_sense_average(self, val, mode=1, channel=1):
        '''
        Sets sense average of channel <channel> to <val>
        
        Input:
            val (int)     : [1, 100]
            mode (str)    : 0 (moving average) | 1 (repeat average) (default) | 2 (median)
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        # Corresponding Command: smuX.measure.filter.count = filterCount
        # Corresponding Command: smuX.measure.filter.enable = 0|1|smuX.FILTER_OFF|smuX.FILTER_ON
        # Corresponding Command: smuX.measure.filter.type = 0|1|2|smuX.FILTER_MOVING_AVG|smuX.FILTER_REPEAT_AVG|smuX.FILTER_MEDIAN
        try:
            logging.debug(__name__ + ': Set sense average of channel {:s} to {:d} and mode {:s}'.format(chr(64+channel), val, self._avg_types[mode]))
            status = not(.5*(1-numpy.sign(val-1)))                             # equals Heaviside(1-val) --> turns on for <val> >= 2
            self._write('smu{:s}.measure.filter.enable = {:d}'.format(chr(96+channel), status))
            if status:
                self._write('smu{:s}.measure.filter.count = {:d}'.format(chr(96+channel), val))
                self._write('smu{:s}.measure.filter.type = {:d}'.format(chr(96+channel), mode))
        except AttributeError as e:
            logging.error(__name__ + ': Invalid input: cannot set sense average of channel {:s} to {:d} and mode {:s}: {:s}'.format(chr(64+channel), val, self._avg_types[mode], e))
    
    
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
        # Corresponding Command: 0|1|smuX.FILTER_OFF|smuX.FILTER_ON = smuX.measure.filter.enable
        # Corresponding Command: 0|1|2|smuX.FILTER_MOVING_AVG|smuX.FILTER_REPEAT_AVG|smuX.FILTER_MEDIAN = smuX.measure.filter.type
        try:
            logging.debug(__name__ + ': Get sense average of channel {:s}'.format(chr(64+channel)))
            status = bool(int(float(self._ask('smu{:s}.measure.filter.enable'.format(chr(96+channel))))))
            val = int(float(self._ask('smu{:s}.measure.filter.count'.format(chr(96+channel)))))
            mode = int(float(self._ask('smu{:s}.measure.filter.type'.format(chr(96+channel)))))
            return status, val, mode
        except ValueError as e:
            logging.error(__name__ + ': Sense average of channel {:s} not specified: {:s}'.format(chr(64+channel), e))
    
    
    def set_plc(self, val):
        '''
        Sets power line cycle (PLC) to <val>
        
        Input:
            plc (int) : -1 (auto) | 50 | 60
        Output:
            None
        '''
        # Corresponding Command: localnode.linefreq = frequency
        # Corresponding Command: localnode.autolinefreq = flag
        try:
            logging.debug(__name__ + ': Set PLC to {:s}'.format(str(val)))
            cmd = {-1:'autolinefreq = true', 50:'linefreq = 50', 60:'linefreq = 60'}
            self._write('localnode.{:s}'.format(cmd[int(val)]))
        except ValueError as e:
            logging.error(__name__ + ': Invalid input: cannot set PLC to {:s}: {:s}'.format(val, e))
    
    
    def get_plc(self):
        '''
        Gets power line cycle (PLC)
        
        Input:
            None
        Output:
            val (float) : 50 | 60
        '''
        # Corresponding Command: frequency = localnode.linefreq
        # Corresponding Command: flag = localnode.autolinefreq
        try:
            logging.debug(__name__ + ': Get PLC')
            return float(self._ask('localnode.linefreq'))
        except ValueError as e:
            logging.error(__name__ + ': PLC not specified: {:s}'.format(e))
    
    
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
            logging.debug(__name__ + ': Set sense integrarion time of channel {:s} to {:f} PLC'.format(chr(64+channel), val))
            self._write('smu{:s}.measure.nplc = {:f}'.format(chr(96+channel), val))
        except ValueError as e:
            logging.error(__name__ + ': Invalid input: cannot set NPLC of channel {:s} to {:d}: {:s}'.format(chr(64+channel), val, e))
    
    
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
            logging.debug(__name__ + ': Get sense integrarion time of channel {:s}'.format(chr(64+channel)))
            return float(self._ask('smu{:s}.measure.nplc'.format(chr(96+channel))))
        except ValueError as e:
            logging.error(__name__ + ': Number of PLC of channel {:s} not specified: {:s}'.format(chr(64+channel), e))
    
    
    def set_status(self, status, channel=1):
        '''
        Sets output status of channel <channel> to <status>
        
        Input:
            status (int)  : 0 (off) | 1 (on) | 2 (high Z)
            channel (int) : 1 | 2
        Output:
            None
        '''
        # Corresponding Command: smuX.source.output = 0|1|2|smuX.OUTPUT_OFF|smuX.OUTPUT_ON|smuX.OUTPUT_HIGH_Z
        try:
            logging.debug(__name__ + ': Set output status of channel {:s} to {:d}'.format(chr(64+channel), status))
            self._write('smu{:s}.source.output = {:d}'.format(chr(96+channel), status))
        except AttributeError as e:
            logging.error(__name__ + ': Invalid input: cannot set output status of channel {:s} to %r: {:s}'.format(chr(64+channel), status, e))
    
    
    def get_status(self, channel=1):
        '''
        Gets output status of channel <channel>
        
        Input:
            channel (int) : 1 | 2
        Output:
            status (int)  : 0 (off) | 1 (on) | 2 (high Z)
        '''
        # Corresponding Command: 0|1|2|smuX.OUTPUT_OFF|smuX.OUTPUT_ON|smuX.OUTPUT_HIGH_Z = smuX.source.output
        try:
            logging.debug(__name__ + ': Get status of channel {:s}'.format(chr(64+channel)))
            return int(float(self._ask('smu{:s}.source.output'.format(chr(96+channel)))))
        except ValueError as e:
            logging.error(__name__ + ': Status of channel {:s} not specified: {:s}'.format(chr(64+channel), e))
    
    
    def set_stati(self, status):
        '''
        Sets output status of both channels to <status>
        
        Input:
            status (int)  : 0 (off) | 1 (on) | 2 (high Z)
        Output:
            None
        '''
        for channel in [1,2]: self.set_status(status=status, channel=channel)
    
    
    def get_stati(self):
        '''
        Gets output status of both channels
        
        Input:
            None
        Output:
            status (int)  : 0 (off) | 1 (on) | 2 (high Z)
        '''
        stati = []
        for channel in [1,2]: stati.append(self.get_status(channel=channel))
        return stati
    
    
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
            logging.debug(__name__ + ': Set bias value of channel {:s} to {:f}'.format(chr(64+channel), val))
            self._write('smu{:s}.source.level{:s} = {:f}'.format(chr(96+channel), self._smu_command[self.get_bias_mode(channel=channel)], val))
        except AttributeError as e:
            logging.error(__name__ + ': Invalid input: cannot set bias value of channel {:s} to {:f}: {:s}'.format(chr(64+channel), val, e))
    
    
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
            logging.debug(__name__ + ': Get bias value of channel {:s}'.format(chr(64+channel)))
            return float(self._ask('smu{:s}.source.level{:s}'.format(chr(96+channel), self._smu_command[self.get_bias_mode(channel=channel)])))
        except ValueError as e:
            logging.error(__name__ + ': Cannot get bias value of channel {:s}: {:s}'.format(chr(64+channel), e))
    
    
    def get_sense_value(self, channel=1, **readingBuffer):
        '''
        Gets sense value of channel <channel>
        
        Input:
            channel (int)   : 1 | 2
            **readingBuffer : readingBuffer (str): 'smuX.nvbuffer1' (default)
        Output:
            val (float)
        '''
        # Corresponding Command: reading= smuX.measure.Y()
        # Corresponding Command: reading = smuX.measure.Y(readingBuffer)
        try:
            logging.debug(__name__ + ': Get sense value of channel {:s}'.format(chr(64+channel)))
            if 'readingBuffer' in readingBuffer:
                return float(self._ask('smu{:s}.measure.{:s}({:s})'.format(chr(96+channel), self._smu_command[self.get_sense_mode(channel=channel)], readingBuffer.get('readingBuffer', 'smu{:s}.nvbuffer1'.format(chr(96+channel))))))
            else:
                return float(self._ask('smu{:s}.measure.{:s}()'.format(chr(96+channel), self._smu_command[self.get_sense_mode(channel=channel)])))
        except ValueError as e:
            logging.error(__name__ + ': Cannot get sense value of channel {:s}: {:s}'.format(chr(64+channel), e))
    
    
    def get_sense_value_iv(self, channel=1, **readingBuffer):
        '''
        Gets both current and voltage sense value of channel <channel>
        
        Input:
            channel (int)   : 1 | 2
            **readingBuffer : iReadingBuffer (str): 'smuX.nvbuffer1' (default)
                              vReadingBuffer (str): 'smuX.nvbuffer2' (default)
        Output:
            i_val (float)
            v_val (float)
        '''
        # Corresponding Command: iReading, vReading= smuX.measure.iv()
        # Corresponding Command: iReading, vReading = smuX.measure.iv(iReadingBuffer)
        # Corresponding Command: iReading, vReading = smuX.measure.iv(iReadingBuffer, vReadingBuffer)
        try:
            logging.debug(__name__ + ': Get current and voltage sense value of channel {:s}'.format(chr(64+channel)))
            if 'iReadingBuffer' in readingBuffer and 'vReadingBuffer' in readingBuffer:
                return numpy.array([float(val) for val in self._ask('smu{:s}.measure.iv({:s}, {:s})'.format(chr(96+channel), readingBuffer.get('iReadingBuffer', 'smu{:s}.nvbuffer1'.format(chr(96+channel))), readingBuffer.get('vReadingBuffer', 'smu{:s}.nvbuffer2'.format(chr(96+channel))))).split('\t')])
            elif 'iReadingBuffer' in readingBuffer:
                return numpy.array([float(val) for val in self._ask('smu{:s}.measure.iv({:s})'.format(chr(96+channel), readingBuffer.get('iReadingBuffer', 'smu{:s}.nvbuffer1'.format(chr(96+channel))))).split('\t')])
            else: return numpy.array([float(val) for val in self._ask('smu{:s}.measure.iv()'.format(chr(96+channel))).split('\t')])
        except ValueError as e:
            logging.error(__name__ + ': Cannot get current and voltage sense value of channel {:s}: {:s}'.format(chr(64+channel), e))
    
    
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
            logging.debug(__name__ + ': Set voltage of channel {:s} to {:s}'.format(channel, str(val)))
            self._write('smu{:s}.source.levelv = {:s}'.format(chr(96+channel), val))
        except AttributeError as e:
            logging.error(__name__ + ': Invalid input: cannot set voltage of channel {:s} to {:f}: {:s}'.format(channel, val, e))
    
    
    def get_voltage(self, channel=1, **readingBuffer):
        '''
        Gets voltage value of channel <channel>
        
        Input:
            channel (int)   : 1 | 2
            **readingBuffer : readingBuffer (str): 'smuX.nvbuffer1' (default)
        Output:
            val (float)
        '''
        # Corresponding Command: reading= smuX.measure.Y()
        # Corresponding Command: reading = smuX.measure.Y(readingBuffer)
        try:
            logging.debug(__name__ + ': Get voltage of channel {:s}'.format(chr(64+channel)))
            if 'readingBuffer' in readingBuffer:
                return float(self._ask('smu{:s}.measure.v({:s})'.format(chr(96+channel), readingBuffer.get('readingBuffer', 'smu{:s}.nvbuffer1'.format(chr(96+channel))))))
            else:
                return float(self._ask('smu{:s}.measure.v()'.format(chr(96+channel))))
        except ValueError as e:
            logging.error(__name__ + ': Cannot get voltage of channel {:s}: {:s}'.format(chr(64+channel), e))
    
    
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
            logging.debug(__name__ + ': Set current of channel {:s} to {:s}'.format(channel, str(val)))
            self._write('smu{:s}.source.leveli = {:s}'.format(chr(96+channel), val))
        except AttributeError as e:
            logging.error(__name__ + ': Invalid input: cannot set current of channel {:s} to {:f}: {:s}'.format(channel, val, e))
    
    
    def get_current(self, channel=1, **readingBuffer):
        '''
        Gets current value of channel <channel>
        
        Input:
            channel (int)   : 1 | 2
            **readingBuffer : readingBuffer (str): 'smuX.nvbuffer1' (default)
        Output:
            val (float)
        '''
        # Corresponding Command: reading= smuX.measure.Y()
        # Corresponding Command: reading = smuX.measure.Y(readingBuffer)
        try:
            logging.debug(__name__ + ': Get current of channel {:s}'.format(chr(64+channel)))
            if 'readingBuffer' in readingBuffer:
                return float(self._ask('smu{:s}.measure.i({:s})'.format(chr(96+channel), readingBuffer.get('readingBuffer', 'smu{:s}.nvbuffer1'.format(chr(96+channel))))))
            else:
                return float(self._ask('smu{:s}.measure.i()'.format(chr(96+channel))))
        except ValueError as e:
            logging.error(__name__ + ': Cannot get current of channel {:s}: {:s}'.format(chr(64+channel), e))
    
    
    def ramp_bias(self, stop, step, step_time=0.1, channel=2):
        '''
        Ramps bias value of channel <channel> from recent value to <stop>
        
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
        for val in numpy.arange(start, stop, step)+step:
            self.set_bias_value(val, channel=channel)
            time.sleep(step_time)
    
    
    def set_sweep_parameters(self, sweep, channel=1, channel2=2, **readingBuffer):
        '''
        Sets sweep parameters <sweep> and prepares instrument for VV-mode or IV-mode.
        VV-mode needs two different channels (bias channel <channel> and sense channel <channel2>), IV-mode and VI-mode only one (<channel>).
        
        Input:
            sweep obj(float) : start, stop, step
            channel (int)    : 1 (default) | 2
            channel2 (int)   : 1 | 2 (default)
            **readingBuffer  : iReadingBuffer (str): 'smu<channel>.nvbuffer1' (default)
                               vReadingBuffer (str): 'smu<channel2>.nvbuffer2' (default)
        Output:
            None
        '''
        # Corresponding Command: format.data = value
        # Corresponding Command: format.asciiprecision = precision
        # Corresponding Command: smuX.trigger.source.linearY(startValue, endValue, points)
        # Corresponding Command: smuX.trigger.source.action = action
        # Corresponding Command: smuX.trigger.measure.action = action
        # Corresponding Command: bufferVar.clear()
        # Corresponding Command: smuX.trigger.measure.iv(ibuffer, vbuffer)
        # Corresponding Command: smuX.trigger.count = triggerCount
        # Corresponding Command: smuX.trigger.arm.count = triggerArmCount
        try:
            self._write('format.data = format.ASCII')
            self._write('format.asciiprecision = 6')
            if self._sweep_mode == 0:                                          # VV-mode
                if self._pseudo_bias_mode == 0:                                # current bias
                    self._start = float(sweep[0])/self._dAdV
                    self._stop  = float(sweep[1])/self._dAdV
                    self._step  = numpy.abs(float(sweep[2]))/self._dAdV
                elif self._pseudo_bias_mode == 1:                              # voltage bias
                    self._start = float(sweep[0])/self._amp
                    self._stop  = float(sweep[1])/self._amp
                    self._step  = numpy.abs(float(sweep[2]))/self._amp
                self._step_signed = numpy.sign(self._stop-self._start)*numpy.abs(self._step)
                self.set_bias_value(val=self._start, channel=channel)
                self._iReadingBuffer = readingBuffer.get('iReadingBuffer', 'smu{:s}.nvbuffer1'.format(chr(96+((self._pseudo_bias_mode+1)%2+channel%2)%2+1)))
                self._vReadingBuffer = readingBuffer.get('vReadingBuffer', 'smu{:s}.nvbuffer1'.format(chr(96+((self._pseudo_bias_mode+1)%2+channel2%2)%2+1)))
                cmd =  '{:s}.clear()'.format(self._iReadingBuffer)
                cmd += '{:s}.appendmode = 1'.format(self._iReadingBuffer)
                cmd += '{:s}.clear()'.format(self._vReadingBuffer)
                cmd += '{:s}.appendmode = 1'.format(self._vReadingBuffer)
            elif self._sweep_mode in [1, 2]:                                   # IV-mode or VI-mode
                self._start = float(sweep[0])
                self._stop  = float(sweep[1])
                self._step  = float(sweep[2])
                self._iReadingBuffer = readingBuffer.get('iReadingBuffer', 'smu{:s}.nvbuffer1'.format(chr(96+channel)))
                self._vReadingBuffer = readingBuffer.get('vReadingBuffer', 'smu{:s}.nvbuffer2'.format(chr(96+channel)))
                self._nop = int(numpy.abs((self._stop-self._start)/self._step)+1)
                cmd =  'smu{:s}.trigger.source.linear{:s}({:f}, {:f}, {:d})'.format(chr(96+channel), self._smu_command[self.get_bias_mode(channel=channel)], self._start, self._stop, self._nop)
                cmd += 'smu{:s}.trigger.source.action = 1'.format(chr(96+channel))
                cmd += 'smu{:s}.trigger.measure.action = 1'.format(chr(96+channel))
                cmd += '{:s}.clear()'.format(self._iReadingBuffer)
                cmd += '{:s}.clear()'.format(self._vReadingBuffer)
                cmd += 'smu{:s}.trigger.measure.iv({:s}, {:s})'.format(chr(96+channel), self._iReadingBuffer, self._vReadingBuffer)
                cmd += 'smu{:s}.trigger.count = {:d}'.format(chr(96+channel), self._nop)
                cmd += 'smu{:s}.trigger.arm.count = 1'.format(chr(96+channel))
            self._write(cmd)
            self._prepare_stb('status.OSB')
            time.sleep(1e-3)
        except (AttributeError, ValueError) as e:
            logging.error(__name__ + ': Cannot set sweep parameters: {:s}'.format(e))
    
    
    def get_tracedata(self, channel=1, channel2=2, **readingBuffer):
        '''
        Starts bias sweep of channel <channel_bias> and gets trace data of channel <channel_sense>
        
        Input:
            channel (int)    : 1 (default) | 2
            channel2 (int)   : 1 | 2 (default)
            **readingBuffer  : iReadingBuffer (str): 'smu<channel>.nvbuffer1' (default)
                               vReadingBuffer (str): 'smu<channel2>.nvbuffer2' (default)
        Output:
            bias_values (numpy.array(float))
            sense_values (numpy.array(float))
        '''
        # Corresponding Command: bufferVar.clear()
        # Corresponding Command: bufferVar.appendmode = state
        # Corresponding Command: smuX.source.levelY = sourceLevel
        # Corresponding Command: reading = smuX.measure.Y(readingBuffer)
        # Corresponding Command: numberOfReadings = bufferVar.n
        # Corresponding Command: smuX.trigger.initiate()
        # Corresponding Command: waitcomplete()
        try:
            if self._sweep_mode == 0:                                          # VV-mode
                # sweep channel and measure channel2
                cmd =  'for i = {:f}, {:f}, {:f} do'.format(self._start, self._stop+self._step_signed/2., self._step_signed)
                cmd += '\tsmu{:s}.source.levelv = i'.format(chr(96+channel))
                cmd += '\tsmu{:s}.measure.v({:s})'.format(chr(96+((self._pseudo_bias_mode+1)%2+channel%2)%2+1),  self._iReadingBuffer)
                cmd += '\tsmu{:s}.measure.v({:s})'.format(chr(96+((self._pseudo_bias_mode+1)%2+channel2%2)%2+1), self._vReadingBuffer)
                cmd += 'end\n'
                self._write(cmd)
            elif self._sweep_mode in [1, 2]:                                   # IV-mode or VI-mode
                # sweep and measure channel
                self._write('smu{:s}.trigger.initiate()'.format(chr(96+channel)))
                self._write('waitcomplete()')
            self._wait_for_stb()
            time.sleep(0.1)
            # read data
            self._write('*CLS')
            self._prepare_stb('status.MAV')
            self._write('printbuffer(1, {:s}.n, {:s}, {:s})'.format(self._iReadingBuffer, self._iReadingBuffer, self._vReadingBuffer))        
            self._wait_for_stb()
            try:
                data = numpy.fromstring(string=self._visainstrument.read(), dtype=float, count=-1, sep=',')
                I_values = data[0::2]
                V_values = data[1::2]
            except ValueError as e:
                logging.error(__name__ + ': Cannot read data: {:s}'.format(e))
                raise ValueError('Cannot read data: {:s}'.format(e))
            if self._sweep_mode == 0:                                          # VV-mode
                if self._pseudo_bias_mode == 0:                                # current bias
                    I_values *= self._dAdV
                    V_values /= self._amp
                elif self._pseudo_bias_mode == 1:                              # voltage bias
                    I_values /= self._dVdA
                    V_values *= self._amp
            return I_values, V_values
        except ValueError as e:
            logging.error(__name__ + ': Cannot take sweep trace data: {:s}'.format(e))
    
    def take_IV(self, sweep, channel=1, channel2=2, **readingBuffer):
        '''
        Takes IV curve with sweep parameters <sweep> in doing a bias sweep of channel
        <channel_bias> and measure data of channel <channel_sense>
        
        Input:
            sweep obj(float) : start, stop, step
            channel (int)    : 1 (default) | 2
            channel2 (int)   : 1 | 2 (default)
            **readingBuffer  : iReadingBuffer (str): 'smu<channel>.nvbuffer1' (default)
                               vReadingBuffer (str): 'smu<channel2>.nvbuffer2' (default)
        Output:
            I_values (numpy.array(float))
            V_values (numpy.array(float))
        '''
        if self._sweep_mode == 0:                                              # VV-mode
            self.set_sweep_parameters(sweep=sweep, channel=channel, channel2=channel2, **readingBuffer)
            return self.get_tracedata(channel=channel, channel2=channel2, **readingBuffer)
        elif self._sweep_mode in [1, 2]:                                       # IV-mode or VI-mode
            self.set_sweep_parameters(sweep=sweep, channel=channel, **readingBuffer)
            return self.get_tracedata(channel=channel, **readingBuffer)
    
    
    def _prepare_stb(self, stb):
        '''
        Prepares status bit <stb> for high level query
        
        Input:
            stb (str)
        Output:
            None
        '''
        # Corresponding Command: status.reset()
        # Corresponding Command: status.operation.user.condition = operationRegister
        # Corresponding Command: status.operation.user.enable = operationRegister
        # Corresponding Command: status.operation.user.ptr = operationRegister
        # Corresponding Command: status.operation.enable = operationRegister
        # Corresponding Command: status.request_enable = requestSRQEnableRegister
        cmd = '''status.reset()
                 status.operation.user.condition = 0
                 status.operation.user.enable = status.operation.user.BIT0
                 status.operation.user.ptr = status.operation.user.BIT0
                 status.operation.enable = status.operation.USER
                 status.request_enable = {:s}'''.format(stb)
        return self._write(cmd)
    
    
    def _wait_for_stb(self, wait_time=1e-1):
        '''
        Waits until the status bit occurs
        
        Input:
            None
        Output:
            None
        '''
        # Corresponding Command: status.operation.user.condition = operationRegister
        self._write('status.operation.user.condition = status.operation.user.BIT0')
        self._read_stb()
        time.sleep(wait_time)
        while self._read_stb() == 0:
            time.sleep(wait_time)
    
    
    def set_defaults(self, channel=1, channel2=2):
        '''
        Sets default settings for different sweep modes.
        VV-mode needs two different channels (bias channel <channel> and sense channel <channel2>), IV-mode and VI-mode only one (<channel>).
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        self._write('beeper.enable = 0')
        if self._sweep_mode == 0:                                              # VV-mode
            for chan in [channel, channel2]: self.set_measurement_mode(val=0, channel=chan)
            for chan in [(channel, 1), (channel2, 0)]: self.set_bias_mode(mode=chan[1], channel=chan[0])
            for chan in [channel, channel2]: self.set_sense_mode(mode=1, channel=chan)
            for chan in [channel, channel2]: self.set_bias_range(val=-1, channel=chan)
            for chan in [(channel, -1), (channel2, 200)]: self.set_sense_range(val=chan[1], channel=chan[0])
            for chan in [channel, channel2]: self.set_bias_delay(val=15e-6, channel=chan)
            for chan in [channel, channel2]: self.set_sense_delay(val=15e-6, channel=chan)
            for chan in [channel, channel2]: self.set_sense_nplc(val=1, channel=chan)
            for chan in [channel, channel2]: self.set_sense_average(val=1, mode=1, channel=chan)
        elif self._sweep_mode == 1:                                            # IV-mode
            self.set_measurement_mode(val=1, channel=channel)
            self.set_bias_mode(mode=0, channel=channel)
            self.set_sense_mode(mode=1, channel=channel)
            self.set_bias_range(val=200e-3, channel=channel)
            self.set_sense_range(val=-1, channel=channel)
            self.set_bias_delay(val=15e-6, channel=channel)
            self.set_sense_delay(val=15e-6, channel=channel)
            self.set_sense_nplc(1)
            self.set_sense_average(1)
        elif self._sweep_mode == 2:                                            # VI-mode
            self.set_measurement_mode(val=1, channel=channel)
            self.set_bias_mode(mode=1, channel=channel)
            self.set_sense_mode(mode=0, channel=channel)
            self.set_bias_range(val=200e-3, channel=channel)
            self.set_sense_range(val=-1, channel=channel)
            self.set_bias_delay(val=15e-6, channel=channel)
            self.set_sense_delay(val=15e-6, channel=channel)
            self.set_sense_nplc(1)
            self.set_sense_average(1)
    
    
    def get_all(self, channel=1):
        '''
        Prints all settings of channel <channel>
        
        Input:
            channel (int) : 1 | 2
        Output:
            None
        '''
        logging.info(__name__ + ': Get all')
        print('dAdV               = {:1.0e}A/V'.format(self.get_dAdV()))
        print('dVdA               = {:1.0e}eV/A'.format(self.get_dVdA()))
        print('amplification      = {:1.0e}e'.format(self.get_amp()))
        print('measurement mode   = {:s}'.format(self._measurement_modes[self.get_measurement_mode(channel=channel)]))
        print('bias mode          = {:d}'.format(self.get_bias_mode(channel=channel)))
        print('sense mode         = {:d}'.format(self.get_sense_mode(channel=channel)))
        print('bias range         = {:1.0e}{:s}'.format(self.get_bias_range(channel=channel), self._IV_units[self.get_bias_mode(channel=channel)]))
        print('sense range        = {:1.0e}{:s}'.format(self.get_sense_range(channel=channel), self._IV_units[self.get_sense_mode(channel=channel)]))
        print('bias delay         = {:1.3e}s'.format(self.get_bias_delay(channel=channel)))
        print('sense delay        = {:1.3e}s'.format(self.get_sense_delay(channel=channel)))
        print('sense average      = {:f}'.format(self.get_sense_average(channel=channel)[1]))
        print('sense average type = {:s}'.format(self._avg_types[self.get_sense_average(channel=channel)[2]]))
        print('plc                = {:f}Hz'.format(self.get_plc()))
        print('sense nplc         = {:f}'.format(self.get_sense_nplc(channel=channel)))
        print('status             = {!r}'.format(self.get_status(channel=channel)))
        print('bias value         = {:f}{:s}'.format(self.get_bias_value(channel=channel), self._IV_units[self.get_bias_mode(channel=channel)]))
        print('sense value        = {:f}{:s}'.format(self.get_sense_value(channel=channel), self._IV_units[self.get_sense_mode(channel=channel)]))
        #for err in self.get_error(): print('error\t\t   = {:d}\n\t\t     {:s}\n\t\t     {:d}'.format(err[0], err[1], err[2]))
    
    
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
            logging.info(__name__ + ': Resetting instrument')
            self._write('reset()')
            self._write('status.reset()')
            #self.get_all()
        else:
            try:
                logging.info(__name__ + ': Resetting channel {:s}'.format(chr(64+channel)))
                self._write('smu{:s}.reset()'.format(chr(96+channel)))
            except AttributeError as e:
                logging.error(__name__ + ': Invalid input: cannot reset channel {:s}: {:s}'.format(chr(64+channel), e))
    
    
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
            logging.debug(__name__ + ': Abort running command of channel {:s}'.format(chr(64+channel)))
            return self._write('smu{:s}.abort()'.format(chr(96+channel)))
        except AttributeError as e:
            logging.error(__name__ + ': Cannot abort running command of channel {:s}: {:s}'.format(chr(64+channel), e))
    
    
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
            err = [self._ask('errorqueue.next()').split('\t') for i in range(int(float(self._ask('errorqueue.count'))))]
            err = [[int(float(e[0])), str(e[1]), int(float(e[2]))] for e in err]
            if err == []: err = [[0, 'no error', 0]]
            return err
        except ValueError as e:
            logging.error(__name__ + ': Error not specified: {:s}'.format(e))
    
    
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
        except AttributeError as e:
            logging.error(__name__ + ': Invalid input: cannot clear error: {:s}'.format(e))
    
    
    def close(self):
        '''
        Closes the VISA-instrument to disconnect the instrument
        
        Input:
            None
        Output:
            None
        '''
        try:
            logging.debug(__name__ + ': Close VISA-instrument')
            self._visainstrument.close()
        except AttributeError as e:
            logging.error(__name__ + ': Invalid input: cannot close VISA-instrument: {:s}'.format(e))
    