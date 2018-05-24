# Inficon version 0.1 written by HR@KIT 2012,2018
# updates 05/2017 (JB)

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


import time,sys
import atexit


class Inficon(Instrument):
    '''
    This is the driver for the Inficon Quarz Cristall Monitor

    Usage:
    Initialize with
    <name> = qkit.instruments.create('<name>', 'Inficon', address='<GBIP address>', reset=<bool>)
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the Keithley, and communicates with the wrapper.
        
        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address
            reset (bool)     : resets to default values, default=False
        '''
        
        logging.info(__name__ + ': Initializing instrument Inficon')
        Instrument.__init__(self, name, tags=['physical'])
        #self._address = address
        
        self.setup(address)


    class inficon_cmds(object):
        ack="\x06"
        #ack=" \x06"
        get_hello="H"+ack
        get_rate="S 1"+ack
        get_thickness="S 2"+ack
        get_time="S 3"+ack
        get_film="S 4"+ack
        get_xtal_live="S 5"+ack
        set_thickness_zero = "R 4"+ack
        set_timer_zero = "R 5"+ack
        
    def setup(self,device="/dev/ttyUSB6"):
        # open serial port, 9600, 8,N,1, timeout 1s
        #device="/dev/tty.usbserial"
        baudrate = 9600
        timeout = 0.1
        self.ack = "\x06"

        # Port A on the USB_to_serial converter, Port B ends with K
        #device = "/dev/tty.usbserial-FTB4J8SC"
        #device = "/dev/ttyUSB0" 
        self.ser = self._std_open(device,baudrate,timeout)
        atexit.register(self.ser.close)
  
        
        # load inficon comands
        self.cmds = self.inficon_cmds()
        
    def _std_open(self,device,baudrate,timeout):
        return serial.Serial(device, baudrate, timeout=timeout)
        
        
    def remote_cmd(self,cmd):
        self.ser.write(cmd)
        
        time.sleep(0.1)
        #value = self.ser.readline().strip("\x06")
        rem_char = self.ser.inWaiting()
        
        value = self.ser.read(rem_char).strip(self.ack)
        #print "##"+value+"##"+value.strip()+"###"
        return value #value.strip()
    
    def get_hello(self):
        return self.remote_cmd(self.cmds.get_hello)
    def get_rate(self, nm=False):
        rate = float(self.remote_cmd(self.cmds.get_rate))
        if nm:
            #return rate in nm
            return rate/10.
        else:
            # return rate in A (10^-10m)
            return rate

    def get_thickness(self, nm=False):
        thickness = float(self.remote_cmd(self.cmds.get_thickness))
        if nm:
            # return thickness in nm
            return thickness*100.
        else:
            # return thickness in kA (10^-7m)
            return thickness
        
if __name__ == "__main__":
    rd=Inficon("rd",address="COM5")
    #print rd.getHello()
    print 'Rate:',rd.get_rate()
    print 'Thickness:',rd.get_thickness()
