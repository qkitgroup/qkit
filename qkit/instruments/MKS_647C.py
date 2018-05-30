# MKS MFC Controller 647C DEV version 1.0 written by HR/JB@KIT 10/2013
# Rewritten for qkit/evaporate/deposition service HR@KIT2018 
# Mass flow controller monitor/controller

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
import time,sys
import atexit
import logging
import numpy
import serial
from threading import Lock

class MKS_647C(Instrument):
    '''
    This is the driver for the Inficon Quarz Cristall Monitor

    Usage:
    Initialize with
    <name> = qkit.instruments.create('<name>', 'MKS_647C', address='<GBIP address>', reset=<bool>)
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the Keithley, and communicates with the wrapper.
        
        Input:
            name (string)    : name of the instrument
            address (string) : serial address
            reset (bool)     : resets to default values, default=False
        '''
        
        logging.info(__name__ + ': Initializing instrument MKS_647C')
        Instrument.__init__(self, name, tags=['physical'])
        
    
        self.predef_channels   = {"Ar":1, "N2":2, "O2":3, "ArO":4}
        self.predef_gasCorfact = {"Ar":"0137", "N2":"0100", "O2":"0100", "ArO":"0137"}
        self.predef_flowRange  = {"Ar":6, "N2":6, "O2":6, "ArO":3} # 100,100,100,10

        self.mutex = Lock()
        self.setup(address)

        
    def setup(self,address = "COM5"):
        #channel = channel
        baudrate = 9600
        timeout = 1
        # open serial port, 9600, 8,N,1, timeout 1s
        # address="/dev/tty.usbserial"       
        # Port A on the USB_to_serial converter, Port B ends with K
        # address = "/dev/cu.usbserial-FTK3DEL5A"
        # address = "/dev/ttyUSB3" 

        self.SerialPort = self._std_open(address,baudrate,timeout)
        atexit.register(self.SerialPort.close)
        
    def _std_open(self,device,baudrate,timeout):
        return serial.Serial(device, baudrate, timeout=timeout)
    def getSerialPort(self):
        return self.SerialPort
    def getMutex(self):
        return self.mutex

    def remote_cmd(self,cmd):
        # the 647C requires carriage return termination
        cmd += '\r'
        with self.mutex:
            self.SerialPort.write(cmd)
        
            time.sleep(0.2)   #increase from .1 to .2
            #value = self.ser.readline().strip("\x06")
            rem_char = self.SerialPort.inWaiting()
        
            value = self.SerialPort.read(rem_char) # .strip("\x06")
            time.sleep(0.2)   #to avoid wrong communication
            return value.strip()
        
        
        
    def getFlowSetPoint(self,channel):
    	cmd = "FS " + str(channel) +" R"
    	flow = self.remote_cmd(cmd)   #gives N2 flow #indent error?
    	return float(flow)/10*self.getGasCorrectionFactor(channel)

    def setFlowSetPoint(self,channel,value):
        cmd = "FS " + str(channel) + str(int(float(value)/self.getGasCorrectionFactor(channel)*10))
        return self.remote_cmd(cmd)   
    
    
    def getActualFlow(self,channel):
        cmd = "FL " + str(channel)
        flow = self.remote_cmd(cmd)   #gives N2 flow
        return float(flow)/10*self.getGasCorrectionFactor(channel)
    
    
    def getPressureSetPoint(self):
        cmd = "PS R"
        return self.remote_cmd(cmd)
    def setPressureSetPoint(self,value):
        # value in 0.1 percent of fullscale: 0..1100
        cmd = "PS "+str(value)
        return self.remote_cmd(cmd)    
    
    def getActualPressure(self):
        cmd = "PR"
        return self.remote_cmd(cmd)
        
    def getActualPCS(self):
        #check for PCS
        cmd = "PC"
        return self.remote_cmd(cmd)
    
    def setPressureMode(self,On = True):
        # On = 1 (Auto)
        # Off = 0
        if On:
            cmd = "PM 1"
        else:
            cmd = "PM 0"
        return self.remote_cmd(cmd)
    
    def PressureModeOn(self):
        cmd = "PM R"
        status = self.remote_cmd(cmd)
        if int(status) == 1:
            return True
        else:
            return False
        
    def setFlowRange(self,channel,value):
        """
        # most likely only 3 and 6 are used 
        0  = 1.000 SCCM 
        1  = 2.000 SCCM 
        2  = 5.000 SCCM 
        3  = 10.00 SCCM 
        4  = 20.00 SCCM 
        5  = 50.00 SCCM 
        6  = 100.0 SCCM 
        7  = 200.0 SCCM 
        8  = 500.0 SCCM 
        9  = 1.000 SLM
        10 = 2.000 SLM 
        11 = 5.000 SLM 
        12 = 10.00 SLM 
        13 = 20.00 SLM 
        14 = 50.00 SLM 
        15 = 100.0 SLM 
        16 = 200.0 SLM 
        17 = 400.0 SLM 
        18 = 500.0 SLM 
        19 = 1.000 SCMM 
        20 = 1.000 SCFH
        21 = 2.000 SCFH
        22 = 5.000 SCFH
        23 = 10.00 SCFH
        24 = 20.00 SCFH
        25 = 50.00 SCFH
        26 = 100.0 SCFH
        27 = 200.0 SCFH
        28 = 500.0 SCFH
        29 = 1.000 SCFM
        30 = 2.000 SCFM
        31 = 5.000 SCFM
        32 = 10.00 SCFM
        33 = 20.00 SCFM
        34 = 50.00 SCFM
        35 = 100.0 SCFM
        36 = 200.0 SCFM
        37 = 500.0 SCFM
        38 = 30.00 SLM
        39 = 300.0 SLM 
        
        """
        cmd = "RA "+str(channel)+" "+str(value)
        return self.remote_cmd(cmd)
        
    def setFlowRange10sccm(self,channel):
        return self.setFlowRange(channel,3)
        
    def setFlowRange100sccm(self,channel):
        return self.setFlowRange(channel,6)
    
    def getFlowRange(self,channel):
        # from manual,
        flows = [1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0, 500.0, 
                 1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0, 400.0, 500.0, 
                 1.0, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0, 500.0, 
                 1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0, 500.0, 30.0, 300.0]
        units = ['SCCM', 'SCCM', 'SCCM', 'SCCM', 'SCCM', 'SCCM', 'SCCM', 'SCCM', 'SCCM', 
                 'SLM', 'SLM ', 'SLM ', 'SLM ', 'SLM ', 'SLM ', 'SLM ', 'SLM ', 'SLM ', 'SLM ', 
                 'SCMM', 'SCFH', 'SCFH', 'SCFH', 'SCFH', 'SCFH', 'SCFH', 'SCFH', 'SCFH', 
                 'SCFH', 'SCFM', 'SCFM', 'SCFM', 'SCFM', 'SCFM', 'SCFM', 'SCFM', 'SCFM', 
                 'SCFM', 'SLM', 'SLM ']
        
        cmd = "RA "+str(channel)+" R"
        flownum = int(self.remote_cmd(cmd))
        return flows[flownum],units[flownum]
    
    def setGasCorrectionFactor(self,channel,factor):
    	#ffactor = "00" + str(factor).strip(".")
        cmd = "GC "+str(channel)+str(factor)
        return self.remote_cmd(cmd)
    
    def getGasCorrectionFactor(self,channel):
        cmd = "GC "+str(channel)+" R"
        res = self.remote_cmd(cmd)
	return float(res)/100
    
    def setMode(self,channel,mode = 0, master_channel = 0):
        """
        MO c m [i]channel
        c = 1..8 
        m = 0 mode = independent
        m = 1 mode = slave
        m = 2 mode = extern
        m = 3 mode = PCS
        m = 9 mode = test
        i = 1..8 modeindex, reference to master (only if m equal 1) 
        """
        if mode == 1:
            cmd = "MO "+ str(channel) +" 1 "+ str(master_channel)
        else:
            cmd = "MO "+ str(channel) +str(mode)
        return self.remote_cmd(cmd)

    def getMode(self,channel):
        master_channel = -1
        cmd = "GC "+str(channel)+" R"
        mode, master_channel = (self.remote_cmd(cmd)).split()
        return int(mode), int(master_channel)
    
    
    def setHighLimit(self,channel,l):   #in 0.1 percent: 0..1100
        cmd = "HL " + str(channel) + " " + str(l)
        return self.remote_cmd(cmd)
        
    def setLowLimit(self,channel,l):
        cmd = "LL " + str(channel) + " " + str(l)
        return self.remote_cmd(cmd)
        
    def getHighLimit(self,channel):   #in 0.1 percent: 0..1100
        cmd = "HL " + str(channel) + " R"
        return self.remote_cmd(cmd)
        
    def getLowLimit(self,channel):
        cmd = "LL " + str(channel) + " R"
        return self.remote_cmd(cmd)
    
    def setPressureUnit(self,pu = 13):
        cmd = "PU " + str(pu)
        return self.remote_cmd(cmd)
    """ 
    15: 1mbar
    13: 100ubar
    11: 1ubar
    """
    def getPressureUnit(self):
        cmd = "PU R"
        return self.remote_cmd(cmd)
        
    
    def setOnAll(self):
    	return self.remote_cmd("ON 0")
    def setOn(self,channel):
        return self.remote_cmd("ON " + str(channel))
    def setOffAll(self):
        return self.remote_cmd("OF 0")
    def setOff(self,channel):
        return self.remote_cmd("OF " + str(channel))
        
        
    def check_channelStatus(self,channel):
        return self.remote_cmd("ST " + str(channel))
        
    def setDefault(self):
        return self.remote_cmd("DF")
        
    def hardware_reset(self):
        return self.remote_cmd("RE")
        
    def getVersion(self):
        return self.remote_cmd("ID")
	 
    """
    # commands for setting values with the power supply
    
    def check_range(self,value,minval,maxval):
        if value < minval or value > maxval:
            print "value out of range error: " + str(value) + " " + str(minval) + " " + str(maxval)
            raise ValueError
        
    def setOn(self,ON = False):
        if ON:
            self.remote_cmd('A')        
        else:
            self.remote_cmd('B')            
	"""
   
    def init_controller(self):
        print ("Initializing controller...")
        self.setPressureUnit()
        for chan_name in self.predef_channels.keys():
            channel  = self.predef_channels[chan_name]
            self.setFlowSetPoint(channel,0)
            self.setFlowRange(channel,self.predef_flowRange[chan_name])
            self.setGasCorrectionFactor(channel,self.predef_gasCorfact[chan_name])

	"""
    channel = 1	#Argon
	self.setFlowSetPoint(channel,0)
	self.setFlowRange100sccm(channel)
	self.setGasCorrectionFactor(channel,"0137")

	channel = 2	#N2
	self.setFlowSetPoint(channel,0)
	self.setFlowRange100sccm(channel)
	self.setGasCorrectionFactor(channel,"0100")
	
	channel = 3	#O2
	self.setFlowSetPoint(channel,0)
	self.setFlowRange100sccm(channel)
	self.setGasCorrectionFactor(channel,"0100")
	
	channel = 4	#ArO2
	self.setFlowSetPoint(channel,0)
	self.setFlowRange10sccm(channel)
	self.setGasCorrectionFactor(channel,"0137") #1.12
	print("Done.")
    """
if __name__ == "__main__":

    MKS = MKS_647C("MKS",address= "COM6")
    #mutex = Ar.getMutex()
    #N2 = MKS647C_Dev(2,mutex)
    #O2 = MKS647C_Dev(3,mutex)
    #ArO = MKS647C_Dev(4,mutex)
    
    print("Setting off all",MKS.setOffAll())

    MKS.init_controller()
    """
    print "Version: ",Ar.getVersion()
    print Ar.getFlowSetPoint()
    print N2.getFlowSetPoint()
    print O2.getFlowSetPoint()
    print ArO.getFlowSetPoint()

    print Ar.getGasCorrectionFactor()
    print N2.getGasCorrectionFactor()
    
    print Ar.getActualFlow()
    print N2.getActualFlow()
    print O2.getActualFlow()
    print ArO.getActualFlow()
    
    print Ar.setFlowSetPoint(19)
    print N2.setFlowSetPoint(15)
    print O2.setFlowSetPoint(16)
    print ArO.setFlowSetPoint(7)
    
    time.sleep(1)
    
    print Ar.getFlowSetPoint()
    print N2.getFlowSetPoint()
    print O2.getFlowSetPoint()
    print ArO.getFlowSetPoint()
    
    print Ar.getFlowRange()
    print N2.getFlowRange()
    print O2.getFlowRange()
    print ArO.getFlowRange()
    
    print Ar.getActualPressure()
    
    print Ar.setFlowRange100sccm()
    print N2.setFlowRange10sccm()
    print O2.setFlowRange100sccm()
    print ArO.setFlowRange10sccm()
    
    print Ar.getFlowSetPoint()
    print N2.getFlowSetPoint()
    print O2.getFlowSetPoint()
    print ArO.getFlowSetPoint()
    
    print Ar.getGasCorrectionFactor()
    print Ar.setGasCorrectionFactor("0120")
    print Ar.getGasCorrectionFactor()
    
    print Ar.getPressureUnit()
    """
