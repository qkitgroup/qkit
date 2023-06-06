# EdwardsActiveDigitalController by JB@KIT 09/2014
# USB interface for Edwards Controller
# modified for using with Raspberry Pi 03/2015
# pressure readout device @ UFO: G1, G2
# model: D39591000 (enhanced)

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

import numpy as np
import time,sys
import atexit
import serial

class Edwards_p_gauge(object):
        
    def __init__(self, device='/dev/ttyUSB1'):
    
        #Instrument.__init__(self, name, tags=['physical'])
        '''
        self.add_parameter('condenser_pressure',
            type=types.FloatType,
            flags=Instrument.FLAG_GET, units='mbar')
        self.add_parameter('still_pressure',
            type=types.FloatType,
            flags=Instrument.FLAG_GET, units='mbar')
        '''
        # open serial port, 9600, 8,N,1, timeout 1s
        #device = address   #"COM4"
        baudrate = 9600
        timeout = 1
        # Port B on the USB_to_serial converter
        #device = "/dev/ttyUSB1"
        self.ser = self._std_open(device,baudrate,timeout)
        atexit.register(self.ser.close)
        
    def serial_close(self):
        self.ser.close()
        
    def _std_open(self,device,baudrate,timeout):
        return serial.Serial(device, baudrate, timeout=timeout)
                
    def remote_cmd(self,cmd):
        cmd+='\r\n'
        time.sleep(0.3)
        self.ser.write(cmd)
        
        time.sleep(0.5)   #wait 0.5s
        #value = self.ser.readline().strip("\x06")
        rem_char = self.ser.inWaiting()
        
        value = self.ser.read(rem_char) # .strip("\x06")
        #print "##"+value.strip()+"###"
        try:
            return float(value.strip())
        except Exception as m:
            print m, value.strip()
            return 0

    #read out status
    def get_condenser_pressure(self):
        try:
            return self.remote_cmd("?GA1")
        except Exception as detail:
            print "Error: ",detail
            return 0
            
    def get_still_pressure(self):
        try:
            return self.remote_cmd("?GA2")
        except Exception as detail:
            print "Error: ",detail
            return 0
    
    def get_all(self):
        return self.get_condenser_pressure(), self.get_still_pressure()

if __name__ == "__main__":   #if executed as main (and not imported)
    time.sleep(0.1) 
    rd = Edwards_p_gauge()
    print str(rd.get_all())
 