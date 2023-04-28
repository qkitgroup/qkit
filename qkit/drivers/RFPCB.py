# qtLAB preliminary driver for RF frontend PCB
# filename: RFPCB.py
# Robert Gartmann <gartmann@kit.edu>, 2021

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
import zerorpc
import types
import logging
import json
import warnings
from time import sleep
from enum import Enum

class RFPCB(Instrument):
    '''
    This is the pre-release python driver for the RF frontend PCB
    Usage:
        Initialise with
        <name> = instruments.create('<name>', "RFPCB", address='<TCP/IP>:<port>')
    '''

    def __init__(self, name, address, model = 'RFPCB', ifcal = False):
        '''
        Initializes the ZeroRPC Client to communicate with according Server (RPi).
        Input:
            name (string)    : name of the instrument
            address (string) : TCPIP Address including port e.g. "10.22.197.145:4242"
        '''

        logging.info(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name)
        self._address = "tcp://" + address
        self._model = model
        # self._statusdict = {}
        self._rpc = zerorpc.Client()
        self._rpc.connect(self._address)
        
        self._frequency = 4e9
        self._power = -30
        
        self._ifcal = ifcal
        self._iffreq = 2
        self._rffreq = 8
        self._nominaltxatt = 30
        self._txifslopecomp = [[3.1, 1], [3.2, 3], [3.3, 5], [3.4, 7], [3.5, 8], [3.6, 9], [3.7, 10]] # PCB 1 ca
        #[[3.1, 1], [3.2, 3], [3.3, 5], [3.4, 7], [3.5, 8], [3.6, 9], [3.7, 10]] # PCB 1 ca
        #[[3.1, 1], [3.2, 3], [3.3, 5], [3.4, 7], [3.5, 9], [3.6, 10], [3.7, 10]] # Agressive PCB3 values
        #[[3.1, 1], [3.2, 2], [3.3, 3], [3.4, 4], [3.5, 5], [3.6, 6], [3.7, 7]] # Bare BB to IF 
        self._nominalrxatt = 30
        self._rxifslopecomp = [[2, 0], [2.3, 0], [2.8, 2], [3, 4], [3.2, 6], [3.4, 6.5], [3.6, 7], [3.8, 9], [3.9, 10]] # PCB 1 ca
        #[[2, 0], [2.3, 0], [2.8, 2], [3, 4], [3.2, 6], [3.4, 6.5], [3.6, 7], [3.8, 9], [3.9, 10]] # PCB 1 ca
        #[[2, 0], [2.3, 0], [2.8, 2], [3, 4], [3.2, 6], [3.4, 8], [3.6, 10], [3.8, 12], [4, 13]] # Agressive PCB3 values
        #[[2, 1], [2.3, 0], [2.8, 1], [3, 2], [3.2, 3], [3.4, 4], [3.6, 5], [3.8, 6], [4, 7]] # Bare IF to BB
        
        self.set_hf_attenuation(self._power)
        #self.set_frequency

        # Implement parameters
        self.add_parameter('frequency', type=float,
            flags=Instrument.FLAG_GETSET,
            minval=4e9, maxval=12e9,
            units='Hz')
        self.add_parameter('power', type=float,
            flags=Instrument.FLAG_GETSET,
            minval=-30, maxval=0,
            units='dBm')
        self.add_parameter('status', type=bool,
            flags=Instrument.FLAG_GETSET)
        
        self.off()
        # Implement functions
        # self.get_all(True)

    # initialization related TODO: implement read function (drivers need to be done first)

    def set_rflo_powerdown(self, boolean):
        self._rpc.writeval("RFLO", "power_down", int(boolean))
        self._rpc.writeval("RFLO", "write_regs_to_chip", 1)

    def set_iflo_powerdown(self, boolean):
        self._rpc.writeval("ZFLO", "power_down", int(boolean))
        self._rpc.writeval("ZFLO", "write_regs_to_chip", 1)

    def set_txpilot_powerdown(self, boolean):
        self._rpc.writeval("TXPilot", "power_down", int(boolean))
        self._rpc.writeval("TXPilot", "write_regs_to_chip", 1)

    def set_rxpilot_powerdown(self, boolean):
        self._rpc.writeval("RXPilot", "power_down", int(boolean))
        self._rpc.writeval("RXPilot", "write_regs_to_chip", 1)


    def set_rflo_enable_a(self, boolean):
        self._rpc.writeval("RFLO", "enable_a", int(boolean))
        self._rpc.writeval("RFLO", "write_regs_to_chip", 1)

    def set_iflo_enable_a(self, boolean):
        self._rpc.writeval("ZFLO", "enable_a", int(boolean))
        self._rpc.writeval("ZFLO", "write_regs_to_chip", 1)

    def set_txpilot_enable_a(self, boolean):
        self._rpc.writeval("TXPilot", "enable_a", int(boolean))
        self._rpc.writeval("TXPilot", "write_regs_to_chip", 1)

    def set_rxpilot_enable_a(self, boolean):
        self._rpc.writeval("RXPilot", "enable_a", int(boolean))
        self._rpc.writeval("RXPilot", "write_regs_to_chip", 1)


    def set_rflo_enable_b(self, boolean):
        self._rpc.writeval("RFLO", "enable_b", int(boolean))
        self._rpc.writeval("RFLO", "write_regs_to_chip", 1)

    def set_iflo_enable_b(self, boolean):
        self._rpc.writeval("ZFLO", "enable_b", int(boolean))
        self._rpc.writeval("ZFLO", "write_regs_to_chip", 1)

    def set_txpilot_enable_b(self, boolean):
        self._rpc.writeval("TXPilot", "enable_b", int(boolean))
        self._rpc.writeval("TXPilot", "write_regs_to_chip", 1)

    def set_rxpilot_enable_b(self, boolean):
        self._rpc.writeval("RXPilot", "enable_b", int(boolean))
        self._rpc.writeval("RXPilot", "write_regs_to_chip", 1)


    def set_rflo_frequency(self, value):
        self._rpc.writeval("RFLO", "vco_out_frequency", int(value))
        self._rpc.writeval("RFLO", "recalibrate", 1)
        self._rpc.writeval("RFLO", "write_regs_to_chip", 1)
        self._rffreq = value/1e9

    def set_iflo_frequency(self, value):
        self._rpc.writeval("ZFLO", "vco_out_frequency", int(value))
        self._rpc.writeval("ZFLO", "recalibrate", 1)
        self._rpc.writeval("ZFLO", "write_regs_to_chip", 1)
        self._rpc.writeval("Demodulator", "lo_match_mhz", int(value/1e6))
        #self._rpc.writeval("Demodulator", "lo_match_mhz", 
        #    int(3000 if value > 3.9e9 else int(value/1e6)))
        self._rpc.writeval("Demodulator", "write_regs_to_chip", 1)
        self._iffreq = value/1e9
        #self.set_iflo_output_b_power(5 if value < 3.5e9 else 31)
        

    def set_txpilot_frequency(self, value):
        self._rpc.writeval("TXPilot", "vco_out_frequency", int(value))
        self._rpc.writeval("TXPilot", "recalibrate", 1)
        self._rpc.writeval("TXPilot", "write_regs_to_chip", 1)

    def set_rxpilot_frequency(self, value):
        self._rpc.writeval("RXPilot", "vco_out_frequency", int(value))
        self._rpc.writeval("RXPilot", "recalibrate", 1)
        self._rpc.writeval("RXPilot", "write_regs_to_chip", 1)


    def set_rflo_output_a_power(self, value):
        self._rpc.writeval("RFLO", "output_a_power", int(value))
        self._rpc.writeval("RFLO", "write_regs_to_chip", 1)

    def set_iflo_output_a_power(self, value):
        self._rpc.writeval("ZFLO", "output_a_power", int(value))
        self._rpc.writeval("ZFLO", "write_regs_to_chip", 1)

    def set_txpilot_output_a_power(self, value):
        self._rpc.writeval("TXPilot", "output_a_power", int(value))
        self._rpc.writeval("TXPilot", "write_regs_to_chip", 1)

    def set_rxpilot_output_a_power(self, value):
        self._rpc.writeval("RXPilot", "output_a_power", int(value))
        self._rpc.writeval("RXPilot", "write_regs_to_chip", 1)


    def set_rflo_output_b_power(self, value):
        self._rpc.writeval("RFLO", "output_b_power", int(value))
        self._rpc.writeval("RFLO", "write_regs_to_chip", 1)

    def set_iflo_output_b_power(self, value):
        self._rpc.writeval("ZFLO", "output_b_power", int(value))
        self._rpc.writeval("ZFLO", "write_regs_to_chip", 1)

    def set_txpilot_output_b_power(self, value):
        self._rpc.writeval("TXPilot", "output_b_power", int(value))
        self._rpc.writeval("TXPilot", "write_regs_to_chip", 1)

    def set_rxpilot_output_b_power(self, value):
        self._rpc.writeval("RXPilot", "output_b_power", int(value))
        self._rpc.writeval("RXPilot", "write_regs_to_chip", 1)


    def set_linopt(self, value):
        if (value > 3000):
            print("Linopt would exceed safe limits!\n Defaulting to 3V55")
            value = 3000
        self._rpc.setlinopt(value)

    def set_hf_attenuation(self, value1): # ,value2
        #if (value2 == 0):
        self._nominaltxatt = abs(value1)
        self._rpc.SetHFAtt(value1, 0) # Could also set voltages manually
        

    def set_demod_attenuation(self, value):
        self._nominalrxatt = value
        self._rpc.writeval("Demodulator", "attenuation", int(value))
        self._rpc.writeval("Demodulator", "write_regs_to_chip", 1)
        
#    def set_demod_band(self,value):
#        self._rpc.writeval("Demodulator", "band", int(value))
#        self._rpc.writeval("Demodulator", "write_regs_to_chip", 1)
        
#    def set_demod_dc_offset_i(self, value):
#        self._rpc.writeval("Demodulator", "dc_offset_i", int(value))
#        self._rpc.writeval("Demodulator", "write_regs_to_chip", 1)
#    
#    def set_demod_dc_offset_q(self, value):
#        self._rpc.writeval("Demodulator", "dc_offset_q", int(value))
#        self._rpc.writeval("Demodulator", "write_regs_to_chip", 1)

    def set_demod_gain(self, value):
        self._rpc.writeval("Demodulator", "gain", int(value))
        self._rpc.writeval("Demodulator", "write_regs_to_chip", 1)
        
    def set_demod_gain_error(self, value):
        self._rpc.writeval("Demodulator", "gain_error", int(value))
        self._rpc.writeval("Demodulator", "write_regs_to_chip", 1)
        
    #def set_demod_hd2i(self, value):
    #def set_demod_hd2q(self, value):
    #def set_demod_hd3i(self, value):
    #def set_demod_hd3q(self, value):
    #def set_demod_im2(self, value):
    #def set_demod_im3(self, value):
    #def set_demod_im3i(self, value):
    #def set_demod_im3q(self, value):
    #def set_demod_ip3(self, value):
    #def set_demod_lo_bias(self, value): 
#    def set_demod_lo_match_c1(self, value):
#        self._rpc.writeval("Demodulator", "lo_match_c1", int(value))
#        self._rpc.writeval("Demodulator", "write_regs_to_chip", 1)
#    
#    def set_demod_lo_match_c2(self, value):
#        self._rpc.writeval("Demodulator", "lo_match_c2", int(value))
#        self._rpc.writeval("Demodulator", "write_regs_to_chip", 1)
#        
#    def set_demod_lo_match_inductor(self, value):
#        self._rpc.writeval("Demodulator", "lo_match_inductor", int(value))
#        self._rpc.writeval("Demodulator", "write_regs_to_chip", 1)
        
    def set_demod_phase_error(self, value):
        self._rpc.writeval("Demodulator", "phase_error", int(value))
        self._rpc.writeval("Demodulator", "write_regs_to_chip", 1)
        
    def reinitialise(self):
        self._rpc.writeval("Demodulator", "init", 1)
        self._rpc.writeval("Demodulator", "write_regs_to_chip", 1)
        self._rpc.writeval("ZFLO", "init", 1)
        self._rpc.writeval("RFLO", "init", 1)
        self._rpc.writeval("TXPilot", "init", 1)
        self._rpc.writeval("RXPilot", "init", 1)
        
    #def set_demod_rf_switch(self, value):

    def do_get_frequency(self, query=True):
        '''
        Get frequency of device
        Input:
            query (bool): Refresh parameters from device memory if True
        Output:
            microwave frequency (Hz)
        '''
        # TODO: read from LOs to calculate band
        return self._frequency
        
    def do_set_frequency(self, frequency, offset = 100e6, method="mixsweep", rfmult=1):
        '''
        Set frequency of device.
        Default BB frequency is 100MHz.
        Default method is sweeping the RF LO.
        Input:
            freq (float) : Frequency in Hz
        Output:
            None
        '''
        #logging.debug(__name__ + ' : setting frequency to %s Hz' % (frequency*1.0e9))
        
        iflo = 4e9 #Filtered 1,8 GHz to 5 GHz
        rflo = 8e9 #Filtered 3,8 GHz to 8,4 GHz
        
        if(method == "ifsweep"):
            # RF LO stationary, IF variable, USB
            # This can reduce spurs from RF LO harmonics.
            # IF drops by 10dB towards 4 GHz though.
            if(frequency <= 6e9 or frequency >= 10e9):
                rflo = 8e9
            elif(frequency > 6e9 and frequency <= 8e9):
                rflo = 4e9
            elif(frequency > 8e9 and frequency < 10e9):
                rflo = 6e9
            else:
                print("No valid LO configuration found!")
            iflo = abs(frequency - rflo) + offset
        elif(method == "ifsweep_extend"):
            # IF level drops even further for 5 GHz.
            if(frequency <= 6.5e9):
                rflo = 8.5e9
            elif(frequency > 6.5e9 and frequency < 9e9):
                rflo = 4e9
            elif(frequency >= 9e9 and frequency < 12e9):
                rflo = 7e9
            else:
                print("No valid LO configuration found!")
            iflo = abs(frequency - rflo) + offset
        elif(method == "rfsweep"):
            # IF LO stationary 2.3G => highest amplitude, RF variable
            # Low IF causes in band spurs (DSB)!
            iflo = 2.3e9 - offset # 2.3G with coupler for optimal level
            if(frequency <= 6.1e9):
                rflo = frequency + iflo 
            elif(frequency > 6.1e9 and frequency < 10.7e9):
                rflo = frequency - iflo
            elif(frequency >= 10.7):
                rflo = 8.4e9
                iflo = frequency - rflo 
            else:
                print("No valid LO configuration:")
            iflo += offset
        elif(method == "rfsweep_extend"):
            iflo = 4.5e9 - offset # RFLO Filter (<8G) & output filter (<12G) swapped
            rflo = frequency - iflo 
            if (rflo < 3.8e9):
                rflo = frequency + iflo
            iflo += offset
        elif(method == "mixsweep"):
            if(frequency <= 5e9):
                iflo = rflo - frequency + offset
            elif(frequency <= 9e9):
                iflo = 3e9  #### EDIT TODO: ALARM, soll 3G, 2G ist nur Test
                rflo = frequency + iflo - offset
            elif(frequency > 9e9 and frequency < 10e9):
                rflo = 12e9
                iflo = rflo - frequency - offset
            else:
                print("No valid LO configuration found!")
        else:
            print("Please select linear combination method!")
        
        self._iffreq = iflo/1e9
        self._rffreq = rflo/1e9
        
        if self._ifcal:
            txindex = 0
            rxindex = 0
            for i in range(0, len(self._txifslopecomp)):
                if (self._iffreq > self._txifslopecomp[i][0]):
                    txindex = i
            for i in range(0, len(self._rxifslopecomp)):
                if (self._iffreq > self._rxifslopecomp[i][0]):
                    rxindex = i
            #print("Indices: {:d} \t {:d}".format(txindex, rxindex))
            newtxatt = self._nominaltxatt - self._txifslopecomp[txindex][1]
            newrxatt = self._nominalrxatt - self._rxifslopecomp[rxindex][1]
            #print("Att: {:d}/{:d} \t {:d}/{:d}".format(
            #    newtxatt, self._nominaltxatt, newrxatt, self._nominalrxatt))
            if newtxatt < 0:
                newtxatt = 0
                print("TX slope cannot be compensated!")
            if newrxatt < 0:
                newrxatt = 0
                print("RX slope cannot be compensated!")
            self._rpc.SetHFAtt(newtxatt, 0)
            self._rpc.writeval("Demodulator", "attenuation", int(newrxatt))
            self._rpc.writeval("Demodulator", "write_regs_to_chip", 1)
        self._frequency = frequency
        self.set_iflo_frequency(iflo)
        self.set_rflo_frequency(rflo/rfmult)

    def do_get_power(self, query=True):
        '''
        Get output power of device
        Input:
            query (bool): Refresh parameters from device memory if True
        Output:
            microwave power (dBm)
        '''
        #TODO: implement read
        return self._power

    def do_set_power(self, power = 0):
        '''
        Sets 0 to 30 dB RF attenuation.
        Output level depends on modulator input or pilot power
        (usually around -10 to 0 dBm max.)
        Input:
            power (float) : "Power" in dBm
        Output:
            None
        '''
        #logging.debug(__name__ + ' : setting power to %s dBm' % power)
        self._power = power
        self.set_hf_attenuation(abs(power))

    def do_get_status(self, query=True):
        '''
        Get status of output channel
        Input:
            query (bool): Refresh parameters from device memory if True
        Output:
            True (on) or False (off)
        '''
        #self.get_all(query)
        # TODO: implement read
        return self._status

    def do_set_status(self, status):
        '''
        Set status of output (Bool)
        Input:
            status (bool): enable LOs or disable everything
        Output:
            None
        '''
        #logging.debug(__name__ + ' : setting status to "%s"' % status)
        if status:
            self.set_rflo_enable_a(1)
            self.set_rflo_enable_b(1)
            self.set_rflo_output_a_power(0)
            self.set_rflo_output_b_power(0)

            self.set_iflo_enable_a(1)
            self.set_iflo_enable_b(1)
            self.set_iflo_output_a_power(0)
            self.set_iflo_output_b_power(31)
            
            self.set_rflo_powerdown(0)
            self.set_iflo_powerdown(0)
        else:
            self.set_rflo_powerdown(1)
            self.set_iflo_powerdown(1)
            self.set_txpilot_powerdown(1)
            self.set_rxpilot_powerdown(1)
        self._status = bool(status)


    #shortcuts
    def off(self):
        '''Turn everything Off'''
        self.set_status(0)

    def on(self):
        '''Turn LOs On'''
        self.set_status(1)
