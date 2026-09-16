# Driver for IQ Mixers in mm-Wave Timedomain Setup. 
#
# Jonas Kaemmerer <jonas.kaemmerer@kit.edu>, 2026
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
import time
import types
import logging
import os
import numpy as np
if qkit.module_available("matplotlib"):
    import matplotlib.pyplot as plt
import sys, gc
from copy import copy
from scipy.optimize import minimize_scalar


class mmWave_IQ_Mixer(Instrument):
    
    """
    Wrapper for operating the MMIQ IQ Mixers in the mm-Wave Timedoain setup.
    Partially based on qkit/IQ_Mixer Class by Andre Schneider.
    """
    
    def __init__(self, name, LO , rfdc_I , rfdc_Q ): 
        Instrument.__init__(self, name, tags=['virtual'])
           
        #self._sample = sample
        
        self._LO = LO # The MW source acting as LO
        
        self._fsup = None
        self._FSUP_connected = False
        
        self._inverted_sideband = False
        
        self._pulsegen = None       # Pulse Generatror of FPGA digital unit cell
        self._pulsegen_manual_use = False
        
        #self._rfdc = None            #  RF Data Converter - DAC
        #self._rfdc_calibration = False  
        self._rfdc_I = rfdc_I     #  RF Data Converter - DAC for I port
        self._rfdc_Q = rfdc_Q     #  RF Data Converter - DAC for Q port
        
        self._rfdc_I.mixer_mode = "c2c" # Ensures that FPGA is configured 
        self._rfdc_Q.mixer_mode = "c2c" # to output complex signal for IQ Mixer
        
        print("Setting Mixer Mode c2c")
        
        self.add_parameter('LO_power', 
                           type = float,
                           flags = super().FLAG_GETSET,
                           minval= 3 , maxval = 13 , 
                           units = "dBm"
                           )
        
        self.add_parameter('LO_frequency', 
                           type = float,
                           flags = super().FLAG_GETSET,
                           minval = 5e9 , maxval = 40e9 , 
                           units = "Hz"
                           )
        
        self.add_parameter('status', 
                           type = bool,
                           flags = super().FLAG_GETSET,
                           )
        
        self.add_parameter('blanking', 
                           flags=super().FLAG_GETSET,
                           type=bool
                           )
        
        self.add_parameter('inverted_sideband', 
                           flags=super().FLAG_GETSET,
                           type=bool
                           )
        
        self.add_parameter('PulseGenerator_manual_use', 
                           flags=super().FLAG_GET,
                           type=bool
                           )
        
        self.add_parameter('rfdc_frequency', 
                           flags = super().FLAG_GETSET,
                           type = float
                           )
        
        #self.add_function('reset')
        
        self.add_function ('get_all')
        
    
    def get_all(self):
        
        self.get_LO_power()
        self.get_LO_frequency()
        self.get_status()
        self.get_blanking()
    
    #################################
    ## Set/Get Function Definition ##
    #################################    
    
    
    def do_get_status(self):
        '''
        Reads the output status from the instrument.
        Information whether LO is turned on or off.

        Input:
            None

        Output:
            status (string) : 'On' or 'Off'
        '''
        
        logging.debug(__name__ + ' : get status')
        
        return self._LO.get_status()


    def do_set_status(self, status):
        '''
        Set the output status of the instrument. Turns LO  on or off.

        Input:
            status (string) : 'On' or 'Off'

        Output:
            None
        '''
        logging.debug(__name__ + ' : set status to %s' % status)
        
        self._LO.set_status(status)
        


    def do_set_blanking(self, blanking_status=False):
        '''
        Set the output blanking of the instrument (blanking means the ouput 
                                                   will be turned off when the 
                                                   frequency changes)

        Input:
            status (bool) : True or False

        Output:
            None
        '''
        logging.debug(__name__ + ' : set blanking to {blanking_status}')

        self._LO.set_blanking(blanking_status)


    def do_get_blanking(self):
        '''
        Get the output blanking of the instrument. 
        (blanking means the output will be turned off when the 
        frequency changes)

        Input:
            NONE

        Output:
            bool True, False
        '''
        
        logging.debug(__name__ + ' : get blanking status')

        return self._LO.get_blanking()


    def do_get_LO_frequency(self):
        '''
        Reads the frequency of the signal from the instrument

        Input:
            None

        Output:
            freq (float) : Frequency in Hz
        '''
        
        logging.debug(__name__ + ' : get frequency')
        
        return self._LO.get_frequency()

    def do_set_LO_frequency(self, freq):
        '''
        Set the frequency of the instrument

        Input:
            freq (float) : Frequency in Hz

        Output:
            None
        '''
        
        logging.debug(__name__ + f' : set frequency to {freq}')
        
        self._LO.set_frequency(freq)


    def do_get_LO_power(self):
        '''
        Reads the power of the signal from the instrument

        Input:
            None

        Output:
            ampl (?) : power in dBm
        '''
        
        logging.debug(__name__ + ' : get power')
        
        return self._LO.get_power()


    def do_set_LO_power(self, amp):
        '''
        Set the power of the signal

        Input:
            amp (float) : power in dBm

        Output:
            None
        '''
        
        logging.debug(__name__ + f' : set power to {amp}')
        
        self._LO.set_power(amp)
        
    def do_set_inverted_sideband(self , inv):
        
        logging.debug(__name__ + f' : set inverted_sideband to {inv}')
        self._inverted_sideband = inv
        
    def do_get_inverted_sideband(self):
        
        logging.debug(__name__ + ' : get inverted_sideband')
        return self._inverted_sideband
    
    def do_get_PulseGenerator_manual_use(self):
        
        logging.debug(__name__ + ' : get PulseGenerator_manual_use')
        return self._pulsegen_manual_use
    
    def do_set_rfdc_frequency(self, freq):
        
        logging.debug(__name__ + ' : set rfdc_frequency')
        self._rfdc_I.mixer_frequency = freq
        self._rfdc_Q.mixer_frequency = freq
    
    def do_get_rfdc_frequency(self):
        
        logging.debug(__name__ + ' : get rfdc_frequency')
        return self._rfdc_I.mixer_frequency
        
        
    ###########################
    ## Calibration with FSUP ##
    ###########################
    
    def connect_FSUP(self, FSUP):
        self._fsup = FSUP
        self._FSUP_connected = True
    
    def disconnect_FSUP(self):
        self._fsup = None
        self._FSUP_connected = False
        
    
    def connect_PulseGen_for_manual_use(self, pulsegen):
        ## qiccontroller pulsgen of a digital unitcell is 
        ## handed over to IQ_mixer instance
        
        self._pulsegen = pulsegen
        self._pulsegen_manual_use = True
    
    def disconnect_PulseGen_for_manual_use(self):
        self._pulsegen = None
        self._pulsegen_manual_use = False
        
    
    def get_NCO_freq(self , IF_frequency):
        
        """
        Calculate the frequency of the NCO in the digital unit cell, given a
        desired IF_frequency and fixed mixer frequency of the DAC.
        """

        if IF_frequency < self.get_rfdc_frequency():
            
            raise ValueError('RFdc mixer frequency is too large.')
        
        else:
            
            digunit_nco_freq = IF_frequency - self.get_rfdc_frequency()
            
            return digunit_nco_freq
    
    def play_CW_tone( self , IF_frequency , LO_frequency , status):
        
        self._pulsegen.pulses = {
                "CW on": {
                    "trigger": 1,
                    "length": 4e-9,
                    "hold": True,
                },
                "CW off": {
                    "trigger": 2,
                    "length": 4e-9,
                    "amplitude": 0,
                },
            }
        
        self._pulsegen.trigger_manually(2) # CW off
        self.set_status( False )
        
        self._pulsegen.internal_frequency = np.round(self.get_NCO_freq(IF_frequency),0)
        
        self.set_LO_frequency( LO_frequency )
        self.set_status( True )
        
        if status:
            self._pulsegen.trigger_manually(1) # CW on
        else:
            self._pulsegen.trigger_manually(2) # CW off
        
    
    def test_spectrum( self , IF_frequency , LO_frequency  ):
        
        self._fsup.set_startfreq( LO_frequency - 4 * IF_frequency )
        self._fsup.set_stopfreq( LO_frequency + 4 * IF_frequency )
        self._fsup.set_continuous_sweep_mode("OFF")
        
        self.play_CW_tone(IF_frequency , LO_frequency , status = True)
        
        self._fsup.start_measurement()
        
        self.play_CW_tone(IF_frequency , LO_frequency , status = False)
                
        return self._fsup.get_freqpoints() , self._fsup.get_trace()
    
    def zoom_spectrum( self , IF_frequency , LO_frequency , center_freq , span ):
        
        self._fsup.set_centerfreq( center_freq )
        self._fsup.set_freqspan( span )
        self._fsup.set_continuous_sweep_mode("OFF")
        
        self.play_CW_tone(IF_frequency , LO_frequency , status = True)
        
        self._fsup.start_measurement()
        
        self.play_CW_tone(IF_frequency , LO_frequency , status = False)
                
        return self._fsup.get_freqpoints() , self._fsup.get_trace()
    
    
    def focus(self, frequency, marker):
        self._fsup.enable_marker(1, 'OFF')
        self._fsup.enable_marker(2, 'OFF')
        self._fsup.enable_marker(3, 'OFF')
        self._fsup.enable_marker(4, 'OFF')
        self._fsup.set_continuous_sweep_mode('OFF')
        
        
        self._fsup.set({
            'centerfreq': frequency,
            'freqspan': 40e3,
            'averages': 2,
            'nop': 2001,
            'resolutionBW': 10,
            'videoBW': 10
        })
        
        self._fsup.set_marker(marker, frequency)
        self._fsup.start_measurement()
        
    
    
    def measure_sideband(self, IF_frequency , LO_frequency , 
                         amp_i = 1, amp_q = 1,
                         phase = "disable" ,
                         marker = 1):
        
        ## Measure the unwanted sideband to be suppressed in SSB mixer scheme.
        
        # Apply new amplitude settings
        
        ##self._pulsegen.amplitude_calibration = (amp_i, amp_q)
        self._rfdc_I.update_qmc( gain_correction = amp_i , 
                               phase_correction = phase , 
                               offset_correction = "disable"
                               )
        self._rfdc_Q.update_qmc( gain_correction = amp_q , 
                               phase_correction = "disable" , 
                               offset_correction = "disable"
                               )
        
        # 2. Generate CW
        self._pulsegen.internal_frequency = self.get_NCO_freq(IF_frequency)
        
        self.set_status(False)
        self.set_LO_frequency( LO_frequency )
        self.set_status(True)
    
        # CW tone on
        self._pulsegen.trigger_manually(1)
    
        # 4. Measure
        if  self._inverted_sideband:
            self.focus(LO_frequency + IF_frequency , marker)
        else:
            self.focus(LO_frequency - IF_frequency , marker)
            
        level = self._fsup.get_marker_level(marker)
    
        # CW tone off
        self._pulsegen.trigger_manually(2)
    
        return level
    
    def measure_signal(self,  IF_frequency , LO_frequency , 
                         amp_i = 1, amp_q = 1,
                         phase = "disable" ,
                         marker = 1):
        
        ## Measure the unwanted sideband to be suppressed in SSB mixer scheme.
        
        # Apply new amplitude settings
        self._rfdc_I.update_qmc( gain_correction = amp_i , 
                               phase_correction = phase , 
                               offset_correction = "disable"
                               )
        self._rfdc_Q.update_qmc( gain_correction = amp_q , 
                               phase_correction = "disable" , 
                               offset_correction = "disable"
                               )
    
        # 2. Generate CW
        self._pulsegen.internal_frequency =  self.get_NCO_freq(IF_frequency)
        
        self.set_status(False)
        self.set_LO_frequency( LO_frequency )
        self.set_status(True)
    
        # CW tone on
        self._pulsegen.trigger_manually(1)
    
        # 4. Measure
        if self._inverted_sideband:
            self.focus(LO_frequency - IF_frequency , marker)
        else:
            self.focus(LO_frequency + IF_frequency , marker)
            
            
        level = self._fsup.get_marker_level(marker)
    
        # CW tone off
        self._pulsegen.trigger_manually(2)
    
        return level

    
    def calibrate_amplitude(self, IF_frequency, LO_frequency, 
                            bounds=(0.4, 1.0), iterations=2):
    
        # initial guess
        amp_i = 1.0
        amp_q = 1.0
        
        print('calibrate_amplitude')
        
        for index in range(iterations):
    
            # --- optimize I ---
            
            def cost_I(a):
                
                sideband = self.measure_sideband(a, amp_q, 
                                             IF_frequency , LO_frequency )
                
                signal = self.measure_signal(a, amp_q, 
                                             IF_frequency , LO_frequency )
                
                # convert to linear scale
                sideband = 10**(sideband/10)
                signal = 10**(signal/10)
                
                return sideband / signal 
    
            res_I = minimize_scalar(cost_I,
                                    bounds=bounds,
                                    method="bounded",
                                    options={"xatol": 0.01})
            amp_i = res_I.x
            
            print("I iteration " + str(index) + " done." )
    
            # --- optimize Q ---
            
            def cost_Q(a):
                
                sideband = self.measure_sideband(amp_i, a, 
                                             IF_frequency , LO_frequency)
                
                signal = self.measure_signal(amp_i, a, 
                                             IF_frequency , LO_frequency)
                
                # convert to linear scale
                sideband = 10**(sideband/10)
                signal = 10**(signal/10)
                
                return sideband / signal
    
            res_Q = minimize_scalar(cost_Q,
                                    bounds=bounds,
                                    method="bounded",
                                    options={"xatol": 0.01})
            
            amp_q = res_Q.x
            
            print("Q iteration " + str(index) + " done." )
        
        # Write final calibration
        
        self._pulsegen.amplitude_calibration = (amp_i, amp_q)
    
        return amp_i, amp_q

    

