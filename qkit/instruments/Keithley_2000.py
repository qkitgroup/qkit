# filename: keithley 2000.py
# version 0.1 written by JB,JNV, HR@KIT 2017-
# QKIT driver for a Keithley Multimeter 2000 

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


import qkit
from qkit.core.instrument_base import Instrument

import logging
import numpy
import time,sys
import atexit
import serial

class Keithley_2000(Instrument):
    '''
    This is the driver for the Keithley 2636A Source Meter

    Usage:
    Initialize with
    <name> = qkit.instruments.create('<name>', 'Keithley', address='<GBIP address>', reset=<bool>)
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the Keithley, and communicates with the wrapper.
        
        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address
            reset (bool)     : resets to default values, default=False
        '''
        # Start VISA communication
        logging.info(__name__ + ': Initializing instrument Keithley 2000')
        Instrument.__init__(self, name, tags=['physical'])
        #self._address = address
        
        self.setup(address)

    def setup(self,device="/dev/ttyUSB7"):

        baudrate = 9600
        timeout = 0.1
        
        self.ser = self._std_open(device,baudrate,timeout)
        atexit.register(self.ser.close)
        
    def _std_open(self,device,baudrate,timeout):
        
        # open serial port, 9600, 8,N,1, timeout 0.1
        return serial.Serial(device, baudrate, timeout=timeout)
        
    def remote_cmd(self,cmd):
        cmd+="\r"

        # clear queue first, old data,etc
        rem_char = self.ser.inWaiting()
        if rem_char:
            self.ser.read(rem_char)
        
        # send command
        self.ser.write(cmd)
        # wait until data is processed
        time.sleep(1)
        # read back
        rem_char = self.ser.inWaiting()
        return self.ser.read(rem_char).strip('\r')
    
    def get_current_dc(self):
        value = self.remote_cmd(":MEAS:CURR:DC?")
        try:
            return float(value)
        except Exception as m:
            print m
            return 0


    def get_resistance(self):
        return float(self.remote_cmd(":MEAS:RES?"))



if __name__ == "__main__":
    k = Keithley_2000(name = "rmes", address="COM3")
    print "DC current: {:.4g}A".format(k.get_current_dc())
