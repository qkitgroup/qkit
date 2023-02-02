#This is a clone of the UHFLI driver that is being adapted to the MFLI, work under construcion


# ZI_UHFLI driver, Julian Ferrero
#
# This program is free software; you can redistribute it an d/or modify
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
#from _ZI_toolkit import daq_module_toolz
import zhinst.utils
import logging
from time import sleep
import numpy as np

class ZI_MFLI(Instrument):

    def __init__(self, name, device_id):

       # Input:
       #     name (string)    : name of the instrument
       #     device_id : serial number of the instrument
       
        logging.info(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical', "lock-in amplifier"])
        
        self._device_id = device_id
        self._trigger_mode_dict = {"continuous" : 0,
                                   "edge" : 1,
                                   "pulse" : 3,
                                   "tracking" : 4,
                                   "digital" : 2,
                                   "hardware" : 6,
                                   "pulse_counter" : 8}
        self._inv_trigger_mode_dict = {v: k for k, v in self._trigger_mode_dict.items()}
        self._difference_mode_dict = {"off" : 0,
                                      "inverted" : 1}
        self._filter_settling_factors = {r"63.2%" : [1.0, 2.15, 3.26, 4.35, 
                                                   5.43, 6.51, 7.58, 8.64],
                                         r"90%" : [2.3, 3.89, 5.32, 6.68, 
                                                   7.99, 9.27, 10.53, 11.77],
                                         r"99%" : [4.61, 6.64, 8.41, 10.05, 
                                                   11.6, 13.11, 14.57, 16]}
        self._inv_difference_mode_dict = {v: k for k, v in self._difference_mode_dict.items()}
                
        #Set the apilevel to the highest supported by your device, to unlock most of the functionalities.
        #Create an apisession, to be able to control the device from python.     
        self._apilevel = 6
        self._bad_device_message = "No MFLI device found."
        (self.daq, self.device, _) = zhinst.utils.create_api_session(self._device_id, self._apilevel, 
                                        required_devtype = "MFLI", 
                                        required_err_msg = self._bad_device_message)
        zhinst.utils.api_server_version_check(self.daq)     
        
        #Add Instrument parameters in a way that qkit knows they are there
        '''
        signal ins:
        '''
        
        self.add_parameter("input_range", type = float,
                           flags = ZI_MFLI.FLAG_GETSET,
                           channels = (0, 1), channel_prefix = "ch%d_",
                           minval = 10e-3, maxval = 1.5, 
                           units = "V")
        
        self.add_parameter("input_scaling", type = float,
                           flags = ZI_MFLI.FLAG_GETSET,
                           channels = (0, 1), channel_prefix = "ch%d_",
                           minval = 1e-12, maxval = 1e12)
        
        self.add_parameter("input_ac_coupling", type = bool,
                           flags = ZI_MFLI.FLAG_GETSET,
                           channels = (0, 1), channel_prefix = "ch%d_")
        
        self.add_parameter("input_50ohm", type = bool,
                           flags = ZI_MFLI.FLAG_GETSET,
                           channels = (0, 1), channel_prefix = "ch%d_") 
        
        self.add_parameter("input_autorange", type = bool,
                           flags = ZI_MFLI.FLAG_GETSET,
                           channels = (0, 1), channel_prefix = "ch%d_")
        
        self.add_parameter("input_difference", type = str,
                           flags = ZI_MFLI.FLAG_GETSET,
                           channels = (0, 1), channel_prefix = "ch%d_")
        '''
        oscillators
        '''        
        self.add_parameter("carrier_freq", type = float, 
                           flags = ZI_MFLI.FLAG_GETSET,
                           channels = (0, 1), channel_prefix = "ch%d_",
                           minval = 0, maxval = 600e6,
                           units = "Hz", tags = ["sweep"])
        '''
        demodulators:
        '''
        self.add_parameter("demod_harmonic", type = int,
                           flags = ZI_MFLI.FLAG_GETSET,
                           channels = (0, 7), channel_prefix = "dem%d_",
                           minval = 1, maxval = 1023)
        
        self.add_parameter("phase_offs", type = float,
                           flags = ZI_MFLI.FLAG_GETSET,
                           channels = (0, 7), channel_prefix = "dem%d_",
                           minval = 0, maxval = 360,
                           units = "deg", tags = ["sweep"])

        self.add_parameter("autophase", type = bool,
                           flags = ZI_MFLI.FLAG_GETSET,
                           channels = (0, 7), channel_prefix = "dem%d_")
        
        self.add_parameter("filter_order", type = int,
                           flags = ZI_MFLI.FLAG_GETSET,
                           channels = (0, 7), channel_prefix = "dem%d_",
                           minval = 1, maxval = 8)
        
        self.add_parameter("filter_timeconst", type = float,
                           flags = ZI_MFLI.FLAG_GETSET,
                           channels = (0, 7), channel_prefix = "dem%d_",
                           minval = 102.6e-9, maxval = 76.35,
                           units = "s", tags = ["sweep"])
        
        self.add_parameter("filter_sinc", type = bool,
                           flags = ZI_MFLI.FLAG_GETSET,
                           channels = (0, 7), channel_prefix = "dem%d_")
        
        self.add_parameter("demod_enable", type = bool,
                           flags = ZI_MFLI.FLAG_GETSET,
                           channels = (0, 7), channel_prefix = "dem%d_")
        
        self.add_parameter("sample_rate", type = float,
                           flags = ZI_MFLI.FLAG_GETSET,
                           channels = (0, 7), channel_prefix = "dem%d_",
                           minval = 1.676, maxval = 14.06e6, 
                           units = "Hz", tags = ["sweep"])
        
        self.add_parameter("trigger_mode", type = str,
                           flags = ZI_MFLI.FLAG_GETSET,
                           channels = (0, 7), channel_prefix = "dem%d_")
        '''
        signal outs:
        '''
        self.add_parameter("output", type = bool,
                           flags = ZI_MFLI.FLAG_GETSET,
                           channels = (0, 1), channel_prefix = "ch%d_")

        self.add_parameter("output_50ohm", type = bool,
                           flags = ZI_MFLI.FLAG_GETSET,
                           channels = (0, 1), channel_prefix = "ch%d_")
        
        self.add_parameter("output_range", type = float,
                           flags = ZI_MFLI.FLAG_GETSET,
                           channels = (0, 1), channel_prefix = "ch%d_",
                           minval = 75e-3, maxval = 1.5,
                           units = "V")
        
        self.add_parameter("output_offset", type = float,
                           flags = ZI_MFLI.FLAG_GETSET,
                           channels = (0, 1), channel_prefix = "ch%d_",
                           minval = -1.5, maxval = 1.5,
                           units = "V")
        
        self.add_parameter("output_amplitude", type = float,
                           flags = ZI_MFLI.FLAG_GETSET,
                           channels = (0, 1), channel_prefix = "ch%d_",
                           minval = -1.5, maxval = 1.5,
                           units = "V")
        
        self.add_parameter("output_autorange", type = bool,
                           flags = ZI_MFLI.FLAG_GETSET,
                           channels = (0, 1), channel_prefix = "ch%d_")
                
        self.add_parameter("output_amp_enable", type = bool,
                           flags = ZI_MFLI.FLAG_GETSET,
                           channels = (0, 1), channel_prefix = "ch%d_")
        
        '''
        Software parameters:
        '''
        self.add_parameter("step_recovery", type = str,
                          flags = self.FLAG_SET | self.FLAG_SOFTGET,
                          channels = (0, 7), channel_prefix = "dem%d_")
        
        for demod_index in range(8):
            self.set(f"dem{demod_index}_step_recovery", r"99%")
        self.settling_times = [0] * 8
        self.calc_all_settling_times()
        
        #Tell qkit which functions are intended for public use
        self.add_function("disable_everything")
        self.add_function("calc_settling_time")
        self.add_function("wait_settle_time")
        self.add_function("wait_longest_settle_time")
        self.add_function("calc_all_settling_times")
        


    def disable_everything(self):
        zhinst.utils.disable_everything(self.daq, self.device)
        
    def calc_settling_time(self, demod_index):
        step_recovery = self.get(f'dem{demod_index}_step_recovery')
        tc = self.get(f'dem{demod_index}_filter_timeconst') 
        order = self.get(f"dem{demod_index}_filter_order")
        return tc * self._filter_settling_factors[step_recovery][order - 1]
        
    def wait_settle_time(self, demod_index):
        sleep(self.settling_times[demod_index])
        
    def wait_longest_settle_time(self):
        sleep(self.longest_settling_time)
        
    def calc_all_settling_times(self):
        for demod_index in range(8):
            self.settling_times[demod_index] = self.calc_settling_time(demod_index)
        self.longest_settling_time = max(self.settling_times)
        
    '''
    signal ins
    '''        
    def _do_set_input_range(self, newrange, channel):
        logging.debug(__name__ + ' : setting range on input channel %s to %s V' % (channel, newrange))
        self.daq.setDouble("/%s/sigins/%s/range" % (self._device_id, channel), newrange)
        #self.daq.sync()
    
    def _do_get_input_range(self, channel):
        logging.debug(__name__ + ' : getting range on input channel %s' % channel)
        return round(float(self.daq.getDouble("/%s/sigins/%s/range" % (self._device_id, channel))), 3)
    
    def _do_set_input_scaling(self, newscale, channel):
        logging.debug(__name__ + ' : setting scaling on input channel %s to %s' % (channel, newscale))
        self.daq.setDouble("/%s/sigins/%s/scaling" % (self._device_id, channel), newscale)
        #self.daq.sync()
    
    def _do_get_input_scaling(self, channel):
        logging.debug(__name__ + ' : getting scaling on input channel %s' % channel)
        return round(float(self.daq.getDouble("/%s/sigins/%s/scaling" % (self._device_id, channel))), 3)
    
    
    def _do_set_input_ac_coupling(self, onoff, channel):
        if onoff:
            logging.debug(__name__ + ' : setting coupling on input channel %s to ac' % channel)
            status = 1
        else:
            logging.debug(__name__ + ' : setting coupling on input channel %s to dc' % channel)
            status = 0
        self.daq.setInt('/%s/sigins/%s/ac' % (self._device_id, channel), status)
        #self.daq.sync()
    
    def _do_get_input_ac_coupling(self, channel):
        logging.debug(__name__ + ' : getting the coupling on input channel %s' % channel)
        if self.daq.getInt('/%s/sigins/%s/ac' % (self._device_id, channel)):
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
        self.daq.setInt('/%s/sigins/%s/imp50' % (self._device_id, channel), status)
        #self.daq.sync()
    
    def _do_get_input_50ohm(self, channel):
        logging.debug(__name__ + ' : getting the impedance of input channel %s' % channel)
        if self.daq.getInt('/%s/sigins/%s/imp50' % (self._device_id, channel)):
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
        self.daq.setInt('/%s/sigins/%s/autorange' % (self._device_id, channel), status)
        #self.daq.sync()
    
    def _do_get_input_autorange(self, channel):
        logging.debug(__name__ + ' : getting the autorange status of input channel %s' % channel)
        if self.daq.getInt('/%s/sigins/%s/autorange' % (self._device_id, channel)):
            return True
        else:
            return False
        
        
    def _do_set_input_difference(self, newmode, channel):
        logging.debug(__name__ + " : setting difference mode on input channel %s to %s" % (channel, newmode))
        try:
            self.daq.setInt('/%s/sigins/%s/diff' % (self._device_id, channel), self._difference_mode_dict[newmode])
        except:
            logging.warning("Hahahaha. Your difference mode is invaliiiiid!")
    
    def _do_get_input_difference(self, channel):
        logging.debug(__name__ + ' : getting difference mode on input channel %s' % channel)
        return self._inv_difference_mode_dict[self.daq.getInt('/%s/sigins/%s/diff' % (self._device_id, channel))]
    '''
    oscillators
    '''    
    def _do_set_carrier_freq(self, newfreq, channel):
        logging.debug(__name__ + ' : setting carrier frequency on channel %s to %s Hz' % (channel, newfreq))
        self.daq.setDouble("/%s/oscs/%s/freq" % (self._device_id, channel), newfreq)
        #self.daq.sync()
    
    def _do_get_carrier_freq(self, channel):
        logging.debug(__name__ + ' : getting carrier frequency on channel %s' % channel)
        return round(float(self.daq.getDouble("/%s/oscs/%s/freq" % (self._device_id, channel))), 3)
    '''
    demodulators
    '''
    def _do_set_demod_harmonic(self, newharmonic, channel):
        logging.debug(__name__ + " : setting harmonic on demodulator %s to %s" % (channel, newharmonic))
        self.daq.setInt("/%s/demods/%s/harmonic" % (self._device_id, channel), newharmonic)
        #self.daq.sync()
    
    def _do_get_demod_harmonic(self, channel):
        logging.debug(__name__ + ' : getting harmonic on demodulator %s' % channel)
        return int(self.daq.getInt("/%s/demods/%s/harmonic" % (self._device_id, channel)))


    def _do_set_phase_offs(self, newoffs, channel):
        logging.debug(__name__ + " : setting phase offset on demodulator %s to %s deg" % (channel, newoffs))
        self.daq.setDouble("/%s/demods/%s/phaseshift" % (self._device_id, channel), newoffs)
        #self.daq.sync()
    
    def _do_get_phase_offs(self, channel):
        logging.debug(__name__ + ' : getting phase offset on demodulator %s' % channel)
        return round(float(self.daq.getDouble("/%s/demods/%s/phaseshift" % (self._device_id, channel))), 3)    
        
    def _do_set_input_autophase(self, onoff, channel):
        if onoff:
            logging.debug(__name__ + ' : activating autophase on input channel %s' % channel)
            status = 1
        else:
            logging.debug(__name__ + ' : deactivating autophase on input channel %s' % channel)
            status = 0
        self.daq.setInt('/%s/demods/%s/phaseadjust' % (self._device_id, channel), status)
        #self.daq.sync()
    
    def _do_get_input_autophase(self, channel):
        logging.debug(__name__ + ' : getting the autorange status of input channel %s' % channel)
        if self.daq.getInt('/%s/demods/%s/phaseadjust' % (self._device_id, channel)):
            return True
        else:
            return False
    
    
    def _do_set_filter_order(self, neworder, channel):
        logging.debug(__name__ + " : setting filter order on demodulator %s to %s" % (channel, neworder))
        self.daq.setInt('/%s/demods/%s/order' % (self._device_id, channel) , neworder)
        self.settling_times[channel] = self.calc_settling_time(channel)
        self.longest_settling_time = max(self.settling_times)
        #self.daq.sync()
        self.wait_settle_time(channel)        
        
    def _do_get_filter_order(self, channel):
        logging.debug(__name__ + ' : getting filter order on demodulator %s' % channel)
        return(self.daq.getInt('/%s/demods/%s/order' % (self._device_id, channel)))
        
        
    def _do_set_filter_timeconst(self, newtc, channel):
        logging.debug(__name__ + " : setting filter time constant on demodulator %s to %s s" % (channel, newtc))
        self.daq.setDouble('/%s/demods/%s/timeconstant' % (self._device_id, channel), newtc)
        self.settling_times[channel] = self.calc_settling_time(channel)
        self.longest_settling_time = max(self.settling_times)
        
        #self.daq.sync()
        self.wait_settle_time(channel)
    
    def _do_get_filter_timeconst(self, channel):
        logging.debug(__name__ + ' : getting filter timeconstant on demodulator %s' % channel)
        return float(self.daq.getDouble('/%s/demods/%s/timeconstant' % (self._device_id, channel)))
    
    
    def _do_set_filter_sinc(self, onoff, channel):
        if onoff:
            logging.debug(__name__ + ' : activating sinc filter on demodulator %s' % channel)
            status = 1
        else:
            logging.debug(__name__ + ' : deactivating sinc filter on demodulator %s' % channel)
            status = 0
        self.daq.setInt('/%s/demods/%s/sinc' % (self._device_id, channel), status)
        #self.daq.sync()
    
    def _do_get_filter_sinc(self, channel):
        logging.debug(__name__ + ' : getting sinc filter status on demodulator %s' % channel)
        if self.daq.getInt('/%s/demods/%s/sinc' % (self._device_id, channel)):
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
        self.daq.setInt('/%s/demods/%s/enable' % (self._device_id, channel), status)
        #self.daq.sync()
    
    def _do_get_demod_enable(self, channel):
        logging.debug(__name__ + ' : getting status of demodulator %s' % channel)
        if self.daq.getInt('/%s/demods/%s/enable' % (self._device_id, channel)):
            return True
        else:
            return False
    
    
    def _do_set_sample_rate(self, newrate, channel):
        logging.debug(__name__ + " : setting sample rate on demodulator %s to %s s" % (channel, newrate))
        self.daq.setDouble('/%s/demods/%s/rate' % (self._device_id, channel), newrate)
        #self.daq.sync()
    
    def _do_get_sample_rate(self, channel):
        logging.debug(__name__ + ' : getting sample rate on demodulator %s' % channel)
        return float(self.daq.getDouble('/%s/demods/%s/rate' % (self._device_id, channel)))
    
    
    def _do_set_trigger_mode(self, newmode, channel):
        logging.debug(__name__ + " : setting trigger mode on demodulator %s to %s" % (channel, newmode))
        try:
            self.daq.setInt('/%s/demods/%s/trigger' % (self._device_id, channel), self._trigger_mode_dict[newmode])
        except:
            logging.warning("You entered an invalid trigger mode, puny human.")
    
    def _do_get_trigger_mode(self, channel):
        logging.debug(__name__ + ' : getting trigger mode on demodulator %s' % channel)
        return self._inv_trigger_mode_dict[self.daq.getInt('/%s/demods/%s/trigger' % (self._device_id, channel))]
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
        self.daq.setInt('/%s/sigouts/%s/on' % (self._device_id, channel), status)
        #self.daq.sync()
    
    def _do_get_output(self, channel):
        logging.debug(__name__ + ' : getting status of output channel %s' % channel)
        if self.daq.getInt('/%s/sigouts/%s/on' % (self._device_id, channel)):
            return True
        else:
            return False


    def _do_set_output_50ohm(self, onoff, channel):
        if onoff:
            logging.debug(__name__ + ' : expecting a 50ohm load on output channel %s' % channel)
            self.set_parameter_bounds("ch%d_output_range" % channel, 75e-3, 750e-3)
            status = 1
        else:
            logging.debug(__name__ + ' : expecting a HiZ load on output channel %s' % channel)
            self.set_parameter_bounds("ch%d_output_range" % channel, 150e-3, 1.5)
            status = 0
        self.daq.setInt('/%s/sigouts/%s/imp50' % (self._device_id, channel), status)
        #self.daq.sync()
    
    def _do_get_output_50ohm(self, channel):
        logging.debug(__name__ + ' : getting the expected load impedance of output channel %s' % channel)
        if self.daq.getInt('/%s/sigouts/%s/imp50' % (self._device_id, channel)):
            return True
        else:
            return False


    def _do_set_output_range(self,newrange,channel):
        valuesarray = np.array([75e-3, 750e-3])
        if not self.daq.getInt('/%s/sigouts/%s/imp50' % (self._device_id, channel)):
            valuesarray = 2 * valuesarray
        if newrange not in valuesarray:
            index = np.searchsorted(valuesarray, newrange, side = 'right')-1
            newrange = valuesarray[index if index >= 0 else 0]
            logging.warning(__name__ + " : Invalid output range value. Setting output range to next lower value: %s" % newrange)
            
        logging.debug(__name__ + ': setting range on output channel %s to %s V' % (channel, newrange))
        self.set_parameter_bounds("ch%d_output_offset" % channel, -newrange, newrange)
        self.set_parameter_bounds("ch%d_output_amplitude" % channel, -newrange, newrange)
        self.daq.setDouble('/%s/sigouts/%s/range' % (self._device_id, channel), newrange)
        #self.daq.sync()
    
    def _do_get_output_range(self, channel):
        logging.debug(__name__ + ' : getting range on output channel %s' % channel)
        return float(self.daq.getDouble('/%s/sigouts/%s/range' % (self._device_id, channel)))
    
    
    def _do_set_output_offset(self, newoffs, channel):
        logging.debug(__name__ + " : setting offset on output channel %s to %s s" % (channel, newoffs))
        self.daq.setDouble('/%s/sigouts/%s/offset' % (self._device_id, channel), newoffs)
        #self.daq.sync()
    
    def _do_get_output_offset(self, channel):
        logging.debug(__name__ + " : getting offset on output channel %s" % channel)
        return float(self.daq.getDouble('/%s/sigouts/%s/offset' % (self._device_id, channel)))
    
    
    def _do_set_output_amplitude(self, newampl, channel):
        logging.debug(__name__ + " : setting amplitude on output channel %s to %s s" % (channel, newampl))
        self.daq.setDouble('/%s/sigouts/%s/amplitudes/%s' % (self._device_id, channel, 3 + 4 * (channel)), newampl)
        #self.daq.sync()
    
    def _do_get_output_amplitude(self, channel):
        logging.debug(__name__ + " : getting amplitude on output channel %s" % channel)
        return float(self.daq.getDouble('/%s/sigouts/%s/amplitudes/%s' % (self._device_id, channel, 3 + 4 * (channel))))
    

    def _do_set_output_autorange(self, onoff, channel):
        if onoff:
            logging.debug(__name__ + ' : activating autorange on output channel %s' % channel)
            status = 1
        else:
            logging.debug(__name__ + ' : deactivating autorange on output channel %s' % channel)
            status = 0
        self.daq.setInt('/%s/sigouts/%s/autorange' % (self._device_id, channel), status)
        #self.daq.sync()
    
    def _do_get_output_autorange(self, channel):
        logging.debug(__name__ + ' : getting autorange status on output channel %s' % channel)
        if self.daq.getInt('/%s/sigouts/%s/autorange' % (self._device_id, channel)):
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
        self.daq.setInt('/%s/sigouts/%s/enables/%s'  % (self._device_id, channel, 3 + 4 * (channel)), status)
        #self.daq.sync()
    
    def _do_get_output_amp_enable(self, channel):
        logging.debug(__name__ + ' : getting amplitude status on output channel %s' % channel)
        if self.daq.getInt('/%s/sigouts/%s/enables/%s'  % (self._device_id, channel, 3 + 4 * (channel))):
            return True
        else:
            return False
    '''
    Software Parameters
    '''
    def _do_set_step_recovery(self, new_rec, channel):
        allowed_recs = self._filter_settling_factors.keys()
        if new_rec not in allowed_recs:
            raise ValueError(f"{__name__}: {new_rec} is not a defined step recovery percentile. The allowed percentiles are {allowed_recs}.")
        logging.debug(__name__ + ' : setting step_recovery to %s' % (new_rec))


if __name__ == "__main__":
    import qkit
    qkit.start()    
    
    MFLI_test = qkit.instruments.create("MFLI_test", "ZI_MFLI", device_id = "dev2587")
    '''
    MFLI_test.set_ch0_carrier_freq(400e6)
    MFLI_test.set_dem8_demod_harmonic(4)
    MFLI_test.set_dem1_phase_offs(10)
    MFLI_test.set_dem1_filter_order(5)
    MFLI_test.set_dem1_filter_timeconst(1e-6)
    MFLI_test.set_dem1_filter_sinc(True)
    MFLI_test.set_dem1_demod_enable(True)
    MFLI_test.set_dem1_sample_rate(5e3)
    MFLI_test.set_dem2_trigger_mode("in3_rising")
    MFLI_test.set_dem3_trigger_mode("in585")
    MFLI_test.set_ch0_output(True)
    MFLI_test.set_ch0_output_50ohm(False)
    MFLI_test.set_ch0_output_range(1500e-3)
    MFLI_test.set_ch0_output_offset(160e-3)
    MFLI_test.set_ch0_output_amplitude(300e-3)
    MFLI_test.set_ch1_output_amplitude(400e-3)
    MFLI_test.set_ch0_output_autorange(False)
    MFLI_test.set_ch1_output_autorange(False)
    MFLI_test.set_ch0_output_amp_enable(True)
    MFLI_test.set_ch1_output_amp_enable(True)
    '''
    MFLI_test.set_dem1_filter_timeconst(1e-3)
    MFLI_test.set_ch0_output_50ohm(True)
    MFLI_test.set_ch0_output_amplitude(300e-3)
    MFLI_test.set_ch0_output_amp_enable(True)
    MFLI_test.set_ch0_output(True)
    MFLI_test.set_ch1_input_range(0.7)
    MFLI_test.set_ch1_input_autorange
    MFLI_test.set_ch1_input_scaling(32)
    MFLI_test.set_ch1_input_ac_coupling(True)
    MFLI_test.set_ch1_input_50ohm(True)
    #MFLI_test.set_ch1_input_autorange(True)
    MFLI_test.set_ch1_input_difference("in2-in1")
    '''
    print(MFLI_test.get_ch0_carrier_freq())
    print(MFLI_test.get_dem1_phase_offs())
    print(MFLI_test.get_dem1_filter_order())
    print(MFLI_test.get_dem1_filter_timeconst())
    print(MFLI_test.get_dem4_filter_sinc())
    print(MFLI_test.get_dem4_demod_enable())
    print(MFLI_test.get_dem1_sample_rate())
    print(MFLI_test.get_dem1_trigger_mode())
    print(MFLI_test.get_ch1_output())
    print(MFLI_test.get_ch0_output_50ohm())
    print(MFLI_test.get_ch0_output_range())
    print(MFLI_test.get_ch0_output_offset())
    print(MFLI_test.get_ch0_output_amplitude())
    print(MFLI_test.get_ch1_output_amplitude())
    '''
    print(MFLI_test.get_ch1_input_range())
    print(MFLI_test.get_ch1_input_scaling())
    print(MFLI_test.get_ch1_input_ac_coupling())
    print(MFLI_test.get_ch1_input_50ohm())
    print(MFLI_test.get_ch1_input_autorange())
    print(MFLI_test.get_ch1_input_difference())
    print("Done!")
    #MFLI_test.disable_everything()
