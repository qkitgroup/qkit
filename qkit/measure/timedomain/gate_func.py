# gate_func.py
# adapted from earlier versions by Jochen Braumueller <jochen.braumueller@kit.edu>, 05/2016

# The gate function resets an AWG to the first waveform of a sequence for state==False and sends a trigger
# by raising a gate for state==True.
# Separate functions are supplied for Tektronix AWG and Tabor AWG

"""
usage and inputs:

 from qkit.measure.timedomain import gate_func
 or: import gate_func
 mspec.set_gate_func(gate_func.Gate_Func(awg = tawg, ni_daq = ftdidaq).gate_fcn)
 #pass the name of the AWG as imported to qtLAB (e.g. fastawg or tawg)
 #with the spectrum card wrapper virtual_measure_spec.py:
 mspec.set_gate_func(gfunc.gate_fcn)
"""

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

import logging
import time
import qkit

class Gate_Func(object):

    def __init__(self, awg, pulser = None, ni_daq = None, ni_daq_ch = 'PFI0:0', sample=None):
        """
        initialize gate function
        inputs:
         - awg: qubit awg instrument object
         - pulser: instrument object (to send out pulse directly from pulser instead of triggering the pulser
         - ni_daq: ni_daq instrument object (in tunnel electronics rack)
         - ni_daq_ch: used channel of ni_daq
         - readout_tabor: tabor awg (2ch of 4ch) for readout
        outputs:
         -
        """
        self.awg = awg
        self._sample = sample
        if pulser:
            self.pulser = qkit.instruments.get(pulser)
            self._gate_high = self.pulser.set_mode_continuous
            self._gate_low = self.pulser.set_mode_gated
        else:
            self.pulser = None
        if ni_daq:
            self.ni_daq = qkit.instruments.get(ni_daq)
            self.ni_daq_ch = ni_daq_ch
            self._gate_high = lambda: self.ni_daq.digital_out(self.ni_daq_ch, 1)
            self._gate_low = lambda: self.ni_daq.digital_out(self.ni_daq_ch, 0)
        else:
            self.ni_daq = None
       
        self.selftriggered = (self.pulser == None and self.ni_daq == None)
        
        if self.selftriggered:
            self._gate_low  =  lambda: self.awg.set({'trigger_time':2, 'p1_trigger_time':2})
            self._gate_high = lambda: self.awg.set({'trigger_time':sample.T_rep, 'p1_trigger_time':sample.T_rep})
        
        if self.selftriggered and not ('Tabor' in self.awg.get_type()):
            raise ValueError("selftriggered mode (without pulser and nidaq) is currently only available for Tabor AWGs.")
        self.ni_daq_ch = ni_daq_ch
        
    def gate_fcn(self, state):
        """
        gate function
        inputs:
         - state: boolean, chooses one of the actions reset or trigger
        outputs:
         -
        """
        if state:   #switch gate to high, let the pulses run
            time.sleep(0.1)
            self._gate_high()
                
        else:   #reset AWG and wait for it
            self._gate_low()
            
            time.sleep(0.025)
            
            if 'Tektronix' in self.awg.get_type():
                self._reset_tek()
            elif 'Tabor' in self.awg.get_type():
                self._reset_tabor()
            else:
                logging.error('AWG unknown')
                raise ImportError
            
    def _reset_tek(self):
        """
        reset Tektronix AWG to first sequence
        """
        tries = 0
        while self.awg.get_seq_position() != 1:
            if tries > 30:
                logging.error('Tektronix AWG does not respond. Aborting.')
                raise ValueError('AWG did not reset to first waveform after %i iterations. There is something seriously going wrong. Check if AWG can enter run mode!'%tries)
            tries += 1
            self.awg.stop()
            self.awg.wait()
            self.awg.run()
            #self.awg.wait()
            time.sleep(0.05*seq_it)

        if tries > 4:
            print('Tektronix AWG reached first waveform after %d iterations.'%tries)
                
    def _reset_tabor(self):
        """
        reset Tabor AWG to first sequence
        """
        # workaround to intialize to first waveform and make the AWG ready
        if "p1_runmode" in self.awg.get_parameter_names():
            self.awg.set_p1_runmode('USER')
            self.awg.set_p2_runmode('USER')
            self.awg.set_p1_runmode('SEQ')
            self.awg.set_p2_runmode('SEQ')
        else:
            self.awg.set_runmode('USER')
            self.awg.set_runmode('SEQ')
        self.awg.fix(verbose=False)
