# ZI_UHFLI driver, Julian Ferrero
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
from _ZI_toolkit import daq_module_toolz
import zhinst.utils
import logging
from time import sleep
import numpy as np

class ZI_UHFLI(Instrument):
    '''
    This is the python driver for the Anritsu MS4642A Vector Network Analyzer

    Usage:
    Initialise with
    <name> = instruments.create('<name>', address='<GPIB address>', reset=<bool>)
    
    '''

    def __init__(self, name, device_id):

       # Input:
       #     name (string)    : name of the instrument
       #     device_id : serial number of the instrument
       
        logging.info(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical', "lock-in amplifier"])
        
        self._device_id = device_id
        self._trigger_mode_dict = {"continuous" : 0,
                                   "in3_rising" : 1,
                                   "in3_falling" : 2,
                                   "in3_both" : 3,
                                   "in3_hi" : 32,
                                   "in3_lo" : 16,
                                   "in4_rising" : 4,
                                   "in4_falling" : 8,
                                   "in4_both" : 12,
                                   "in4_hi" : 128,
                                   "in4_lo" : 64,
                                   "in3|4_rising" : 5,
                                   "in3|4_falling" : 10,
                                   "in3|4_both" : 15,
                                   "in3|4_hi" : 160,
                                   "in3|4_lo" : 80}
        self._inv_trigger_mode_dict = {v: k for k, v in self._trigger_mode_dict.items()}
        self._difference_mode_dict = {"off" : 0,
                                      "inverted" : 1,
                                      "in1-in2" : 2,
                                      "in2-in1" : 3}
        self._inv_difference_mode_dict = {v: k for k, v in self._difference_mode_dict.items()}
                
        #Set the apilevel to the highest supported by your device, to unlock most of the functionalities.
        #Create an apisession, to be able to control the device from python.     
        self._apilevel = 6
        self._bad_device_message = "No UHFLI device found."
        (self.daq, self.device, _) = zhinst.utils.create_api_session(self._device_id, self._apilevel, 
                                        required_devtype = "UHFLI", 
                                        required_err_msg = self._bad_device_message)
        zhinst.utils.api_server_version_check(self.daq)     
                
        # Create a base configuration: Disable all available outputs, awgs, demods, scopes,...
        zhinst.utils.disable_everything(self.daq, self.device)
        
        #Add Instrument parameters in a way that qkit knows they are there
        '''
        signal ins:
        '''
        self.add_parameter("input_range", type = float,
                           flags = ZI_UHFLI.FLAG_GETSET,
                           channels = (1, 2), channel_prefix = "ch%d_",
                           minval = 10e-3, maxval = 1.5, 
                           units = "V")
        
        self.add_parameter("input_scaling", type = float,
                           flags = ZI_UHFLI.FLAG_GETSET,
                           channels = (1, 2), channel_prefix = "ch%d_",
                           minval = 1e-12, maxval = 1e12)
        
        self.add_parameter("input_ac_coupling", type = bool,
                           flags = ZI_UHFLI.FLAG_GETSET,
                           channels = (1, 2), channel_prefix = "ch%d_")
        
        self.add_parameter("input_50ohm", type = bool,
                           flags = ZI_UHFLI.FLAG_GETSET,
                           channels = (1, 2), channel_prefix = "ch%d_") 
        
        self.add_parameter("input_autorange", type = bool,
                           flags = ZI_UHFLI.FLAG_GETSET,
                           channels = (1, 2), channel_prefix = "ch%d_")
        
        self.add_parameter("input_difference", type = str,
                           flags = ZI_UHFLI.FLAG_GETSET,
                           channels = (1, 2), channel_prefix = "ch%d_")
        '''
        oscillators
        '''        
        self.add_parameter("carrier_freq", type = float, 
                           flags = ZI_UHFLI.FLAG_GETSET,
                           channels = (1, 2), channel_prefix = "ch%d_",
                           minval = 0, maxval = 600e6,
                           units = "Hz", tags = ["sweep"])
        '''
        demodulators:
        '''
        self.add_parameter("demod_harmonic", type = int,
                           flags = ZI_UHFLI.FLAG_GETSET,
                           channels = (1, 8), channel_prefix = "dem%d_",
                           minval = 1, maxval = 1023)
        
        self.add_parameter("phase_offs", type = float,
                           flags = ZI_UHFLI.FLAG_GETSET,
                           channels = (1, 8), channel_prefix = "dem%d_",
                           minval = 0, maxval = 360,
                           units = "deg", tags = ["sweep"])
        
        self.add_parameter("filter_order", type = int,
                           flags = ZI_UHFLI.FLAG_GETSET,
                           channels = (1, 8), channel_prefix = "dem%d_",
                           minval = 1, maxval = 8)
        
        self.add_parameter("filter_timeconst", type = float,
                           flags = ZI_UHFLI.FLAG_GETSET,
                           channels = (1, 8), channel_prefix = "dem%d_",
                           minval = 102.6e-9, maxval = 76.35,
                           units = "s", tags = ["sweep"])
        
        self.add_parameter("filter_sinc", type = bool,
                           flags = ZI_UHFLI.FLAG_GETSET,
                           channels = (1, 8), channel_prefix = "dem%d_")
        
        self.add_parameter("demod_enable", type = bool,
                           flags = ZI_UHFLI.FLAG_GETSET,
                           channels = (1, 8), channel_prefix = "dem%d_")
        
        self.add_parameter("sample_rate", type = float,
                           flags = ZI_UHFLI.FLAG_GETSET,
                           channels = (1, 8), channel_prefix = "dem%d_",
                           minval = 1.676, maxval = 14.06e6, 
                           units = "Hz", tags = ["sweep"])
        
        self.add_parameter("trigger_mode", type = str,
                           flags = ZI_UHFLI.FLAG_GETSET,
                           channels = (1, 8), channel_prefix = "dem%d_")
        '''
        signal outs:
        '''
        self.add_parameter("output", type = bool,
                           flags = ZI_UHFLI.FLAG_GETSET,
                           channels = (1, 2), channel_prefix = "ch%d_")

        self.add_parameter("output_50ohm", type = bool,
                           flags = ZI_UHFLI.FLAG_GETSET,
                           channels = (1, 2), channel_prefix = "ch%d_")
        
        self.add_parameter("output_range", type = float,
                           flags = ZI_UHFLI.FLAG_GETSET,
                           channels = (1, 2), channel_prefix = "ch%d_",
                           minval = 750e-3, maxval = 1.5,
                           units = "V")
        
        self.add_parameter("output_offset", type = float,
                           flags = ZI_UHFLI.FLAG_GETSET,
                           channels = (1, 2), channel_prefix = "ch%d_",
                           minval = -1.5, maxval = 1.5,
                           units = "V")
        
        self.add_parameter("output_amplitude", type = float,
                           flags = ZI_UHFLI.FLAG_GETSET,
                           channels = (1, 2), channel_prefix = "ch%d_",
                           minval = -1.5, maxval = 1.5,
                           units = "V")
        
        self.add_parameter("output_autorange", type = bool,
                           flags = ZI_UHFLI.FLAG_GETSET,
                           channels = (1, 2), channel_prefix = "ch%d_")
                
        self.add_parameter("output_amp_enable", type = bool,
                           flags = ZI_UHFLI.FLAG_GETSET,
                           channels = (1, 2), channel_prefix = "ch%d_")
        
        #Tell qkit which functions are intended for public use
        self.add_function("disable_everything")
        
        
        #public use functions
    def disable_everything(self):
        zhinst.utils.disable_everything(self.daq, self.device)
        
        
        #Set and get functions for the qkit wrapper, not intended for public use
        '''
        signal ins
        '''
        
    def _do_set_input_range(self, newrange, channel):
        logging.debug(__name__ + ' : setting range on input channel %s to %s V' % (channel, newrange))
        self.daq.setDouble("/%s/sigins/%s/range" % (self._device_id, channel-1), newrange)
        self.daq.sync()
    
    def _do_get_input_range(self, channel):
        logging.debug(__name__ + ' : getting range on input channel %s' % channel)
        return round(float(self.daq.getDouble("/%s/sigins/%s/range" % (self._device_id, channel-1))), 3)
    
    def _do_set_input_scaling(self, newscale, channel):
        logging.debug(__name__ + ' : setting scaling on input channel %s to %s' % (channel, newscale))
        self.daq.setDouble("/%s/sigins/%s/scaling" % (self._device_id, channel-1), newscale)
        self.daq.sync()
    
    def _do_get_input_scaling(self, channel):
        logging.debug(__name__ + ' : getting scaling on input channel %s' % channel)
        return round(float(self.daq.getDouble("/%s/sigins/%s/scaling" % (self._device_id, channel-1))), 3)
    
    
    def _do_set_input_ac_coupling(self, onoff, channel):
        if onoff:
            logging.debug(__name__ + ' : setting coupling on input channel %s to ac' % channel)
            status = 1
        else:
            logging.debug(__name__ + ' : setting coupling on input channel %s to dc' % channel)
            status = 0
        self.daq.setInt('/%s/sigins/%s/ac' % (self._device_id, channel-1), status)
        self.daq.sync()
    
    def _do_get_input_ac_coupling(self, channel):
        logging.debug(__name__ + ' : getting the coupling on input channel %s' % channel)
        if self.daq.getInt('/%s/sigins/%s/ac' % (self._device_id, channel-1)):
            return True
        else:
            return False
        
        
    def _do_set_input_50ohm(self, onoff, channel):
        if onoff:
            logging.debug(__name__ + ' : setting impedance on input channel %s to 50ohm' % channel)
            status = 1
        else:
            logging.debug(__name__ + ' : setting impedance on input channel %s to 1 MOhm' % channel)
            status = 0
        self.daq.setInt('/%s/sigins/%s/imp50' % (self._device_id, channel-1), status)
        self.daq.sync()
    
    def _do_get_input_50ohm(self, channel):
        logging.debug(__name__ + ' : getting the impedance of input channel %s' % channel)
        if self.daq.getInt('/%s/sigins/%s/imp50' % (self._device_id, channel-1)):
            return True
        else:
            return False
        
        
    def _do_set_input_autorange(self, onoff, channel):
        if onoff:
            logging.debug(__name__ + ' : activating autorange on input channel %s' % channel)
            status = 1
        else:
            logging.debug(__name__ + ' : deactivating autorange on input channel %s' % channel)
            status = 0
        self.daq.setInt('/%s/sigins/%s/autorange' % (self._device_id, channel-1), status)
        self.daq.sync()
    
    def _do_get_input_autorange(self, channel):
        logging.debug(__name__ + ' : getting the autorange status of input channel %s' % channel)
        if self.daq.getInt('/%s/sigins/%s/autorange' % (self._device_id, channel-1)):
            return True
        else:
            return False
        
        
    def _do_set_input_difference(self, newmode, channel):
        logging.debug(__name__ + " : setting difference mode on input channel %s to %s" % (channel, newmode))
        try:
            self.daq.setInt('/%s/sigins/%s/diff' % (self._device_id, channel-1), self._difference_mode_dict[newmode])
        except:
            logging.warning("Hahahaha. Your difference mode is invaliiiiid!")
    
    def _do_get_input_difference(self, channel):
        logging.debug(__name__ + ' : getting difference mode on input channel %s' % channel)
        return self._inv_difference_mode_dict[self.daq.getInt('/%s/sigins/%s/diff' % (self._device_id, channel-1))]
    '''
    oscillators
    '''    
    def _do_set_carrier_freq(self, newfreq, channel):
        logging.debug(__name__ + ' : setting carrier frequency on channel %s to %s Hz' % (channel, newfreq))
        self.daq.setDouble("/%s/oscs/%s/freq" % (self._device_id, channel-1), newfreq)
        self.daq.sync()
    
    def _do_get_carrier_freq(self, channel):
        logging.debug(__name__ + ' : getting carrier frequency on channel %s' % channel)
        return round(float(self.daq.getDouble("/%s/oscs/%s/freq" % (self._device_id, channel-1))), 3)
    '''
    demodulators
    '''
    def _do_set_demod_harmonic(self, newharmonic, channel):
        logging.debug(__name__ + " : setting harmonic on demodulator %s to %s" % (channel, newharmonic))
        self.daq.setInt("/%s/demods/%s/harmonic" % (self._device_id, channel-1), newharmonic)
        self.daq.sync()
    
    def _do_get_demod_harmonic(self, channel):
        logging.debug(__name__ + ' : getting harmonic on demodulator %s' % channel)
        return int(self.daq.getInt("/%s/demods/%s/harmonic" % (self._device_id, channel-1)))


    def _do_set_phase_offs(self, newoffs, channel):
        logging.debug(__name__ + " : setting phase offset on demodulator %s to %s deg" % (channel, newoffs))
        self.daq.setDouble("/%s/demods/%s/phaseshift" % (self._device_id, channel-1), newoffs)
        self.daq.sync()
    
    def _do_get_phase_offs(self, channel):
        logging.debug(__name__ + ' : getting phase offset on demodulator %s' % channel)
        return round(float(self.daq.getDouble("/%s/demods/%s/phaseshift" % (self._device_id, channel-1))), 3)
    
    
    def _do_set_filter_order(self, neworder, channel):
        logging.debug(__name__ + " : setting filter order on demodulator %s to %s" % (channel, neworder))
        self.daq.setInt('/%s/demods/%s/order' % (self._device_id, channel-1) , neworder)
        self.daq.sync()        
        
    def _do_get_filter_order(self, channel):
        logging.debug(__name__ + ' : getting filter order on demodulator %s' % channel)
        return(self.daq.getInt('/%s/demods/%s/order' % (self._device_id, channel-1)))
        
        
    def _do_set_filter_timeconst(self, newtc, channel):
        logging.debug(__name__ + " : setting filter time constant on demodulator %s to %s s" % (channel, newtc))
        self.daq.setDouble('/%s/demods/%s/timeconstant' % (self._device_id, channel-1), newtc)
        self.daq.sync()
        sleep(10 * newtc)
    
    def _do_get_filter_timeconst(self, channel):
        logging.debug(__name__ + ' : getting filter timeconstant on demodulator %s' % channel)
        return float(self.daq.getDouble('/%s/demods/%s/timeconstant' % (self._device_id, channel-1)))
    
    
    def _do_set_filter_sinc(self, onoff, channel):
        if onoff:
            logging.debug(__name__ + ' : activating sinc filter on demodulator %s' % channel)
            status = 1
        else:
            logging.debug(__name__ + ' : deactivating sinc filter on demodulator %s' % channel)
            status = 0
        self.daq.setInt('/%s/demods/%s/sinc' % (self._device_id, channel-1), status)
        self.daq.sync()
    
    def _do_get_filter_sinc(self, channel):
        logging.debug(__name__ + ' : getting sinc filter status on demodulator %s' % channel)
        if self.daq.getInt('/%s/demods/%s/sinc' % (self._device_id, channel-1)):
            return True
        else:
            return False
    
    
    def _do_set_demod_enable(self, onoff, channel):
        if onoff:
            logging.debug(__name__ + ' : activating demodulator %s' % channel)
            status = 1
        else:
            logging.debug(__name__ + ' : deactivating demodulator %s' % channel)
            status = 0
        self.daq.setInt('/%s/demods/%s/enable' % (self._device_id, channel-1), status)
        self.daq.sync()
    
    def _do_get_demod_enable(self, channel):
        logging.debug(__name__ + ' : getting status of demodulator %s' % channel)
        if self.daq.getInt('/%s/demods/%s/enable' % (self._device_id, channel-1)):
            return True
        else:
            return False
    
    
    def _do_set_sample_rate(self, newrate, channel):
        logging.debug(__name__ + " : setting sample rate on demodulator %s to %s s" % (channel, newrate))
        self.daq.setDouble('/%s/demods/%s/rate' % (self._device_id, channel-1), newrate)
        self.daq.sync()
    
    def _do_get_sample_rate(self, channel):
        logging.debug(__name__ + ' : getting sample rate on demodulator %s' % channel)
        return float(self.daq.getDouble('/%s/demods/%s/rate' % (self._device_id, channel-1)))
    
    
    def _do_set_trigger_mode(self, newmode, channel):
        logging.debug(__name__ + " : setting trigger mode on demodulator %s to %s" % (channel, newmode))
        try:
            self.daq.setInt('/%s/demods/%s/trigger' % (self._device_id, channel-1), self._trigger_mode_dict[newmode])
        except:
            logging.warning("You entered an invalid trigger mode, puny human.")
    
    def _do_get_trigger_mode(self, channel):
        logging.debug(__name__ + ' : getting trigger mode on demodulator %s' % channel)
        return self._inv_trigger_mode_dict[self.daq.getInt('/%s/demods/%s/trigger' % (self._device_id, channel-1))]
    '''
    signal outs
    '''
    def _do_set_output(self, onoff, channel):
        if onoff:
            logging.debug(__name__ + ' : activating output channel %s' % channel)
            status = 1
        else:
            logging.debug(__name__ + ' : deactivating output channel %s' % channel)
            status = 0
        self.daq.setInt('/%s/sigouts/%s/on' % (self._device_id, channel-1), status)
        self.daq.sync()
    
    def _do_get_output(self, channel):
        logging.debug(__name__ + ' : getting status of output channel %s' % channel)
        if self.daq.getInt('/%s/sigouts/%s/on' % (self._device_id, channel-1)):
            return True
        else:
            return False


    def _do_set_output_50ohm(self, onoff, channel):
        if onoff:
            logging.debug(__name__ + ' : expecting a 50ohm load on output channel %s' % channel)
            self.set_parameter_bounds("ch%d_output_range" % channel, 75e-3, 150e-3)
            status = 1
        else:
            logging.debug(__name__ + ' : expecting a HiZ load on output channel %s' % channel)
            self.set_parameter_bounds("ch%d_output_range" % channel, 750e-3, 1.5)
            status = 0
        self.daq.setInt('/%s/sigouts/%s/imp50' % (self._device_id, channel-1), status)
        self.daq.sync()
    
    def _do_get_output_50ohm(self, channel):
        logging.debug(__name__ + ' : getting the expected load impedance of output channel %s' % channel)
        if self.daq.getInt('/%s/sigouts/%s/imp50' % (self._device_id, channel-1)):
            return True
        else:
            return False


    def _do_set_output_range(self,newrange,channel):
        valuesarray = np.array([75e-3, 750e-3])
        if not self.daq.getInt('/%s/sigouts/%s/imp50' % (self._device_id, channel-1)):
            valuesarray = 2 * valuesarray
        if newrange not in valuesarray:
            index = np.searchsorted(valuesarray, newrange, side = 'right')-1
            newrange = valuesarray[index if index >= 0 else 0]
            logging.warning(__name__ + " : Invalid output range value. Setting output range to next lower value: %s" % newrange)
            
        logging.debug(__name__ + ': setting range on output channel %s to %s V' % (channel-1, newrange))
        self.set_parameter_bounds("ch%d_output_offset" % channel, -newrange, newrange)
        self.set_parameter_bounds("ch%d_output_amplitude" % channel, -newrange, newrange)
        self.daq.setDouble('/%s/sigouts/%s/range' % (self._device_id, channel-1), newrange)
        self.daq.sync()
    
    def _do_get_output_range(self, channel):
        logging.debug(__name__ + ' : getting range on output channel %s' % channel)
        return float(self.daq.getDouble('/%s/sigouts/%s/range' % (self._device_id, channel-1)))
    
    
    def _do_set_output_offset(self, newoffs, channel):
        logging.debug(__name__ + " : setting offset on output channel %s to %s s" % (channel, newoffs))
        self.daq.setDouble('/%s/sigouts/%s/offset' % (self._device_id, channel-1), newoffs)
        self.daq.sync()
    
    def _do_get_output_offset(self, channel):
        logging.debug(__name__ + " : getting offset on output channel %s" % channel)
        return float(self.daq.getDouble('/%s/sigouts/%s/offset' % (self._device_id, channel-1)))
    
    
    def _do_set_output_amplitude(self, newampl, channel):
        logging.debug(__name__ + " : setting amplitude on output channel %s to %s s" % (channel, newampl))
        self.daq.setDouble('/%s/sigouts/%s/amplitudes/%s' % (self._device_id, channel-1, 3 + 4 * (channel-1)), newampl)
        self.daq.sync()
    
    def _do_get_output_amplitude(self, channel):
        logging.debug(__name__ + " : getting amplitude on output channel %s" % channel)
        return float(self.daq.getDouble('/%s/sigouts/%s/amplitudes/%s' % (self._device_id, channel-1, 3 + 4 * (channel-1))))
    

    def _do_set_output_autorange(self, onoff, channel):
        if onoff:
            logging.debug(__name__ + ' : activating autorange on output channel %s' % channel)
            status = 1
        else:
            logging.debug(__name__ + ' : deactivating autorange on output channel %s' % channel)
            status = 0
        self.daq.setInt('/%s/sigouts/%s/autorange' % (self._device_id, channel-1), status)
        self.daq.sync()
    
    def _do_get_output_autorange(self, channel):
        logging.debug(__name__ + ' : getting autorange status on output channel %s' % channel)
        if self.daq.getInt('/%s/sigouts/%s/autorange' % (self._device_id, channel-1)):
            return True
        else:
            return False
        

    def _do_set_output_amp_enable(self, onoff, channel):
        if onoff:
            logging.debug(__name__ + ' : activating amplitude on output channel %s' % channel)
            status = 1
        else:
            logging.debug(__name__ + ' : deactivating amplitude on channel %s' % channel)
            status = 0
        self.daq.setInt('/%s/sigouts/%s/enables/%s'  % (self._device_id, channel-1, 3 + 4 * (channel-1)), status)
        self.daq.sync()
    
    def _do_get_output_amp_enable(self, channel):
        logging.debug(__name__ + ' : getting amplitude status on output channel %s' % channel)
        if self.daq.getInt('/%s/sigouts/%s/enables/%s'  % (self._device_id, channel-1, 3 + 4 * (channel-1))):
            return True
        else:
            return False        


if __name__ == "__main__":
    import qkit
    qkit.start()    
    
    UHFLI_test = qkit.instruments.create("UHFLI_test", "ZI_UHFLI", device_id = "dev2587")
    '''
    UHFLI_test.set_ch1_carrier_freq(400e6)
    UHFLI_test.set_dem8_demod_harmonic(4)
    UHFLI_test.set_dem1_phase_offs(10)
    UHFLI_test.set_dem1_filter_order(5)
    UHFLI_test.set_dem1_filter_timeconst(1e-6)
    UHFLI_test.set_dem1_filter_sinc(True)
    UHFLI_test.set_dem1_demod_enable(True)
    UHFLI_test.set_dem1_sample_rate(5e3)
    UHFLI_test.set_dem2_trigger_mode("in3_rising")
    UHFLI_test.set_dem3_trigger_mode("in585")
    UHFLI_test.set_ch1_output(True)
    UHFLI_test.set_ch1_output_50ohm(False)
    UHFLI_test.set_ch1_output_range(1500e-3)
    UHFLI_test.set_ch1_output_offset(160e-3)
    UHFLI_test.set_ch1_output_amplitude(300e-3)
    UHFLI_test.set_ch2_output_amplitude(400e-3)
    UHFLI_test.set_ch1_output_autorange(False)
    UHFLI_test.set_ch2_output_autorange(False)
    UHFLI_test.set_ch1_output_amp_enable(True)
    UHFLI_test.set_ch2_output_amp_enable(True)
    '''
    UHFLI_test.set_ch2_input_range(0.5)
    UHFLI_test.set_ch2_input_scaling(32)
    UHFLI_test.set_ch2_input_ac_coupling(True)
    UHFLI_test.set_ch2_input_50ohm(True)
    UHFLI_test.set_ch2_input_autorange(True)
    UHFLI_test.set_ch2_input_difference("in2-in1")
    '''
    print(UHFLI_test.get_ch1_carrier_freq())
    print(UHFLI_test.get_dem1_phase_offs())
    print(UHFLI_test.get_dem1_filter_order())
    print(UHFLI_test.get_dem1_filter_timeconst())
    print(UHFLI_test.get_dem4_filter_sinc())
    print(UHFLI_test.get_dem4_demod_enable())
    print(UHFLI_test.get_dem1_sample_rate())
    print(UHFLI_test.get_dem1_trigger_mode())
    print(UHFLI_test.get_ch2_output())
    print(UHFLI_test.get_ch1_output_50ohm())
    print(UHFLI_test.get_ch1_output_range())
    print(UHFLI_test.get_ch1_output_offset())
    print(UHFLI_test.get_ch1_output_amplitude())
    print(UHFLI_test.get_ch2_output_amplitude())
    '''
    print(UHFLI_test.get_ch1_input_range())
    print(UHFLI_test.get_ch1_input_scaling())
    print(UHFLI_test.get_ch1_input_ac_coupling())
    print(UHFLI_test.get_ch1_input_50ohm())
    print(UHFLI_test.get_ch1_input_autorange())
    print(UHFLI_test.get_ch1_input_difference())
    print("Done!")
    UHFLI_test.disable_everything()