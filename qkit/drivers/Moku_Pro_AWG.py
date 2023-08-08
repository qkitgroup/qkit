# Moku Pro AWG driver, Thomas Koch
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
#from _ZI_toolkit import daq_module_toolz
from moku.instruments import ArbitraryWaveformGenerator
import logging
from time import sleep
import numpy as np
import math

from qupulse.pulses import TablePT, FunctionPT, PointPT, SequencePT, RepetitionPT, ForLoopPT, AtomicMultiChannelPT
from qupulse.serialization import PulseStorage, DictBackend
from qupulse.pulses.plotting import plot, render

class Moku_Pro_AWG(Instrument):
    
    def __init__(self, name, device_ip):
        # Input:
        #     name (string) : name of the instrument
        #     device_ip (string): ip of the instrument in the local network
      
        logging.info(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical', "AWG"])      
        
        self.awg = ArbitraryWaveformGenerator('192.168.1.60', force_connect=True)
        
        self.output_configs = [{},{},{},{}]
        
        self._amplitudes = [0, 0, 0, 0]
        self._frequency = 250e6
        self._point_num = 2**16
        self._V_offsets = [0, 0, 0, 0]
        self._update_rates = ["312.5Ms", "312.5Ms", "312.5Ms", "312.5Ms"]
        # Add parameters to wrapper
        
        self.add_parameter("amplitude", type = float,
                           flags = Instrument.FLAG_GETSET,
                           channels = (1,4), units = 'V',
                           minval = 0, maxval = 10,
                           channel_prefix = "ch%d_")
        
        self.add_parameter("frequency", type = float ,
                           flags = Instrument.FLAG_GETSET,
                           unit = "Hz",
                           minval = 0.001, maxval = 250e6)
        
        self.add_parameter("point_num", type = int,
                           flags = Instrument.FLAG_GETSET,
                           minval = 1, maxval = 2**16)
        
        self.add_parameter("offset", type = float,
                           flags = Instrument.FLAG_GETSET,
                           channels = (1,4), units = "V",
                           minval = 0, maxval = 5,
                           channel_prefix = "ch%d_")
        
        self.add_parameter("sampling_rate", type = int,
                           flags = Instrument.FLAG_GET)
                           
        self.add_parameter("update_rate", type = str,
                           flags = Instrument.FLAG_GETSET,
                           channels = (1,4),
                           channel_prefix = "ch%d_")
        
        # Add functions to wrapper
        
        self.add_function("generate_waveform")
        self.add_function("enable_output")
        self.add_function("disable_output")
        self.add_function("continuous_mode")
        self.add_function("burst_mode")
        self.add_function("configure_outputs")
    
    # parameters
    
    def _do_set_amplitude(self, voltage, channel):
        self._amplitudes[channel-1] = voltage
        logging.debug(__name__ + " : setting amplitude of channel %s to %s." %(channel, voltage))
        
    def _do_get_amplitude(self, channel):
        return self._amplitudes[channel-1]
    
    
    def _do_set_frequency(self, freq):
        self._frequency = freq
        logging.debug(__name__ + " : setting frequency to %s." %freq)

    def _do_get_frequency(self):
        return self._frequency
    

    def _do_set_point_num(self, num):
        self._point_num = num
        logging.debug(__name__ + " : setting number of points to %s." %num)
        
    def _do_get_point_num(self):
        return self._point_num
        
    def _do_set_update_rate(self, rate_string, channel):
        if rate_string in ["1.25Gs", "600MS", "312.5Ms"]:
            self._update_rates[channel-1] = rate_string
            logging.debug(__name__ + " : update rate of channel %s changed to %s" %(channel, rate_string))
        else:
            raise Exception("The only possible update rates are 1.25Gs, 600MS and 312.5Ms")
            
        
    def _do_get_update_rate(self, channel):
        return self._update_rates[channel-1]
    
    
    
    def _do_set_offset(self, voltage, channel):
        self._V_offsets[channel-1] = voltage
        logging.debug(__name__ + " : setting offset voltage of channel %s to %s." %(channel, voltage))
        
    def _do_get_offset(self, channel):
        return self._V_offsets[channel-1]
    
    def _do_get_sampling_rate(self):
        return self._frequency * (self._point_num-1)
    
    
        
    # functions   
    
    def generate_waveform(self, channel, pulse_array):
        
        self.output_configs[channel-1] = self.awg.generate_waveform(channel = channel, sample_rate = self._update_rates[channel-1],
                                                                   lut_data = list(pulse_array),
                                                                   frequency = self._frequency,
                                                                   amplitude = self._amplitudes[channel-1],
                                                                   offset = self._V_offsets[channel-1])
        
    def enable_output(self, channel):
        self.awg.enable_output(channel, True)
        
    def disable_output(self, channel):
        self.awg.enable_output(channel, False)
        
    
    def continuous_mode(self, channel):
        self.awg.disable_modulation(channel = channel)
    
    def burst_mode(self, channel, trigger_source, trigger_mode, burst_cycles, trigger_level):
        self.awg.burst_modulate(channel = channel, trigger_source = trigger_source, 
                                trigger_mode = trigger_mode, burst_cycles = burst_cycles, 
                                trigger_level = trigger_level)
        
    def configure_outputs(self,data_dict, triggered = False, trigger_source = "Input1", trigger_mode = "NCycle", burst_cycles = 1, trigger_level = 0.5):
        if type(data_dict) != dict:
            raise TypeError(f"{__name__}: Cannot use {type(data_dict)} input. Data must be an dict with channel names and corresponding wave data.")
        
        self.test_dict = data_dict
        channel_names = []
        for key in data_dict:
            channel_names.append(key)
        
        for i in range(len(channel_names)):
            #index = [s for s in channel_names[i] if s.isdigit()]
            if any(x in channel_names[i] for x in ["Trig","trig"]):
                if type(data_dict[channel_names[i]]) == dict:
                    if "samples" not in data_dict[channel_names[i]]:
                        raise KeyError("Unkown dict keys. Wave data needs to be part of the \"samples\" key.")
                    trigArray = np.concatenate(data_dict[channel_names[i]]["samples"])
                else:
                    trigArray = data_dict[channel_names[i]]
                    
                pulseArray = trigArray
                
            else:
                if type(data_dict[channel_names[i]]) == dict:
                    if "samples" not in data_dict[channel_names[i]]:
                        raise KeyError("Unkown dict keys. Wave data needs to be part of the \"samples\" key.")
                    waveArray = np.concatenate(data_dict[channel_names[i]]["samples"])
                else:
                    waveArray = data_dict[channel_names[i]]
                    
                pulseArray = waveArray
                
            maxV = round(math.ceil(max(abs(pulseArray))*1e4)*1e-4,4) 
            self._amplitudes[i] = maxV
            
            self.generate_waveform(i+1, pulseArray/maxV)
            
            if triggered:
                self.burst_mode(channel = i+1, trigger_source = trigger_source,
                                trigger_mode = trigger_mode, burst_cycles = burst_cycles, 
                                trigger_level = trigger_level)
            else:
                self.continuous_mode(channel = i+1)
                
            

                                  
                                      
                                      
                                      
        