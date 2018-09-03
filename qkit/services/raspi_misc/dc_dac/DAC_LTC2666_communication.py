#!/usr/bin/env python2
# DAC_LTC2666_communication.py by JB@KIT 01/2018

'''
Communication script between Raspberry Pi and DAC Board based on SPI commands. Requires the python package spidev 
installed on the Raspberry.
Raspberry Pi 3 model pin configuration: MOSI: 19, MISO: 21, SCLK: 23, Chip select CE0: 24 (in use with dac0), CE1: 26 (dac1). 
DAC model: LTC2666-16. 

Internal reference: REF floating, RD bit = 0.

The SPI communication can be performed with a 24bit word or alternatively with a 32bit word, 
both of which allowing for echo readback verifying data transfer. 
At present, the 24bit variant is implemented.
'''

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

import time,sys
import logging

import spidev

def bytes_from_nibbles(nibbles):
    '''
    Combine a list of 6 nibbles (1 nibble = 4bit) into a 24bit load sequence, consisting out of a list of 3 bytes.
    '''
    if len(nibbles) != 6: raise ValueError
    return [(nibbles[0]<<4)+nibbles[1],(nibbles[2]<<4)+nibbles[3],(nibbles[4]<<4)+nibbles[5]]
    

class DAC_LTC2666(object):
    '''
    SPI communication class. Objects are 8-channel DAC boards.
    '''
    def __init__(self, cs = 0, word32 = False):
        '''
        Inputs:
        - cs: chip select connection
        - word32: switch to the 32bit version by passing 'True', default: 24bit
        '''
        self.word32 = word32
    
        self.SPIBUS = cs   #chip select
        self.spi = spidev.SpiDev()
        self.spi.open(0,self.SPIBUS)
        
        self.init()
        
    def verify_connection(self):
        ''' send no operation command and validate the echo readback '''
        if not self.word32: logging.warning("Currently, the SPI communication is set up with a 24bit word. Echo readback possibly not supported.")
        no_op = bytes_from_nibbles([15,0,0,0,0,0])
        self.write(no_op)
        if self.write(no_op) == no_op:
            return True
        else:
            return False
        
    def init(self):
        '''
        Initializes to internal reference. 
        Currently, all channels are used with +-5V output span, which does not have to be set when 
        using a correct MSP jumper setting.
        '''
        #set to internal reference mode
        self.write(bytes_from_nibbles([7,0,0,0,0,0]))
        
        #set all channels to +- 5V output span, not needed when MSP jumpers correctly set
        #for i in range(8):
        #    self.spi.xfer(bytes_from_nibbles([6,i,0,0,0,2])
        
        #self.verify_connection()
        
    def write(self, byte_arr):
        '''
        Generic SPI write command. Returns the SPI echo readback.
        '''
        if self.word32:
            return self.spi.xfer([0]+byte_arr)
        else:
            return self.spi.xfer2(byte_arr)   #write value in input register
        
    def update_output(self,channel):
        '''
        Update output according to input register. Used to acknowledge the previous command, which is returned.
        '''
        return self.write(bytes_from_nibbles([1,channel,0,0,0,0]))

    def set_val(self, channel, val):
        '''
        Set value in 0..2**16-1, 16bit resolution.
        Returns True for successful readback, returns False if an error occurred in the readback.
        '''
        byte_arr = bytes_from_nibbles([0,channel,(val>>12) & 15,(val>>8) & 15,(val>>4) & 15,val & 15])
        self.write(byte_arr)
        #echo readback delivers the previous input word and can be used to verify data transfer
        readback = self.update_output(channel)
        if readback == byte_arr:
            return True
        else:
            logging.error("{:s}: SPI communication not acknowledged.".format(__name__))
            return False

    def set_voltage(self, channel, voltage):
        '''
        Set voltage in range -5V..5V, using self.set_val(...).
        '''
        val = int((voltage+5.)/10*2**16)
        if val < 0 or val >= 2**16:
            logging.error("{:s}: Value to be set out of range.".format(__name__))
            return False
        else:
            return self.set_val(channel,val)

                

if __name__ == "__main__":   #if executed as main (and not imported)
    time.sleep(0.1) 
    
    dac = DAC_LTC2666(cs = 0)
    if dac.verify_connection():
        for ch in range(8):
            dac.set_voltage(ch,0)
        print 'ok'
    else: print 'Connection not valid.'
 