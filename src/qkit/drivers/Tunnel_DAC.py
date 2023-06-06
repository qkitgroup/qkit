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
try:
    from qkit.core.instrument_base import Instrument
except:
    # debug mode
    logging.getLogger().setLevel(logging.INFO)
    logging.warning(__name__ + ': unable to load instrument module. entering standalone mode.')
    class Instrument:
        FLAG_SET = 0x01
        FLAG_GET = 0x02
        def __init__(self, name, tags):
            pass
        def add_parameter(self, name, type, flags, channels = (), minval = None, maxval = None, units = None, format = None, tags = None):
            pass
        def add_function(self, func):
            pass
from pyftdi.pyftdi.ftdi import Ftdi
from pyftdi.pyftdi.usbtools import UsbTools 

'''
    Tunnelelektronik DAC w/ FTDI USB interface
'''
class Tunnel_DAC(Instrument):

    def __init__(self, name, serial = None, channel = 'A0', numdacs=3, delay = 1e-3):
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
        vid, pid, self._serial, channels, description = devs[0]
        # parse channel string
        if(len(channel) != 2):
            logging.error(__name__ + ': channel identifier must be a string of length 2. ex. A0, D5.')
        self._channel = 1 + ord(channel[0]) - ord('A')
        self._bit = ord(channel[1]) - ord('0')
        if((self._channel < 1) or (self._channel > channels)):
            logging.error(__name__ + ': channel %c is not supported by this device.'%(chr(ord('A')+self._channel-1)))
        if((self._bit < 0) or (self._bit > 7)):
            logging.error(__name__ + ': subchannel must be between 0 and 7, not %d.'%self._bit)

        # open device
        self._conn.open(vid, pid, interface = self._channel, serial = self._serial)
        logging.info(__name__ + ': using converter with serial #%s'%self._serial)
        self._conn.set_bitmode(0xFF, Ftdi.BITMODE_BITBANG)
        # 80k generates bit durations of 12.5us, 80 is magic :(
        # magic?: 4 from incorrect BITBANG handling of pyftdi, 2.5 from 120MHz instead of 48MHz clock of H devices
        # original matlab code uses 19kS/s
        self._conn.set_baudrate(19000/80)

        # house keeping        
        self._numdacs = numdacs
        self._sleeptime = (10. + 16.*self._numdacs)*12.5e-6 + delay # 1st term from hardware parameters, 2nd term from USB  
        self._minval = -5000.
        self._maxval = 5000.
        self._resolution = 16 # DAC resolution in bits
        self._voltages = [0.]*numdacs
        
        self.add_parameter('voltage', type=float, flags=Instrument.FLAG_SET, channels=(1, self._numdacs),
                           minval = self._minval, maxval = self._maxval, units='mV', format = '%.02f') # tags=['sweep']
        self.add_function('set_voltages')
        self.add_function('commit')


    def _encode(self, data, channel = 0, bits_per_item = 16, big_endian = True):
        '''
            convert binary data into line symbols
            
            the tunnel electronic DAC logic box triggers on rising 
            signal edges and samples data after 18us. we use a line
            code with three bits of duration 12us, where a logical 1
            is encoded as B"110" and a logical 0 is encoded as B"100".
            
            the line data is returned as a byte string with three bytes/symbol.
            
            Input:
                data - a vector of data entities (usually a string or list of integers)
                channel - a number in [0, 7] specifying the output bit on the USB-to-UART chip
                bits_per_item - number of bits to extract from each element of the data vector
        '''
        # build line code for the requested channel
        line_1 = chr(1<<channel)
        line_0 = chr(0)
        line_code = [''.join([line_0, line_1, line_1]), ''.join([line_0, line_1, line_0])]
        # do actual encoding
        result = []
        result.append(10*line_0)
        for item in data:
            for bit in (range(bits_per_item-1, -1, -1) if big_endian else range(0, bits_per_item)):
                result.append(line_code[1 if(item & (1<<bit)) else 0])
        result.append(10*line_0)
        return ''.join(result)


    def commit(self):
        '''
            send updated parameter values to the physical DACs via USB
        '''
        # normalize, scale, clip voltages
        voltages = [-1+2*(x-self._minval)/(self._maxval-self._minval) for x in self._voltages]
        voltages = [max(-2**(self._resolution-1), min(2**(self._resolution-1)-1, int(2**(self._resolution-1)*x))) for x in voltages]
        # encode and send
        data = self._encode(reversed(voltages), self._bit, self._resolution)
        self._conn.write_data(data)
        # wait for the FTDI fifo to clock the data to the DACs
        sleep(self._sleeptime)


    def do_set_voltage(self, value, channel):
        '''
            immediately update voltage on channel ch
            parameter checking is done by qtlab
        '''
        self._voltages[channel-1] = value
        self.commit()


    def set_voltages(self, valuedict):
        '''
            update voltages on several channels simultaneously
            todo: update instrument panel display
        '''
        for channel, value in valuedict.iteritems():
            # bounds checking & clipping
            if((channel < 1) or (channel > self._numdacs)):
                logging.error(__name__ + ': channel %d out of range.'%channel)
                continue
            value = float(value)
            if((value < self._minval) or (value >= self._maxval)):
                logging.error(__name__ + ': value %f out of range. clipping.'%value)
                value = max(self._minval, min(self._maxval, value)) # does not handle maxval correctly
            self._voltages[channel-1] = value
        self.commit()
