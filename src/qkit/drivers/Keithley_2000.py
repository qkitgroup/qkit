# filename: Keithley_2000.py
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
    This is the driver for the Keithley 2000 Source Meter

    Usage:
    Initialize with
    <name> = qkit.instruments.create('<name>', 'Keithley_2000', address='<GBIP address>', reset=<bool>)
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
        
        self._rvol = 1
        self.rvc_mode   = False
        self.four_wire  = False
        self.setup(address)

    def setup(self, device="/dev/ttyUSB7"):
        baudrate = 9600
        timeout = 0.1
        
        self.ser = self._std_open(device,baudrate,timeout)
        atexit.register(self.ser.close)
        
    def _std_open(self,device,baudrate,timeout):
        # open serial port, 9600, 8,N,1, timeout 0.1
        return serial.Serial(device, baudrate, timeout=timeout)
        
    def remote_cmd(self, cmd):
        cmd += "\r"

        # clear queue first, old data,etc
        rem_char = self.ser.inWaiting()
        if rem_char:
            self.ser.read(rem_char)
        
        # send command
        self.ser.write(str.encode(cmd))
        # wait until data is processed
        time.sleep(1)
        # read back
        rem_char = self.ser.inWaiting()
        
        retval = self.ser.read(rem_char)
        #print(retval)
        return retval #str(retval)#.strip('\r')
    
    def get_current_dc(self):   #Return DC Current in auto-range
        value = self.remote_cmd(":MEAS:CURR:DC?")
        try:
            return float(value)
        except Exception as m:
            print(m)
            return 

    def get_resistance(self):
        if self.rvc_mode:
            return self._rvol/self.get_data()
        else:
            if self.four_wire:
                return self.get_resistance_4W()
            else:
                return self.get_resistance_2W()
                
    def get_data(self):
        try:
            ret = self.remote_cmd(":DATA?")
            return float(ret)
        except ValueError as e:
            print(e)
            print(ret)
            return numpy.NaN        

    def get_resistance_2W(self):
        try:
            ret = self.remote_cmd(":MEAS:RES?")
            return float(ret)
        except ValueError as e:
            print(e)
            print(ret)
            return numpy.NaN

    def get_resistance_4W(self):
        try:
            ret = self.remote_cmd(":MEAS:FRES?")
            return float(ret)
        except ValueError as e:
            print(e)
            print(ret)
            return numpy.NaN

    def set_measure_4W(self,four_wire):
        ''' Sets 2 or 4 wire measurement mode '''
        self.four_wire = four_wire
        
    def set_resistance_via_current(self, status):
        self.rvc_mode = status
        self.ser.write(str.encode(":FUNC 'CURR:DC' \r"))
        self.ser.write(str.encode(":CURR:DC:RANG:AUTO OFF \r"))
        self.ser.write(str.encode(":CURR:DC:RANG 1e-3 \r"))

    def set_reverence_voltage(self, voltage):
        self._rvol = voltage
        
    def set_current_range(self, range_value):
        if 1e-3 <= range_value <= 1:
            self.ser.write(str.encode(":CURR:DC:RANG %.04f \r"%(range_value)))
        else:
            print("Range must be decimal power of 10 between 1A and 10mA")

if __name__ == "__main__":
    KEITH = Keithley_2000(name = "Keithley_2000", address="COM6")
    print("DC current: {:.4g}A".format(KEITH.get_current_dc()))
