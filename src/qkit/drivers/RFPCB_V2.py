# qtLAB preliminary driver for RF frontend PCB
# filename: RFPCB.py
# Robert Gartmann <gartmann@kit.edu>, 2021
# Marius Frohn <uzrfo@student.kit.edu>, 2022

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
#import zerorpc
#import types
import logging
#import json
import warnings
from time import sleep
import math
#from enum import Enum

import grpc
from proto_gen import hflo_pb2_grpc as HFL_grpc
from proto_gen import hflo_pb2 as HFL
#from proto_gen import lmx2594evm_pb2_grpc as HFL_grpc
#from proto_gen import lmx2594evm_pb2 as HFL
from proto_gen import hfdemodulator_pb2_grpc as HFD_grpc
from proto_gen import hfdemodulator_pb2 as HFD
from proto_gen import hfattenuator_pb2_grpc as HFA_grpc
from proto_gen import hfattenuator_pb2 as HFA
from proto_gen import hfsuperv2_pb2_grpc as SuperV2_grpc
from proto_gen import hfsuperv2_pb2 as SuperV2

class RFPCB_V2(Instrument):
    '''
    This is the pre-release python driver for the RF frontend PCB
    Usage:
        Initialise with
        <name> = instruments.create('<name>', "RFPCB", address='<TCP/IP>:<port>')
        Set/Get Power and Frequency implemented as Qkit Instrument paramters
        Call gRPC functions with 
        <name>.xyz_stub.Function(XYZ.ProtoType(param_name=*value*)) # Dont forget UpdateWrite!
    '''
    def __init__(self, name, address, model = 'RFPCB'):
        '''
        Initializes the ZeroRPC Client to communicate with according Server (RPi).
        Input:
            name (string)    : name of the instrument
            address (string) : Servicehub Address including port e.g. "192.168.99.132:50058" for Platform or "192.168.99.206:50058" for NanoPi
        '''

        # Init Qkit Instrument
        logging.info(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name)
        self._model = model

        # connect to IPESH
        self._channel = grpc.insecure_channel(address)
        self.hfl_stub = HFL_grpc.HfLOServiceStub(self._channel)
        #self.hfl_stub = HFL_grpc.LMX2594EVMServiceStub(self._channel)
        self.hfd_stub = HFD_grpc.HfDemodulatorServiceStub(self._channel)
        self.hfa_stub = HFA_grpc.HfAttenuatorServiceStub(self._channel)
        self.v2_stub = SuperV2_grpc.HfSuperV2ServiceStub(self._channel)

        # default values for Instrument
        self._connection = True
        self._status = False
        self._power = 30

        # Endpoint Index List
        # will be used with '...index=self.EPDict.index("name")...'
        # must be adjusted according to order of eps on devices (check IPESH info)
        self.EPDict = ["TXPL", "RXPL", "IFLO", "RFLO"]

        # Implement parameters
        # Main
        self.add_parameter('frequency', type=float,
            tags=["Main", "Multi"],
            minval=4e9, maxval=12e9, units='Hz')
        self.add_parameter('power', type=float,
            tags=["Main", "Attenuator"],
            minval=0, maxval=30, units='dBm')
        self.add_parameter('status', type=bool, tags=["Main", "Multi"])
        self.add_parameter('connection', type=bool, tags=["Main"])
        # Detail
        self.add_parameter('iflo_frequency', type=float,
            tags=["Detail", "LO"], listen_to=[], # Add frequency once implemented
            minval=9765625.0, maxval=15e9, units='Hz')
        self.add_parameter('rflo_frequency', type=float,
            tags=["Detail", "LO"], listen_to=[], # Add frequency once implemented
            minval=9765625.0, maxval=15e9, units='Hz')
        self.add_parameter('txpl_frequency', type=float,
            tags=["Detail", "LO"], 
            minval=9765625.0, maxval=15e9, units='Hz')
        self.add_parameter('rxpl_frequency', type=float,
            tags=["Detail", "LO"], 
            minval=9765625.0, maxval=15e9, units='Hz')
        self.add_parameter('demod_lo_match', type=int,
            tags=["Detail", "Demodulator"], listen_to=[], # Add frequency,iflo once implemented
            minval=3e8, maxval=6e9, units='Hz')
        self.add_parameter('demod_gain', type=int, 
            tags=["Detail", "Demodulator"], 
            minval=int(0), maxval=int(7), unit='dB')
        self.add_parameter('demod_gain_error', type=float, 
            tags=["Detail", "Demodulator"], 
            minval=-50.0, maxval=50.0, unit='cdB')
        self.add_parameter('demod_attenuation', type=int, 
            tags=["Detail", "Demodulator"], 
            minval=int(0), maxval=int(31), unit='dB')
        self.add_parameter('demod_phase_error', type=float, 
            tags=["Detail", "Demodulator"], 
            minval=-4.14, maxval=1.94, unit='1°')
        self.add_parameter('demod_dc_offset_i', type=float, 
            tags=["Detail", "Demodulator"], 
            minval=-70, maxval=100, unit='mV')
        self.add_parameter('demod_dc_offset_q', type=float, 
            tags=["Detail", "Demodulator"], 
            minval=-70, maxval=100, unit='mV')

    # --- Provide set/get for instrument parameters ---
    # Main
    def do_get_frequency(self, query=True):
        '''
        Get frequency of device
        (So far C++ implementation only returns viable results for mixsweep)
        Input:
            None
        Output:
            freq (float) : Frequency in Hz
        '''
        #return self.v2_stub.GetDeviceFreq(SuperV2.Empty()).value
        return 4e9
    def do_set_frequency(self, frequency, offset = 100e6, method="mixsweep"):
        '''
        Set frequency of device.
        Default BB frequency is 100MHz.
        Default method for sweeping is mixsweep.
        Input:
            freq (float) : Frequency in Hz
        Output:
            None
        '''
        self.v2_stub.Sweep( SuperV2.SweepInput(frequency = frequency, power = self._power, offset = offset, method = method) )

    def do_get_power(self, query=True):
        '''
        Get output power of device
        Input:
            query (bool): Refresh parameters from device memory if True
        Output:
            (float) microwave power in dBm
        '''
        return self.hfa_stub.GetAttenuation( HFA.EndpointIndex(value = 0) ).value
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
        self._power=power
        self.hfa_stub.SetAttenuation( HFA.Double(index = HFA.EndpointIndex(value = 0), value = abs(power)) )
    
    def do_get_connection(self):
        '''
        Is Instrument connected to IPESH?
        '''
        return self._connection
    def do_set_connection(self, connect):
        '''
        True: (Re)establish connection to IPESH channel and init stubs
        False: Close channel
        '''
        if connect:
            try:
                self._channel.close()
            except:
                pass
            self._channel = grpc.insecure_channel(address)
            self.hfl_stub = HFL_grpc.HfLOServiceStub(self._channel)
            self.hfd_stub = HFD_grpc.HfDemodulatorServiceStub(self._channel)
            self.hfa_stub = HFA_grpc.HfAttenuatorServiceStub(self._channel)
            self.v2_stub = SuperV2_grpc.HfSuperV2ServiceStub(self._channel)
        else:
            try:
                self._channel.close()
            except:
                pass

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
        Legacy functionality, manually starting up LOs as required preferred to reduce risk of overheating
        Input:
            status (bool): enable LOs or disable everything
        Output:
            None
        '''
        self._status = status
        if status:
            self.on()
        else:
            self.off()

    # Detail
    def do_get_iflo_frequency(self):
        return self.hfl_stub.GetFrequency( HFL.EndpointIndex(value=self.EPDict.index("IFLO")) ).value
    def do_set_iflo_frequency(self, value):
        self.hfl_stub.SetFrequency( HFL.WriteDouble(index=HFL.EndpointIndex(value=self.EPDict.index("IFLO")), value=value) )
        self.hfl_stub.UpdateWrite( HFL.EndpointIndex(value=self.EPDict.index("IFLO")) )
        self.do_set_demod_lo_match(int(value))

    def do_get_rflo_frequency(self):
        return self.hfl_stub.GetFrequency(HFL.EndpointIndex(value=self.EPDict.index("RFLO"))).value
    def do_set_rflo_frequency(self, value):
        self.hfl_stub.SetFrequency( HFL.WriteDouble(index=HFL.EndpointIndex(value=self.EPDict.index("RFLO")), value=value) )
        self.hfl_stub.UpdateWrite( HFL.EndpointIndex(value=self.EPDict.index("RFLO")) )

    def do_get_txpl_frequency(self):
        return self.hfl_stub.GetFrequency(HFL.EndpointIndex(value=self.EPDict.index("TXPL"))).value
    def do_set_txpl_frequency(self, value):
        self.hfl_stub.SetFrequency( HFL.WriteDouble(index=HFL.EndpointIndex(value=self.EPDict.index("TXPL")), value=value) )
        self.hfl_stub.UpdateWrite( HFL.EndpointIndex(value=self.EPDict.index("TXPL")) )

    def do_get_rxpl_frequency(self):
        return self.hfl_stub.GetFrequency(HFL.EndpointIndex(value=self.EPDict.index("RXPL"))).value
    def do_set_rxpl_frequency(self, value):
        self.hfl_stub.SetFrequency( HFL.WriteDouble(index=HFL.EndpointIndex(value=self.EPDict.index("RXPL")), value=value) )
        self.hfl_stub.UpdateWrite( HFL.EndpointIndex(value=self.EPDict.index("RXPL")) )

    def do_get_demod_lo_match(self):
        return self.hfd_stub.GetLoMatchMHz(HFD.EndpointIndex(value=0)).value
    def do_set_demod_lo_match(self, value):
        self.hfd_stub.SetLoMatchMHz(HFD.WriteNum(index=HFD.EndpointIndex(value=0), value=value))
        self.hfd_stub.UpdateWrite(HFD.EndpointIndex(value=0))

    def do_get_demod_gain(self):
        return self.hfd_stub.GetGain(HFD.EndpointIndex(value=0)).value
    def do_set_demod_gain(self, value):
        self.hfd_stub.SetGain(HFD.WriteNum(index=HFD.EndpointIndex(value=0), value=value))
        self.hfd_stub.UpdateWrite(HFD.EndpointIndex(value=0))

    def do_get_demod_gain_error(self):
        return self.hfd_stub.GetGainErrorCdB(HFD.EndpointIndex(value=0)).value
    def do_set_demod_gain_error(self, value):
        self.hfd_stub.SetGainErrorCdB(HFD.WriteDouble(index=HFD.EndpointIndex(value=0), value=value))
        self.hfd_stub.UpdateWrite(HFD.EndpointIndex(value=0))

    def do_get_demod_attenuation(self):
        return self.hfd_stub.GetAttenuation(HFD.EndpointIndex(value=0))
    def do_set_demod_attenuation(self, value):
        self.hfd_stub.SetAttenuation(HFD.WriteNum(index=HFD.EndpointIndex(value=0), value=value))
        self.hfd_stub.UpdateWrite(HFD.EndpointIndex(value=0))

    def do_get_demod_phase_error(self):
        return self.hfd_stub.GetPhaseErrorDeg(HFD.EndpointIndex(value=0)).value
    def do_set_demod_phase_error(self, value):
        self.hfd_stub.SetPhaseErrorDeg(HFD.WriteDouble(index=HFD.EndpointIndex(value=0), value=value))
        self.hfd_stub.UpdateWrite(HFD.EndpointIndex(value=0))

    def do_get_demod_dc_offset_i(self):
        return self.hfd_stub.GetDcOffsetImV(HFD.EndpointIndex(value=0)).value
    def do_set_demod_dc_offset_i(self, value):
        self.hfd_stub.SetDcOffsetImV(HFD.WriteDouble(index=HFD.EndpointIndex(value=0), value=value))
        self.hfd_stub.UpdateWrite(HFD.EndpointIndex(value=0))

    def do_get_demod_dc_offset_q(self):
        return self.hfd_stub.GetDcOffsetQmV(HFD.EndpointIndex(value=0)).value
    def do_set_demod_dc_offset_q(self, value):
        self.hfd_stub.SetDcOffsetQmV(HFD.WriteDouble(index=HFD.EndpointIndex(value=0), value=value))
        self.hfd_stub.UpdateWrite(HFD.EndpointIndex(value=0))
    
    # --- Legacy support --- 
    # Direct usage of proto stubs is preferrable and provides more detailed functionality
    def on(self):
        """
        Set power to original value and turn up all LOs at full power. 
        Obsolete function, manually starting up LOs as required preferred to reduce risk of overheating
        """
        self.do_set_power(self._power)
        self.v2_stub.Startup(SuperV2.StartInfo( lmx_list = [#SuperV2.LMXStart(name="RXPL", power_a=0, power_b=0), 
                                                            #SuperV2.LMXStart(name="TXPL", power_a=0, power_b=0), 
                                                            SuperV2.LMXStart(name="RFLO", power_a=0, power_b=0), 
                                                            SuperV2.LMXStart(name="IFLO", power_a=0, power_b=0)] ))
        self.v2_stub.UpdateWrite(SuperV2.EndpointList(devices=["TXPL", "RXPL", "IFLO", "RFLO"]))
    def off(self):
        """
        Set power as low as possible and disable all LOs
        """
        self.do_set_power(30)
        self.v2_stub.Startup(SuperV2.StartInfo( lmx_list = [SuperV2.LMXStart(name="RXPL"), 
                                                            SuperV2.LMXStart(name="TXPL"), 
                                                            SuperV2.LMXStart(name="RFLO"), 
                                                            SuperV2.LMXStart(name="IFLO")] ))
        self.v2_stub.UpdateWrite(SuperV2.EndpointList(devices=["TXPL", "RXPL", "IFLO", "RFLO"]))

    def set_rflo_powerdown(self, boolean):
        if boolean:
            self.hfl_stub.PowerDown( HFL.EndpointIndex(value=self.EPDict.index("RFLO")) )
        else:
            self.hfl_stub.PowerUp( HFL.EndpointIndex(value=self.EPDict.index("RFLO")) )
        self.hfl_stub.UpdateWrite( HFL.EndpointIndex(value=self.EPDict.index("RFLO")) )
    def set_iflo_powerdown(self, boolean):
        if boolean:
            self.hfl_stub.PowerDown( HFL.EndpointIndex(value=self.EPDict.index("IFLO")) )
        else:
            self.hfl_stub.PowerUp( HFL.EndpointIndex(value=self.EPDict.index("IFLO")) )
        self.hfl_stub.UpdateWrite( HFL.EndpointIndex(value=self.EPDict.index("IFLO")) )
    def set_txpilot_powerdown(self, boolean):
        if boolean:
            self.hfl_stub.PowerDown( HFL.EndpointIndex(value=self.EPDict.index("TXPL")) )
        else:
            self.hfl_stub.PowerUp( HFL.EndpointIndex(value=self.EPDict.index("TXPL")) )
        self.hfl_stub.UpdateWrite( HFL.EndpointIndex(value=self.EPDict.index("TXPL")) )
    def set_rxpilot_powerdown(self, boolean):
        if boolean:
            self.hfl_stub.PowerDown( HFL.EndpointIndex(value=self.EPDict.index("RXPL")) )
        else:
            self.hfl_stub.PowerUp( HFL.EndpointIndex(value=self.EPDict.index("RXPL")) )
        self.hfl_stub.UpdateWrite( HFL.EndpointIndex(value=self.EPDict.index("RXPL")) )

    def set_rflo_enable_a(self, boolean):
        if boolean:
            self.hfl_stub.EnableOutputA( HFL.EndpointIndex(value=self.EPDict.index("RFLO")) )
        else:
            self.hfl_stub.DisableOutputA( HFL.EndpointIndex(value=self.EPDict.index("RFLO")) )
        self.hfl_stub.UpdateWrite( HFL.EndpointIndex(value=self.EPDict.index("RFLO")) )
    def set_iflo_enable_a(self, boolean):
        if boolean:
            self.hfl_stub.EnableOutputA( HFL.EndpointIndex(value=self.EPDict.index("IFLO")) )
        else:
            self.hfl_stub.DisableOutputA( HFL.EndpointIndex(value=self.EPDict.index("IFLO")) )
        self.hfl_stub.UpdateWrite( HFL.EndpointIndex(value=self.EPDict.index("IFLO")) )
    def set_txpilot_enable_a(self, boolean):
        if boolean:
            self.hfl_stub.EnableOutputA( HFL.EndpointIndex(value=self.EPDict.index("TXPL")) )
        else:
            self.hfl_stub.DisableOutputA( HFL.EndpointIndex(value=self.EPDict.index("TXPL")) )
        self.hfl_stub.UpdateWrite( HFL.EndpointIndex(value=self.EPDict.index("TXPL")) )
    def set_rxpilot_enable_a(self, boolean):
        if boolean:
            self.hfl_stub.EnableOutputA( HFL.EndpointIndex(value=self.EPDict.index("RXPL")) )
        else:
            self.hfl_stub.DisableOutputA( HFL.EndpointIndex(value=self.EPDict.index("RXPL")) )
        self.hfl_stub.UpdateWrite( HFL.EndpointIndex(value=self.EPDict.index("RXPL")) )

    def set_rflo_enable_b(self, boolean):
        if boolean:
            self.hfl_stub.EnableOutputB( HFL.EndpointIndex(value=self.EPDict.index("RFLO")) )
        else:
            self.hfl_stub.DisableOutputB( HFL.EndpointIndex(value=self.EPDict.index("RFLO")) )
        self.hfl_stub.UpdateWrite( HFL.EndpointIndex(value=self.EPDict.index("RFLO")) )
    def set_iflo_enable_b(self, boolean):
        if boolean:
            self.hfl_stub.EnableOutputB( HFL.EndpointIndex(value=self.EPDict.index("IFLO")) )
        else:
            self.hfl_stub.DisableOutputB( HFL.EndpointIndex(value=self.EPDict.index("IFLO")) )
        self.hfl_stub.UpdateWrite( HFL.EndpointIndex(value=self.EPDict.index("IFLO")) )
    def set_txpilot_enable_b(self, boolean):
        if boolean:
            self.hfl_stub.EnableOutputB( HFL.EndpointIndex(value=self.EPDict.index("TXPL")) )
        else:
            self.hfl_stub.DisableOutputB( HFL.EndpointIndex(value=self.EPDict.index("TXPL")) )
        self.hfl_stub.UpdateWrite( HFL.EndpointIndex(value=self.EPDict.index("TXPL")) )
    def set_rxpilot_enable_b(self, boolean):
        if boolean:
            self.hfl_stub.EnableOutputB( HFL.EndpointIndex(value=self.EPDict.index("RXPL")) )
        else:
            self.hfl_stub.DisableOutputB( HFL.EndpointIndex(value=self.EPDict.index("RXPL")) )
        self.hfl_stub.UpdateWrite( HFL.EndpointIndex(value=self.EPDict.index("RXPL")) )

    def set_rflo_output_a_power(self, value):
        self.hfl_stub.SetOutputPowerA( HFL.WriteNum(index=HFL.EndpointIndex(value=self.EPDict.index("RFLO")), value=value) )
        self.hfl_stub.UpdateWrite( HFL.EndpointIndex(value=self.EPDict.index("RFLO")) )
    def set_iflo_output_a_power(self, value):
        self.hfl_stub.SetOutputPowerA( HFL.WriteNum(index=HFL.EndpointIndex(value=self.EPDict.index("IFLO")), value=value) )
        self.hfl_stub.UpdateWrite( HFL.EndpointIndex(value=self.EPDict.index("IFLO")) )
    def set_txpilot_output_a_power(self, value):
        self.hfl_stub.SetOutputPowerA( HFL.WriteNum(index=HFL.EndpointIndex(value=self.EPDict.index("TXPL")), value=value) )
        self.hfl_stub.UpdateWrite( HFL.EndpointIndex(value=self.EPDict.index("TXPL")) )
    def set_rxpilot_output_a_power(self, value):
        self.hfl_stub.SetOutputPowerA( HFL.WriteNum(index=HFL.EndpointIndex(value=self.EPDict.index("RXPL")), value=value) )
        self.hfl_stub.UpdateWrite( HFL.EndpointIndex(value=self.EPDict.index("RXPL")) )

    def set_rflo_output_b_power(self, value):
        self.hfl_stub.SetOutputPowerB( HFL.WriteNum(index=HFL.EndpointIndex(value=self.EPDict.index("RFLO")), value=value) )
        self.hfl_stub.UpdateWrite( HFL.EndpointIndex(value=self.EPDict.index("RFLO")) )
    def set_iflo_output_b_power(self, value):
        self.hfl_stub.SetOutputPowerB( HFL.WriteNum(index=HFL.EndpointIndex(value=self.EPDict.index("IFLO")), value=value) )
        self.hfl_stub.UpdateWrite( HFL.EndpointIndex(value=self.EPDict.index("IFLO")) )
    def set_txpilot_output_b_power(self, value):
        self.hfl_stub.SetOutputPowerB( HFL.WriteNum(index=HFL.EndpointIndex(value=self.EPDict.index("TXPL")), value=value) )
        self.hfl_stub.UpdateWrite( HFL.EndpointIndex(value=self.EPDict.index("TXPL")) )
    def set_rxpilot_output_b_power(self, value):
        self.hfl_stub.SetOutputPowerB( HFL.WriteNum(index=HFL.EndpointIndex(value=self.EPDict.index("RXPL")), value=value) )
        self.hfl_stub.UpdateWrite( HFL.EndpointIndex(value=self.EPDict.index("RXPL")) )
    """
    def set_linopt(self, value):
        self._rpc.setlinopt(value)
    """
    def set_hf_attenuation(self, value):
        self.do_set_power(value)
    def reinitialise(self):
        self.v2_stub.Reset(SuperV2.EndpointList(devices=["TXPL", "RXPL", "IFLO", "RFLO", "Demod"]))    

    def set_rxpilot_frequency(self, value):
        self.do_set_rxpl_frequency(value)
    def set_txpilot_frequency(self, value):
        self.do_set_txpl_frequency(value)
    
    # These legacy functions should now be generated from Qkit parameters automatically
    # Warning: Units changed for gain/phase error. LO freqs can now be floats
    """
    def set_demod_attenuation(self, value):
        self._nominalrxatt = value
        self._rpc.writeval("Demodulator", "attenuation", int(value))
        self._rpc.writeval("Demodulator", "write_regs_to_chip", 1)
    def set_demod_gain(self, value):
        self._rpc.writeval("Demodulator", "gain", int(value))
        self._rpc.writeval("Demodulator", "write_regs_to_chip", 1)
    def set_demod_gain_error(self, value):
        self._rpc.writeval("Demodulator", "gain_error", int(value))
        self._rpc.writeval("Demodulator", "write_regs_to_chip", 1)
    def set_demod_phase_error(self, value):
        self._rpc.writeval("Demodulator", "phase_error", int(value))
        self._rpc.writeval("Demodulator", "write_regs_to_chip", 1)

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
        self._rpc.writeval("Demodulator", "write_regs_to_chip", 1)
        self._iffreq = value/1e9
    """
