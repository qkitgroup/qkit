# MKS MFC Controller 647C DEV version 1.0 written by HR/JB@KIT 10/2013
# Rewritten for qkit/evaporate/deposition service HR,YS@KIT 2018
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
    This is the driver for the MKS 647C four channel mass flow controller.

    Usage:
    Initialize with
    <name> = qkit.instruments.create('<name>', 'MKS_647C', address='<GBIP address>', reset=<bool>)
    """

    def __init__(self, name, address, reset=False):
        """
        Initializes the MKS, and communicates with the wrapper.
        
        Args:
            name (string)    : Name of the instrument
            address (string) : Serial address
            reset (bool)     : Resets to default values, default=False
        """
        
        logging.info(__name__ + ': Initializing instrument MKS_647C')
        Instrument.__init__(self, name, tags=['physical'])

        self.predef_pressure_unit = 13 # 100 ubar, depends on baratron
        self.predef_channels = {"Ar": 1, "N2": 2, "O2": 3, "ArO": 4}
        self.predef_gasCorfact = {"Ar": 1.37, "N2": 1.0, "O2": 1.0, "ArO": 1.37}  # Values as they are predefined in MKS
        self.predef_flowRange = {"Ar": 6, "N2": 6, "O2": 6, "ArO": 3}  # 100sccm, 100sccm, 100sccm, 10sccm

        self.mutex = Lock()
        self.setup(address)

        self.init_controller(reset=reset)
        
    def setup(self, address="COM10"):
        baudrate = 9600
        timeout = 1

        self.serial_port = self._std_open(address, baudrate, timeout)
        atexit.register(self.serial_port.close)
        
    def _std_open(self, device, baudrate, timeout):
        return serial.Serial(device, baudrate, timeout=timeout)

    def get_serial_port(self):
        return self.serial_port

    def get_mutex(self):
        return self.mutex

    def remote_cmd(self, cmd):
        # the 647C requires carriage return termination
        cmd += '\r'
        with self.mutex:
            self.serial_port.write(cmd)
        
            time.sleep(0.2)   #increase from .1 to .2
            #value = self.ser.readline().strip("\x06")
            rem_char = self.serial_port.inWaiting()
        
            value = self.serial_port.read(rem_char) # .strip("\x06")
            time.sleep(0.2)   #to avoid wrong communication
            return value.strip()

    """
    INSTRUMENT SETUP
    """
    def set_default(self):
        return self.remote_cmd("DF")

    def hardware_reset(self):
        return self.remote_cmd("RE")

    def get_version(self):
        return self.remote_cmd("ID")

    def init_controller(self, reset=False):
        """
        Initialize the MKS.
        Units and ranges required for value conversion are loaded and stored in self variables.

        If reset=True, the default values as defined by predef_... in __init__ are set and all channels are turned off.

        Args:
            reset: Reset the MKS to default values.

        Returns:
            Nothing but makes available:
            self.pressure_range, self.pressure_unit and self.flow_settings used internally for unit conversion.
        """
        print ("Initializing controller...")

        self.set_pressure_unit(self.predef_pressure_unit)
        self.pressure_range, self.pressure_unit = self.get_pressure_range()

        self.flow_settings = {}

        if reset:
            self.set_off_all()

        for chan_name in self.predef_channels.keys():
            channel = self.predef_channels[chan_name]
            self.flow_settings[channel] = {}
            if reset:
                self.set_off(channel)
                self.set_flow_range(channel, self.predef_flowRange[chan_name])
                self.set_gas_correction_factor(channel, self.predef_gasCorfact[chan_name])
            flow_range, flow_unit = self.get_flow_range(channel)
            gas_corr_fact = self.get_gas_correction_factor(channel)
            self.flow_settings[channel] = {"flow_range": float(flow_range),
                                           "flow_unit": str(flow_unit),
                                           "gas_corr_fact": float(gas_corr_fact)}
            if reset:
                self.set_flow(channel, 0)
        
        print ("Controller initialized.")
        if reset:
            print ("Values were resetted to predef values defined in __init__ and flow was turned off.")
        else:
            print ("No values were resetted.")
        print ("Channel settings are available as flow_settings[channel].")
        print ("Pressure settings: ")
        print (self.get_pressure_range())
        print ("Flow settings: ")
        for chan in self.flow_settings:
            print (chan, self.flow_settings[chan])

        return

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

    def set_gas_correction_factor(self, channel, factor):
        """
        Set the gas correction factor for a given channel.

        Args:
            channel: Channel for which the gas correction factor is to be set.
            factor: The gas correction factor to be set.
        
        Note:
            This changes the gas settings to "USER, since the driver has no option to choose the gas directly.
            Chosing Argon directly from the menu on the controller gives a correction factor of 1.37.
            Nitrogen and Oxygen both are set to 1 by the device.
            This is programmed here in the predef vales of __init__.
        """
        cmd = "GC " + str(channel) + " " + str(int(factor*100))# '{fact:04d}'.format(fact=int(factor*100))
        ret = self.remote_cmd(cmd)
        gas_corr_fact = self.get_gas_correction_factor(channel)
        self.flow_settings[channel]["gas_corr_fact"] = float(gas_corr_fact)
        return ret

    def get_gas_correction_factor(self, channel):
        """
        Check gas correction factor of a channel.

        Args:
            channel: Channel to be checked.
        
        Returns:
            Gas correction factor.
        """
        cmd = "GC " + str(channel) + " R"
        res = self.remote_cmd(cmd)
        return float(res)/100.

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
        ret = self.remote_cmd(cmd)
        flow_range, flow_unit = self.get_flow_range(channel)
        self.flow_settings[channel]["flow_range"] = float(flow_range)
        self.flow_settings[channel]["flow_unit"] = str(flow_unit)
        return ret

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
                 'SLM', 'SLM', 'SLM', 'SLM', 'SLM', 'SLM', 'SLM', 'SLM', 'SLM', 'SLM',
                 'SCMM', 'SCFH', 'SCFH', 'SCFH', 'SCFH', 'SCFH', 'SCFH', 'SCFH', 'SCFH',
                 'SCFH', 'SCFM', 'SCFM', 'SCFM', 'SCFM', 'SCFM', 'SCFM', 'SCFM', 'SCFM',
                 'SCFM', 'SLM', 'SLM']

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
        
    def get_low_limit(self, channel):
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
            Actual flow of a given channel in units defined by flow range.
        """
        cmd = "FL " + str(channel)
        flow = self.remote_cmd(cmd)
        return float(flow)*self.flow_settings[channel]['flow_range']*self.flow_settings[channel]['gas_corr_fact']/1000.

    def set_flow(self, channel, value):
        """
        Enter flow setpoint of a channel.
        (old name: setFlowSetPoint)

        Args:
            channel: Channel for which the flow is set.
            value: Flow to be set in units defined by flow range.
        """
        cmd = "FS " + str(channel) + str(int(round(value / self.flow_settings[channel]['flow_range'] /
                                                   self.flow_settings[channel]['gas_corr_fact']*1000.)))
        # print cmd
        return self.remote_cmd(cmd)

    def get_flow_setpoint(self, channel):
        """
        Check for flow setpoint of a channel.
        (old name: getFlowSetPoint)

        Args:
            channel: Channel for which the flow is set.
        
        Returns:
            Flow setpoint of a given channel in units defined by flow range.
        """
        cmd = "FS " + str(channel) +" R"
        ret = self.remote_cmd(cmd)
        # print ret
        return float(ret)*self.flow_settings[channel]['flow_range']*self.flow_settings[channel]['gas_corr_fact']/1000.

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
        ret = self.remote_cmd(cmd)
        self.pressure_range, self.pressure_unit = self.get_pressure_range()
        return ret

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
    
    def get_pressure_range(self):
        pressures = [1., 10., 100., 1000., 1., 10., 100., 1000., 1., 10., 100., 1., 10., 100., 1000., 1., 10., 100.,
                     1000., 1., 10., 100., 1., 10., 100., 1., 10., 100., 1000., 2., 5., 20., 50., 200., 500., 2000.,
                     5000., 2., 5., 20., 50., 200., 500., 2000., 5000., 2., 5., 20., 50., 2., 5., 20., 50., 200., 500.,
                     2000., 5000., 2., 5., 20., 50., 200., 500., 2000., 5000., 2., 5., 20., 50., 2., 5., 20., 50., 200.,
                     500., 2., 5., 20., 50., 200., 500., 2000., 5000., 1., 2., 5., 10]
        units = ['mTorr', 'mTorr', 'mTorr', 'mTorr', 'Torr', 'Torr', 'Torr', 'Torr', 'kTorr', 'kTorr', 'kTorr', 'uBar',
                 'uBar', 'uBar', 'uBar', 'mBar', 'mBar', 'mBar', 'mBar', 'Bar', 'Bar', 'Bar', 'Pa', 'Pa', 'Pa', 'kPa',
                 'kPa', 'kPa', 'kPa', 'mTorr', 'mTorr', 'mTorr', 'mTorr', 'mTorr', 'mTorr', 'mTorr', 'mTorr', 'Torr',
                 'Torr', 'Torr', 'Torr', 'Torr', 'Torr', 'Torr', 'Torr', 'kTorr', 'kTorr', 'kTorr', 'kTorr', 'ubar',
                 'ubar', 'ubar', 'ubar', 'ubar', 'ubar', 'ubar', 'ubar', 'mbar', 'mbar', 'mbar', 'mbar', 'mbar', 'mbar',
                 'mbar', 'mbar', 'bar', 'bar', 'bar', 'bar', 'Pa', 'Pa', 'Pa', 'Pa', 'Pa', 'Pa', 'kPa', 'kPa', 'kPa',
                 'kPa', 'kPa', 'kPa', 'kPa', 'kPa', 'Mpa', 'Mpa', 'Mpa', 'Mpa']
        pnum = int(self.get_pressure_unit())
        return pressures[pnum], units[pnum]

    def get_pressure(self):
        """
        Check for pressure.
        (old name: getActualPressure)

        Returns:
            Actual pressure.
            Converted from 0.1 percent of full scale.
        """
        cmd = "PR"
        return float(self.remote_cmd(cmd))*self.pressure_range/1000

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

    def set_pressure(self, value):
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

    MKS = MKS_647C("MKS", address="COM10")

    MKS.init_controller()
