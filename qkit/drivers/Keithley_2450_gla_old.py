# filename: Keithley_2450.py
# version 0.1 written by 
# QKIT driver for a Keithley Multimeter 2450



import qkit
from qkit.core.instrument_base import Instrument

from qkit import visa 

import logging
import numpy
import time,sys
import atexit
#import serial #used for GPIB connections

class Keithley_2450_gla(Instrument):
    '''
    This is the driver for the Keithley 2450 Source Meter
    Set ip address manually on instrument, e.g. TCPIP::10.22.197.50::5025::SOCKET
    Usage:
    Initialize with
    <name> = qkit.instruments.create('<name>', 'Keithley_2450', address='<IP address>', reset=<bool>)
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the Keithley, and communicates with the wrapper.
        
        Input:
            name (string)    : name of the instrument
            address (string) : IP address
            reset (bool)     : resets to default values, default=False
        '''
        # Start VISA communication
        logging.info(__name__ + ': Initializing instrument Keithley 2450')
        Instrument.__init__(self, name, tags=['physical'])
        self._address = address
        self._visainstrument = visa.instrument(self._address)
        self._visainstrument.read_termination="\n"
        self._visainstrument.timeout = 5000
        self._rvol = 1
        self.rvc_mode   = False #resistance via current
        self.four_wire  = False
        #self.setup(address) #used for GPIB connections

    #def setup(self, device="COM1"):
     #   baudrate = 9600
     #   timeout = None #0.1
        
     #   self.ser = self._std_open(device,baudrate,timeout)
     #   atexit.register(self.ser.close)
        
    #def _std_open(self,device,baudrate,timeout):
        # open serial port, 9600, 8,N,1, timeout 0.1
      #  return serial.Serial(device, baudrate, timeout=timeout)
 

    # def remote_cmd(self, cmd):
    #     cmd += "\r"

    #     # clear queue first, old data,etc
    #     rem_char = self.ser.inWaiting()
    #     if rem_char:
    #         self.ser.read(rem_char)
        
    #     # send command
    #     self.ser.write(str.encode(cmd))
    #     # wait until data is processed
    #     time.sleep(1)
    #     # read back
    #     rem_char = self.ser.inWaiting()
        
    #     retval = self.ser.read(rem_char)
    #     #print(retval)
    #     return retval #str(retval)#.strip('\r')

    def reset(self):
        '''
        Resets the instrument to default values

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : resetting instrument')
        self._visainstrument.write('*RST')
        #self.get_all()     
    
    # def get_current_dc(self):   #Return DC Current in auto-range
    #     value = self.remote_cmd(":MEAS:CURR:DC?")
    #     try:
    #         return float(value)
    #     except Exception as m:
    #         print(m)
    #         return 

    def get_current_dc(self):   #Return DC Current in auto-range
        value = self._visainstrument.query(":MEAS:CURR:DC?")
        try:
            return float(value)
        except Exception as m:
            print(m)
            return         
    
    def get_voltage_dc(self):   #Return DC Current in auto-range
        value = self._visainstrument.query(":MEAS:VOLT:DC?")
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
                
    def get_data(self, startindex, endindex):
        '''Ending index of the buffer has to be specified'''
        try:
            ret = self._visainstrument.query(":TRACe:DATA? {}, {}".format(startindex,endindex))
            return float(ret)
        except ValueError as e:
            print(e)
            print(ret)
            return numpy.NaN        

    def get_resistance_2W(self):
        try:
            self._visainstrument.write(":OUTP ON")
            ret = self._visainstrument.query(":MEAS:RES?")
            self._visainstrument.write(":OUTP OFF")
            return float(ret)
            
        except ValueError as e:
            print(e)
            print(ret)
            return numpy.NaN

    def get_resistance_4W(self):
        try:
            self._visainstrument.write(":OUTP ON")
            ret = self._visainstrument.query(":MEAS:RES?")
            self._visainstrument.write(":OUTP OFF")
            return float(ret)
        except ValueError as e:
            print(e)
            print(ret)
            return numpy.NaN

    def set_measure_4W(self,four_wire):
        ''' Sets 2 or 4 wire measurement mode '''
        self.four_wire = four_wire
        
    # def set_resistance_via_current(self, status):
    #     self.rvc_mode = status
    #     self._visainstrument.write(str.encode(":SENS:CURR \r"))  
    #     self._visainstrument.write(str.encode(":SENS:CURR:DC:RANG:AUTO OFF \r"))
    #     self._visainstrument.write(str.encode(":SENS:CURR:DC:RANG 1e-3 \r"))

    def set_resistance_via_current(self, status):
        self.rvc_mode = status
        self._visainstrument.write(":SENS:FUNC:CURR")  
        self._visainstrument.write(":SENS:CURR:DC:RANG:AUTO OFF")
        self._visainstrument.write(":SENS:CURR:DC:RANG 1e-3")

    def set_reverence_voltage(self, voltage):
        self._rvol = voltage
        
    # def set_current_range(self, range_value):
    #     if 1e-3 <= range_value <= 1:
    #         self._visainstrument.write(str.encode(":CURR:DC:RANG %.04f \r"%(range_value)))
    #     else:
    #         print("Range must be decimal power of 10 between 1A and 10mA")

    def set_current_range(self, range_value):
        self._visainstrument.write(":SENS:CURR:RANG {}".format(range_value))

    def set_output(self, output):
        if output:
            self._visainstrument.write(":OUTP ON")
        else:
            self._visainstrument.write(":OUTP OFF")

    def set_voltage_source(self, volt):
        #self._visainstrument.write("SENS:FUNC 'CURR'") 
        self._visainstrument.write("SOUR:FUNC VOLT")
        self._visainstrument.write("SOUR:VOLT {}".format(volt))

    def set_current_source(self, curr):
        #self._visainstrument.write("SENS:FUNC 'VOLT'")
        self._visainstrument.write("SOUR:FUNC CURR")
        self._visainstrument.write("SOUR:CURR {}".format(curr))

    def set_voltage_range(self, range_value):
        self._visainstrument.write(":SENS:VOLT:RANG {}".format(range_value))

    def set_current_range_auto(self, auto):
        if auto:
            self._visainstrument.write(":SENS:CURR:RANG:AUTO ON")
        else:
            self._visainstrument.write(":SENS:CURR:RANG:AUTO OFF")

    def set_voltage_range_auto(self, auto):
        if auto:
            self._visainstrument.write(":SENS:VOLT:RANG:AUTO ON")
        else:
            self._visainstrument.write(":SENS:VOLT:RANG:AUTO OFF")
              
    #def set_test(self):
     #   self._visainstrument.write("*RST")
      #  self._visainstrument.write("SENS:FUNC "VOLT"")
	
if __name__ == "__main__":
    KEITH = Keithley_2450(name = "Keithley_2450", address="10.22.197.8")
    print("DC current: {:.4g}A".format(KEITH.get_current_dc()))
