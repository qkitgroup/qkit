# IVVI.py class, to perform the communication between the Wrapper and the device
# Pieter de Groot <pieterdegroot@gmail.com>, 2008
# Martijn Schaafsma <qtlab@mcschaafsma.nl>, 2008
# Reinier Heeres <reinier@heeres.eu>, 2008
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

from instrument import Instrument
import types
import pyvisa.vpp43 as vpp43
from time import sleep
import logging
import numpy

class IVVIDIG_main(Instrument):
    '''
    This is the python driver for the IVVI-rack with S5a data module control

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'IVVIDIG', address='<ASRL address>')
    '''

    def __init__(self, name, address):
        '''
        Initialzes the IVVIDIG, and communicates with the wrapper

        Input:
            name (string)        : name of the instrument
            address (string)     : ASRL address
        Output:
            None
        '''
        logging.info(__name__ + ' : Initializing instrument IVVIDIG')
        Instrument.__init__(self, name, tags=['physical'])

        self._address = address

        #FIXME: numdacs is now variable!?
        self._numdacs = 16

        # Add functions
        #self.add_function('get_dac')
        self.add_function('set_dac')

        self._open_serial_connection()

    def __del__(self):
        '''
        Closes up the IVVI driver

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Deleting IVVI instrument')
        self._close_serial_connection()

    # open serial connection
    def _open_serial_connection(self):
        '''
        Opens the ASRL connection using vpp43
        baud=115200, databits=8, stop=one, parity=odd, no end char for reads

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Opening serial connection')
        self._session = vpp43.open_default_resource_manager()
        self._vi = vpp43.open(self._session, self._address)

        vpp43.set_attribute(self._vi, vpp43.VI_ATTR_ASRL_BAUD, 115200)
        vpp43.set_attribute(self._vi, vpp43.VI_ATTR_ASRL_DATA_BITS, 8)
        vpp43.set_attribute(self._vi, vpp43.VI_ATTR_ASRL_STOP_BITS,
            vpp43.VI_ASRL_STOP_ONE)
        vpp43.set_attribute(self._vi, vpp43.VI_ATTR_ASRL_PARITY,
            vpp43.VI_ASRL_PAR_ODD)
        vpp43.set_attribute(self._vi, vpp43.VI_ATTR_ASRL_END_IN,
            vpp43.VI_ASRL_END_NONE)

    # close serial connection
    def _close_serial_connection(self):
        '''
        Closes the serial connection

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Closing serial connection')
        vpp43.close(self._vi)

    def _empty_buffer(self):
        '''
        empty buffer of COM port
        '''
        logging.debug(__name__ + ' : do communication with instrument')
        data_out_string =  vpp43.read(self._vi, vpp43.get_attribute(self._vi, vpp43.VI_ATTR_ASRL_AVAIL_NUM))
        return data_out_string

    # Conversion of data
    def _mvoltage_to_bytes(self, mvoltage, dacrange):
        '''
        Converts a mvoltage on a 0mV-4000mV scale to a 16-bit integer equivalent
        output is a list of two bytes

        Input:
            mvoltage (float) : a mvoltage in the 0mV-4000mV range

        Output:
            (dataH, dataL) (int, int) : The high and low value byte equivalent
        '''
        logging.debug(__name__ + ' : Converting %f mVolts to bytes' % mvoltage)
        dr = dacrange[1] - dacrange[0]
        ds = dacrange[0]
        bytevalue = int(round((mvoltage-ds)*65535/dr))
        dataH = int(bytevalue/256)
        dataL = bytevalue - dataH*256
        return (dataH, dataL)

    def _bytes_to_mvoltage(self, bytes, dacrange):
        '''
        Converts a list of bytes to a list containing
        the corresponding mvoltages
        '''
        logging.debug(__name__ + ' : Converting bytes to mvoltages')
        dr = dacrange[1] - dacrange[0]
        ds = dacrange[0]
        value = ((bytes[0]*256 + bytes[1])/65535.0*dr) + ds
        return value

    # Communication with device
    def get_dac(self, channel, dacrange=(-2000, 2000)):
        '''
        Returns the value of the specified dac

        Input:
            channel (int) : 1 based index of the dac

        Output:
            voltage (float) : dacvalue in mV
        '''
        logging.debug(__name__ + ' : reading voltage from dac_%s' % channel)
        try:
            allbytes = self._get_dac_bytes()
            bytes = (allbytes[2*channel], allbytes[1+2*channel])
            mvoltage = self._bytes_to_mvoltage(bytes, dacrange)
            return mvoltage
        except IndexError as detail:
            print 'Error. Device might be disconnected: ',detail
    
    def get_dac_raw(self):
        '''
        Returns the values of all dacs in the binary format

        Input:

        Output:
            voltage (int) : array with dacvalues as binary numbers
        '''
        logging.debug(__name__ + ' : reading voltage from all dacs')
        try:
            allbytes = self._get_dac_bytes()
            return numpy.array(allbytes)
        except IndexError as detail:
            print 'Error. Device might be disconnected: ',detail
    
    def get_dac_all(self, dacrange=(-2000, 2000)):
        '''
        Returns the values of all dacs

        Input:

        Output:
            voltage (float) : array with dacvalues in mV
        '''
        logging.debug(__name__ + ' : reading voltage from all dacs')
        try:
            allbytes = self._get_dac_bytes()
            mvoltage=numpy.zeros(16)
            for channel in range(1,16) :
                bytes = (allbytes[2*channel], allbytes[1+2*channel])
                mvoltage[channel-1] = self._bytes_to_mvoltage(bytes, dacrange)
            return mvoltage
        except IndexError as detail:
            print 'Error. Device might be disconnected: ',detail

    def set_dac(self, channel, mvoltage, dacrange=(-2000, 2000)):
        '''
        Sets the specified dac to the specified voltage

        Input:
            mvoltage (float) : output voltage in mV
            channel (int)    : 1 based index of the dac

        Output:
            reply (string) : errormessage
        '''
        logging.debug(__name__ + ' : setting voltage of dac_%s to %.01f mV' % \
            (channel, mvoltage))
        (DataH, DataL) = self._mvoltage_to_bytes(mvoltage, dacrange)
        ###message = "%c%c%c%c%c%c%c%c" % (8, 0, 2, 1, 3, sl_ch, DataH, DataL)
        #print DataH,DataL
        message = "%c%c%c%c%c%c%c" % (7, 0, 2, 1, channel, DataH, DataL)
        try:
            reply = self._send_and_read(message)
        except IndexError as detail:
            print 'Error. Device might be disconnected: ',detail
            
        return reply
    
    def reset_dac(self, dacrange=(-2000, 2000)):
        '''
        Sets all dacs to 0 mV
        Attention: It is assumed that all dacs have the same dacrange

        Input:
        
        Output:
            reply (string) : errormessage
        '''
        try:
            logging.debug(__name__ + ' : setting voltage of all dacs to 0 mV')
            (DataH, DataL) = self._mvoltage_to_bytes(0, dacrange)
            ###message = "%c%c%c%c%c%c%c%c" % (8, 0, 2, 1, 3, sl_ch, DataH, DataL)
            for channel in range(1,16):
                message = "%c%c%c%c%c%c%c" % (7, 0, 2, 1, channel, DataH, DataL)
                reply = self._send_and_read(message)
            return reply
        except IndexError as detail:
            print 'Error. Device might be disconnected: ',detail

    def _get_dac_bytes(self):
        '''
        Reads from device and returns all dacvoltages in a list

        Input:
            None

        Output:
            voltages (float[]) : list containing all dacvoltages (in mV)
        '''
        logging.debug(__name__ + ' : getting dac voltages from instrument')
        ###message = "%c%c%c%c" % (4, 0, self._numdacs*2+2, 2)
        message = "%c%c%c%c" % (4, 0, 34, 2)
        reply = self._send_and_read(message)
        return reply

    def _send_and_read(self, message):
        '''
        Performs the communication with the device
        Raises an error if one occurred
        Returns a list of bytes

        Input:
            message (string)    : string conform the IVVI protocol

        Output:
            data_out_numbers (int[]) : return message
        '''
        logging.debug(__name__ + ' : do communication with instrument')
        vpp43.write(self._vi, message)
        sleep(0.1)
        data_out_string =  vpp43.read(self._vi, vpp43.get_attribute(self._vi, vpp43.VI_ATTR_ASRL_AVAIL_NUM))
        sleep(0.1)
        data_out_numbers = [ord(s) for s in data_out_string]

        if (data_out_numbers[1] != 0) or (len(data_out_numbers) != data_out_numbers[0]):
            logging.error(__name__ + ' : Error while reading : %s', data_out_numbers)

        return data_out_numbers

