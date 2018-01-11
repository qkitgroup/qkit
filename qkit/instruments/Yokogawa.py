# Yokogawa.py driver for Yokogawa GS820 multi channel source measure unit
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
import logging
import numpy
import time
from distutils.version import LooseVersion


class Yokogawa(Instrument):
    '''
    This is the driver for the Yokogawa GS820 Multi Channel Source Measure Unit
    
    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Yokogawa', address='<GBIP address>', reset=<bool>)
    '''
    
    def __init__(self, name, address, reset=False):
        '''
        Initializes the Yokogawa_GS820, and communicates with the wrapper.
        
        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address
            reset (bool)     : resets to default values, default=False
        '''
        # Start VISA communication
        logging.info(__name__ + ' : Initializing instrument Yokogawa_GS820')
        Instrument.__init__(self, name, tags=['physical'])
        self._address = address
        self._visainstrument = visa.instrument(self._address)
        
        # Set termination characters (nessecarry for Ethernet communication)
        if  LooseVersion(visa.__version__) < LooseVersion("1.5.0"):            # pyvisa 1.4
            self._visainstrument.term_chars = ''
        else:                                                                  # pyvisa 1.8
            self._visainstrument.read_termination  = ''
            self._visainstrument.write_termination = ''
        
        # Global constants
        self._measurement_modes     = {0:'2-wire', 1:'4-wire'}
        self._IV_modes              = {0:'curr', 1:'volt'}
        self._IV_units              = {0:'A', 1:'V'}
        self._bias_status_register  = [('EOS1', 'CH1 End of Sweep'),
                                       ('RDY1', 'CH1 Ready for Sweep'),
                                       ('LL01', 'CH1 Low Limiting'),
                                       ('LHI1', 'CH1 High Limiting'),
                                       ('TRP1', 'CH1 Tripped'),
                                       ('EMR1', 'CH1 Emergency (Temperature/Current over)'),
                                       ('', ''),
                                       ('', ''),
                                       ('EOS2', 'CH2 End of Sweep'),
                                       ('RDY2', 'CH2 Ready for Sweep'),
                                       ('LL02', 'CH2 Low Limiting'),
                                       ('LHI2', 'CH2 High Limiting'),
                                       ('TRP2', 'CH2 Tripped'),
                                       ('EMR2', 'CH2 Emergency (Temperature/Current over)'),
                                       ('ILC',  'Inter Locking'),
                                       ('SSB',  'Start Sampling Error')]
        self._sense_status_register = [('EOM1', 'CH1 End of Measure'),
                                       ('', ''),
                                       ('CLO1', 'CH1 Compare result is Low'),
                                       ('CHI1', 'CH1 Compare result is High'),
                                       ('', ''),
                                       ('OVR1', 'CH1 Over Range'),
                                       ('', ''),
                                       ('', ''),
                                       ('EOM2', 'CH2 End of Measure'),
                                       ('', ''),
                                       ('CLO2', 'CH2 Compare result is Low'),
                                       ('CHI2', 'CH1 Compare result is High'),
                                       ('', ''),
                                       ('OVR2', 'CH2 Over Range'),
                                       ('EOT', 'End of Trace'),
                                       ('TSE', 'Trigger Sampling Error')]
        
        # external measuremnt setup
        self._dAdV = 1
        self._dVdA = 1
        self._amp = 1
        self._sweep_mode = 0       # VV-mode
        self._pseudo_bias_mode = 0 # current bias
        
        # Reset
        if reset: self.reset()
        else: self.get_all()
    
    
    
    def _write(self, msg):
        '''
        Sends a visa command <msg>
        
        Input:
            msg (str)
        Output:
            None
        '''
        return self._visainstrument.write(msg)
    
    
    def _ask(self, msg):
        '''
        Sends a visa command <msg> and returns the read answer <ans>
        
        Input:
            msg (str)
        Output:
            ans (str)
        '''
        if '?' in msg: return self._visainstrument.ask(msg).rstrip()
        else: return self._visainstrument.ask('%s?' % msg).rstrip()
    
    
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
    
    
    def set_pseudo_bias_mode(self, mode=0):
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
            mode (int) : 0 (current bias) | 1 (voltage bias)
        '''
        return self._pseudo_bias_mode
    
    
    def set_measurement_mode(self, val, channel=1):
        '''
        Sets measurement mode (wiring system) of channel <channel> to <val>
        
        Input:
            channel (int) : 1 (default) | 2
            val (int)     : 0 (2-wire) | 1 (4-wire)
        Output:
            None
        '''
        # Corresponding Command: [:CHANnel<n>]:SENSe:REMote 1|0|ON|OFF
        try:
            logging.debug(__name__ + ' : set measurement mode of channel %i to %i' % (channel, val))
            self._write(':chan%i:sens:rem %i' % (channel, val))
        except AttributeError:
            logging.error(__name__ + ': Invalid input: cannot set measurement mode of channel %i to %f' % (channel, val))
    
    
    def get_measurement_mode(self, channel=1):
        '''
        Gets measurement mode (wiring system) of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            val (int)     : 0 (2-wire) | 1 (4-wire)
        '''
        # Corresponding Command: [:CHANnel<n>]:SENSe:REMote 1|0|ON|OFF
        try:
            logging.debug(__name__ + ': get measurement mode of channel %i' % channel)
            return int(self._ask(':chan%i:sens:rem' % channel))
        except ValueError:
            logging.error(__name__ + ': Measurement mode of channel %i not specified:' % channel)
    
    
    def set_sync(self, val):
        '''
        Sets the interchannel synchronization to <val>
        (The first channel is always the "master", the second the "slave")
        
        Input:
            val (bool) : 0 (off) | 1 (on)
        Output:
            None
        '''
        # Corresponding Command: :SYNChronize:CHANnel 1|0|ON|OFF
        try:
            logging.debug(__name__ + ': Set the channels in synchronized mode to %i' % val)
            self._write(':sync:chan %i' % val)
        except AttributeError:
            logging.error(__name__ + ': Invalid input: cannot set the interchannel synchronization to %f' % val)
    
    
    def get_sync(self):
        '''
        Gets the interchannel synchronization
        
        Input:
            None
        Output:
            val (bool) : 0 (off) | 1 (on)
        '''
        # Corresponding Command: :SYNChronize:CHANnel 1|0|ON|OFF
        try:
            logging.debug(__name__ + ': Get the channels in synchronized mode')
            return bool(int(self._ask(':sync:chan')))
        except ValueError:
            logging.error(__name__ + ': Interchannel synchronization not specified:')
    
    
    def set_bias_mode(self, mode, channel=1):
        '''
        Sets bias mode of channel <channel> to <mode> regime
        
        Input:
            mode (int)    : 0 (current) | 1 (voltage)
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        # Corresponding Command: [:CHANnel<n>]:SOURce:FUNCtion VOLTage|CURRent
        try:
            logging.debug(__name__ + ': Set bias mode of channel %i to %s' % (channel, mode))
            self._write(':chan%i:sour:func %s' % (channel, self._IV_modes[mode]))
        except AttributeError:
            logging.error(__name__ + ': Invalid input: cannot set bias mode of channel %i to %s' % (channel, mode))
    
    
    def get_bias_mode(self, channel=1):
        '''
        Gets bias mode of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            mode (int)    : 0 (current) | 1 (voltage)
        '''
        # Corresponding Command: [:CHANnel<n>]:SOURce:FUNCtion VOLTage|CURRent
        try:
            logging.debug(__name__ + ': get bias mode of channel %i' % channel)
            return int(self._IV_modes.keys()[self._IV_modes.values().index(self._ask(':chan%i:sour:func' % channel).lower())])
        except ValueError:
            logging.error(__name__ + ': Bias mode of channel %i not specified:' % channel)
    
    
    def set_sense_mode(self, mode, channel=1):
        '''
        Sets sense mode of channel <channel> to <mode> regime
        
        Input:
            mode (int)    : 0 (current) | 1 (voltage)
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        # Corresponding Command: [:CHANnel<n>]:SENSe:FUNCtion VOLTage|CURRent
        try:
            logging.debug(__name__ + ': Set sense mode of channel %i to %s' % (channel, mode))
            self._write(':chan%i:sens:func %s' % (channel, self._IV_modes[mode]))
        except AttributeError:
            logging.error(__name__ + ': Invalid input: cannot set sense mode of channel %i to %s' % (channel, mode))
    
    
    def get_sense_mode(self, channel=1):
        '''
        Gets sense mode <mdoe> of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            mode (str)    : 'volt' | 'curr'
        '''
        # Corresponding Command: [:CHANnel<n>]:SENSe:FUNCtion VOLTage|CURRent
        try:
            logging.debug(__name__ + ': Get sense mode of channel %i' % channel)
            return int(self._IV_modes.keys()[self._IV_modes.values().index(self._ask(':chan%i:sens:func' % channel).lower())])
        except ValueError:
            logging.error(__name__ + ': Sense mode of channel %i not specified:' % channel)
    
    
    def set_bias_range(self, val, channel=1):
        '''
        Sets bias range of channel <channel> to <val>
        
        Input:
            val (float)   : -1 (auto) | 200mV | 2V | 7V | 18V | 200nA | 2uA | 20uA | 200uA | 2mA | 20mA | 200mA | 1 A | 3A
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        # Corresponding Command: [:CHANnel<n>]:SOURce[:VOLTage]:RANGe <voltage>|MINimum|MAXimum|UP|DOWN 
        # Corresponding Command: [:CHANnel<n>]:SOURce[:CURRent]:RANGe <current>|MINimum|MAXimum|UP|DOWN 
        try:
            logging.debug(__name__ + ': Set bias voltage range of channel %i to %f' % (channel, val))
            if val == -1: self._write(':chan%i:sour:rang:auto 1' % channel)
            else: self._write(':chan%i:sour:rang %f' % (channel, val))
        except AttributeError:
            logging.error(__name__ + ': Invalid input: cannot set bias range of channel %i to %f' % (channel, val))
    
    
    def get_bias_range(self, channel=1):
        '''
        Gets bias range for the current mode.
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            val (float)   : 200mV | 2V | 7V | 18V | 200nA | 2uA | 20uA | 200uA | 2mA | 20mA | 200mA | 1 A | 3A
        '''
        # Corresponding Command: [:CHANnel<n>]:SOURce[:VOLTage]:RANGe <voltage>|MINimum|MAXimum|UP|DOWN 
        # Corresponding Command: [:CHANnel<n>]:SOURce[:CURRent]:RANGe <current>|MINimum|MAXimum|UP|DOWN 
        try:
            logging.debug(__name__ + ': Get bias voltage range of channel %i' % channel)
            return float(self._ask(':chan%i:sour:rang' % channel))
        except ValueError:
            logging.error(__name__ + ': Bias range of channel %i not specified:' % channel)
    
    
    def set_sense_range(self, val, channel=1):
        '''
        Sets sense range of channel <channel> to <val>
        
        Input:
            val (float)   : -1 (auto) | 200mV | 2V | 7V | 18V | 200nA | 2uA | 20uA | 200uA | 2mA | 20mA | 200mA | 1 A | 3A
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        # Corresponding Command: [:CHANnel<n>]:SENSe[:VOLTage]:RANGe <voltage>|MINimum|MAXimum|UP|DOWN
        # Corresponding Command: [:CHANnel<n>]:SENSe[:CURRent]:RANGe <current>|MINimum|MAXimum|UP|DOWN
        try:
            logging.debug(__name__ + ': Set sense range of channel %i to %f' % (channel, val))
            if val == -1: self._write(':chan%i:sens:rang:auto 1' % channel)
            else: self._write(':chan%i:sens:rang %f' % (channel, val))
        except AttributeError:
            logging.error(__name__ + ': Invalid input: cannot set sense range of channel %i to %f' % (channel, val))
    
    
    def get_sense_range(self, channel=1):
        '''
        Gets sense range for the current mode.
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            val (float)   : 200mV | 2V | 7V | 18V | 200nA | 2uA | 20uA | 200uA | 2mA | 20mA | 200mA | 1 A | 3A
        '''
        # Corresponding Command: [:CHANnel<n>]:SENSe[:VOLTage]:RANGe <voltage>|MINimum|MAXimum|UP|DOWN
        # Corresponding Command: [:CHANnel<n>]:SENSe[:CURRent]:RANGe <current>|MINimum|MAXimum|UP|DOWN
        try:
            logging.debug(__name__ + ': Get sense range of channel %i' % channel)
            return float(self._ask(':chan%i:sens:rang' % channel))
        except ValueError:
            logging.error(__name__ + ': Sense range of channel %i not specified:' % channel)
    
    
    def set_bias_trigger(self, mode, channel=1, **val):
        '''
        Sets bias trigger mode of channel <channel> to <mode> and value <val>
        If <mode> is 'timer' it can be set to <time>
        
        Input:
            mode (str)    : ext (external) | aux (auxiliary) | tim1 (timer1) | tim2 (timer2) | sens (sense)
            channel (int) : 1 (default) | 2
            **val         : 100us <= time (float) <= 3600.000000s
        Output:
            None
        '''
        # Corresponding Command: [:CHANnel<n>]:SOURce:TRIGger EXTernal|AUXiliary|TIMer1|TIMer2|SENSe
        # Corresponding Command: :TRIGger:TIMer1 <time>|MINimum|MAXimum
        try:
            logging.debug(__name__ + ': Set bias trigger of channel %i to %s' % (channel, mode))
            self._write(':chan%i:sour:trig %s' % (channel, mode))
            if 'time' in val: self._write(':trig:%s %f' % (mode, val.get('time', 50e-3)))
        except AttributeError:
            logging.error(__name__ + ': Invalid input: cannot set bias trigger of channel %i to %s' % (channel, mode))
    
    
    def get_bias_trigger(self, channel=1):
        '''
        Gets bias trigger of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            trigger (str) : ext (external) | aux (auxiliary) | tim1 (timer1) | tim2 (timer2) | sens (sense)
        '''
        # Corresponding Command: [:CHANnel<n>]:SOURce:TRIGger EXTernal|AUXiliary|TIMer1|TIMer2|SENSe
        try:
            logging.debug(__name__ + ': Get bias trigger of channel %i' % channel)
            return str(self._ask(':chan%i:sour:trig' % channel).lower())
        except ValueError:
            logging.error(__name__ + ': Bias trigger of channel %i not specified:' % channel)
    
    
    def set_sense_trigger(self, mode, channel=1, **val):
        '''
        Sets sense trigger mode of channel <channel> to <trigger> and value <val>
        If <mode> is 'timer' it can be set to <time>
        
        Input:
            mode (str)    : ext (external) | aux (auxiliary) | tim1 (timer1) | tim2 (timer2) | sens (sense)
            channel (int) : 1 (default) | 2
            **val         : 100us <= time (float) <= 3600.000000s
        Output:
            None
        '''
        # Corresponding Command: [:CHANnel<n>]:SENSe:TRIGger EXTernal|AUXiliary|TIMer1|TIMer2|SENSe
        # Corresponding Command: :TRIGger:TIMer1 <time>|MINimum|MAXimum
        try:
            logging.debug(__name__ + ': Set sense trigger of channel %i to %s' % (channel, mode))
            self._write(':chan%i:sens:trig %s' % (channel, mode))
            if 'time' in val: self._write(':trig:%s %f' % (mode, val.get('time', 50e-3)))
        except AttributeError:
            logging.error(__name__ + ': Invalid input: cannot set sense trigger of channel %i to %s' % (channel, mode))
    
    
    def get_sense_trigger(self, channel=1):
        '''
        Gets sense trigger of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            trigger (str) : ext (external) | aux (auxiliary) | tim1 (timer1) | tim2 (timer2) | sens (sense)
        '''
        # Corresponding Command: [:CHANnel<n>]:SENSe:TRIGger EXTernal|AUXiliary|TIMer1|TIMer2|SENSe
        try:
            logging.debug(__name__ + ': Get sense trigger of channel %i' % channel)
            return str(self._ask(':chan%i:sens:trig' % channel).lower())
        except ValueError:
            logging.error(__name__ + ': Sense trigger of channel %i not specified:' % channel)
    
    
    def set_bias_delay(self, val, channel=1):
        '''
        Sets bias delay of channel <channel> to <val>
        
        Input:
            val (float)   : 15us <= delay <= 3600s
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        # Corresponding Command: [:CHANnel<n>]:SOURce:DELay <time>|MINimum|MAXimum
        try:
            logging.debug(__name__ + ': Set bias delay of channel %i to %f' % (channel, val))
            self._write(':chan%i:sour:del %f' % (channel, val))
        except AttributeError:
            logging.error(__name__ + ': Invalid input: cannot set bias delay of channel %i to %f' % (channel, val))
    
    
    def get_bias_delay(self, channel=1):
        '''
        Gets bias delay of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            val (float)
        '''
        # Corresponding Command: [:CHANnel<n>]:SOURce:DELay <time>|MINimum|MAXimum
        try:
            logging.debug(__name__ + ': Get bias delay of channel %i' % channel)
            return float(self._ask(':chan%i:sour:del' % channel))
        except ValueError:
            logging.error(__name__ + ': Bias delay of channel %i not specified:' % channel)
    
    
    def set_sense_delay(self, val, channel=1):
        '''
        Sets sense delay of channel <channel> to <val>
        
        Input:
            val (float)   : 15us <= delay <= 3600s
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        # Corresponding Command: [:CHANnel<n>]:SOURce:DELay <time>|MINimum|MAXimum
        try:
            logging.debug(__name__ + ': Set sense delay of channel %i to %f' % (channel, val))
            self._write(':chan%i:sens:del %f' % (channel, val))
        except AttributeError:
            logging.error(__name__ + ': Invalid input: cannot set sense delay of channel %i to %f' % (channel, val))
    
    
    def get_sense_delay(self, channel=1):
        '''
        Gets sense delay of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            val (float)
        '''
        # Corresponding Command: [:CHANnel<n>]:SENSe:DELay <time>|MINimum|MAXimum
        try:
            logging.debug(__name__ + ': Get sense delay of channel %i' % channel)
            return float(self._ask(':chan%i:sens:del' % channel))
        except ValueError:
            logging.error(__name__ + ': Sense delay of channel %i not specified:' % channel)
    
    
    def set_sense_average(self, val, channel=1):
        '''
        Sets sense average of channel <channel> to <val>.
        If <val> is less than 1 average status is turned off, but the set value remains.
        
        Input:
            val (int)
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        # Corresponding Command: [:CHANnel<n>]:SENSe:AVERage[:STATe] 1|0|ON|OFF
        # Corresponding Command: [:CHANnel<n>]:SENSe:AVERage:COUNt <integer>|MINimum|MAXimum
        try:
            logging.debug(__name__ + ': Set sense average of channel %i to %i' % (channel, val))
            status = not(.5*(1-numpy.sign(val-1)))                             # equals Heaviside(1-val) --> turns on for <val> >= 2
            self._write(':chan%i:sens:aver:stat %i' % (channel, status))
            if status: self._write(':chan%i:sens:aver:coun %i' % (channel, val))
        except AttributeError:
            logging.error(__name__ + ': Invalid input: cannot set sense average of channel %i to %i' % (channel, val))
    
    
    def get_sense_average(self, channel=1):
        '''
        Gets sense average of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            status (bool)
            val (int)
        '''
        # Corresponding Command: [:CHANnel<n>]:SENSe:AVERage[:STATe] 1|0|ON|OFF
        # Corresponding Command: [:CHANnel<n>]:SENSe:AVERage:COUNt <integer>|MINimum|MAXimum
        try:
            logging.debug(__name__ + ': Get sense average of channel %i' % channel)
            status = bool(int(self._ask(':chan%i:sens:aver:stat' % channel)))
            val = int(self._ask(':chan%i:sens:aver:coun' % channel))
            return status, val
        except ValueError:
            logging.error(__name__ + ': Sense average of channel %i not specified:' % channel)
    
    
    def set_plc(self, plc):
        '''
        Sets power line cycle (PLC) to <plc>
        
        Input:
            plc (int) : -1 (auto) | 50 | 60
        Output:
            None
        '''
        # Corresponding Command: :SYSTem:LFRequency 50|60
        # Corresponding Command: :SYSTem:LFRequency:AUTO 1|0|ON|OFF
        try:
            logging.debug(__name__ + ': Set PLC to %s' % str(plc))
            cmd = {-1:':auto 1', 50:' 50', 60:' 60'}
            self._write('syst:lfr%s' % cmd.get(int(plc), cmd[-1]))
        except ValueError:
            logging.error(__name__ + ': PLC not specified:')
    
    
    def get_plc(self):
        '''
        Gets power line cycle (PLC)
        
        Input:
            None
        Output:
            plc (int) : 50 | 60
        '''
        # Corresponding Command: :SYSTem:LFRequency 50|60
        # Corresponding Command: :SYSTem:LFRequency:AUTO 1|0|ON|OFF
        try:
            logging.debug(__name__ + ': Get PLC')
            return int(self._ask('syst:lfr'))
        except ValueError:
            logging.error(__name__ + ': PLC not specified:')
    
    
    def set_sense_nplc(self, val, channel=1):
        '''
        Sets sense integrarion time of channel <channel> with the <val>-fold of one power line cycle
        
        Input:
            channel (int) : 1 (default) | 2
            val (int)     : [1, 25]
        Output:
            None
        '''
        # Corresponding Command: [:CHANnel<n>]:SENSe:NPLC <real number>|MINimum|MAXimum
        try:
            logging.debug(__name__ + ': Set sense integrarion time of channel %i to %i PLC' % (channel, val))
            self._write(':chan%i:sens:nplc %i' % (channel, val))
        except ValueError:
            logging.error(__name__ + ': Number of PLC of channel %i not specified:' % channel)
    
    
    def get_sense_nplc(self, channel=1):
        '''
        Gets sense integrarion time of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            val (int)
        '''
        # Corresponding Command: [:CHANnel<n>]:SENSe:NPLC <real number>|MINimum|MAXimum
        try:
            logging.debug(__name__ + ': Get sense integrarion time of channel %i' % channel)
            return float(self._ask(':chan%i:sens:nplc' % channel))
        except ValueError:
            logging.error(__name__ + ': Number of PLC of channel %i not specified:' % channel)
    
    
    def set_status(self, status, channel=1):
        '''
        Sets output status of channel <channel> to <status>
        
        Input:
            status (bool) : False (off) | True (on)
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        # Corresponding Command: [:CHANnel<n>]:OUTput:STATus 1|0|ON|OFF
        try:
            logging.debug(__name__ + ': Set output status of channel %i to %r' % (channel, status))
            self._write(':chan%i:outp:stat %i' % (channel, status))
        except AttributeError:
            logging.error(__name__ + ': Invalid input: cannot set output status of channel %i to %r' % (channel, status))
    
    
    def get_status(self, channel=1):
        '''
        Gets output status of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            status (bool) : False (off) | True (on)
        '''
        # Corresponding Command: [:CHANnel<n>]:OUTput:STATus 1|0|ON|OFF
        try:
            logging.debug(__name__ + ': Get output status of channel %i' % channel)
            return bool(int(self._ask(':chan%i:outp:stat' % channel)))
        except ValueError:
            logging.error(__name__ + ': Status of channel %i not specified:' % channel)
    
    
    def set_stati(self, status):
        '''
        Sets output status of both channels to <status>
        
        Input:
            status (int)  : 0 (off) | 1 (on) | 2 (high Z)
        Output:
            None
        '''
        for channel in range(1,3): self.set_status(status=status, channel=channel)
    
    
    def get_stati(self):
        '''
        Gets output status of both channels
        
        Input:
            None
        Output:
            status (int)  : 0 (off) | 1 (on) | 2 (high Z)
        '''
        stati = []
        for channel in range(1,3): stati.append(self.get_status(channel=channel))
        return stati
    
    
    def set_bias_value(self, val, channel=1):
        '''
        Sets bias value of channel <channel> to value >val>
        
        Input:
            val (float)
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        # Corresponding Command: [:CHANnel<n>]:SOURce[:VOLTage]:LEVel <voltage>|MINimum|MAXimum
        # Corresponding Command: [:CHANnel<n>]:SOURce[:CURRent]:LEVel <current>|MINimum|MAXimum
        try:
            logging.debug(__name__ + ' : Set bias value of channel %i to %f' % (channel, val))
            self._write(':chan%i:sour:lev %f' % (channel, val))
        except AttributeError:
            logging.error(__name__ + ': Invalid input: cannot set bias value of channel %i to %f' % (channel, val))
    
    
    def get_bias_value(self, channel=1):
        '''
        Gets bias value of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            val (float)
        '''
        # Corresponding Command: [:CHANnel<n>]:SOURce[:VOLTage]:LEVel <voltage>|MINimum|MAXimum
        # Corresponding Command: [:CHANnel<n>]:SOURce[:CURRent]:LEVel <current>|MINimum|MAXimum
        try:
            logging.debug(__name__ + ' : Get bias value of channel %i' % channel)
            return float(self._ask(':chan%i:sour:lev' % channel))
        except ValueError:
            logging.error(__name__ + ': Cannot get bias value of channel %i:' % channel)
    
    
    def get_sense_value(self, channel=1):
        '''
        Gets sense value of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            val (float)
        '''
        # Corresponding Command: [:CHANnel<n>]:MEASure?
        # Corresponding Command: [:CHANnel<n>]:FETCh? [DUAL]
        try:
            logging.debug(__name__ + ' : Get sense value of channel %i' % channel)
            #return float(self._ask(':chan%i:meas' % channel))
            return float(self._ask(':chan%i:fetc' % channel))
        except ValueError:
            logging.error(__name__ + ': Cannot get sense value of channel %i:' % channel)
    
    
    def set_voltage(self, val, channel=1):
        '''
        Sets voltage value of channel <channel> to <val>
        
        Input:
            val (float)
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        if self.get_bias_mode(channel) == 1:                                   # voltage bias
            return self.set_bias_value(val, channel)
        elif self.get_bias_mode(channel) == 0:                                 # current bias
            logging.error(__name__ + ': Cannot set voltage value of channel %i: in the current bias' % channel)
    
    
    def get_voltage(self, channel=1):
        '''
        Gets voltage value of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            val (float)
        '''
        if self.get_bias_mode(channel) == 1:                                   # voltage bias
            return self.get_bias_value(channel)
        elif self.get_sense_mode(channel) == 1:                                # voltage sense
            return self.get_sense_value(channel)
        else:
            logging.error(__name__ + ': Cannot get voltage value of channel %i: neihter bias nor sense in voltage mode' % channel)
    
    
    def set_current(self, val, channel=1):
        '''
        Sets current value of channel <channel> to <val>
        
        Input:
            val (float)
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        if self.get_bias_mode(channel) == 0:                                   # current bias
            return self.set_bias_value(val, channel)
        elif self.get_bias_mode(channel) == 1:                                 # voltage bias
            logging.error(__name__ + ': Cannot set current value of channel %i: in the voltage bias' % channel)
    
    
    def get_current(self, channel=1):
        '''
        Gets current value of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            val (float)
        '''
        if self.get_bias_mode(channel) == 0:                                   # current bias
            return self.get_bias_value(channel)
        elif self.get_sense_mode(channel) == 0:                                # current sense
            return self.get_sense_value(channel)
        else:
            logging.error(__name__ + ': Cannot get current value of channel %i: neihter bias nor sense in current mode' % channel)
    
    
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
        start = self.get_current(channel=channel)
        if (stop < start): step = -step
        for val in numpy.arange(start, stop, step)+step:
            self.set_current(val, channel=channel)
            time.sleep(step_time)
    
    
    def set_sweep_start(self, val, channel=1):
        '''
        Sets sweep start value of channel <channel> to <val>
        
        Input:
            val (float)
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        # Corresponding Command: [:CHANnel<n>]:SOURce[:VOLTage]:SWEep:STARt <voltage>|MINiumum|MAXimum
        try:
            logging.debug(__name__ + ': Set sweep start of channel %i to %f' % (channel, val))
            #self._write(':chan%i:sour:swe:star %f' % (channel, val))
            self._write(':chan%i:sour:%s:swe:star %f' % (channel, self._IV_modes[self.get_bias_mode(channel)], val))
        except AttributeError:
            logging.error(__name__ + ': Invalid input: cannot set sweep start of channel %i to %f' % (channel, val))
    
    
    def get_sweep_start(self, channel=1):
        '''
        Gets sweep start value of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            val (float)
        '''
        # Corresponding Command: [:CHANnel<n>]:SOURce[:VOLTage]:SWEep:STARt <voltage>|MINiumum|MAXimum
        try:
            logging.debug(__name__ + ': Get sweep start of channel %i' % channel)
            return float(self._ask(':chan%i:sour:%s:swe:star' % (channel, self._IV_modes[self.get_bias_mode(channel)])))
            #return float(self._ask(':chan%i:sour:swe:star' % channel))
        except ValueError:
            logging.error(__name__ + ': Sweep start of channel %i not specified:' % channel)
    
    
    def set_sweep_stop(self, val, channel=1):
        '''
        Sets sweep stop value of channel <channel> to <val>
        
        Input:
            val (float)
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        # Corresponding Command: [:CHANnel<n>]:SOURce[:VOLTage]:SWEep:STARt <voltage>|MINiumum|MAXimum
        try:
            logging.debug(__name__ + ': Set sweep stop of channel %i to %f' % (channel, val))
            self._write(':chan%i:sour:%s:swe:stop %f' % (channel, self._IV_modes[self.get_bias_mode(channel)], val))
            #self._write(':chan%i:sour:swe:stop %f' % (channel, val))
        except AttributeError:
            logging.error(__name__ + ': Invalid input: cannot set sweep stop of channel %i to %f' % (channel, val))
    
    
    def get_sweep_stop(self, channel=1):
        '''
        Gets sweep stop value of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            val (float)
        '''
        # Corresponding Command: [:CHANnel<n>]:SOURce[:VOLTage]:SWEep:STARt <voltage>|MINiumum|MAXimum
        try:
            logging.debug(__name__ + ': Get sweep stop of channel %i' % channel)
            return float(self._ask(':chan%i:sour:%s:swe:stop' % (channel, self._IV_modes[self.get_bias_mode(channel)])))
            #return float(self._ask(':chan%i:sour:swe:stop' % channel))
        except ValueError:
            logging.error(__name__ + ': Sweep stop of channel %i not specified:' % channel)
    
    
    def set_sweep_step(self, val, channel=1):
        '''
        Sets sweep step value of channel <channel> to <val>
        
        Input:
            val (float)
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        # Corresponding Command: [:CHANnel<n>]:SOURce[:VOLTage]:SWEep:STARt <voltage>|MINiumum|MAXimum
        try:
            logging.debug(__name__ + ': Set sweep step of channel %i to %f' % (channel, val))
            self._write(':chan%i:sour:%s:swe:step %f' % (channel, self._IV_modes[self.get_bias_mode(channel)], val))
            #self._write(':chan%i:sour:swe:step %f' % (channel, val))
        except AttributeError:
            logging.error(__name__ + ': Invalid input: cannot set sweep step of channel %i to %f' % (channel, val))
    
    
    def get_sweep_step(self, channel=1):
        '''
        Gets sweep step value of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            val (float)
        '''
        # Corresponding Command: [:CHANnel<n>]:SOURce[:VOLTage]:SWEep:STARt <voltage>|MINiumum|MAXimum
        try:
            logging.debug(__name__ + ': Get sweep step of channel %i' % channel)
            return float(self._ask(':chan%i:sour:%s:swe:step' % (channel, self._IV_modes[self.get_bias_mode(channel)])))
            #return float(self._ask(':chan%i:sour:swe:step' % channel))
        except ValueError:
            logging.error(__name__ + ': Sweep step of channel %i not specified:' % channel)
    
    
    def get_sweep_nop(self, channel=1):
        '''
        Gets sweep nop of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            val (int)
        '''
        try:
            logging.debug(__name__ + ': Get sweep nop of channel %i' % channel)
            return int((self.get_sweep_stop(channel=channel)-self.get_sweep_start(channel=channel))/self.get_sweep_step(channel=channel)+1)
        except ValueError:
            logging.error(__name__ + ': Sweep nop of channel %i not specified:' % channel)
    
    
    def get_sweeptime(self, channel=1):
        '''
        Gets sweep time of channel <channel>
        
        Input:
            channel (int): 1 | 2
        Output:
            val (float)
        '''
        try:
            logging.debug(__name__ + ': Get sweep time of channel %i' % channel)
            return float((self.get_nplc(channel=channel)/self.get_plc(channel=channel)+self.get_bias_delay(channel=channel)+self.get_sense_delay(channel=channel))*(self.get_sweep_nop(channel=channel)-1))
        except ValueError:
            logging.error(__name__ + ': Sweep time of channel %i not specified:' % channel)
    
    
    def set_sweep_parameters(self, sweep, channel=1, channel2=2):
        '''
        Sets sweep parameters <sweep> and prepares instrument for VV-mode or IV-mode.
        VV-mode needs two different channels (bias channel <channel> and sense channel <channel2>), IV-mode and VI-mode only one (<channel>).
        
        Input:
            sweep obj(float) : start, stop, step
            channel (int)    : 1 (default) | 2
            channel2 (int)   : 1 | 2 (default)
        Output:
            None
        '''
        # Corresponding Command: [:CHANnel<n>]:SOURce:MODE FIXed|SWEep|LIST|SINGle
        # Corresponding Command: [:CHANnel<n>]:SWEep:TRIGger EXTernal|AUXiliary|TIMer1|TIMer2|SENSe
        # Corresponding Command: :TRACe:POINts <integer>|MINimum|MAXimum
        # Corresponding Command: :TRACe:CHANnel<n>:DATA:FORMat ASCii|BINary
        # Corresponding Command: :TRACe:BINary:REPLy BINary|ASCii
        # Corresponding Command: :TRACe[:STATe] 1|0|ON|OFF
        if self._sweep_mode == 0:                                              # VV-mode
            try:
                if self._pseudo_bias_mode == 0:     # current bias
                    self.set_sweep_start(val=float(sweep[0])/self._dAdV, channel=channel)
                    self.set_sweep_stop(val=float(sweep[1])/self._dAdV, channel=channel)
                    self.set_sweep_step(val=numpy.abs(float(sweep[2]))/self._dAdV, channel=channel) 
                if self._pseudo_bias_mode == 1:     # voltage bias
                    self.set_sweep_start(val=float(sweep[0])/self._amp, channel=channel)
                    self.set_sweep_stop(val=float(sweep[1])/self._amp, channel=channel)    
                    self.set_sweep_step(val=numpy.abs(float(sweep[2]))/self._amp, channel=channel)
                self.set_bias_trigger(mode='sens', channel=channel)
                self.set_sense_trigger(mode='sour', channel=channel2)
                self.set_bias_value(val=self.get_sweep_start(channel=channel), channel=channel)
                self._write(':chan%i:sour:mode swe' % channel)
                self._write(':chan%i:swe:trig ext' % channel)
                self._write(':trac:poin max')  # alternative: self._write(':trac:poin %i' % self.get_sweep_nop(channel=channel))
                self._write(':trac:chan%i:data:form asc' % channel2)
                self._write(':trac:bin:repl asc')
                self.set_sync(True)
            except:
                logging.error(__name__ + ': Cannot set sweep parameters od channel % i and %i.' % (channel, channel2))
        elif self._sweep_mode in [1, 2]:                                       # IV-mode or VI-mode
            try:
                self.set_sweep_start(val=float(sweep[0]), channel=channel)
                self.set_sweep_stop(val=float(sweep[1]), channel=channel)
                self.set_sweep_step(val=numpy.abs(float(sweep[2])), channel=channel)
                self.set_bias_trigger(mode='sens', channel=channel)
                self.set_sense_trigger(mode='sour', channel=channel)
                self.set_bias_value(val=self.get_sweep_start(channel=channel), channel=channel)
                self._write(':chan%i:sour:mode swe' % channel)
                self._write(':chan%i:swe:trig ext' % channel)
                self._write(':trac:poin max')  # alternative: self._write(':trac:poin %i' % self.get_sweep_nop(channel=channel))
                self._write(':trac:chan%i:data:form asc' % channel)
                self._write(':trac:bin:repl asc')
            except:
                logging.error(__name__ + ': Cannot set sweep parameters of channel %i' % channel)
    
    
    def get_tracedata(self, channel=1, channel2=2):
        '''
        Starts bias sweep and gets trace data in the VV-mode or IV-mode.
        VV-mode needs two different channels (bias channel <channel> and sense channel <channel2>), IV-mode and VI-mode only one (<channel>).
        
        Input:
            channel (int)    : 1 (default) | 2
            channel2 (int)   : 1 | 2 (default)
        Output:
            I_values (numpy.array(float))
            V_values (numpy.array(float))
        '''
        # Corresponding Command: [:CHANnel<n>]:INITiate [DUAL]
        # Corresponding Command: :STARt
        # Corresponding Command: :TRACe[:STATe] 1|0|ON|OFF
        # Corresponding Command: :TRACe:CHANnel<n>:DATA:READ? [TM|DO|DI|SF|SL|MF|ML|LC|HC|CP]
        if self._sweep_mode == 0:                                              # VV-mode
            try:
                self._write(':chan%i:init' % channel)
                self._wait_for_ready_for_sweep(channel=channel)
                self._write(':trac:stat 1')
                self._wait_for_OPC()
                time.sleep(100e-6)
                self._write(':star')
                self._wait_for_end_of_sweep(channel=channel)
                time.sleep(self.get_sense_delay(channel=channel2))
                self._wait_for_end_of_measure(channel=channel2)
                self._write(':trac:stat 0')
                if self._pseudo_bias_mode == 0:     # current bias
                    I_values = numpy.fromstring(string=self._ask('trac:chan%i:data:read? sl' % channel),  dtype=float, sep=',')*self._dAdV
                    V_values = numpy.fromstring(string=self._ask('trac:chan%i:data:read? ml' % channel2), dtype=float, sep=',')/self._amp
                if self._pseudo_bias_mode == 1:     # voltage bias
                    V_values = numpy.fromstring(string=self._ask('trac:chan%i:data:read? sl' % channel),  dtype=float, sep=',')*self._amp
                    I_values = numpy.fromstring(string=self._ask('trac:chan%i:data:read? ml' % channel2), dtype=float, sep=',')/self._dAdV
                return I_values, V_values
            except:
                logging.error(__name__ + ': Cannot take sweep data of channel % i and %i.' % (channel, channel2))
        elif self._sweep_mode in [1, 2]:                                       # IV-mode or VI-mode
            try:
                self._write(':chan%i:init' % channel)
                self._wait_for_ready_for_sweep(channel=channel)
                self._write(':trac:stat 1')
                self._wait_for_OPC()
                self._write(':star')
                self._wait_for_end_of_sweep(channel=channel)
                time.sleep(self.get_sense_delay(channel=channel))
                self._wait_for_end_of_measure(channel=channel)
                self._write(':trac:stat 0')
                if self._sweep_mode == 1:                                      # IV-mode
                    I_values = numpy.array([float(val) for val in self._ask('trac:chan%i:data:read? sl' % channel).split(',')])
                    V_values = numpy.array([float(val) for val in self._ask('trac:chan%i:data:read? ml' % channel).split(',')])
                if self._sweep_mode == 2:                                      # VI-mode
                    V_values = numpy.array([float(val) for val in self._ask('trac:chan%i:data:read? sl' % channel).split(',')])
                    I_values = numpy.array([float(val) for val in self._ask('trac:chan%i:data:read? ml' % channel).split(',')])
                return I_values, V_values
            except:
                logging.error(__name__ + ': Cannot take sweep of channel %i:' % channel)
    
   
    def take_IV(self, sweep, channel=1, channel2=2):
        '''
        Takes IV curve with sweep parameters <sweep> in the VV-mode or IV-mode.
        VV-mode needs two different channels (bias channel <channel> and sense channel <channel2>), IV-mode and VI-mode only one (<channel>).
        
        Input:
            sweep obj(float): start, stop, step
            channel_bias (int)  : 1 (default) | 2
            channel_sense (int) : 1 | 2 (default)
        Output:
            bias_values (numpy.array(float))
            sense_values (numpy.array(float))
        '''
        if self._sweep_mode == 0:                                              # VV-mode
            self.set_sweep_parameters(sweep=sweep, channel=channel, channel2=channel2)
            return self.get_tracedata(channel=channel, channel2=channel2)
        elif self._sweep_mode in [1, 2]:                                       # IV-mode or VI-mode
            self.set_sweep_parameters(sweep=sweep, channel=channel)
            return self.get_tracedata(channel=channel)
    
    
    def get_bias_status_register(self):
        '''
        Gets the entire bias status register
        
        Input:
            None
        Output:
            status_register (bool):
                0:  CH1 End of Sweep
                1:  CH1 Ready for Sweep
                2:  CH1 Low Limiting
                3:  CH1 High Limiting
                4:  CH1 Tripped
                5:  CH1 Emergency (Temperature/Current over)
                6:  ---
                7:  ---
                8:  CH2 End of Sweep
                9:  CH2 Ready for Sweep
                10: CH2 Low Limiting
                11: CH2 High Limiting
                12: CH2 Tripped
                13: CH2 Emergency (Temperature/Current over)
                14: Inter Locking
                15: Start Sampling Error
        '''
        # Corresponding Command: :STATus:SOURce:CONDition?
        try:
            logging.debug(__name__ + ': Get bias status register')
            bias_status_register = int(self._ask(':stat:sour:cond'))
            ans = []
            for i in range(16):
                ans.append(2**i == (bias_status_register) & 2**i)
            return ans
        except ValueError:
            logging.error(__name__ + ': Bias status register not specified:')
    
    
    def is_end_of_sweep(self, channel=1):
        '''
        Gets event of bias status register entry "End for Sweep" of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            val (bool)    : True | False
        '''
        # Corresponding Command: :STATus:SOURce:EVENt?
        try:
            logging.debug(__name__ + ': Get bias status register event "End of Sweep" of channel %i' % channel)
            return 2**(0+8*(channel-1)) == (int(self._ask(':stat:sour:even'))) & 2**(0+8*(channel-1))
        except ValueError:
            logging.error(__name__ + ': Status register event "End of Sweep" of channel %i not specified:' % channel)
    
    
    def _wait_for_end_of_sweep(self, channel=1):
        '''
        Waits until the event of status register entry "End for Sweep" of channel <channel> occurs
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        while not (self.is_end_of_sweep(channel=channel)):
            time.sleep(100e-3)
    
    
    def is_ready_for_sweep(self, channel=1):
        '''
        Gets condition of bias status register entry "Ready for Sweep" of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            val (bool)    : True | False
        '''
        # Corresponding Command: :STATus:SOURce:CONDition?
        try:
            logging.debug(__name__ + ': Get bias status register event "Ready of Sweep" of channel %i' % channel)
            return 2**(1+8*(channel-1)) == (int(self._ask(':stat:sour:cond'))) & 2**(1+8*(channel-1))
        except ValueError:
            logging.error(__name__ + ': Status register condition "Ready for Sweep" of channel %i not specified:' % channel)
    
    
    def _wait_for_ready_for_sweep(self, channel=1):
        '''
        Waits until the condition of status register entry "Ready for Sweep" of channel <channel> occurs
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        while not (self.is_ready_for_sweep(channel=channel)):
            time.sleep(100e-3)
    
    
    def get_sense_status_register(self):
        '''
        Gets the entire sense status register
        
        Input:
            None
        Output:
            status_register (bool):
                0:  CH1 End of Measure
                1:  ---
                2:  CH1 Compare result is Low
                3:  CH1 Compare result is High
                4:  ---
                5:  CH1 Over Range
                6:  ---
                7:  ---
                8:  CH2 End of Measure
                9:  ---
                10: CH2 Compare result is Low
                11: CH2 Compare result is High
                12: ---
                13: CH2 Over Range
                14: End of Trace
                15: Trigger Sampling Error
        '''
        # Corresponding Command: :STATus:SENSe:CONDition?
        try:
            logging.debug(__name__ + ': Get sense status register')      
            sense_status_register = int(self._ask(':stat:sens:cond'))
            ans = []
            for i in range(16):
                ans.append(2**i == (sense_status_register) & 2**i)
            return ans
        except ValueError:
            logging.error(__name__ + ': Sense status register not specified:')
    
    
    def is_end_of_measure(self, channel=1):
        '''
        Gets condition of sense status register entry "End of Measure" of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            val (bool)    : True | False
        '''
        # Corresponding Command: :STATus:SENSe:CONDition?
        try:            
            logging.debug(__name__ + ': Get sense status register event "End of Measure" of channel %i' % channel)
            return 2**(0+8*(channel-1)) == (int(self._ask(':stat:sens:cond'))) & 2**(0+8*(channel-1))
        except ValueError:
            logging.error(__name__ + ': Status register event "End of Measure" of channel %i not specified:' % channel)
    
    
    def _wait_for_end_of_measure(self, channel=1):
        '''
        Waits until the condition of sense register entry "End for Measure" of channel <channel> occurs
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        while not (self.is_end_of_measure(channel=channel)):
            time.sleep(100e-3)
    
    
    def is_end_of_trace(self, channel=1):
        '''
        Gets condition of sense status register entry "End of Trace" of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            val (bool)    : True | False
        '''
        # Corresponding Command: :STATus:SENSe:CONDition?
        try:
            logging.debug(__name__ + ': Get sense status register event "End of Trace" of channel %i' % channel)
            return 2**14 == (int(self._ask(':stat:sens:cond'))) & 2**14
        except ValueError:
            logging.error(__name__ + ': Status register event "End of Trace" of channel %i not specified:' % channel)
    
    
    def _wait_for_end_of_trace(self, channel=1):
        '''
        Waits until the condition of sense register entry "End for Trace" of channel <channel> occurs
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        while not (self.is_end_of_trace(channel=channel)):
            time.sleep(100e-3)
    
    
    def is_OPC(self):
        '''
        Gets condition of status register entry "Operation comlete"
        
        Input:
            None
        Output:
            val (bool) : True | False
        '''
        # Corresponding Command: *OPC
        try:            
            logging.debug(__name__ + ': Get status register condition "Operation comlete"')
            return bool(int(self._ask('*OPC')))
        except ValueError:
            logging.error(__name__ + ': Status register condition "Operation comlete" not specified:')
        
    
    
    def _wait_for_OPC(self):
        '''
        Waits until the event of register entry "Operatiom Complete" of occurs
        
        Input:
            None
        Output:
            None
        '''
        while not (self.is_OPC()):
            time.sleep(1e-3)
    
    
    def set_defaults(self, channel=1, channel2=2):
        '''
        Sets default settings for different sweep modes.
        VV-mode needs two different channels (bias channel <channel> and sense channel <channel2>), IV-mode and VI-mode only one (<channel>).
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        self._write(':syst:beep 0')
        if self._sweep_mode == 0:                                              # VV-mode
            for chan in [channel, channel2]: self.set_measurement_mode(val=0, channel=chan)
            for chan in [(channel, 1), (channel2,0)]: self.set_bias_mode(mode=chan[1], channel=chan[0])
            for chan in [channel, channel2]: self.set_sense_mode(mode=1, channel=chan)
            for chan in [channel, channel2]: self.set_bias_range(val=-1, channel=chan)
            for chan in [(channel, -1), (channel2, 18)]: self.set_sense_range(val=chan[1], channel=chan[0])
            for chan in [channel, channel2]: self.set_bias_delay(val=200e-6, channel=chan)
            for chan in [channel, channel2]: self.set_sense_delay(val=15e-6, channel=chan)
            for chan in [channel, channel2]: self.set_sense_nplc(val=1, channel=chan)
            for chan in [channel, channel2]: self.set_sense_average(val=1, channel=chan)
            for chan in [channel, channel2]: self._write('chan%i:sens:zero:auto 0' % chan)
        elif self._sweep_mode == 1:                                            # IV-mode
            self.set_measurement_mode(val=1, channel=channel)
            self.set_bias_mode(mode=0, channel=channel)
            self.set_sense_mode(mode=1, channel=channel)
            self.set_bias_range(val=200e-3, channel=channel)
            self.set_sense_range(val=-1, channel=channel)
            self.set_bias_trigger(mode='sens', channel=channel)
            self.set_sense_trigger(mode='sour', channel=channel)
            self.set_bias_delay(val=200e-6, channel=channel)
            self.set_sense_delay(val=15e-6, channel=channel)
            self.set_sense_nplc(1)
            self.set_sense_average(1)
            self._write('chan%i:sens:zero:auto 0' % channel)
        elif self._sweep_mode == 2:                                            # VI-mode
            self.set_measurement_mode(val=1, channel=channel)
            self.set_bias_mode(mode=1, channel=channel)
            self.set_sense_mode(mode=0, channel=channel)
            self.set_bias_range(val=200e-3, channel=channel)
            self.set_sense_range(val=-1, channel=channel)
            self.set_bias_trigger(mode='sens', channel=channel)
            self.set_sense_trigger(mode='sour', channel=channel)
            self.set_bias_delay(val=200e-6, channel=channel)
            self.set_sense_delay(val=15e-6, channel=channel)
            self.set_sense_nplc(1)
            self.set_sense_average(1)
            self._write('chan%i:sens:zero:auto 0' % channel)
    
    
    def get_all(self, channel=1):
        '''
        Prints all settings of channel <channel>
        
        Input:
            channel (int) : 1 (default) | 2
        Output:
            None
        '''
        print('dAdV               = %eA/V' % self.get_dAdV())
        print('dVdA               = %eV/A' % self.get_dVdA())
        print('amplification      = %e'    % self.get_amp())
        print('synchronization    = %r'    % self.get_sync())
        print('measurement mode   = %s'    % self._measurement_modes[self.get_measurement_mode(channel=channel)])
        print('bias mode          = %s'    % self._IV_modes[self.get_bias_mode(channel=channel)])
        print('sense mode         = %s'    % self._IV_modes[self.get_sense_mode(channel=channel)])
        print('bias range         = %e%s'  % (self.get_bias_range(channel=channel), self._IV_units[self.get_bias_mode(channel=channel)]))
        print('sense range        = %e%s'  % (self.get_sense_range(channel=channel), self._IV_units[self.get_sense_mode(channel=channel)]))
        print('bias trigger       = %s'    % self.get_bias_trigger(channel=channel))
        print('sense trigger      = %s'    % self.get_sense_trigger(channel=channel))
        print('bias delay         = %es'   % self.get_bias_delay(channel=channel))
        print('sense delay        = %es'   % self.get_sense_delay(channel=channel))
        print('sense average      = %i'    % self.get_sense_average(channel=channel)[1])
        print('plc                = %fHz'  % self.get_plc())
        print('sense nplc         = %i'    % self.get_sense_nplc(channel=channel))
        print('status             = %r'    % self.get_status(channel=channel))
        print('bias value         = %f%s'  % (self.get_bias_value(channel=channel), self._IV_units[self.get_bias_mode(channel=channel)]))
        print('sense value        = %f%s'  % (self.get_sense_value(channel=channel), self._IV_units[self.get_sense_mode(channel=channel)]))
        print('sweep start        = %f%s'  % (self.get_sweep_start(channel=channel), self._IV_units[self.get_bias_mode(channel=channel)]))
        print('sweep stop         = %f%s'  % (self.get_sweep_stop(channel=channel), self._IV_units[self.get_bias_mode(channel=channel)]))
        print('sweep step         = %f%s'  % (self.get_sweep_step(channel=channel), self._IV_units[self.get_bias_mode(channel=channel)]))
        print('sweep nop          = %i'    % self.get_sweep_nop(channel=channel))
        for err in self.get_error(): print('error              = %i\t%s' % (err[0], err[1]))
        currBSR = self.get_bias_status_register()
        BSR = [('\n\t%s:\t%r\t(%s)' % (bsr[0], currBSR[i], bsr[1])) for i, bsr in enumerate(self._bias_status_register) if bsr != ('', '')]
        print 'Bias status register:'+''.join(BSR)
        currSSR = self.get_sense_status_register()
        SSR = [('\n\t%s:\t%r\t(%s)' % (ssr[0], currSSR[i], ssr[1])) for i, ssr in enumerate(self._sense_status_register) if ssr != ('', '')]
        print 'Bias status register:'+''.join(SSR)
    
    
    def reset(self):
        '''
        Resets the instrument to factory settings
        
        Input:
            None
        Output:
            None
        '''
        # Corresponding Command: *RST
        try:
            logging.debug(__name__ + ': resetting instrument')
            self._write('*RST')
        except AttributeError:
            logging.error(__name__ + ': Invalid input: cannot reset')
    
    
    def get_error(self):
        '''
        Gets error of instrument
        
        Input:
            None
        Output:
            error (str)
        '''
        # Corresponding Command: :SYSTem:ERRor?
        try:
            logging.debug(__name__ + ': Get errors')
            err = [self._ask(':syst:err').split(',',1)]
            while err[-1] != ['0', '"No error"']:
                err.append(self._ask(':syst:err').split(',',1))
            if len(err) > 1: err = err[:-1]
            err = [[int(e[0]), str(e[1][1:-1])] for e in err]
            return err
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
        # Corresponding Command: *CLS
        try:
            logging.debug(__name__ + ': Clear error')
            self._write('*CLS')
        except AttributeError:
            logging.error(__name__ + ': Invalid input: cannot clear error')
    
    
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
        except AttributeError:
            logging.error(__name__ + ': Invalid input: cannot close VISA-instrument')
    
    
    def ready(self, channel_bias=1, channel_sense=2):
        '''
        This is a proxy function, returning True when the IVD has finished the sweep
        
        Input:
            None
        Output:
            ready (bool)
        '''
        return self.is_end_of_sweep(channel=channel_bias)
        '''
        if self.is_end_of_sweep(channel=channel_bias):
            time.sleep(self.get_sense_delay(channel=channel_sense))
            self._wait_for_end_of_measure(channel=channel_sense)
            return True
        else:
            return False
        '''
    
    
    
    ### OLD VERSION: sweep I, measure V of one channel
    """
#    def set_sense_integration_time(self, val, channel=1):
#        '''
#        Sets get sense integration time of channel <channel> to <val>
#        
#        Input:
#            val (float)   : integer multiples of PLC (2e-2 @ 50Hz)
#            channel (int) : 1 (default) | 2
#        Output:
#            None
#        '''
#        try:
#            logging.debug(__name__ + ': Set sense integration time of channel %i to %f' % (channel, val))
#            nplc = int(val*self.get_plc())
#            self.set_sense_nplc(val=nplc, channel=channel) 
#        except ValueError:
#            logging.error(__name__ + ': Sense integrarion time of channel %i not specified:' % channel)
#    
#    def get_sense_integration_time(self, channel=1):
#        '''
#        Gets get sense integration time of channel <channel>
#        
#        Input:
#            None
#        Output:
#            val (float)
#        '''
#        try:
#            logging.debug(__name__ + ': Get sense integration time of channel %i' % channel)
#            return self.get_sense_nplc(channel=channel)/self.get_plc()
#        except ValueError:
#            logging.error(__name__ + ': Sense integration time not specified:')
#    
#    def set_sweep_step_time(self, val, trigger='tim1', channel=1):
#        '''
#        Sets bias trigger to <trigger> of channel <channel> with sweep step time <val>
#        
#        Input:
#            val (float)
#            trigger (str) : 'tim1' | 'tim2'
#            channel (int) : 1 (default) | 2
#        Output:
#            None
#        '''
#        try:
#            logging.debug(__name__ + ': Set step time (trigger %i) of channel %s to %f' % (channel, trigger, val))
#            self.set_bias_trigger(mode=trigger, channel=channel, time=val)
#        except AttributeError:
#            logging.error(__name__ + ': Invalid input: cannot set sweep step time of channel %i to %f' % (channel, val))
#    
#    def get_sweep_step_time(self, channel=1):
#        '''
#        Gets sweep step time if bias trigger of channel <channel> is 'timer'
#        
#        Input:
#            channel (int) : 1 (default) | 2
#        Output:
#            val (float)
#        '''
#        try:
#            logging.debug(__name__ + ': get step time (trigger tim%i) of channel %i' % (channel, channel))
#            if self.get_bias_trigger(channel=channel).lower()[0:3] == 'tim': return(float(self._ask(':trig:%s' % self.get_bias_trigger(channel=channel))))
#        except ValueError:
#            logging.error(__name__ + ': Sweep step time of channel %i not specified:' % channel)
    """
    