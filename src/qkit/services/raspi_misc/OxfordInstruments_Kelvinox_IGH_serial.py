# OxfordInstruments_Kelvinox_IGH.py class, to perform the communication between the Wrapper and the device
# Guenevere Prawiroatmodjo <guen@vvtp.tudelft.nl>, 2009
# Pieter de Groot <pieterdegroot@gmail.com>, 2009
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

import sys
import time
import numpy as np
import serial


class OxfordInstruments_Kelvinox_IGH_serial(object):

    '''
    This is the python driver for the Oxford Instruments Kelvinox IGH Dilution Refrigerator and
    Intelligent Dilution Refrigerator Power Supply (IDR PS).

    Note: Since the ISOBUS allows for several instruments to be managed in parallel, the command
    which is sent to the device starts with '@n', where n is the ISOBUS instrument number.
    '''

#TODO: auto update script
#TODO: get doesn't always update the wrapper! (e.g. when input is an int and output is a string)

    def __init__(self, device='/dev/ttyUSB0'): 

        '''
        Initializes the Oxford Instruments Kelvinox IGH Dilution Refrigerator.

        Input:
            optional device (string)     :  '/dev/ttyUSB1'

        Output:
            None
        '''

        self.ser = serial.Serial(device, 9600, timeout=1)

    def remote_cmd(self, cmd):
		
        cmd += '\r\n'
        self.ser.write(cmd)
        time.sleep(0.3)
        rem_char = self.ser.inWaiting()
        value = self.ser.read(rem_char)
        value = value.replace('\xffR','',)
        value = value.replace('+','')
        value = value.replace('\r','')
	
        return value

###### TODO

    def identify(self):
        '''
        Identify the device

        Input:
            None
        Output:
            None
        '''
        #return self._execute('V')

    def remote(self):
        '''
        Set control to remote & unlocked

        Input:
            None
        Output:
            None
        '''
        # Set control to local & locked
        #self.set_remote_status(3)

    def local(self):
        '''
        Set control to local & locked

        Input:
            None
        Output:
            None
        '''
        # Set control to local & locked
        #self.set_remote_status(0)

    def set_remote_status(self, mode):
        '''
        Set remote control status.

        Input:
            mode(int) :
            0 : "Local and locked",
            1 : "Remote and locked",
            2 : "Local and unlocked",
            3 : "Remote and unlocked",

        Output:
            None
        '''
        
		#status = {
        #0 : "Local and locked",
        #1 : "Remote and locked",
        #2 : "Local and unlocked",
        #3 : "Remote and unlocked",
        #}
        #self._execute('C%s' % mode)

############

    def get_1K_pot_temp(self):

        '''
        Get 1K Pot Temperature from device.
        Input:
            None

        Output:
            result (float) : 1K Pot Temperature in mK
        '''
        result = self.remote_cmd("R2")
	
	try:
	    return float(result)
	except ValueError:
	    return 0.0

    def get_mix_chamber_temp(self):

        '''
        Get Mix Chamber Temperature
        Input:
            None
        Output:
            result (float) : Mix Chamber Temperature in mK
        '''
        result = self.remote_cmd("R3")
	
	try:
	    return float(result)
	except ValueError:
	    return 0.0

    def get_G1(self):
        '''
        Get Pressure G1
        Input:
            None

        Output:
            result (float) : G1 Pressure in mBar
        '''
        result = self.remote_cmd("R14")
	
	try:
	    return float(result)
	except ValueError:
	    return 0.0

    def get_G2(self):
        '''
        Get Pressure G2
        Input:
            None

        Output:
            result (float) : G2 Pressure in mBar
        '''
        result = self.remote_cmd("R15")
	
	try:
	    return float(result)
	except ValueError:
	    return 0.0

    def get_G3(self):
        '''
        Get Pressure G3
        Input:
            None

        Output:
            result (float) : G3 Pressure in mBar
        '''
        result = self.remote_cmd("R16")
	
	try:
	    return float(result)
	except ValueError:
	    return 0.0

    def get_P1(self):
        '''
        Get Pressure P1
        Input:
            Non

        Output:
            result (float) : P1 Pressure in mBar
        '''
        result = self.remote_cmd("R20")
	
	try:
	    return float(result)
	except ValueError:
	    return 0.0















