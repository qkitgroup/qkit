# Windfreaktech SynthHD Microwave Source
# Andre Schneider <erdna.na@gmail.com>, 2015
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

import qkit
from qkit.core.instrument_base import Instrument
from qkit import visa
import types
import logging
import math
from time import sleep
import numpy as np
from scipy.interpolate import RegularGridInterpolator
from distutils.version import LooseVersion


class Windfreaktech_SynthHD(Instrument):
    '''
    This is the python QTLab driver for the Windfreaktech SynthHD microwave source
    '''

    def __init__(self, name, address, model='Windfreaktech'):
        '''
        Initializes the Windfreaktech_SynthHD, and communicates with the wrapper.
        
        Input:
            name (string)    : name of the instrument
            address (string) : address
        '''
        logging.info(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])

        self._address = address
        self._model = model
        self._visainstrument = visa.instrument(self._address)
        if LooseVersion(visa.__version__) < LooseVersion("1.5.0"):
            self._visainstrument.term_chars = '\n'
        else:
            self._visainstrument.write_termination = '\n'
            self._visainstrument.read_termination = '\n'
        self._numchannels = 2
        self._frequency = [None, None, None]
        self._power = [None, None, None]

        # Implement parameters
        self.add_parameter('frequency', type=float,
                           flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
                           channels=(1, self._numchannels), minval=0, maxval=13.6e9, units='Hz', channel_prefix='ch%d_')

        self.add_parameter('power_level', type=float,
                           flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
                           channels=(1, self._numchannels), minval=0, maxval=45000, units='arbu',
                           channel_prefix='ch%d_')

        self.add_parameter('power', type=float,
                           flags=Instrument.FLAG_GETSET,
                           channels=(1, self._numchannels), minval=-70, maxval=20, units='dBm', channel_prefix='ch%d_')

        self.add_parameter('status', type=bool,
                           flags=Instrument.FLAG_GETSET,
                           channels=(1, self._numchannels), channel_prefix='ch%d_')

        self.add_function('get_all')
        self.add_function('reload_calibration')
        # self.add_function('set_PLL_frequency')
        # self.add_function('get_PLL_frequency')

        self.reload_calibration()
        self.get_all()
        self.set_PLL_frequency(10e6)

    # initialization related
    def get_all(self):
        self.get_ch1_frequency()
        self.get_ch2_frequency()
        self.get_ch1_status()
        self.get_ch2_status()
        self._visainstrument.write("C0h1C1h1")
        pass

    # Communication with device

    def reload_calibration(self):
        '''
        reloads power calibration from file Windfreaktech_SynthHD.cal in instruments folder.
        '''
        try:
            data = np.loadtxt(qkit.cfg.get('instruments_dir') + '/Windfreaktech_SynthHD.cal')
            f = data[1:, 0]
            p = data[0, 1:]
            values = data[1:, 1:]
            self._interp_amplitude = RegularGridInterpolator((f, p), values).__call__

        except IOError:
            raise IOError('Calibration file for WFT MW Source not found')

    def delete(self):
        '''
        Use this to close the session with the device. It is more likely to work again afterwards.
        '''
        self.__del__()

    def __del__(self):
        self._visainstrument.close()
        print("Session closed.")

    def set_PLL_frequency(self, frequency):
        '''
        set the reference frequency for the PLL in Hz
        and set 'x' to 0 (external reference clock)
        if frequency == False: Set clock to internal reference
        '''
        if frequency == False:
            self._visainstrument.write("*%fx1" % (27))
        else:
            self._visainstrument.write("*%fx0" % (frequency / 1e6))

    def get_PLL_frequency(self):
        return float(self._visainstrument.ask("*?")) * 1e6

    def do_get_frequency(self, channel):
        self._frequency[channel] = float(self._visainstrument.ask('C%if?' % (channel - 1))) * 1e6
        return self._frequency[channel]

    def do_set_frequency(self, frequency, channel):
        '''
        Set frequency of device

        Input:
            freq (float) : Frequency in Hz

        Output:
            None
        '''
        self._frequency[channel] = frequency
        self._visainstrument.write('C%if%.9f' % (channel - 1, frequency / 1e6))
        self.do_set_power(self._power[channel], channel)

    def do_get_power_level(self, channel):
        return float(self._visainstrument.ask('C%ia?' % (channel - 1)))

    def do_set_power_level(self, level, channel):
        '''
        Set uncalibrated power level of device
        Usually, you should use set_power which accepts values in dBm

        Input:
            level (float) : (0=mimimum, 45000=maximum)

        Output:
            None
        '''
        self._visainstrument.write('C%ia%.3f' % (channel - 1, level))

    def do_get_power(self, channel):
        '''
        this only returns the stored power value and does not communicate with the device!
        '''
        if self._power[channel] == None:
            print("Power was not set since reload of driver. You have to do this to get a proper value.")
        return self._power[channel]

    def do_set_power(self, power, channel):
        '''
        Set output power of device

        Input:
            power (float) : Power in dBm

        Output:
            None
        '''
        if (np.isnan(float(self._interp_amplitude((self._frequency[channel], power))))):
            raise ValueError(
                'The possible minimum and maximum output power of this microwave source does depend on the frequency. Unfortunately, your desired combination of frequency and output power is not possible.')
        else:
            self._power[channel] = power
            self.do_set_power_level(int(self._interp_amplitude((self._frequency[channel], power))), channel)

    def do_get_status(self, channel):
        return bool(int(self._visainstrument.ask('C%ir?' % (channel - 1))))

    def do_set_status(self, status, channel):
        '''
        Set status of output channel
        Sets 'r' (output-parameter)  as well as 'E' (PLL Chip Enable) according to the manual

        Input:
            status : True or False 

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting status to "%s"' % status)
        if status == True:
            self._visainstrument.write('C%ir1E1' % (channel - 1))
        elif status == False:
            self._visainstrument.write('C%ir0E0' % (channel - 1))
        else:
            raise ValueError("set_status(): Please use either True or False")

    # shortcuts
    def off1(self):
        '''
        Set ch1 status to 'off'

        Input:
            None

        Output:
            None
        '''
        self.set_ch1_status(False)

    def off2(self):
        self.set_ch2_status(False)

    def off(self):
        '''
        turns both outputs off
        '''
        self.set_ch1_status(False)
        self.set_ch2_status(False)

    def on1(self):
        '''
        Set status to 'on'

        Input:
            None

        Output:
            None
        '''
        self.set_ch1_status(True)

    def on2(self):
        self.set_ch2_status(True)

    def write(self, msg):
        return self._visainstrument.write(msg)

    def ask(self, msg):
        return self._visainstrument.ask(msg)
