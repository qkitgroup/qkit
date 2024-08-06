"""
This module provides drivers for accessing the IVVI's Bias DACs. 

For more information about the IVVI visit https://qtwork.tudelft.nl/~schouten/ivvi/index-ivvi.htm .
The underlying communication protocol is explained at https://qtwork.tudelft.nl/~schouten/ivvi/doc-d5/rs232linkformat.txt .

Improvements compared to legacy codebase include
- added various serial port connection types in SerialPortCommunication module
- underlying driver version readback
- internal book-keeping of set DAC-range-knobs using helper class IVVI_DAC_Group to allow adjusted conversions at different DACs
- enhanced qkit conformity and integration

Author: Marius Frohn <uzrfo@student.kit.edu>
Version: 2.3; (07/2024) 

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

import logging
from qkit.core.instrument_base import Instrument
import SerialPortCommunication as SPC

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
        Helper class for keeping track of set DAC ranges at IVVI D5 module and binary <-> mV conversion
        IVVI can switch DAC polization between negative, centered around 0 and positive in groups of 4. 
        """
        def __init__(self, val1: float, val2: float):
            self.low = min(val1, val2)
            self.high = max(val1, val2)
        def __str__(self) -> str:
            return "IVVI DAC range helper object for {} to {} mV".format(self.low, self.high)
        def mv2bytes(self, mvolt: float) -> tuple[int, int]:
            if mvolt < self.low or mvolt > self.high:
                raise ValueError
            else:
                bytevalue = int(round(65535*(mvolt - self.low)/(self.high - self.low)))
                return (bytevalue//256, bytevalue % 256)
        def bytes2mv(self, byte_high: int, byte_low: int) -> float:
            # Correct readback expected, no value checking
            return self.low + (self.high - self.low)*(256*byte_high + byte_low)/65536

    # available ranges
    DACRangeNeg = IVVI_DAC_Group(-4000, 0)
    DACRangeBip = IVVI_DAC_Group(-2000, 2000)
    DACRangePos = IVVI_DAC_Group(0, 4000)
    RangeIdent = { "pos": DACRangePos, "bip": DACRangeBip, "neg": DACRangeNeg, 
                "Pos": DACRangePos, "Bip": DACRangeBip, "Neg": DACRangeNeg, 
                "POS": DACRangePos, "BIP": DACRangeBip, "NEG": DACRangeNeg, 
                "+"  : DACRangePos, "0"  : DACRangeBip, "-"  : DACRangeNeg  }

    def __init__(self, name: str, connection: SPC.SerialPortCommunication, knob_config: list[str] = ["0", "0", "0", "0"], reset_on_init: bool = True):
        """
        Initialzes the IVVI Bias DAC by communicating via serial port

        Input:
            name (str)            : name of the instrument
            connection_type (str) : how to connect to the 
            knob_config (list)    : initially set DAC group ranges
            reset_on_init (bool)  : reset all dacs to 0 after initialization or keep as is
            **kwargs (if SerialPort)   
                port (str)        : name of the to be connected to port
                timeout (float)   : timeout passed to underlying pyserial object (write & read)
                timeskip (float)  : buffer time for waiting for underlying pyserial object to update sent/received data
            **kwargs (if ethernet)
                address (string)  : IP-Adress of to be connected to device

        Output:
            None
        """
        Instrument.__init__(self, name, tags=['physical'])
        self.connection = connection
        for j in range(16):
            self.__dict__["do_set_DAC_{}_voltage".format(j + 1)] = lambda mVolt, j=j: self.set_dac(j + 1, mVolt)
            self.__dict__["do_get_DAC_{}_voltage".format(j + 1)] = lambda j=j: self.get_dac(j + 1)
            self.add_parameter("DAC_{}_voltage".format(j + 1), type=float, minval=self.DACRangeBip.low, maxval=self.DACRangeBip.high, units='mV')
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
        Set all DACs to 0 mV, adjusted to their currently set range

        Input:
            None

        Output:
            None
        """
        for channel in range(16):
            self.set_dac(channel + 1, 0)
    
    def set_dac(self, channel: int, mVolt: float):
        """
        Set DAC channel to given voltage, if value is valid within set range

        Input:
            channel (int) : 1-based channel index (DAC #1 -> channel = 1, not 0)
            mVolt (float) : to be set voltage in mV
        
        Output:
            None
        """
        try:
            self.handle_readback_error_flag(self.connection.communicate([7, 0, 2, 1, channel] + list(self.dac_ranges[(channel - 1)//4].mv2bytes(mVolt)), 2))
        except ValueError:
            print("Given voltage {} mV not within selected DAC-range {} .. {} mV".format(mVolt, self.dac_ranges[(channel - 1)//4].low, self.dac_ranges[(channel - 1)//4].high))

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
        Returns list of set DAC voltages in mV

        Input:
            None

        Output:
            (list[float]) : set DAC voltages in mV
        """
        data = self.get_dacs_raw()
        return [self.dac_ranges[channel//4].bytes2mv(data[2*channel], data[2*channel + 1]) for channel in range(16)]

    def get_dac(self, channel: int) -> float:
        """
        Returns set voltage at specific DAC channel

        Input: 
            channel (int) : 1-based channel index (DAC #1 -> channel = 1, not 0)

        Output:
            (float) : voltage in mV
        """
        data = self.get_dacs_raw()
        return self.dac_ranges[(channel - 1)//4].bytes2mv(data[2*channel - 2], data[2*channel - 1]) 

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
