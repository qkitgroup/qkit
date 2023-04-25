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

from time import sleep
import types
import logging
import re
from bitstring import BitArray # http://packages.python.org/bitstring/
from qkit.core.instrument_base import Instrument
try: from pyftdi.ftdi import Ftdi
except: from pyftdi.pyftdi.ftdi import Ftdi
try: from pyftdi.usbtools import UsbTools 
except: from pyftdi.pyftdi.usbtools import UsbTools

'''
    FTDI USB interface as replacement of the NI-DAQ digital out
'''
class FTDI_DAQ(Instrument):
    _ports = []
    _port = None
    _last_byte = chr(0)
    _aliases = {}

    def __init__(self, name, serial = None, port = 'A', baudrate = 115200):
        '''
            discover and initialize Tunnel_DAC hardware
            
            Input:
                serial - serial number of the FTDI converter
                channel - 2 character channel id the DAC is connected to;
                    the first byte identifies the channel (A..D for current devices)
                    the second byte identifies the bit within that channel (0..7)
                numdacs - number of DACs daisy-chained on that line
                delay - communications delay assumed between PC and the USB converter
        '''
        logging.info(__name__+ ': Initializing instrument Tunnel_DAC')
        Instrument.__init__(self, name, tags=['physical'])
        
        self._conn = Ftdi()
        # VIDs and PIDs of converters used
        vps = [
            (0x0403, 0x6011), # FTDI UM4232H 4ch
            (0x0403, 0x6014)  # FTDI UM232H 1ch
        ]
        # explicitly clear device cache of UsbTools
        #UsbTools.USBDEVICES = []
        # find all devices and obtain serial numbers
        devs = self._conn.find_all(vps)
        # filter list by serial number if provided
        if(serial != None):
            devs = [dev for dev in devs if dev[2] == serial]
        if(len(devs) == 0):
            logging.error(__name__ + ': failed to find matching FTDI devices.')
        elif(len(devs) > 1):
            logging.error(__name__ + ': more than one converter found and no serial number given.')
            logging.info(__name__ + ': available devices are: %s.'%str([dev[2] for dev in devs]))
        vid, pid, self._serial, ports, description = devs[0]
        self._ports = [chr(ord('A') + i) for i in range(ports)]

        # open device
        (self._port, bit) = self._parse_channel_string(port)
        self._conn.open(vid, pid, interface = ord(self._port) - ord('A') + 1, serial = self._serial)
        logging.info(__name__ + ': using converter with serial #%s'%self._serial)
        self._conn.set_bitmode(0xFF, Ftdi.BITMODE_BITBANG)
        self._set_baudrate(baudrate)

        # provide user interface
        self.add_parameter('port', type=str, flags=Instrument.FLAG_GET)
        #self.add_parameter('aliases', type=types.DictType, flags=Instrument.FLAG_GETSET)
        self.add_function('digital_out')
        self.add_function('digital_stream')
        self.add_function('set_aliases')
        self.add_function('get_aliases')

    def do_get_port(self):
        return self._port

    def set_aliases(self, aliases):
        '''
            define channel aliases
            accepts a dictionary that resolves alias names to internal channel names
        '''
        self._aliases = aliases
    
    def get_aliases(self):
        '''
            retrieve channel aliases
        '''
        return self._aliases

    def digital_out(self, channel, status):
        '''
            set a bit/byte on a FTDI channel
        '''
        (port, bit) = self._parse_channel_string(channel)
        if(bit != None):
            if(status): 
                byte = chr(ord(self._last_byte) | (1<<bit))
            else:
                byte = chr(ord(self._last_byte) & ~(1<<bit))
        else:
            byte = chr(0xff) if status else chr(0)
        self._conn.write_data(byte)
        self._last_byte = byte

    def digital_stream(self, channel, samples, rate):
        '''
            write a serial bit/byte stream to the device
            rate max 6 MHz for ft4232h chip
        '''
        (port, bit) = self._parse_channel_string(channel)
        # convert bit stream into byte stream
        if(bit != None):
            byte = 1<<bit
            samples = [(chr(ord(self._last_byte) | byte) if x else (chr(ord(self._last_byte) & ~byte))) for x in BitArray(samples)]
        # output data on the device
        self._set_baudrate(rate)
        self._conn.write_data(''.join(samples))
        self._last_byte = samples[-1]

    def _parse_channel_string(self, channel):
        '''
            parses a channel string into a (port, bit) tuple
        '''
        # translate aliases
        if(self._aliases.has_key(channel)):
            channel = self._aliases[channel]
        
        # parse & mangle channel string
        m = re.match('(?P<port>[A-Z]+[0-9]*)(?P<bit>:[0-9]+)?', channel).groupdict()
        if(m == None):
            raise ValueError('channel identifier %s not understood.'%channel)
        port = m['port']
        if(m['bit'] != None): 
            bit = int(m['bit'].lstrip(':'))
        else:
            bit = None
        
        # check if the channel exists on this device
        if(not (port in self._ports)):
            raise ValueError('prot %s not supported by this device.'%port)
        if((self._port != None) and (port != self._port)):
            raise ValueError('this implementation can not change the port identifier outside __init__.')
        if((bit != None) and ((bit < 0) or (bit > 7))):
            raise ValueError('bit number must be between 0 and 7, not %d.'%bit)
        
        return (port, bit)
        
    def _set_baudrate(self, baudrate):
        ''' 
            change baud rate of the FTDIs serial engine
        '''
        # 80k generates bit durations of 12.5us, 80 is magic :(
        # magic?: 4 from incorrect BITBANG handling of pyftdi, 2.5 from 120MHz instead of 48MHz clock of H devices
        self._baudrate =  baudrate
        self._conn.set_baudrate(baudrate/80)
