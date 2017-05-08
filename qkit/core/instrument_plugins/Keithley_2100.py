# Keithley_2100.py driver for Keithley 2100 DMM
# Pieter de Groot <pieterdegroot@gmail.com>, 2008
# Martijn Schaafsma <qtlab@mcschaafsma.nl>, 2008
# Reinier Heeres <reinier@heeres.eu>, 2008 - 2010
#
# Update december 2009:
# Michiel Jol <jelle@michieljol.nl>
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
import types
import logging
import numpy

import qt

def bool_to_str(val):
    '''
    Function to convert boolean to 'ON' or 'OFF'
    '''
    if val == True:
        return "ON"
    else:
        return "OFF"

class Keithley_2100(Instrument):
    '''
    This is the driver for the Keithley 2100 Multimeter

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Keithley_2100',
        address='<GBIP address>',
        reset=<bool>,
        change_display=<bool>,
        change_autozero=<bool>)
    '''

    def __init__(self, name, address, reset=False,
            change_display=True, change_autozero=True):
        '''
        Initializes the Keithley_2100, and communicates with the wrapper.

        Input:
            name (string)           : name of the instrument
            address (string)        : GPIB address
            reset (bool)            : resets to default values
            change_display (bool)   : If True (default), automatically turn off
                                        display during measurements.
            change_autozero (bool)  : If True (default), automatically turn off
                                        autozero during measurements.
        Output:
            None
        '''
        # Initialize wrapper functions
        logging.info('Initializing instrument Keithley_2100')
        Instrument.__init__(self, name, tags=['physical'])

        # Add some global constants
        self._address = address
        self._visainstrument = visa.instrument(self._address)
        self._modes = ['VOLT:AC', 'VOLT:DC', 'CURR:AC', 'CURR:DC', 'RES',
            'FRES', 'TEMP', 'FREQ']
        self._change_display = change_display
        self._change_autozero = change_autozero
        self._averaging_types = ['MOV','REP']
        self._trigger_sent = False

        # Add parameters to wrapper
        self.add_parameter('range',
            flags=Instrument.FLAG_GETSET,
            units='', minval=0.1, maxval=1000, type=types.FloatType)
        self.add_parameter('trigger_count',
            flags=Instrument.FLAG_GETSET,
            units='#', type=types.IntType)
        self.add_parameter('trigger_delay',
            flags=Instrument.FLAG_GETSET,
            units='s', minval=-1, maxval=999999.999, type=types.FloatType)
        self.add_parameter('trigger_source',
            flags=Instrument.FLAG_GETSET,
            units='')
        self.add_parameter('mode',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType, units='',
            option_list=self._modes)
        self.add_parameter('resolution',
            flags=Instrument.FLAG_GETSET,
            units='#', type=types.StringType)
        self.add_parameter('readval', flags=Instrument.FLAG_GET,
            units='AU',
            type=types.FloatType,
            tags=['measure'])
        self.add_parameter('nplc',
            flags=Instrument.FLAG_GETSET,
            units='#', type=types.FloatType, minval=0.01, maxval=50)
        self.add_parameter('display', flags=Instrument.FLAG_GETSET,
            type=types.BooleanType)
        self.add_parameter('autozero', flags=Instrument.FLAG_GETSET,
            type=types.BooleanType)
        self.add_parameter('averaging', flags=Instrument.FLAG_GETSET,
            type=types.BooleanType)
        self.add_parameter('averaging_count',
            flags=Instrument.FLAG_GETSET,
            units='#', type=types.IntType, minval=1, maxval=100)
        self.add_parameter('averaging_type',
            flags=Instrument.FLAG_GETSET,
            type=types.StringType, units='')
        self.add_parameter('autorange',
            flags=Instrument.FLAG_GETSET,
            units='',
            type=types.BooleanType)

        # Add functions to wrapper
        self.add_function('set_mode_volt_ac')
        self.add_function('set_mode_volt_dc')
        self.add_function('set_mode_curr_ac')
        self.add_function('set_mode_curr_dc')
        self.add_function('set_mode_res')
        self.add_function('set_mode_fres')
        self.add_function('set_mode_temp')
        self.add_function('set_mode_freq')
        self.add_function('set_range_auto')
        self.add_function('reset_trigger')
        self.add_function('reset')
        self.add_function('get_all')

        self.add_function('read')

        self.add_function('send_trigger')
        self.add_function('fetch')

        # Connect to measurement flow to detect start and stop of measurement
        qt.flow.connect('measurement-start', self._measurement_start_cb)
        qt.flow.connect('measurement-end', self._measurement_end_cb)

        self.reset()
        self.get_all()
        if not reset:
            self.set_defaults()

# --------------------------------------
#           functions
# --------------------------------------

    def reset(self):
        '''
        Resets instrument to default values

        Input:
            None

        Output:
            None
        '''
        logging.debug('Resetting instrument')
        self._visainstrument.write('*RST')
        self.get_all()

    def set_defaults(self):
        '''
        Set to driver defaults:
        Output=data only
        Mode=Volt:DC
        Digits=7
        Range=10 V
        NPLC=1
        Averaging=off
        '''

#        self._visainstrument.write('SYST:PRES')
#        self._visainstrument.write(':FORM:ELEM READ')
            # Sets the format to only the read out, all options are:
            # READing = DMM reading, UNITs = Units,
            # TSTamp = Timestamp, RNUMber = Reading number,
            # CHANnel = Channel number, LIMits = Limits reading

        self.set_mode_volt_dc()
        self.set_resolution('MIN')
        self.set_range(10)
        self.set_nplc(1)
        self.set_averaging(False)

    def get_all(self):
        '''
        Reads all relevant parameters from instrument

        Input:
            None

        Output:
            None
        '''
        logging.info('Get all relevant data from device')
        self.get_mode()
        self.get_range()
        self.get_trigger_count()
        self.get_trigger_delay()
        self.get_trigger_source()
        self.get_mode()
        self.get_resolution()
        self.get_nplc()
        self.get_display()
        self.get_autozero()
        self.get_averaging()
        self.get_averaging_count()
        self.get_averaging_type()
        self.get_autorange()

    def read(self):
        '''
        Old function for read-out, links to get_readval()
        '''
        logging.debug('Link to get_readval()')
        return self.get_readval()

    def send_trigger(self):
        '''
        Send trigger to Keithley, use when triggering is not continous.
        '''
        logging.debug('Sending trigger')
        self._visainstrument.write('INIT')
        self._trigger_sent = True

    def fetch(self):
        '''
        Get data at this instance, not recommended, use get_readval.
        Use send_trigger() to trigger the device.
        Note that Readval is not updated since this triggers itself.
        '''

        if self._trigger_sent:
            logging.debug('Fetching data')
            reply = self._visainstrument.ask('FETCH?')
            self._trigger_sent = False
            return float(reply[0:15])
        else:
            logging.warning('No trigger sent, use send_trigger')

    def set_mode_volt_ac(self):
        '''
        Set mode to AC Voltage

        Input:
            None

        Output:
            None
        '''
        logging.debug('Set mode to AC Voltage')
        self.set_mode('VOLT:AC')

    def set_mode_volt_dc(self):
        '''
        Set mode to DC Voltage

        Input:
            None

        Output:
            None
        '''
        logging.debug('Set mode to DC Voltage')
        self.set_mode('VOLT:DC')

    def set_mode_curr_ac(self):
        '''
        Set mode to AC Current

        Input:
            None

        Output:
            None
        '''
        logging.debug('Set mode to AC Current')
        self.set_mode('CURR:AC')

    def set_mode_curr_dc(self):
        '''
        Set mode to DC Current

        Input:
            None

        Output:
            None
        '''
        logging.debug('Set mode to DC Current')
        self.set_mode('CURR:DC')

    def set_mode_res(self):
        '''
        Set mode to Resistance

        Input:
            None

        Output:
            None
        '''
        logging.debug('Set mode to Resistance')
        self.set_mode('RES')

    def set_mode_fres(self):
        '''
        Set mode to 'four wire Resistance'

        Input:
            None

        Output:
            None
        '''
        logging.debug('Set mode to "four wire resistance"')
        self.set_mode('FRES')

    def set_mode_temp(self):
        '''
        Set mode to Temperature

        Input:
            None

        Output:
            None
        '''
        logging.debug('Set mode to Temperature')
        self.set_mode('TEMP')

    def set_mode_freq(self):
        '''
        Set mode to Frequency

        Input:
            None

        Output:
            None
        '''
        logging.debug('Set mode to Frequency')
        self.set_mode('FREQ')

    def set_range_auto(self, mode=None):
        '''
        Old function to set autorange, links to set_autorange()
        '''
        logging.debug('Redirect to set_autorange')
        self.set_autorange(True)

    def reset_trigger(self):
        '''
        Reset trigger status

        Input:
            None

        Output:
            None
        '''
        logging.debug('Resetting trigger')
        self._visainstrument.write(':ABOR')


# --------------------------------------
#           parameters
# --------------------------------------

    def do_get_readval(self):
        '''
        Waits for the next value available and returns it as a float.
        Note that if the reading is triggered manually, a trigger must
        be send first to avoid a time-out.

        Input:
            None

        Output:
            value(float) : last triggerd value on input
        '''
        logging.debug('Read next value')
        #FIXME: correct for 2100?
        text = self._visainstrument.ask('READ?')
        return float(text[0:15])

    def do_set_range(self, val, mode=None):
        '''
        Set range to the specified value for the
        designated mode. If mode=None, the current mode is assumed

        Input:
            val (float)   : Range in specified units
            mode (string) : mode to set property for. Choose from self._modes

        Output:
            None
        '''
        logging.debug('Set range to %s' % val)
        self._set_func_par_value(mode, 'RANG', val)

    def do_get_range(self, mode=None):
        '''
        Get range for the specified mode.
        If mode=None, the current mode is assumed.

        Input:
            mode (string) : mode to set property for. Choose from self._modes

        Output:
            range (float) : Range in the specified units
        '''
        logging.debug('Get range')
        return float(self._get_func_par(mode, 'RANG'))

    def do_set_resolution(self, val, mode=None):
        '''
        Set resolution to the specified value
        If mode=None the current mode is assumed

        Input:
            val (float)   : Resolution
            mode (string) : mode to set property for. Choose from self._modes

        Output:
            None
        '''
        logging.debug('Set resolution to %s' % val)
        mode = self._determine_mode(mode)
        self._visainstrument.write('SENS:%s:RES %s' % (mode, val))
        return True

    def do_get_resolution(self, mode=None):
        '''
        Get resolution
        If mode=None the current mode is assumed

        Input:
            mode (string) : mode to set property for. Choose from self._modes

        Output:
            resolution (float)
        '''
        logging.debug('Getting resolution')
        mode = self._determine_mode(mode)
        return self._visainstrument.ask('SENS:%s:RES?' % mode)

    def do_set_nplc(self, val, mode=None, unit='APER'):
        '''
        Set integration time to the specified value in Number of Powerline Cycles.
        To set the integrationtime in seconds, use set_integrationtime().
        Note that this will automatically update integrationtime as well.
        If mode=None the current mode is assumed

        Input:
            val (float)   : Integration time in nplc.
            mode (string) : mode to set property for. Choose from self._modes.

        Output:
            None
        '''
        logging.debug('Set integration time to %s PLC' % val)
        self._set_func_par_value(mode, 'NPLC', val)
        
    def do_get_nplc(self, mode=None, unit='APER'):
        '''
        Get integration time in Number of PowerLine Cycles.
        To get the integrationtime in seconds, use get_integrationtime().
        If mode=None the current mode is assumed

        Input:
            mode (string) : mode to get property of. Choose from self._modes.

        Output:
            time (float) : Integration time in PLCs
        '''
        logging.debug('Read integration time in PLCs')
        return float(self._get_func_par(mode, 'NPLC'))

    def do_set_trigger_count(self, val):
        '''
        Set trigger count
        if val>9999 count is set to INF

        Input:
            val (int) : trigger count

        Output:
            None
        '''
        logging.debug('Set trigger count to %s' % val)
        if val > 9999:
            val = 'INF'
        self._set_func_par_value('TRIG', 'COUN', val)

    def do_get_trigger_count(self):
        '''
        Get trigger count

        Input:
            None

        Output:
            count (int) : Trigger count
        '''
        logging.debug('Read trigger count from instrument')
        ans = self._get_func_par('TRIG', 'COUN')
        try:
            ret = int(ans)
        except:
            ret = 0

        return ret

    def do_set_trigger_delay(self, val):
        '''
        Set trigger delay to the specified value

        Input:
            val (float) : Trigger delay in seconds or -1 for auto

        Output:
            None
        '''
        if val == -1:
            logging.debug('Set trigger delay to auto')
            self._set_func_par_value('TRIG', 'DEL:AUTO', 'OFF')
        else:
            logging.debug('Set trigger delay to %s sec', val)
            self._set_func_par_value('TRIG', 'DEL', '%s' % val)

    def do_get_trigger_delay(self):
        '''
        Read trigger delay from instrument

        Input:
            None

        Output:
            delay (float) : Delay in seconds, or -1 for auto
        '''
        logging.debug('Read trigger delay from instrument')
        val = self._get_func_par('TRIG', 'DEL:AUTO')
        if val == '1':
            return -1
        else:
            return self._get_func_par('TRIG', 'DEL')

    def do_set_trigger_source(self, val):
        '''
        Set trigger source

        Input:
            val (string) : Trigger source

        Output:
            None
        '''
        logging.debug('Set Trigger source to %s' % val)
        self._set_func_par_value('TRIG', 'SOUR', val)

    def do_get_trigger_source(self):
        '''
        Read trigger source from instrument

        Input:
            None

        Output:
            source (string) : The trigger source
        '''
        logging.debug('Getting trigger source')
        return self._get_func_par('TRIG', 'SOUR')

    def do_set_mode(self, mode):
        '''
        Set the mode to the specified value

        Input:
            mode (string) : mode to be set. Choose from self._modes

        Output:
            None
        '''

        logging.debug('Set mode to %s', mode)
        if mode in self._modes:
            string = 'SENS:FUNC "%s"' % mode
            self._visainstrument.write(string)

            if mode.startswith('VOLT'):
                self._change_units('V')
            elif mode.startswith('CURR'):
                self._change_units('A')
            elif mode.startswith('RES'):
                self._change_units('Ohm')
            elif mode.startswith('FREQ'):
                self._change_units('Hz')

        else:
            logging.error('invalid mode %s' % mode)

        self.get_all()
            # Get all values again because some paramaters depend on mode

    def do_get_mode(self):
        '''
        Read the mode from the device

        Input:
            None

        Output:
            mode (string) : Current mode
        '''
        string = 'SENS:FUNC?'
        logging.debug('Getting mode')
        ans = self._visainstrument.ask(string)
        ans = ans.strip('"')
        if ans == 'VOLT':
            ans = 'VOLT:DC'
        elif ans == 'CURR':
            ans = 'CURR:DC'
        return ans

    def do_get_display(self):
        '''
        Read the staturs of diplay

        Input:
            None

        Output:
            True = On
            False= Off
        '''
        logging.debug('Reading display from instrument')
        reply = self._visainstrument.ask('DISP?')
        return bool(int(reply))

    def do_set_display(self, val):
        '''
        Switch the diplay on or off.

        Input:
            val (boolean) : True for display on and False for display off

        Output

        '''
        logging.debug('Set display to %s' % val)
        val = bool_to_str(val)
        return self._visainstrument.write('DISP %s' % val)

    def do_get_autozero(self):
        '''
        Read the staturs of the autozero function

        Input:
            None

        Output:
            reply (boolean) : Autozero status.
        '''
        logging.debug('Reading autozero status from instrument')
        reply = self._visainstrument.ask(':ZERO:AUTO?')
        return bool(int(reply))

    def do_set_autozero(self, val):
        '''
        Switch the diplay on or off.

        Input:
            val (boolean) : True for display on and False for display off

        Output

        '''
        logging.debug('Set autozero to %s' % val)
        val = bool_to_str(val)
        return self._visainstrument.write('SENS:ZERO:AUTO %s' % val)

    def do_set_averaging(self, val, mode=None):
        '''
        Switch averaging on or off.
        If mode=None the current mode is assumed

        Input:
            val (boolean)
            mode (string) : mode to set property for. Choose from self._modes.

        Output:
            None
        '''
        logging.debug('Set averaging to %s ' % val)
        val = bool_to_str(val)
        self._visainstrument.write('SENS:AVER:STAT %s' % val)

    def do_get_averaging(self, mode=None):
        '''
        Get status of averaging.
        If mode=None the current mode is assumed

        Input:
            mode (string) : mode to set property for. Choose from self._modes.

        Output:
            result (boolean)
        '''
        logging.debug('Get averaging')
        reply = self._visainstrument.ask('SENS:AVER:STAT?')
        return bool(int(reply))

    def do_set_averaging_count(self, val, mode=None):
        '''
        Set averaging count.
        If mode=None the current mode is assumed

        Input:
            val (int)   : Averaging count.
            mode (string) : mode to set property for. Choose from self._modes.

        Output:
            None
        '''
        logging.debug('Set averaging_count to %s ' % val)
        self._visainstrument.write('SENS:AVER:COUN %d' % val)

    def do_get_averaging_count(self, mode=None):
        '''
        Get averaging count.
        If mode=None the current mode is assumed

        Input:
            mode (string) : mode to get property for. Choose from self._modes.

        Output:
            result (int) : Averaging count
        '''
        logging.debug('Get averaging count')
        reply = self._visainstrument.ask('SENS:AVER:COUN?')
        return int(float(reply))

    def do_set_autorange(self, val, mode=None):
        '''
        Switch autorange on or off.
        If mode=None the current mode is assumed

        Input:
            val (boolean)
            mode (string) : mode to set property for. Choose from self._modes.

        Output:
            None
        '''
        logging.debug('Set autorange to %s ' % val)
        val = bool_to_str(val)
        self._set_func_par_value(mode, 'RANG:AUTO', val)

    def do_get_autorange(self, mode=None):
        '''
        Get status of averaging.
        If mode=None the current mode is assumed

        Input:
            mode (string) : mode to set property for. Choose from self._modes.

        Output:
            result (boolean)
        '''
        logging.debug('Get autorange')
        reply = self._get_func_par(mode, 'RANG:AUTO')
        return bool(int(reply))

    def do_set_averaging_type(self, type, mode=None):
        '''
        Set the averaging_type to the specified value
        If mode=None the current mode is assumed

        Input:
            type (string) : averaging type to be set. Choose from self._averaging_types
                            or choose 'moving' or 'repeat'.
            mode (string) : mode to set property for. Choose from self._modes

        Output:
            None
        '''

        logging.debug('Set averaging type to %s', type)
        if type is 'moving':
            type='MOV'
        elif type is 'repeat':
            type='REP'

        if type in self._averaging_types:
            self._visainstrument.write('SENS:AVER:TCON %s' % type)
        else:
            logging.error('invalid type %s' % type)

    def do_get_averaging_type(self, mode=None):
        '''
        Read the mode from the device
        If mode=None the current mode is assumed

        Input:
            mode (string) : mode to get property for. Choose from self._modes.

        Output:
            type (string) : Current avering type for specified mode.
        '''
        logging.debug('Get averaging type')
        ans = self._visainstrument.ask('SENS:AVER:TCON?')
        if ans.startswith('REP'):
            ans='repeat'
        elif ans.startswith('MOV'):
            ans='moving'
        return ans
# --------------------------------------
#           Internal Routines
# --------------------------------------

    def _change_units(self, unit):
        self.set_parameter_options('readval', units=unit)

    def _determine_mode(self, mode):
        '''
        Return the mode string to use.
        If mode is None it will return the currently selected mode.
        '''
        logging.debug('Determine mode with mode=%s' % mode)
        if mode is None:
            mode = self.get_mode(query=False)
        if mode not in self._modes and mode not in ('INIT', 'TRIG', 'SYST', 'DISP'):
            logging.warning('Invalid mode %s, assuming current' % mode)
            mode = self.get_mode(query=False)
        return mode

    def _set_func_par_value(self, mode, par, val):
        '''
        For internal use only!!
        Changes the value of the parameter for the function specified

        Input:
            mode (string) : The mode to use
            par (string)  : Parameter
            val (depends) : Value

        Output:
            None
        '''
        mode = self._determine_mode(mode)
        string = ':%s:%s %s' % (mode, par, val)
        logging.debug('Set instrument to %s' % string)
        self._visainstrument.write(string)

    def _get_func_par(self, mode, par):
        '''
        For internal use only!!
        Reads the value of the parameter for the function specified
        from the instrument

        Input:
            func (string) : The mode to use
            par (string)  : Parameter

        Output:
            val (string) :
        '''
        mode = self._determine_mode(mode)
        string = ':%s:%s?' % (mode, par)
        ans = self._visainstrument.ask(string)
        logging.debug('ask instrument for %s (result %s)' % \
            (string, ans))
        return ans

    def _measurement_start_cb(self, sender):
        '''
        Things to do at starting of measurement
        '''
        if self._change_display:
            self.set_display(False)
            #Switch off display to get stable timing
        if self._change_autozero:
            self.set_autozero(False)
            #Switch off autozero to speed up measurement

    def _measurement_end_cb(self, sender):
        '''
        Things to do after the measurement
        '''
        if self._change_display:
            self.set_display(True)
        if self._change_autozero:
            self.set_autozero(True)

