"""
This module provides drivers for accessing the IVVI's Bias DACs. 

For more information about the IVVI visit https://qtwork.tudelft.nl/~schouten/ivvi/index-ivvi.htm .
The underlying communication protocol is explained at https://qtwork.tudelft.nl/~schouten/ivvi/doc-d5/rs232linkformat.txt .

Improvements compared to legacy codebase include
- added serial port connection possibility
- underlying driver version readback
- internal book-keeping of set DAC-range-knobs using helper class IVVI_DAC_Group to allow dynamically adjusted conversions at different DACs
- enhanced qkit conformity and integration

Author: Marius Frohn <uzrfo@student.kit.edu>
Version: 2.1; (07/2024) 

(Legacy DOC-string)
IVVI.py class, to perform the communication between the Wrapper and the device
Pieter de Groot <pieterdegroot@gmail.com>, 2008
Martijn Schaafsma <qtlab@mcschaafsma.nl>, 2008
Reinier Heeres <reinier@heeres.eu>, 2008

extended by Tim Wolz to access the IVVI via Ethernet.
Data is sent as a string via Ethernet to a Raspberry Pi, 
where it is converted to asci code and sent to the IVVI
Ethernet connection based on the lazy pirate pattern by Daniel Lundin <dln(at)eintr(dot)org> 

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

import logging, serial, serial.tools.list_ports, serial.serialutil, time, zmq
from qkit.core.instrument_base import Instrument

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


class IVVI_BiasDAC(Instrument):
    """
    This driver provides access to the IVVI's bias DACs
    It can either be used via serial port with a direct cable connection or via ethernet if i.e. a RasbPi is set up as a man-in-the-middle

    Initialize with
    <name> = instruments.create('<name>', 'IVVI_BiasDAC', <"Ethernet"/"SerialPort">, **kwargs)
    """
    def __init__(self, name: str, connection_type: str, knob_config: list[str] = ["0", "0", "0", "0"], reset_on_init: bool = True, **kwargs):
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
        if connection_type == "SerialPort":
            self.connection = IVVI_SerialPort(**kwargs)
        elif connection_type == "Ethernet":
            self.connection = IVVI_Ethernet(**kwargs)
        else:
            print("Unknown connection_type '{}'. Needs to be 'Ethernet' or 'SerialPort'".format(connection_type))
            raise ValueError
        for i in range(16):
            def channel_setter(mVolt):
                return self.set_dac(i + 1, mVolt)
            self.__dict__["do_set_DAC_{}_voltage".format(i + 1)] = channel_setter
            def channel_getter():
                return self.get_dac(i + 1)
            self.__dict__["do_get_DAC_{}_voltage".format(i + 1)] = channel_getter
            self.add_parameter("DAC_{}_voltage".format(i + 1), type=float, minval=DACRangeBip.low, maxval=DACRangeBip.high, units='mV')
        self.dac_ranges = [DACRangeBip] * 4
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
        if not ident in RangeIdent:
            print("Given identifier '{}' unkown. Try 'pos', 'bip', 'neg' instead. Group range unchanged".format(ident))
        elif group_num < 0 or group_num >= len(self.dac_ranges):
            print("DAC group number {} out of range 0 .. 3. Group range unchanged".format(group_num))
        else:
            self.dac_ranges[group_num] = RangeIdent[ident]
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
            self.connection.communicate([7, 0, 2, 1, channel] + list(self.dac_ranges[(channel - 1)//4].mv2bytes(mVolt)))
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
        return self.connection.communicate([4, 0, 34, 2])
    
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
        return self.connection.communicate([4, 0, 3, 4])[0]


class IVVI_SerialPort:
    """
    Helper class handling communication via serial port
    Possible port names can be found before initialization with get_ports()
    """
    @staticmethod
    def get_ports():
        """
        Shortcut for serial.tools.list_ports.main()
        Implemented as static function so one can determine to be used port name before instrument creation

        Input:
            None
        
        Output:
            (None): prints information about currently available serial ports
        """
        serial.tools.list_ports.main()
    
    def __init__(self, port: str = "COM3", timeout: float = 3, timeskip: float = 0.01):
        self.timeskip = timeskip
        try:
            self.ser = serial.Serial(port=port, baudrate=115200, parity=serial.PARITY_ODD, stopbits=serial.STOPBITS_ONE, timeout=timeout, write_timeout=timeout)
        except serial.serialutil.SerialException:
            print("Error while trying to open serial port '{}' for IVVI. Port not connected?".format(port))
            raise serial.serialutil.SerialException
        self.ser.close()
    
    def __del__(self):
        self.ser.close()
    
    def communicate(self, message: list[int]) -> list[int]:
        """
        Main communication protocol of the serial port connection with integrated error flag interpretation

        Input:
            message (list[int]) : to be sent message
        
        Output:
            (list[int]) : received response, stripped off size & error flag bytes 
        """
        self.ser.open()
        if self.ser.in_waiting > 0:
            # clear input if something still in waiting for whetever reason
            self.ser.read(self.ser.in_waiting)
            time.sleep(self.timeskip)
        self.ser.write(bytes(message))
        time.sleep(self.timeskip)
        readback = list(self.ser.read(self.ser.in_waiting))
        if len(readback != readback[0]):
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
        time.sleep(self.timeskip)
        self.ser.close()
        return readback[2:]
    

class IVVI_Ethernet:
    """
    Helper class handling communication via ethernet
    """
    def __init__(self, address='10.22.197.115'):
        self._address = address
        self._port = 6543
        self.REQUEST_TIMEOUT = 2500
        self.REQUEST_RETRIES = 3
        self._open_zmq_connection()

    def __del__(self):
        self._close_zmq_connection()

    def _open_zmq_connection(self):
        """
        Connects to the raspberry via zmq/tcp

        Input:
            None

        Output:
            None
        """
        self.context = zmq.Context(1)
        print("Connecting to Raspberry Pi")
        self.client = self.context.socket(zmq.REQ)
        self.client.connect("tcp://%s:%s" % (self._address,self._port)) # raspi address
        self.poll = zmq.Poller()
        self.poll.register(self.client, zmq.POLLIN)
        
    def _close_zmq_connection(self):
        """
        Closes the zmq connection

        Input:
            None

        Output:
            None
        """
        logging.debug(__name__ + ' : Closing ethernet connection')
        self.context.term()

    def communicate(self, message: list[int]) -> list[int]:
        """
        Main communication protocol of the ethernet connection with integrated error flag interpretation

        Input:
            message (list[int]) : to be sent message
        
        Output:
            (list[int]) : received response, stripped off size & error flag bytes 
        """
        logging.debug(__name__ + ' : do communication with instrument')
        message = ("{} "*message[0]).format(*message)
        retries_left = self.REQUEST_RETRIES
        while retries_left:
            self.client.send(message)
            expect_reply = True
            while expect_reply:
                socks = dict(self.poll.poll(self.REQUEST_TIMEOUT))
                if socks.get(self.client) == zmq.POLLIN:
                    data_out_string = self.client.recv()
                    if not data_out_string:
                        break
                    else:
                        retries_left = 0
                        expect_reply = False
                else:
                    print("No response from server, retrying")
                    # Socket is confused. Close and remove it.
                    self.client.setsockopt(zmq.LINGER, 0)
                    self.client.close()
                    self.poll.unregister(self.client)
                    retries_left -= 1
                    if retries_left == 0:
                        print("Server seems to be offline, abandoning")
                        break
                    print("Reconnecting and resending " + message)
                    # Create new connection
                    self._open_zmq_connection()
        readback = [int(s) for s in data_out_string.split(' ')]
        if len(readback != readback[0]):
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