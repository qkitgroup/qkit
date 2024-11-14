"""
This module provides drivers for accessing the IVVI's Bias DACs. 

For more information about the IVVI visit https://qtwork.tudelft.nl/~schouten/ivvi/index-ivvi.htm .
The underlying communication protocol is explained at https://qtwork.tudelft.nl/~schouten/ivvi/doc-d5/rs232linkformat.txt .

Improvements compared to legacy codebase include
- added various serial port connection types in SerialPortCommunication module
- underlying driver version readback
- internal book-keeping of set DAC-range-knobs using helper class IVVI_DAC_Group to allow adjusted conversions at different DACs
- enhanced qkit conformity and integration
- dummy IVD for sweeping given ranges in different modes

Author: Marius Frohn <uzrfo@student.kit.edu>
Version: 2.4; (08/2024) 

(Legacy DOC-string)
IVVI.py class, to perform the communication between the Wrapper and the device
Pieter de Groot <pieterdegroot@gmail.com>, 2008
Martijn Schaafsma <qtlab@mcschaafsma.nl>, 2008
Reinier Heeres <reinier@heeres.eu>, 2008

Extended by Tim Wolz to access the IVVI via Ethernet.
Data is sent as a string via Ethernet to a Raspberry Pi, 
where it is converted to asci code and sent to the IVVI
Ethernet connection based on the lazy pirate pattern by Daniel Lundin <dln(at)eintr(dot)org> 
(Note Marius: Moved to SerialPortCommunication.SerialPortRasbpi)

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""

import logging, time
from qkit.core.instrument_base import Instrument
import SerialPortCommunication as SPC
import numpy as np

class IVVI_BiasDAC(Instrument):
    """
    This driver provides access to the IVVI's bias DACs.
    Usage requires communicating with the IVVI's control box via RS232 serial port connection.
    The SerialPortCommunication module/instrument is intended to do that.

    Initialize with
    <SPC_name> = instruments.create('<SPC_name>', 'SerialPortCommunication', *args for creating connection*)
    <name> = instruments.create('<name>', 'IVVI_BiasDAC', connection=<SPC_name>, **kwargs)
    """

    class IVVI_DAC_Group:
        """
        Helper class for keeping track of set DAC ranges at IVVI D5 module and binary <-> V conversion
        IVVI can switch DAC polization between negative, centered around 0 and positive in groups of 4. 
        """
        def __init__(self, val1: float, val2: float):
            self.low = min(val1, val2)
            self.high = max(val1, val2)
        def __str__(self) -> str:
            return "IVVI DAC range helper object for {} to {} V".format(self.low, self.high)
        def __hash__(self):
            return hash(tuple((self.low, self.high)))
        def v2bytes(self, volt: float) -> tuple[int, int]:
            if volt < self.low or volt > self.high:
                raise ValueError
            else:
                bytevalue = int(round(65535*(volt - self.low)/(self.high - self.low)))
                return (bytevalue//256, bytevalue % 256)
        def bytes2v(self, byte_high: int, byte_low: int) -> float:
            # Correct readback expected, no value checking
            return self.low + (self.high - self.low)*(256*byte_high + byte_low)/65536

    # available ranges
    DACRangeNeg = IVVI_DAC_Group(-4.0, 0.0)
    DACRangeBip = IVVI_DAC_Group(-2.0, 2.0)
    DACRangePos = IVVI_DAC_Group(0.0, 4.0)
    RangeIdent = {  "pos": DACRangePos, "bip": DACRangeBip, "neg": DACRangeNeg, 
                    "Pos": DACRangePos, "Bip": DACRangeBip, "Neg": DACRangeNeg, 
                    "POS": DACRangePos, "BIP": DACRangeBip, "NEG": DACRangeNeg, 
                    "+"  : DACRangePos, "0"  : DACRangeBip, "-"  : DACRangeNeg  }
    ReverseIdent = { DACRangePos: "Pos", DACRangeBip: "Bip", DACRangeNeg: "Neg" }
    
    class DummyIVD:
        """
        This is a primitive dummy for using the IVVI as a IVD. 
        It only takes the value-setting side into consideration (voltage divider v_div or current source dAdV), 
        while e.g. amplification factors when measuring values should be handled within the measure-function.
        Setting status on/off of additionally needed devices should also be handled outside of this class
        """
        def __init__(self):
            """
            These parameters need to be set before sweeping
            """
            self.measure_func = None
            self.sweep_channel = None
            self.delay_setget = None
            self.pseudo_bias_mode = None # 0: current bias; 1: voltage bias
            self.dAdV = None # for current bias
            self.v_div = None # for voltage bias
        def get_sweep_mode(self):
            # 0: V bias V measure, 1: I bias V measure, 2: V bias I measure
            # technically mode 2 also possible, this class cant determine 0 vs 2 without hidden knowledge about measure function though
            return 1 - self.pseudo_bias_mode
        def get_sweep_bias(self):
            return self.pseudo_bias_mode
        def get_sweep_channels(self):
            return [self.sweep_channel]
        def set_status(self, *args, **kwargs):
            pass

    def __init__(self, name: str, connection: SPC.SerialPortCommunication, knob_config: list[str] = ["0", "0", "0", "0"], reset_on_init: bool = True, make_dummy_ivd: bool = False):
        """
        Initialzes the IVVI Bias DAC by communicating via serial port

        Input:
            name (str)                              : name of the instrument
            connection (SerialPortCommunication)    : instrument handling communication, see module
            knob_config (list[str])                 : initially set DAC group ranges
            reset_on_init (bool)                    : reset all dacs to 0 after initialization or keep as is
            make_dummy_ivd (bool)                   : include parameters for using IVVI as IVD

        Output:
            None
        """
        self.dummy_ivd = self.DummyIVD() if make_dummy_ivd else None
        Instrument.__init__(self, name, tags=['physical'])
        self.connection = connection
        for j in range(16):
            self.__dict__["do_set_DAC_{}_voltage".format(j + 1)] = lambda mVolt, j=j: self.set_dac(j + 1, mVolt)
            self.__dict__["do_get_DAC_{}_voltage".format(j + 1)] = lambda j=j: self.get_dac(j + 1)
            self.add_parameter("DAC_{}_voltage".format(j + 1), type=float, minval=self.DACRangeBip.low, maxval=self.DACRangeBip.high, units='V', flags=Instrument.FLAG_GETSET)
        self.dac_ranges = [self.DACRangeBip] * 4
        for i in range(4):
            self.set_dacgroup_range(i, knob_config[i])
        self.add_function("set_dacgroup_range")
        self.add_function("reset_dacs")
        self.add_function("get_driver_version")
        if reset_on_init:
            self.reset_dacs()
        logging.info("{} : Initializing instrument IVVI via serial port with driver version {}".format(self._name, self.get_driver_version()))
    
    def __del__(self):
        """
        Closes up the IVVI driver

        Input:
            None

        Output:
            None
        """
        del self.connection
        logging.info(__name__ + ': Deleting IVVI instrument')
    
    def __getattr__(self, name):
        """
        Add DummyIVD attributes to class, if enabled
        """
        if not self.dummy_ivd is None:
            return self.dummy_ivd.__getattribute__(name)
        else:
            print("Cannot find attribute '{}' for IVVI_BiasCAC, perhaps dummy IVD needs to be enabled".format(name))
            raise AttributeError
    
    @staticmethod
    def handle_readback_error_flag(readback: list[int]) -> list[int]:
        """
        Readback of every command sent to IVVI-rack has the format [*Readback length*, *Error flag byte*, DataByte, DataByte, ...].
        This function checks if readback has in fact the size it claims to have and interprets the error flag.
        It strips these two bytes from the readback and returns only the data bytes.

        Input:
            readback (list[int]): Readback from a communication with IVVI-rack

        Output:
            (list[int]): Data bytes of given readback
        """
        if len(readback) != readback[0]:
            logging.info(__name__ + ": Unknown communication error")
            print(__name__ + ": Unknown communication error")
        if readback[1] == 32:
            logging.info(__name__ + ': Watchdog reset detected')
            print(__name__ + ": Watchdog reset detected")
        elif readback[1] == 64:
            logging.info(__name__ + ': DAC does not exist')
            print(__name__ + ": DAC does not exist")
        elif readback[1] == 128:
            logging.info(__name__ + ': wrong action')
            print(__name__ + ": wrong action")
        return readback[2:]
      
    def set_dacgroup_range(self, group_num: int, ident: str):
        """
        Does NOT change actual polization of the DACs, only possible via knobs at IVVI. 
        Set internal values to according analog positions for correct value conversions!

        Input: 
            group_num (int) : 0 ... 3; index of the DAC group corresponding to DACs 1-4, 5-8, ...
            ident (str)     : Identifier for DAC range. See IVVIDIG_main_eth.RangeIdent for possibilities

        Output:
            None
        """
        if not ident in self.RangeIdent:
            print("Given identifier '{}' unkown. Try 'pos', 'bip', 'neg' instead. Group range unchanged".format(ident))
        elif group_num < 0 or group_num >= len(self.dac_ranges):
            print("DAC group number {} out of range 0 .. 3. Group range unchanged".format(group_num))
        else:
            self.dac_ranges[group_num] = self.RangeIdent[ident]
            for i in range(4):
                self.set_parameter_options("DAC_{}_voltage".format(4*group_num + i + 1), minval=self.dac_ranges[group_num].low, maxval=self.dac_ranges[group_num].high)
    
    def reset_dacs(self):
        """
        Set all DACs to 0 V, adjusted to their currently set range

        Input:
            None

        Output:
            None
        """
        for channel in range(16):
            self.set_dac(channel + 1, 0)
    
    def set_dac(self, channel: int, volt: float):
        """
        Set DAC channel to given voltage, if value is valid within set range

        Input:
            channel (int) : 1-based channel index (DAC #1 -> channel = 1, not 0)
            volt (float) : to be set voltage in V
        
        Output:
            None
        """
        try:
            self.handle_readback_error_flag(self.connection.communicate([7, 0, 2, 1, channel] + list(self.dac_ranges[(channel - 1)//4].v2bytes(volt)), 2))
        except ValueError:
            print("Given voltage {} V not within selected DAC-range {} .. {} V".format(volt, self.dac_ranges[(channel - 1)//4].low, self.dac_ranges[(channel - 1)//4].high))

    def get_dacs_raw(self) -> list[int]:
        """
        Read back all DACs and return data bytes

        Input:
            None

        Output:
            (list[int]) : raw DAC values as [DAC_1_byte_high, DAC_1_byte_low, DAC_2_byte_high, ...]
        """
        return self.handle_readback_error_flag(self.connection.communicate([4, 0, 34, 2], 34))
    
    def get_dacs_list(self) -> list[float]:
        """
        Returns list of set DAC voltages in V

        Input:
            None

        Output:
            (list[float]) : set DAC voltages in V
        """
        data = self.get_dacs_raw()
        return [self.dac_ranges[channel//4].bytes2v(data[2*channel], data[2*channel + 1]) for channel in range(16)]

    def get_dac(self, channel: int) -> float:
        """
        Returns set voltage at specific DAC channel

        Input: 
            channel (int) : 1-based channel index (DAC #1 -> channel = 1, not 0)

        Output:
            (float) : voltage in V
        """
        data = self.get_dacs_raw()
        return self.dac_ranges[(channel - 1)//4].bytes2v(data[2*channel - 2], data[2*channel - 1]) 

    def get_driver_version(self) -> int:
        """
        Returns version number of underlying driver

        Input:
            None

        Output:
            (int) : version number
        """
        # For some unknown reason reading out the driver version outmatically sets it as high byte in DAC1
        # This call fixes this error in an ugly way
        dac_val = self.get_dac(1)
        drive = self.handle_readback_error_flag(self.connection.communicate([4, 0, 3, 4], 3))[0]
        self.set_dac(1, dac_val)
        return drive
    
    def take_IV(self, sweep):
        if self.dummy_ivd is None:
            print("IVVI_BiasDAC needs dummy IVD enabled to take IV-curve")
            raise AttributeError
        start, stop, step, _ = sweep
        setty = []
        getty = []
        for val in np.linspace(start, stop, int(round(np.abs(start-stop)/step+1))):
            if self.dummy_ivd.pseudo_bias_mode: # voltage bias
                self.set_dac(self.dummy_ivd.sweep_channel, val*self.dummy_ivd.v_div)
                setty += [self.get_dac(self.dummy_ivd.sweep_channel)/self.dummy_ivd.v_div]
            else: # current bias
                self.set_dac(self.dummy_ivd.sweep_channel, val/self.dummy_ivd.dAdV)
                setty += [self.get_dac(self.dummy_ivd.sweep_channel)*self.dummy_ivd.dAdV]
            time.sleep(self.dummy_ivd.delay_setget)
            getty += [self.dummy_ivd.measure_func()]
        # return requires I-values first, V-values second independent of what was set/measured
        if self.dummy_ivd.pseudo_bias_mode: # voltage bias
            return np.array(getty), np.array(setty)
        else: # current bias
            return np.array(setty), np.array(getty)

    # qkit parameter documentation
    def get_parameters(self) -> dict:
        """
        Returns info for qkit
        """
        # DAC values in V
        params = {"DAC_{}_voltage".format(i+1): {} for i in range(16)}
        if self.dummy_ivd is None:
            ivd_params = {}
        else:
            ivd_params = {
                "measure_func": {},
                "sweep_channel": {},
                "delay_setget": {},
                "pseudo_bias_mode": {}, 
                "dAdV": {},
                "v_div": {}
            }
        return {**params, **ivd_params}
    
    def get_measure_func(self):
            return self.dummy_ivd.measure_func.__name__ if self.dummy_ivd is not None else None
    def get_sweep_channel(self):
        return self.dummy_ivd.sweep_channel if self.dummy_ivd is not None else None
    def get_delay_setget(self):
        return self.dummy_ivd.delay_setget if self.dummy_ivd is not None else None
    def get_pseudo_bias_mode(self):
        return self.dummy_ivd.pseudo_bias_mode if self.dummy_ivd is not None else None
    def get_dAdV(self):
        return self.dummy_ivd.dAdV if self.dummy_ivd is not None else None
    def get_v_div(self):
        return self.dummy_ivd.v_div if self.dummy_ivd is not None else None
    def get(self, param, **kwargs):
        try:
            return eval("self.get_{}()".format(param))
        except:
            return None
