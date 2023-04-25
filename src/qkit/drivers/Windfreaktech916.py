# Windfreaktech SynthHD Microwave Source
# Andre Schneider <erdna.na@gmail.com>, 2015
# Lukas Gruenhaupt <lukas.gruenhaupt@kit.edu> 05/2018
# Martin Spiecker <martin.spiecker@kit.edu> 2020
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

from qkit.core.instrument_base import Instrument
from qkit import visa
import logging
from time import sleep
import numpy as np
from scipy.interpolate import RectBivariateSpline
from scipy import optimize
from distutils.version import LooseVersion

path_hardcode = r'C:\qkit\qkit\drivers\Windfreak_calibration_files'  # TODO


class Windfreaktech916(Instrument):
    '''
    This is the python QTLab driver for the Windfreaktech SynthHD microwave source
    '''

    def __init__(self, name, address, model='Windfreaktech', serial='290'):
        '''
        Initializes the Windfreaktech_SynthHD, and communicates with the wrapper.
        
        Input:
            name (string)    : name of the instrument
            address (string) : address
            serial (string)  : serial number of the Windfreak source. used to identify the correct calibration file
        '''
        logging.info(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])

        self._address = address
        self._model = model
        self._visainstrument = visa.instrument(self._address)
        self._serial = serial
        
        if LooseVersion(visa.__version__) < LooseVersion("1.5.0"):
            self._visainstrument.term_chars = '\n'
        else:
            self._visainstrument.write_termination = '\n'
            self._visainstrument.read_termination = '\n'
            
        self._numchannels = 2
        self._frequency = np.zeros(2)
        self._power = np.zeros(2)
        self._power_level = np.zeros(2)
        

        # Implement parameters
        self.add_parameter('frequency', type=float,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, self._numchannels), minval=54e6, maxval=13.6e9, units='Hz', channel_prefix='ch%d_')

        self.add_parameter('power_level', type=float,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, self._numchannels), minval=0, maxval=45000, units='arbu', channel_prefix='ch%d_')
    
        self.add_parameter('power', type=float,
            flags=Instrument.FLAG_GETSET,
            channels=(1, self._numchannels), minval=-70, maxval=20, units='dBm', channel_prefix='ch%d_')
        
        self.add_parameter('status', type=bool,
            flags=Instrument.FLAG_GETSET,
            channels=(1, self._numchannels), channel_prefix='ch%d_')
        
        self.add_function('get_all')
        self.load_calibration()
        
        # sets the reference (clock) frequency ###
        #self._visainstrument.write('C0x0')                 #added these two command lines to set the reference
        #self._visainstrument.write('C1x0')		           #to external for both channels
        #self.set_PLL_frequency(10e6)
        
        # switch off self-calibrated temperature compensation 
        # when tested in May 2018, this lead to jumps to the max power value some time after the power was set to a lower value
        self._visainstrument.write('C0Z0')
        self._visainstrument.write('C1Z0')

        # Unmute channels
        self._visainstrument.write('C0h1C1h1')
        self._visainstrument.write('C0h1C1h1')

        # initialize parameters
        self.get_all()



##############################       
### initialization related ###
##############################
        
    def get_all(self):

        self.get_ch1_frequency()
        self.get_ch2_frequency()
        self.get_ch1_power()
        self.get_ch2_power()
        self.get_ch1_power_level()
        self.get_ch2_power_level()
        self.get_ch1_status()
        self.get_ch2_status()
    
###########################################
### Communication with device and setup ###
###########################################
        
    def load_calibration(self):
        '''
        reloads power calibration from file Windfreak_SerialNo_Channel(A/B).cal in instruments\Windfreak_calibration_files folder.
        Calibration file was measured in frequency interval 1 GHz - 13 GHz (frequency interval 10 MHz) and with power_level_parameter 10e3 to 45e3 (steps of 500)
        '''
        
        try:

            data_ChA = np.load(
                path_hardcode + "\Windfreak_" + self._serial + "_ChannelA_calibration_with_freq_and_pow.npy",
                allow_pickle=True)
            data_ChB = np.load(
                path_hardcode + "\Windfreak_" + self._serial + "_ChannelA_calibration_with_freq_and_pow.npy",
                allow_pickle=True)

            f_channelA = data_ChA.item().get("frequency_Hz")
            f_channelB = data_ChB.item().get("frequency_Hz")

            p_channelA = data_ChA.item().get("power_intrinsic_units")
            p_channelB = data_ChB.item().get("power_intrinsic_units")

            cal_matrix_A = data_ChA.item().get("calibration_matrix_dBm")
            cal_matrix_B = data_ChB.item().get("calibration_matrix_dBm")

            # generate the interpolators to estimate the power_level parameter in set_power
            self._interp_amplitudeA = RectBivariateSpline(f_channelA, p_channelA, cal_matrix_A)
            self._interp_amplitudeB = RectBivariateSpline(f_channelB, p_channelB, cal_matrix_B)
                
        except IOError:
            raise IOError('Calibration file of Windfreak source not found')

    def set_PLL_frequency(self, frequency):
        '''
        set the reference frequency for the PLL in Hz
        and set 'x' to 0 (external reference clock)
        if frequency == False: Set clock to internal reference
        '''
        if not frequency:
            self._visainstrument.write("x1".format(27))  # unstable
        else:
            self._visainstrument.write("*{}x0".format(int(frequency/1e6)))

    def get_PLL_frequency(self):
        
        return 1e6 * float(self._visainstrument.query("*?"))
        
#######################
### functionalities ###    
#######################
    
    def do_get_frequency(self, channel):
        
        self._frequency[channel - 1] = 1e6 * float(self._visainstrument.query('C{}f?'.format(channel - 1)))
        return self._frequency[channel - 1]
        
    def do_set_frequency(self, frequency, channel):
        '''
        Set frequency of device

        Input:
            freq (float) : Frequency in Hz

        Output:
            None
        '''
        self._frequency[channel - 1] = frequency
        self._visainstrument.write('C{}f{:.6f}'.format(channel - 1, frequency / 1e6))
        # After every frequency change the power level has to be resetted
        # Since the output power is frequency dependent, the calibrated power is chosen
        # self.do_set_power(self._power[channel - 1], channel)
        
        # sleep since source needs some time to adjust to new settings
        sleep(0.05)

    def do_set_frequency_uncalibrated(self, frequency, channel):
        '''
        Set frequency of device

        Input:
            freq (float) : Frequency in Hz

        Output:
            None
        '''
        self._frequency[channel - 1] = frequency
        self._visainstrument.write('C{}f{:.6f}'.format(channel - 1, frequency / 1e6))
        self._visainstrument.write('C{}a{}'.format(channel - 1, self._power_level[channel - 1]))

        # sleep since source needs some time to adjust to new settings
        sleep(0.05)
    
    def do_get_power_level(self, channel):

        self._power_level[channel - 1] = self._visainstrument.query('C{}a?'.format(channel - 1))
        return self._power_level[channel - 1]
        
    def do_set_power_level(self, level, channel):
        '''
        Set uncalibrated power level of device
        Usually, you should use set_power which accepts values in dBm

        Input:
            level (float) : (0=mimimum, 45000=maximum)

        Output:
            None
        '''
        self._power_level[channel - 1] = level
        self._visainstrument.write('C{}a{}'.format(channel - 1, level))
        
        # sleep since source needs some time to adjust to new settings
        sleep(0.05)
    
    # TODO load files
    def do_get_power(self, channel):
        '''
        this only returns the stored power value and does not communicate with the device!
        '''
        
        if self._power[channel - 1] is None:
            
            print("Power is not calibrated. You have to do this to get a proper value.")
            
        return self._power[channel - 1]
        
    def do_set_power(self, power, channel):
        '''
        Set output power of device

        Input:
            power (float) : Power in dBm

        Output:
            None
        '''
        
        self._power[channel - 1] = power
        
        if channel == 0:
            
            # generate a helper function to find power level for desired power in dBm by finding roots of the function
            helper_fn = lambda x: self._interp_amplitudeA(self._frequency[channel - 1], x) - power
            # by finding the zero of the helper function, the power level value is determined
            pwr_lvl = int(optimize.newton(helper_fn, 20000))
            
            if pwr_lvl > 45000:
                
                print('The minimum and maximum output power of this microwave source depends on frequency. '
                      'Your desired combination of frequency and output power is not possible. '
                      'Power is set to max for this frequency: {}.1f dBm'.format(self._interp_amplitudeA(self._frequency[channel - 1], 45000)))
            else:
                
                self.do_set_power_level(pwr_lvl, channel)
                
        if channel == 1:
            
            # generate a helper function to find power level for desired power in dBm by finding roots of the function
            helper_fn = lambda x: self._interp_amplitudeB(self._frequency[channel - 1], x) - power
            # by finding the zero of the helper function, the power level value is determined
            pwr_lvl = int(optimize.newton(helper_fn, 20000))
            
            if pwr_lvl > 45000:
                
                print ('The minimum and maximum output power of this microwave source depends on frequency. '
                       'Your desired combination of frequency and output power is not possible. '
                       'Power is set to max for this frequency: {}.1f dBm'.format(self._interp_amplitudeB(self._frequency[channel - 1], 45000)))
            else:
                
                self.do_set_power_level(pwr_lvl, channel)

    def do_get_status(self, channel):

        return bool(int(float(self._visainstrument.query('C{}r?'.format(channel - 1)))))
        
    def do_set_status(self, status, channel):
        '''
        Set status of output channel
        Sets 'r' (output-parameter)  as well as 'E' (PLL Chip Enable) according to the manual

        Input:
            channel (int) : 0 for channel A, 1 for channel B
            status        : True or False 

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting status to "{}s"'.format(status))
        
        if status:
             
            self._visainstrument.write('C{}r1E1'.format(channel - 1))
            
        else:
            
            self._visainstrument.write('C{}r0E0'.format(channel - 1))

    def write(self, msg):
        return self._visainstrument.write(msg)    

    def query(self, msg):
        return self._visainstrument.query(msg)
