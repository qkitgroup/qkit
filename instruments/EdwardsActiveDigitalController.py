# EdwardsActiveDigitalController by JB@KIT 09/2014
# pressure readout device @ UFO: G1, G2
# model: D39591000 (enhanced)

from instrument import Instrument
import instruments
import types
import logging
import numpy as np
import time,sys
import atexit
import serial

class EdwardsActiveDigitalController(Instrument):
        
    def __init__(self, name, address):
    
        Instrument.__init__(self, name, tags=['physical'])
        # open serial port, 9600, 8,N,1, timeout 1s
        device = address   #"COM4"
        baudrate = 9600
        timeout = 1
        # Port B on the USB_to_serial converter
        #device = "/dev/ttyUSB1" 
        self.ser = self._std_open(device,baudrate,timeout)
        atexit.register(self.ser.close)
        
    def _std_open(self,device,baudrate,timeout):
        return serial.Serial(device, baudrate, timeout=timeout)
                
    def remote_cmd(self,cmd):
	cmd+='\n'
        self.ser.write(cmd)
        
        time.sleep(1)    #wait 0.5s
        #value = self.ser.readline().strip("\x06")
        rem_char = self.ser.inWaiting()
        
        value = self.ser.read(rem_char) # .strip("\x06")
        print "##"+value+"##"+value.strip()+"###"
        return value #.strip()
     
           
    #read out status
    def getGaugePressure(self):
        try:
            return self.remote_cmd("?GA")
        except Exception as detail:
            print "Error: ",detail
            return 0
    
    

if __name__ == "__main__":   #if executed as main (and not imported)
    time.sleep(1) 
    rd = EdwardsActiveDigitalController()
 