# MKS MFC Controller 647C DEV version 1.0 written by HR/JB@KIT 10/2013
# Rewritten for qkit/evaporate/deposition service HR,YS@KIT2018
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

import logging

import serial
import time,sys
import atexit

from threading import Lock


class MKS_647C(Instrument):
    """
    This is the driver for the Inficon Quarz Cristall Monitor

    Usage:
    Initialize with
    <name> = qkit.instruments.create('<name>', 'MKS_647C', address='<GBIP address>', reset=<bool>)
    """

    def __init__(self, name, address, reset=False):
        """
        Initializes the Keithley, and communicates with the wrapper.
        
        Input:
            name (string)    : name of the instrument
            address (string) : serial address
            reset (bool)     : resets to default values, default=False
        """
        
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

    """
    INSTRUMENT SETUP
    """
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
        print ("Initializing controller...")
        self.setPressureUnit()
        for chan_name in self.predef_channels.keys():
            channel = self.predef_channels[chan_name]
            self.setFlowSetPoint(channel, 0)
            self.setFlowRange(channel, self.predef_flowRange[chan_name])
            self.setGasCorrectionFactor(channel, self.predef_gasCorfact[chan_name])

    """
    CHANNEL SETUP
    """
    def set_mode(self, channel, mode=0, master_channel=0):
        """
        The Mode Selection defines the source of setpoint for each MFC channel. Possible modes are:
            - INDEP = independent
            - SLAVE = dependent to the actual flow of another channel
            - EXTERN = external source for setpoint
            - PCS = external controller
            - PID = built in PID controller
            - TEST = test for maintenance and installation
        (old name: setMode)

        Args:
            channel: Channel to be set.
            mode: Which mode to set
                0 = independent
                1 = slave
                2 = extern
                3 = PCS
                9 = test
            master_channel: Which channel to use as master in slave mode (1).
        """
        if mode == 1:
            cmd = "MO " + str(channel) + " 1 " + str(master_channel)
        else:
            cmd = "MO " + str(channel) + str(mode)
        return self.remote_cmd(cmd)

    def get_mode(self, channel):
        """
        Check for mode.
        (old name: getMode)

        Args:
            channel: Channel to be checked.

        Returns:
            mode, master channel
        """
        master_channel = -1
        cmd = "MO "+str(channel)+" R"
        mode, master_channel = (self.remote_cmd(cmd)).split()
        return int(mode), int(master_channel)

    def setGasCorrectionFactor(self, channel, factor):
        # TODO: Check the correct values for the used gasses and set automatically. (see init_controller)
        # ffactor = "00" + str(factor).strip(".")
        cmd = "GC " + str(channel) + str(factor)
        return self.remote_cmd(cmd)

    def getGasCorrectionFactor(self, channel):
        cmd = "GC " + str(channel) + " R"
        res = self.remote_cmd(cmd)
        # TODO: Check unit, why /100?
        return float(res) / 100

    def set_flow_range(self, channel, value):
        """
        Set flow range for a channel.
        (old name: setFlowRange)

        Note:
            Most likely only 3 and 6 are used.

        Args:
            channel: Channel for which the flow range is to be set.
            value: 0..39
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
        cmd = "RA " + str(channel) + " " + str(value)
        return self.remote_cmd(cmd)

    def set_flow_range_10sccm(self, channel):
        """
        Set flow range for a channel to 10 sccm.
        (old name: setFlowRange10sccm)

        Args:
            channel: Channel for which the flow range is to be set.
        """
        return self.set_flow_range(channel, 3)

    def set_flow_range_100sccm(self, channel):
        """
        Set flow range for a channel to 100 sccm.
        (old name: setFlowRange100sccm)

        Args:
            channel: Channel for which the flow range is to be set.
        """
        return self.set_flow_range(channel, 6)

    def get_flow_range(self, channel):
        """
        Check flow range of a channel.
        (old name: getFlowRange)

        Args:
            channel: Channel for which the flow range is to be checked.

        Reeturns:
            Flow range of the channel.
        """
        flows = [1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0, 500.0,
                 1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0, 400.0, 500.0,
                 1.0, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0, 500.0,
                 1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0, 500.0, 30.0, 300.0]
        units = ['SCCM', 'SCCM', 'SCCM', 'SCCM', 'SCCM', 'SCCM', 'SCCM', 'SCCM', 'SCCM',
                 'SLM', 'SLM ', 'SLM ', 'SLM ', 'SLM ', 'SLM ', 'SLM ', 'SLM ', 'SLM ', 'SLM ',
                 'SCMM', 'SCFH', 'SCFH', 'SCFH', 'SCFH', 'SCFH', 'SCFH', 'SCFH', 'SCFH',
                 'SCFH', 'SCFM', 'SCFM', 'SCFM', 'SCFM', 'SCFM', 'SCFM', 'SCFM', 'SCFM',
                 'SCFM', 'SLM', 'SLM ']

        cmd = "RA " + str(channel) + " R"
        flownum = int(self.remote_cmd(cmd))
        return flows[flownum], units[flownum]

    def set_high_limit(self, channel, limit):   #in 0.1 percent: 0..1100
        """
        Set an upper limit for the flow of a channel.
        (old name: setHighLimit)

        Args:
            channel: Channel for which the limit is to be set.
            limit: The limit to be set in 0.1 percent of full scale.
        """
        cmd = "HL " + str(channel) + " " + str(limit)
        return self.remote_cmd(cmd)

    def get_high_limit(self, channel):  # in 0.1 percent: 0..1100
        """
        Check for upper flow limit of a channel.
        (old name: getHighLimit)

        Args:
            channel: Channel for which the limit is to be checked.

        Returns:
            The set upper limit of the channel.
        """
        cmd = "HL " + str(channel) + " R"
        return self.remote_cmd(cmd)

    def set_low_limit(self, channel, limit):
        """
        Set a lower limit for the flow of a channel.
        (old name: setLowLimit)

        Args:
            channel: Channel for which the limit is to be set.
            limit: The limit to be set in 0.1 percent of full scale.
        """
        cmd = "LL " + str(channel) + " " + str(limit)
        return self.remote_cmd(cmd)
        
    def get_low_limit(self,channel):
        """
        Check for lower flow limit of a channel.
        (old name: getLowLimit)

        Args:
            channel: Channel for which the limit is to be checked.

        Returns:
            The set lower limit of the channel.
        """
        cmd = "LL " + str(channel) + " R"
        return self.remote_cmd(cmd)

    """
    PROCESS
    """
    def set_on_all(self):
        """
        Open main valve.
        (old name: setOnAll)

        Note:
            The channels in use have to be additionally turned on individually.
        """
        return self.remote_cmd("ON 0")

    def set_on(self, channel):
        """
        Open valve for a given channel.
        (old name: setOn)

        Note:
            The main valve has to be turned on separately by set_on_all.

        Args:
            channel: Channel to be turned on.
        """
        return self.remote_cmd("ON " + str(channel))

    def set_off_all(self):
        """
        Close main valve.
        (old name: setOffAll)

        Note:
            When the process is finished, the channels in use should be additionally turned off individually.
        """
        return self.remote_cmd("OF 0")

    def set_off(self, channel):
        """
        Close valve for a given channel.
        (old name: setOff)

        Note:
            The main valve can be turned off separately by set_off_all.

        Args:
            channel: Channel to be turned off.
        """
        return self.remote_cmd("OF " + str(channel))

    def get_channel_status(self, channel):
        """
        Check the status of a channel.
        (old name: check_channelStatus)

        Args:
            channel: Channel to be checked.

        Returns:
            Status bitstring with following bitwise information:
            0:  0/1 - channel off/on
            4:  trip limit low
            5:  trip limit high
            6:  overflow in
            7:  underflow in
            8:  overflow out
            9:  underflow out
            15: not used

        """
        return self.remote_cmd("ST " + str(channel))

    """
    FLOW
    """
    def get_flow(self, channel):
        """
        Check for actual flow of a channel.
        (old name: getActualFlow)

        Args:
            channel: Channel to be checked.

        Returns:
            Actual flow in 0.1 percent of full scale,
            somehow converted, which has to be checked.
        """
        # TODO: Check unit of flow that is returned and add to docstring.
        cmd = "FL " + str(channel)
        flow = self.remote_cmd(cmd)   #gives N2 flow
        return float(flow)/10*self.getGasCorrectionFactor(channel)

    def set_flow(self, channel, value):
        """
        Enter flow setpoint of a channel.
        (old name: setFlowSetPoint)

        Args:
            channel: Channel for which the flow is set.
            value: Flow to be set.
        """
        # TODO: Check unit of flow and add to docstring.
        cmd = "FS " + str(channel) + str(int(float(value)/self.getGasCorrectionFactor(channel)*10))
        return self.remote_cmd(cmd)

    def get_flow_setpoint(self, channel):
        """
        Check for flow setpoint of a channel.
        (old name: getFlowSetPoint)

        Args:
            channel: Channel for which the flow is set.
        """
        # TODO: Check unit of flow and add to docstring.
        cmd = "FS " + str(channel) +" R"
        flow = self.remote_cmd(cmd)   #gives N2 flow #indent error?
        return float(flow)/10*self.getGasCorrectionFactor(channel)

    """
    PRESSURE
    """
    def set_pressure_unit(self, pu=13):
        """
        Set the pressure unit.
        (old name: setPressureUnit)

        Args:
            pu: The number of the unit to be set.
                16: 10 mbar
                15: 1 mbar
                13: 100 ubar
                12: 10 ubar
                11: 1 ubar
        """
        cmd = "PU " + str(pu)
        return self.remote_cmd(cmd)

    def get_pressure_unit(self):
        """
        Get the pressure unit.
        (old name: getPressureUnit)

        Returns:
            The number of the unit set.
                16: 10 mbar
                15: 1 mbar
                13: 100 ubar
                12: 10 ubar
                11: 1 ubar
        """
        cmd = "PU R"
        return self.remote_cmd(cmd)

    def get_pressure(self):
        """
        Check for pressure.
        (old name: getActualPressure)

        Returns:
            Actual pressure in 0.1 percent of full scale.
        """
        cmd = "PR"
        return self.remote_cmd(cmd)

    def set_pressure_mode(self, On=True):
        """
        Enter pressure mode (pressure controlled automatically).
        (old name: setPressureMode)

        Args:
            On (bool): True for on (auto), False for off.
        """
        if On:
            cmd = "PM 1"
        else:
            cmd = "PM 0"
        return self.remote_cmd(cmd)

    def get_pressure_mode(self):
        """
        Check for pressure mode (pressure controlled automatically).
        (old name: PressureModeOn)

        Returns:
            Pressure mode status (True for on (auto), False for off.
        """
        cmd = "PM R"
        status = self.remote_cmd(cmd)
        if int(status) == 1:
            return True
        else:
            return False

    def set_pressure(self,value):
        """
        Enter pressure setpoint.
        (old name: setPressureSetPoint)

        Args:
            Setpoint in 0.1 percent of full scale.
        """
        # value in 0.1 percent of fullscale: 0..1100
        cmd = "PS "+str(value)
        return self.remote_cmd(cmd)

    def get_pressure_setpoint(self):
        """
        Check for pressure setpoint.
        (old name: getPressureSetPoint)

        Returns:
            Pressure setpoint.
        """
        cmd = "PS R"
        return self.remote_cmd(cmd)

    def get_pcs(self):
        """
        Check for PCS in PCS mode for use with an external pressure controller (e.g. type 250).
        All  gas  flow  channels  which  are  configured  in  the  PCS  mode  are regulated through the
        pressure control signal (PCS) according to the ratio of their set points.
        (old name: getActualPCS)

        Returns:
            Actual PCS signal in 0.1 percent of full scale.
        """
        cmd = "PC"
        return self.remote_cmd(cmd)

if __name__ == "__main__":

    MKS = MKS_647C("MKS",address= "COM6")
    # mutex = Ar.getMutex()
    # N2 = MKS647C_Dev(2,mutex)
    # O2 = MKS647C_Dev(3,mutex)
    # ArO = MKS647C_Dev(4,mutex)
    
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
