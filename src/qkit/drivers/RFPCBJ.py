# qtLAB preliminary driver for RF frontend PCB
# filename: RFPCBJ.py
# Nej <jdangel@kit.edu>, 2021

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

class RFPCBJ(Instrument):
    '''
    This is the pre-release python driver for the RF frontend PCB
    Usage:
        Initialise with
        <name> = instruments.create('<name>', "RFPCBJ", address='<TCP/IP>:<port>')
    '''

    def __init__(self, name, address, model = 'RFPCBJ'):
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
#######################
#  shiftreg#
######################
    def set_shiftreg_switch(self, boardnr, channel, boolean):
        self._rpc.writeval("SHIFTREG"+str(boardnr), "switches",str(channel) +"," +str(boolean) )
    def set_shiftreg_attenuation(self, boardnr, channel, value):
        self._rpc.writeval("SHIFTREG"+str(boardnr), "attenuation",str(channel) +"," +str(int(2*value)) )
    def shiftreg_flush(self, boardnr, channel, boolean):
        self._rpc.writeval("SHIFTREG"+str(boardnr), "read_flush",str(channel) +"," +str(boolean) )

#####################
#  LOs#
######################

    def set_lo_powerdown(self,boardnr, boolean):
        self._rpc.writeval("LO"+str(boardnr), "power_down", int(boolean))
    def set_lo_init(self,boardnr):
        self._rpc.writeval("LO"+str(boardnr), "init",1)
        self._rpc.readval("LO"+str(boardnr), "read_regs_from_chip")
    def set_lo_frequency(self,boardnr, f):
        self._rpc.writeval("LO"+str(boardnr), "vco_out_frequency", int(f))
    def set_lo_enable_a(self,boardnr, boolean):
        self._rpc.writeval("LO"+str(boardnr), "enable_a", int(boolean))
    def set_lo_enable_b(self,boardnr, boolean):
        self._rpc.writeval("LO"+str(boardnr), "enable_b", int(boolean))
    def set_lo_power_a(self,boardnr, power):
        self._rpc.writeval("LO"+str(boardnr), "output_a_power", int(power))
    def set_lo_power_b(self,boardnr, power):
        self._rpc.writeval("LO"+str(boardnr), "output_b_power", int(power))
    def set_lo_flush(self,boardnr, boolean):
        self._rpc.writeval("LO"+str(boardnr), "write_regs_to_chip", 1)
    def set_lo_read(self,boardnr):
        self._rpc.readval("LO"+str(boardnr), "read_regs_from_chip")


    # initialization related TODO: implement read function (drivers need to be done first)
    # def get_all(self, query=True):
    #     '''
    #     Get Parameters (frequency, amplitude, output on/off, clock reference) of Device as dictionary
    #     Input:
    #         query (bool): Query from device (true) or relay local info (false)
    #     Output:
    #         Dictionary of device
    #     '''
    #     if not query:
    #         return self._statusdict
    #     self._statusdict = json.loads(self._rpc.readall())
    #     self._frequency = float(self._statusdict["frequency"])
    #     self._power = float(self._statusdict["amplitude"])
    #     self._status = bool(int(self._statusdict["rfoutput"]))
    #     refext = bool(int(self._statusdict["reference_int_ext"]))
    #     refint = bool(int(self._statusdict["reference_tcxo_ocxo"]))
    #     if refext:
    #         self._reference = ReferenceSource.EXTERNAL
    #     elif refint:
    #         self._reference = ReferenceSource.OCXO
    #     else:
    #         self._reference = ReferenceSource.TCXO
    #     return self._statusdict

    # def get_diag(self):
    #     '''
    #     Get diagnostics parameters (Firmware Versions, PLL locks status,
    #          Voltage, Temperature) of Device as dictionary
    #     Input:
    #         None
    #     Output:
    #         Dictionary diagnostics parameters
    #     '''
    #     return json.loads(self._rpc.readdiag())

    def set_rflo_powerdown(self, boolean):
        self._rpc.writeval("RFLO", "power_down", int(boolean))

    def set_iflo_powerdown(self, boolean):
        self._rpc.writeval("ZFLO", "power_down", int(boolean))

    def set_txpilot_powerdown(self, boolean):
        self._rpc.writeval("TXPilot", "power_down", int(boolean))

    def set_rxpilot_powerdown(self, boolean):
        self._rpc.writeval("RXPilot", "power_down", int(boolean))


    def set_rflo_enable_a(self, boolean):
        self._rpc.writeval("RFLO", "enable_a", int(boolean))

    def set_iflo_enable_a(self, boolean):
        self._rpc.writeval("ZFLO", "enable_a", int(boolean))

    def set_txpilot_enable_a(self, boolean):
        self._rpc.writeval("TXPilot", "enable_a", int(boolean))

    def set_rxpilot_enable_a(self, boolean):
        self._rpc.writeval("RXPilot", "enable_a", int(boolean))


    def set_rflo_enable_b(self, boolean):
        self._rpc.writeval("RFLO", "enable_b", int(boolean))

    def set_iflo_enable_b(self, boolean):
        self._rpc.writeval("ZFLO", "enable_b", int(boolean))

    def set_txpilot_enable_b(self, boolean):
        self._rpc.writeval("TXPilot", "enable_b", int(boolean))

    def set_rxpilot_enable_b(self, boolean):
        self._rpc.writeval("RXPilot", "enable_b", int(boolean))


    def set_rflo_frequency(self, value):
        self._rpc.writeval("RFLO", "vco_out_frequency", int(value))
        self._rpc.writeval("RFLO", "recalibrate", 1)

    def set_iflo_frequency(self, value):
        self._rpc.writeval("ZFLO", "vco_out_frequency", int(value))
        self._rpc.writeval("ZFLO", "recalibrate", 1)
        self._rpc.writeval("Demodulator", "lo_match_mhz", int(value/1e6))
        self._rpc.writeval("Demodulator", "write_regs_to_chip", 1)
        

    def set_txpilot_frequency(self, value):
        self._rpc.writeval("TXPilot", "vco_out_frequency", int(value))
        self._rpc.writeval("TXPilot", "recalibrate", 1)

    def set_rxpilot_frequency(self, value):
        self._rpc.writeval("RXPilot", "vco_out_frequency", int(value))
        self._rpc.writeval("RXPilot", "recalibrate", 1)


    def set_rflo_output_a_power(self, value):
        self._rpc.writeval("RFLO", "output_a_power", int(value))

    def set_iflo_output_a_power(self, value):
        self._rpc.writeval("ZFLO", "output_a_power", int(value))

    def set_txpilot_output_a_power(self, value):
        self._rpc.writeval("TXPilot", "output_a_power", int(value))

    def set_rxpilot_output_a_power(self, value):
        self._rpc.writeval("RXPilot", "output_a_power", int(value))


    def set_rflo_output_b_power(self, value):
        self._rpc.writeval("RFLO", "output_b_power", int(value))

    def set_iflo_output_b_power(self, value):
        self._rpc.writeval("ZFLO", "output_b_power", int(value))

    def set_txpilot_output_b_power(self, value):
        self._rpc.writeval("TXPilot", "output_b_power", int(value))

    def set_rxpilot_output_b_power(self, value):
        self._rpc.writeval("RXPilot", "output_b_power", int(value))


    def set_linopt(self, value):
        if (value > 3000):
            print("Linopt would exceed safe limits!\n Defaulting to 3V55")
            value = 3000
        self._rpc.setlinopt(value)

    def set_hf_attenuation(self, value1, value2 = 0):
        self._rpc.SetHFAtt(value1, value2)
        

    def set_demod_attenuation(self, value):
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
        
    def do_set_frequency(self, frequency, offset = 100e6, method="rfsweep"):
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
            iflo = abs(frequency - rflo + offset)
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
            iflo = abs(frequency - rflo + offset) # maybe + 100MHz?
        elif(method == "rfsweep"):
            # IF LO stationary 2.3G => highest amplitude, RF variable
            # Low IF and/or RF frequencyies cause spurs!
            iflo = 2.3e9 - offset
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
        else:
            print("Please select linear combination method!")
        
        self.set_iflo_frequency(iflo)
        self.set_rflo_frequency(rflo)
        self._frequency = frequency

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
            self.set_rflo_output_a_power(5)

            self.set_iflo_enable_a(1)
            self.set_iflo_enable_b(1)
            self.set_iflo_output_a_power(5)
            
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
