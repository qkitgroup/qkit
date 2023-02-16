# Zurich Instruments SHFSG driver by Andras Di Giovanni
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
import numpy as np
from qkit.core.instrument_base import Instrument
import zhinst.ziPython as zi
import zhinst.utils as utils
from zhinst.toolkit import Session
server_host = '127.0.0.1'
server_port = 8004
apilevel_example=6
import time
import zhinst.deviceutils.shfsg as shfsg_utils
from zhinst.toolkit import Session


daq = zi.ziDAQServer(host=server_host, port=server_port, api_level=6)
print("Connected to ziDAQ server.")
daq.sync()
device_interface = '1gbe'
daq.connectDevice("dev12064", device_interface)

print('SHFSG ready to use in 1 second.')

class zi_shfsg(Instrument):
    """
    This is the python driver for the SHFSG, more commonly called SHF

    Initialise with shfsg = qkit.instruments.create("zi_shfsg", "zi_shfsg")
    """

    def __init__(self, name, **kwargs):

        awg_shfsg = daq.awgModule()
        awg_shfsg.set('device', 'DEV12064')
        awg_shfsg.execute()
        daq.sync()
        Instrument.__init__(self, name,  tags=['physical'])

        self._twotonelen = 1000

        # OUTPUT parameters
        self.add_parameter('ch1_centerfreq', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch2_centerfreq', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch3_centerfreq', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch4_centerfreq', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch5_centerfreq', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch6_centerfreq', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch7_centerfreq', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch8_centerfreq', type=float, flags=Instrument.FLAG_GETSET)

        self.add_parameter('ch1_on', type=int, flags=Instrument.FLAG_SET)
        self.add_parameter('ch2_on', type=int, flags=Instrument.FLAG_SET)
        self.add_parameter('ch3_on', type=int, flags=Instrument.FLAG_SET)
        self.add_parameter('ch4_on', type=int, flags=Instrument.FLAG_SET)
        self.add_parameter('ch5_on', type=int, flags=Instrument.FLAG_SET)
        self.add_parameter('ch6_on', type=int, flags=Instrument.FLAG_SET)
        self.add_parameter('ch7_on', type=int, flags=Instrument.FLAG_SET)
        self.add_parameter('ch8_on', type=int, flags=Instrument.FLAG_SET)

        self.add_parameter('ch1_range', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch2_range', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch3_range', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch4_range', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch5_range', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch6_range', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch7_range', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch8_range', type=int, flags=Instrument.FLAG_GETSET)


        # MODULATION parameters
        self.add_parameter('ch1_osc1_freq', type = float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch2_osc1_freq', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch3_osc1_freq', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch4_osc1_freq', type = float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch5_osc1_freq', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch6_osc1_freq', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch7_osc1_freq', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch8_osc1_freq', type=float, flags=Instrument.FLAG_GETSET)

        self.add_parameter('ch1_osc1_Isine', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch2_osc1_Isine', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch3_osc1_Isine', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch4_osc1_Isine', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch5_osc1_Isine', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch6_osc1_Isine', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch7_osc1_Isine', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch8_osc1_Isine', type=float, flags=Instrument.FLAG_GETSET)

        self.add_parameter('ch1_osc1_Icos', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch2_osc1_Icos', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch3_osc1_Icos', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch4_osc1_Icos', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch5_osc1_Icos', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch6_osc1_Icos', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch7_osc1_Icos', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch8_osc1_Icos', type=float, flags=Instrument.FLAG_GETSET)

        self.add_parameter('ch1_osc1_Qsine', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch2_osc1_Qsine', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch3_osc1_Qsine', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch4_osc1_Qsine', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch5_osc1_Qsine', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch6_osc1_Qsine', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch7_osc1_Qsine', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch8_osc1_Qsine', type=float, flags=Instrument.FLAG_GETSET)

        self.add_parameter('ch1_osc1_Qcos', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch2_osc1_Qcos', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch3_osc1_Qcos', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch4_osc1_Qcos', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch5_osc1_Qcos', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch6_osc1_Qcos', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch7_osc1_Qcos', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch8_osc1_Qcos', type=float, flags=Instrument.FLAG_GETSET)

        self.add_parameter('ch1_osc1_Ion', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch2_osc1_Ion', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch3_osc1_Ion', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch4_osc1_Ion', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch5_osc1_Ion', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch6_osc1_Ion', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch7_osc1_Ion', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch8_osc1_Ion', type=int, flags=Instrument.FLAG_GETSET)

        self.add_parameter('ch1_osc1_Qon', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch2_osc1_Qon', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch3_osc1_Qon', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch4_osc1_Qon', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch5_osc1_Qon', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch6_osc1_Qon', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch7_osc1_Qon', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch8_osc1_Qon', type=int, flags=Instrument.FLAG_GETSET)

        #AWG parameters
        self.add_parameter('ch1_samplingrate', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch2_samplingrate', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch3_samplingrate', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch4_samplingrate', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch5_samplingrate', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch6_samplingrate', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch7_samplingrate', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch8_samplingrate', type=int, flags=Instrument.FLAG_GETSET)

        self.add_parameter('ch1_rerun', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch2_rerun', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch3_rerun', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch4_rerun', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch5_rerun', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch6_rerun', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch7_rerun', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ch8_rerun', type=int, flags=Instrument.FLAG_GETSET)

        self.add_parameter('ch1_triggersignal', type=int, flags=Instrument.FLAG_SET)
        self.add_parameter('ch2_triggersignal', type=int, flags=Instrument.FLAG_SET)
        self.add_parameter('ch3_triggersignal', type=int, flags=Instrument.FLAG_SET)
        self.add_parameter('ch4_triggersignal', type=int, flags=Instrument.FLAG_SET)
        self.add_parameter('ch5_triggersignal', type=int, flags=Instrument.FLAG_SET)
        self.add_parameter('ch6_triggersignal', type=int, flags=Instrument.FLAG_SET)
        self.add_parameter('ch7_triggersignal', type=int, flags=Instrument.FLAG_SET)
        self.add_parameter('ch8_triggersignal', type=int, flags=Instrument.FLAG_SET)

        self.add_parameter('ch1_triggerslope', type=int, flags=Instrument.FLAG_SET)
        self.add_parameter('ch2_triggerslope', type=int, flags=Instrument.FLAG_SET)
        self.add_parameter('ch3_triggerslope', type=int, flags=Instrument.FLAG_SET)
        self.add_parameter('ch4_triggerslope', type=int, flags=Instrument.FLAG_SET)
        self.add_parameter('ch5_triggerslope', type=int, flags=Instrument.FLAG_SET)
        self.add_parameter('ch6_triggerslope', type=int, flags=Instrument.FLAG_SET)
        self.add_parameter('ch7_triggerslope', type=int, flags=Instrument.FLAG_SET)
        self.add_parameter('ch8_triggerslope', type=int, flags=Instrument.FLAG_SET)
        self.add_parameter('twotonelen', type = int, flags = Instrument.FLAG_GETSET)
        self.add_parameter('internaltrigger_repetitions', type = int, flags = Instrument.FLAG_GETSET)
        self.add_parameter('internaltrigger_holdoff', type = float, flags = Instrument.FLAG_GETSET)
        self.add_parameter('internaltrigger_on', type = int, flags = Instrument.FLAG_GETSET)
#getter and setter functions

    def do_get_twotonelen(self):
        return self._twotonelen
    def do_set_twotonelen(self, x):
        self._twotonelen = x

    def sync(self):
        daq.sync()

    def get_internaltrigger_progress(self):
        return daq.getDouble('/dev12064/system/internaltrigger/progress')

    def do_get_internaltrigger_repetitions(self):
        return daq.getInt('/dev12064/system/internaltrigger/repetitions')
    def do_set_internaltrigger_repetitions(self, x):
        daq.setInt('/dev12064/system/internaltrigger/repetitions', x)

    def do_get_internaltrigger_holdoff(self):
        return daq.getDouble('/dev12064/system/internaltrigger/holdoff')
    def do_set_internaltrigger_holdoff(self, x):
        daq.setDouble('/dev12064/system/internaltrigger/holdoff', x)

    def do_get_internaltrigger_on(self):
        return daq.getInt('/dev12064/system/internaltrigger/enable')
    def do_set_internaltrigger_on(self, x):
        daq.setInt('/dev12064/system/internaltrigger/enable', x)

    def do_get_ch1_centerfreq(self, query = True):
        return daq.getDouble('/dev12064/synthesizers/0/centerfreq')
    def do_set_ch1_centerfreq(self, x):
        daq.setDouble('/dev12064/synthesizers/0/centerfreq', x)
    def do_get_ch2_centerfreq(self):
        return daq.getDouble('/dev12064/synthesizers/0/centerfreq')
    def do_set_ch2_centerfreq(self, x):
        daq.setDouble('/dev12064/synthesizers/0/centerfreq', x)
    def do_get_ch3_centerfreq(self):
        return daq.getDouble('/dev12064/synthesizers/1/centerfreq')
    def do_set_ch3_centerfreq(self, x):
        daq.setDouble('/dev12064/synthesizers/1/centerfreq', x)
    def do_get_ch4_centerfreq(self):
        return daq.getDouble('/dev12064/synthesizers/1/centerfreq')
    def do_set_ch4_centerfreq(self, x):
        daq.setDouble('/dev12064/synthesizers/1/centerfreq', x)
    def do_get_ch5_centerfreq(self):
        return daq.getDouble('/dev12064/synthesizers/2/centerfreq')
    def do_set_ch5_centerfreq(self, x):
        daq.setDouble('/dev12064/synthesizers/2/centerfreq', x)
    def do_get_ch6_centerfreq(self):
        return daq.getDouble('/dev12064/synthesizers/2/centerfreq')
    def do_set_ch6_centerfreq(self, x):
        daq.setDouble('/dev12064/synthesizers/2/centerfreq', x)
    def do_get_ch7_centerfreq(self):
        return daq.getDouble('/dev12064/synthesizers/3/centerfreq')
    def do_set_ch7_centerfreq(self, x):
        daq.setDouble('/dev12064/synthesizers/3/centerfreq', x)
    def do_get_ch8_centerfreq(self):
        return daq.getDouble('/dev12064/synthesizers/3/centerfreq')
    def do_set_ch8_centerfreq(self, x):
        daq.setDouble('/dev12064/synthesizers/3/centerfreq', x)

    def do_set_ch1_on(self):
        if daq.getInt('/dev12064/sgchannels/0/output/on'):
            daq.setInt('/dev12064/sgchannels/0/output/on', 0)
        else:
            daq.setInt('/dev12064/sgchannels/0/output/on', 1)
    def do_set_ch2_on(self):
        if daq.getInt('/dev12064/sgchannels/1/output/on'):
            daq.setInt('/dev12064/sgchannels/1/output/on', 0)
        else:
            daq.setInt('/dev12064/sgchannels/1/output/on', 1)
    def do_set_ch3_on(self):
        if daq.getInt('/dev12064/sgchannels/2/output/on'):
            daq.setInt('/dev12064/sgchannels/2/output/on', 0)
        else:
            daq.setInt('/dev12064/sgchannels/2/output/on', 1)
    def do_set_ch4_on(self):
        if daq.getInt('/dev12064/sgchannels/3/output/on'):
            daq.setInt('/dev12064/sgchannels/3/output/on', 0)
        else:
            daq.setInt('/dev12064/sgchannels/3/output/on', 1)
    def do_set_ch5_on(self):
        if daq.getInt('/dev12064/sgchannels/4/output/on'):
            daq.setInt('/dev12064/sgchannels/4/output/on', 0)
        else:
            daq.setInt('/dev12064/sgchannels/4/output/on', 1)
    def do_set_ch6_on(self):
        if daq.getInt('/dev12064/sgchannels/5/output/on'):
            daq.setInt('/dev12064/sgchannels/5/output/on', 0)
        else:
            daq.setInt('/dev12064/sgchannels/5/output/on', 1)
    def do_set_ch7_on(self):
        if daq.getInt('/dev12064/sgchannels/6/output/on'):
            daq.setInt('/dev12064/sgchannels/6/output/on', 0)
        else:
            daq.setInt('/dev12064/sgchannels/6/output/on', 1)
    def do_set_ch8_on(self):
        if daq.getInt('/dev12064/sgchannels/7/output/on'):
            daq.setInt('/dev12064/sgchannels/7/output/on', 0)
        else:
            daq.setInt('/dev12064/sgchannels/7/output/on', 1)

    def do_set_ch1_range(self, x):
        daq.setInt('/dev12064/sgchannels/0/output/range', x)
    def do_get_ch1_range(self):
        return daq.getInt('/dev12064/sgchannels/0/output/range')
    def do_set_ch2_range(self, x):
        daq.setInt('/dev12064/sgchannels/1/output/range', x)
    def do_get_ch2_range(self):
        return daq.getInt('/dev12064/sgchannels/1/output/range')
    def do_set_ch3_range(self, x):
        daq.setInt('/dev12064/sgchannels/2/output/range', x)
    def do_get_ch3_range(self):
        return daq.getInt('/dev12064/sgchannels/2/output/range')
    def do_set_ch4_range(self, x):
        daq.setInt('/dev12064/sgchannels/3/output/range', x)
    def do_get_ch4_range(self):
        return daq.getInt('/dev12064/sgchannels/3/output/range')
    def do_set_ch5_range(self, x):
        daq.setInt('/dev12064/sgchannels/4/output/range', x)
    def do_get_ch5_range(self):
        return daq.getInt('/dev12064/sgchannels/4/output/range')
    def do_set_ch6_range(self, x):
        daq.setInt('/dev12064/sgchannels/5/output/range', x)
    def do_get_ch6_range(self):
        return daq.getInt('/dev12064/sgchannels/5/output/range')
    def do_set_ch7_range(self, x):
        daq.setInt('/dev12064/sgchannels/6/output/range', x)
    def do_get_ch7_range(self):
        return daq.getInt('/dev12064/sgchannels/6/output/range')
    def do_set_ch8_range(self, x):
        daq.setInt('/dev12064/sgchannels/7/output/range', x)
    def do_get_ch8_range(self):
        return daq.getInt('/dev12064/sgchannels/7/output/range')

    def do_get_ch1_osc1_freq(self):
        return daq.getDouble('/dev12064/sgchannels/0/oscs/0/freq')
    def do_set_ch1_osc1_freq(self, x):
        daq.setDouble('/dev12064/sgchannels/0/oscs/0/freq', x)
    def do_get_ch2_osc1_freq(self):
        return daq.getDouble('/dev12064/sgchannels/1/oscs/0/freq')
    def do_set_ch2_osc1_freq(self, x):
        daq.setDouble('/dev12064/sgchannels/1/oscs/0/freq', x)
    def do_get_ch3_osc1_freq(self):
        return daq.getDouble('/dev12064/sgchannels/2/oscs/0/freq')
    def do_set_ch3_osc1_freq(self, x):
        daq.setDouble('/dev12064/sgchannels/2/oscs/0/freq', x)
    def do_get_ch4_osc1_freq(self):
        return daq.getDouble('/dev12064/sgchannels/3/oscs/0/freq')
    def do_set_ch4_osc1_freq(self, x):
        daq.setDouble('/dev12064/sgchannels/3/oscs/0/freq', x)
    def do_get_ch5_osc1_freq(self):
        return daq.getDouble('/dev12064/sgchannels/4/oscs/0/freq')
    def do_set_ch5_osc1_freq(self, x):
        daq.setDouble('/dev12064/sgchannels/4/oscs/0/freq', x)
    def do_get_ch6_osc1_freq(self):
       return daq.getDouble('/dev12064/sgchannels/5/oscs/0/freq')
    def do_set_ch6_osc1_freq(self, x):
        daq.setDouble('/dev12064/sgchannels/5/oscs/0/freq', x)
    def do_get_ch7_osc1_freq(self):
        return daq.getDouble('/dev12064/sgchannels/6/oscs/0/freq')
    def do_set_ch7_osc1_freq(self, x):
        daq.setDouble('/dev12064/sgchannels/6/oscs/0/freq', x)
    def do_get_ch8_osc1_freq(self):
        return daq.getDouble('/dev12064/sgchannels/7/oscs/0/freq')
    def do_set_ch8_osc1_freq(self, x):
        daq.setDouble('/dev12064/sgchannels/7/oscs/0/freq', x)

    def do_set_ch1_osc1_Isine(self, x):
        daq.setDouble('/dev12064/sgchannels/0/sines/0/i/sin/amplitude', x)
    def do_get_ch1_osc1_Isine(self):
        return daq.getDouble('/dev12064/sgchannels/0/sines/0/i/sin/amplitude')
    def do_set_ch1_osc1_Icos(self, x):
        daq.setDouble('/dev12064/sgchannels/0/sines/0/i/cos/amplitude', x)
    def do_get_ch1_osc1_Icos(self):
        return daq.getDouble('/dev12064/sgchannels/0/sines/0/i/cos/amplitude')
    def do_set_ch1_osc1_Ion(self, x):
        daq.setInt('/dev12064/sgchannels/0/sines/0/i/enable', x)
    def do_get_ch1_osc1_Ion(self):
        return daq.getInt('/dev12064/sgchannels/0/sines/0/i/enable')
    def do_set_ch2_osc1_Isine(self, x):
        daq.setDouble('/dev12064/sgchannels/1/sines/0/i/sin/amplitude', x)
    def do_get_ch2_osc1_Isine(self):
        return daq.getDouble('/dev12064/sgchannels/1/sines/0/i/sin/amplitude')
    def do_set_ch2_osc1_Icos(self, x):
        daq.setDouble('/dev12064/sgchannels/1/sines/0/i/cos/amplitude', x)
    def do_get_ch2_osc1_Icos(self):
        return daq.getDouble('/dev12064/sgchannels/1/sines/0/i/cos/amplitude')
    def do_set_ch2_osc1_Ion(self, x):
        daq.setInt('/dev12064/sgchannels/1/sines/0/i/enable', x)
    def do_get_ch2_osc1_Ion(self):
        return daq.getInt('/dev12064/sgchannels/1/sines/0/i/enable')
    def do_set_ch3_osc1_Isine(self, x):
        daq.setDouble('/dev12064/sgchannels/2/sines/0/i/sin/amplitude', x)
    def do_get_ch3_osc1_Isine(self):
        return daq.getDouble('/dev12064/sgchannels/2/sines/0/i/sin/amplitude')
    def do_set_ch3_osc1_Icos(self, x):
        daq.setDouble('/dev12064/sgchannels/2/sines/0/i/cos/amplitude', x)
    def do_get_ch3_osc1_Icos(self):
        return daq.getDouble('/dev12064/sgchannels/2/sines/0/i/cos/amplitude')
    def do_set_ch3_osc1_Ion(self, x):
        daq.setInt('/dev12064/sgchannels/2/sines/0/i/enable', x)
    def do_get_ch3_osc1_Ion(self):
        return daq.getInt('/dev12064/sgchannels/2/sines/0/i/enable')
    def do_set_ch4_osc1_Isine(self, x):
        daq.setDouble('/dev12064/sgchannels/3/sines/0/i/sin/amplitude', x)
    def do_get_ch4_osc1_Isine(self):
        return daq.getDouble('/dev12064/sgchannels/3/sines/0/i/sin/amplitude')
    def do_set_ch4_osc1_Icos(self, x):
        daq.setDouble('/dev12064/sgchannels/3/sines/0/i/cos/amplitude', x)
    def do_get_ch4_osc1_Icos(self):
        return daq.getDouble('/dev12064/sgchannels/3/sines/0/i/cos/amplitude')
    def do_set_ch4_osc1_Ion(self, x):
        daq.setInt('/dev12064/sgchannels/3/sines/0/i/enable', x)
    def do_get_ch4_osc1_Ion(self):
        return daq.getInt('/dev12064/sgchannels/3/sines/0/i/enable')
    def do_set_ch5_osc1_Isine(self, x):
        daq.setDouble('/dev12064/sgchannels/4/sines/0/i/sin/amplitude', x)
    def do_get_ch5_osc1_Isine(self):
        return daq.getDouble('/dev12064/sgchannels/4/sines/0/i/sin/amplitude')
    def do_set_ch5_osc1_Icos(self, x):
        daq.setDouble('/dev12064/sgchannels/4/sines/0/i/cos/amplitude', x)
    def do_get_ch5_osc1_Icos(self):
        return daq.getDouble('/dev12064/sgchannels/4/sines/0/i/cos/amplitude')
    def do_set_ch5_osc1_Ion(self, x):
        daq.setInt('/dev12064/sgchannels/4/sines/0/i/enable', x)
    def do_get_ch5_osc1_Ion(self):
        return daq.getInt('/dev12064/sgchannels/4/sines/0/i/enable')
    def do_set_ch6_osc1_Isine(self, x):
        daq.setDouble('/dev12064/sgchannels/5/sines/0/i/sin/amplitude', x)
    def do_get_ch6_osc1_Isine(self):
        return daq.getDouble('/dev12064/sgchannels/5/sines/0/i/sin/amplitude')
    def do_set_ch6_osc1_Icos(self, x):
        daq.setDouble('/dev12064/sgchannels/5/sines/0/i/cos/amplitude', x)
    def do_get_ch6_osc1_Icos(self):
        return daq.getDouble('/dev12064/sgchannels/5/sines/0/i/cos/amplitude')
    def do_set_ch6_osc1_Ion(self, x):
        daq.setInt('/dev12064/sgchannels/5/sines/0/i/enable', x)
    def do_get_ch6_osc1_Ion(self):
        return daq.getInt('/dev12064/sgchannels/5/sines/0/i/enable')
    def do_set_ch7_osc1_Isine(self, x):
        daq.setDouble('/dev12064/sgchannels/6/sines/0/i/sin/amplitude', x)
    def do_get_ch7_osc1_Isine(self):
        return daq.getDouble('/dev12064/sgchannels/6/sines/0/i/sin/amplitude')
    def do_set_ch7_osc1_Icos(self, x):
        daq.setDouble('/dev12064/sgchannels/6/sines/0/i/cos/amplitude', x)
    def do_get_ch7_osc1_Icos(self):
        return daq.getDouble('/dev12064/sgchannels/6/sines/0/i/cos/amplitude')
    def do_set_ch7_osc1_Ion(self, x):
        daq.setInt('/dev12064/sgchannels/6/sines/0/i/enable', x)
    def do_get_ch7_osc1_Ion(self):
        return daq.getInt('/dev12064/sgchannels/6/sines/0/i/enable')
    def do_set_ch8_osc1_Isine(self, x):
        daq.setDouble('/dev12064/sgchannels/7/sines/0/i/sin/amplitude', x)
    def do_get_ch8_osc1_Isine(self):
        return daq.getDouble('/dev12064/sgchannels/7/sines/0/i/sin/amplitude')
    def do_set_ch8_osc1_Icos(self, x):
        daq.setDouble('/dev12064/sgchannels/7/sines/0/i/cos/amplitude', x)
    def do_get_ch8_osc1_Icos(self):
        return daq.getDouble('/dev12064/sgchannels/7/sines/0/i/cos/amplitude')
    def do_set_ch8_osc1_Ion(self, x):
        daq.setInt('/dev12064/sgchannels/7/sines/0/i/enable', x)
    def do_get_ch8_osc1_Ion(self):
        return daq.getInt('/dev12064/sgchannels/7/sines/0/i/enable')


    def do_set_ch1_osc1_Qsine(self, x):
        daq.setDouble('/dev12064/sgchannels/0/sines/0/q/sin/amplitude', x)
    def do_get_ch1_osc1_Qsine(self):
        return daq.getDouble('/dev12064/sgchannels/0/sines/0/q/sin/amplitude')
    def do_set_ch1_osc1_Qcos(self, x):
        daq.setDouble('/dev12064/sgchannels/0/sines/0/q/cos/amplitude', x)
    def do_get_ch1_osc1_Qcos(self):
        return daq.getDouble('/dev12064/sgchannels/0/sines/0/q/cos/amplitude')
    def do_set_ch1_osc1_Qon(self, x):
        daq.setInt('/dev12064/sgchannels/0/sines/0/q/enable', x)
    def do_get_ch1_osc1_Qon(self):
        return daq.getInt('/dev12064/sgchannels/0/sines/0/q/enable')
    def do_set_ch2_osc1_Qsine(self, x):
        daq.setDouble('/dev12064/sgchannels/1/sines/0/q/sin/amplitude', x)
    def do_get_ch2_osc1_Qsine(self):
        return daq.getDouble('/dev12064/sgchannels/1/sines/0/q/sin/amplitude')
    def do_set_ch2_osc1_Qcos(self, x):
        daq.setDouble('/dev12064/sgchannels/1/sines/0/q/cos/amplitude', x)
    def do_get_ch2_osc1_Qcos(self):
        return daq.getDouble('/dev12064/sgchannels/1/sines/0/q/cos/amplitude')
    def do_set_ch2_osc1_Qon(self, x):
        daq.setInt('/dev12064/sgchannels/1/sines/0/q/enable', x)
    def do_get_ch2_osc1_Qon(self):
        return daq.getInt('/dev12064/sgchannels/1/sines/0/q/enable')
    def do_set_ch3_osc1_Qsine(self, x):
        daq.setDouble('/dev12064/sgchannels/2/sines/0/q/sin/amplitude', x)
    def do_get_ch3_osc1_Qsine(self):
        return daq.getDouble('/dev12064/sgchannels/2/sines/0/q/sin/amplitude')
    def do_set_ch3_osc1_Qcos(self, x):
        daq.setDouble('/dev12064/sgchannels/2/sines/0/q/cos/amplitude', x)
    def do_get_ch3_osc1_Qcos(self):
        return daq.getDouble('/dev12064/sgchannels/2/sines/0/q/cos/amplitude')
    def do_set_ch3_osc1_Qon(self, x):
        daq.setInt('/dev12064/sgchannels/2/sines/0/q/enable', x)
    def do_get_ch3_osc1_Qon(self):
        return daq.getInt('/dev12064/sgchannels/2/sines/0/q/enable')
    def do_set_ch4_osc1_Qsine(self, x):
        daq.setDouble('/dev12064/sgchannels/3/sines/0/q/sin/amplitude', x)
    def do_get_ch4_osc1_Qsine(self):
        return daq.getDouble('/dev12064/sgchannels/3/sines/0/q/sin/amplitude')
    def do_set_ch4_osc1_Qcos(self, x):
        daq.setDouble('/dev12064/sgchannels/3/sines/0/q/cos/amplitude', x)
    def do_get_ch4_osc1_Qcos(self):
        return daq.getDouble('/dev12064/sgchannels/3/sines/0/q/cos/amplitude')
    def do_set_ch4_osc1_Qon(self, x):
        daq.setInt('/dev12064/sgchannels/3/sines/0/q/enable', x)
    def do_get_ch4_osc1_Qon(self):
        return daq.getInt('/dev12064/sgchannels/3/sines/0/q/enable')
    def do_set_ch5_osc1_Qsine(self, x):
        daq.setDouble('/dev12064/sgchannels/4/sines/0/q/sin/amplitude', x)
    def do_get_ch5_osc1_Qsine(self):
        return daq.getDouble('/dev12064/sgchannels/4/sines/0/q/sin/amplitude')
    def do_set_ch5_osc1_Qcos(self, x):
        daq.setDouble('/dev12064/sgchannels/4/sines/0/q/cos/amplitude', x)
    def do_get_ch5_osc1_Qcos(self):
        return daq.getDouble('/dev12064/sgchannels/4/sines/0/q/cos/amplitude')
    def do_set_ch5_osc1_Qon(self, x):
        daq.setInt('/dev12064/sgchannels/4/sines/0/q/enable', x)
    def do_get_ch5_osc1_Qon(self):
        return daq.getInt('/dev12064/sgchannels/4/sines/0/q/enable')
    def do_set_ch6_osc1_Qsine(self, x):
        daq.setDouble('/dev12064/sgchannels/5/sines/0/q/sin/amplitude', x)
    def do_get_ch6_osc1_Qsine(self):
        return daq.getDouble('/dev12064/sgchannels/5/sines/0/q/sin/amplitude')
    def do_set_ch6_osc1_Qcos(self, x):
        daq.setDouble('/dev12064/sgchannels/5/sines/0/q/cos/amplitude', x)
    def do_get_ch6_osc1_Qcos(self):
        return daq.getDouble('/dev12064/sgchannels/5/sines/0/q/cos/amplitude')
    def do_set_ch6_osc1_Qon(self, x):
        daq.setInt('/dev12064/sgchannels/5/sines/0/q/enable', x)
    def do_get_ch6_osc1_Qon(self):
        return daq.getInt('/dev12064/sgchannels/5/sines/0/q/enable')
    def do_set_ch7_osc1_Qsine(self, x):
        daq.setDouble('/dev12064/sgchannels/6/sines/0/q/sin/amplitude', x)
    def do_get_ch7_osc1_Qsine(self):
        return daq.getDouble('/dev12064/sgchannels/6/sines/0/q/sin/amplitude')
    def do_set_ch7_osc1_Qcos(self, x):
        daq.setDouble('/dev12064/sgchannels/6/sines/0/q/cos/amplitude', x)
    def do_get_ch7_osc1_Qcos(self):
        return daq.getDouble('/dev12064/sgchannels/6/sines/0/q/cos/amplitude')
    def do_set_ch7_osc1_Qon(self, x):
        daq.setInt('/dev12064/sgchannels/6/sines/0/q/enable', x)
    def do_get_ch7_osc1_Qon(self):
        return daq.getInt('/dev12064/sgchannels/6/sines/0/q/enable')
    def do_set_ch8_osc1_Qsine(self, x):
        daq.setDouble('/dev12064/sgchannels/7/sines/0/q/sin/amplitude', x)
    def do_get_ch8_osc1_Qsine(self):
        return daq.getDouble('/dev12064/sgchannels/7/sines/0/q/sin/amplitude')
    def do_set_ch8_osc1_Qcos(self, x):
        daq.setDouble('/dev12064/sgchannels/7/sines/0/q/cos/amplitude', x)
    def do_get_ch8_osc1_Qcos(self):
        return daq.getDouble('/dev12064/sgchannels/7/sines/0/q/cos/amplitude')
    def do_set_ch8_osc1_Qon(self, x):
        daq.setInt('/dev12064/sgchannels/7/sines/0/q/enable', x)
    def do_get_ch8_osc1_Qon(self):
        return daq.getInt('/dev12064/sgchannels/7/sines/0/q/enable')

    def do_get_ch1_samplingrate(self):
        return daq.getInt('/dev12064/sgchannels/0/awg/time')
    def do_set_ch1_samplingrate(self, x):
        daq.setInt('/dev12064/sgchannels/0/awg/time', x)
    def do_get_ch2_samplingrate(self):
        return daq.getInt('/dev12064/sgchannels/1/awg/time')
    def do_set_ch2_samplingrate(self, x):
        daq.setInt('/dev12064/sgchannels/1/awg/time', x)
    def do_get_ch3_samplingrate(self):
        return daq.getInt('/dev12064/sgchannels/2/awg/time')
    def do_set_ch3_samplingrate(self, x):
        daq.setInt('/dev12064/sgchannels/2/awg/time', x)
    def do_get_ch4_samplingrate(self):
        return daq.getInt('/dev12064/sgchannels/3/awg/time')
    def do_set_ch4_samplingrate(self, x):
        daq.setInt('/dev12064/sgchannels/3/awg/time', x)
    def do_get_ch5_samplingrate(self):
        return daq.getInt('/dev12064/sgchannels/4/awg/time')
    def do_set_ch5_samplingrate(self, x):
        daq.setInt('/dev12064/sgchannels/4/awg/time', x)
    def do_get_ch6_samplingrate(self):
        return daq.getInt('/dev12064/sgchannels/5/awg/time')
    def do_set_ch6_samplingrate(self, x):
        daq.setInt('/dev12064/sgchannels/5/awg/time', x)
    def do_get_ch7_samplingrate(self):
        return daq.getInt('/dev12064/sgchannels/6/awg/time')
    def do_set_ch7_samplingrate(self, x):
        daq.setInt('/dev12064/sgchannels/6/awg/time', x)
    def do_get_ch8_samplingrate(self):
        return daq.getInt('/dev12064/sgchannels/7/awg/time')
    def do_set_ch8_samplingrate(self, x):
        daq.setInt('/dev12064/sgchannels/7/awg/time', x)

    def do_get_ch1_rerun(self):
        return daq.getInt('/dev12064/sgchannels/0/awg/single')
    def do_set_ch1_rerun(self, x):
        if x==1:
            daq.setInt('/dev12064/sgchannels/0/awg/single', 0)
        if x==0:
            daq.setInt('/dev12064/sgchannels/0/awg/single', 1)
        else:
            print("Wrong input for rerun/single.")
    def do_get_ch2_rerun(self):
        return daq.getInt('/dev12064/sgchannels/1/awg/single')
    def do_set_ch2_rerun(self, x):
        if x==1:
            daq.setInt('/dev12064/sgchannels/1/awg/single', 0)
        if x==0:
            daq.setInt('/dev12064/sgchannels/1/awg/single', 1)
        else:
            print("Wrong input for rerun/single.")
    def do_get_ch3_rerun(self):
        return daq.getInt('/dev12064/sgchannels/2/awg/single')
    def do_set_ch3_rerun(self, x):
        if x == 1:
            daq.setInt('/dev12064/sgchannels/2/awg/single', 0)
        if x == 0:
            daq.setInt('/dev12064/sgchannels/2/awg/single', 1)
        else:
            print("Wrong input for rerun/single.")
    def do_get_ch4_rerun(self):
        return daq.getInt('/dev12064/sgchannels/3/awg/single')
    def do_set_ch4_rerun(self, x):
        if x == 1:
            daq.setInt('/dev12064/sgchannels/3/awg/single', 0)
        if x == 0:
            daq.setInt('/dev12064/sgchannels/3/awg/single', 1)
        else:
            print("Wrong input for rerun/single.")
    def do_get_ch5_rerun(self):
        return daq.getInt('/dev12064/sgchannels/4/awg/single')
    def do_set_ch5_rerun(self, x):
        if x==1:
            daq.setInt('/dev12064/sgchannels/4/awg/single', 0)
        if x==0:
            daq.setInt('/dev12064/sgchannels/4/awg/single', 1)
        else:
            print("Wrong input for rerun/single.")
    def do_get_ch6_rerun(self):
        return daq.getInt('/dev12064/sgchannels/5/awg/single')
    def do_set_ch6_rerun(self, x):
        if x==1:
            daq.setInt('/dev12064/sgchannels/5/awg/single', 0)
        if x==0:
            daq.setInt('/dev12064/sgchannels/5/awg/single', 1)
        else:
            print("Wrong input for rerun/single.")
    def do_get_ch7_rerun(self):
        return daq.getInt('/dev12064/sgchannels/6/awg/single')
    def do_set_ch7_rerun(self, x):
        if x == 1:
            daq.setInt('/dev12064/sgchannels/6/awg/single', 0)
        if x == 0:
            daq.setInt('/dev12064/sgchannels/6/awg/single', 1)
        else:
            print("Wrong input for rerun/single.")
    def do_get_ch8_rerun(self):
        return daq.getInt('/dev12064/sgchannels/7/awg/single')
    def do_set_ch8_rerun(self, x):
        if x == 1:
            daq.setInt('/dev12064/sgchannels/7/awg/single', 0)
        if x == 0:
            daq.setInt('/dev12064/sgchannels/7/awg/single', 1)
        else:
            print("Wrong input for rerun/single.")

    def do_set_ch1_triggersignal(self, x):
        daq.setInt('/dev12064/sgchannels/0/awg/auxtriggers/0/channel', x)
    def do_set_ch2_triggersignal(self, x):
        daq.setInt('/dev12064/sgchannels/1/awg/auxtriggers/0/channel', x)
    def do_set_ch3_triggersignal(self, x):
        daq.setInt('/dev12064/sgchannels/2/awg/auxtriggers/0/channel', x)
    def do_set_ch4_triggersignal(self, x):
        daq.setInt('/dev12064/sgchannels/3/awg/auxtriggers/0/channel', x)
    def do_set_ch5_triggersignal(self, x):
        daq.setInt('/dev12064/sgchannels/4/awg/auxtriggers/0/channel', x)
    def do_set_ch6_triggersignal(self, x):
        daq.setInt('/dev12064/sgchannels/5/awg/auxtriggers/0/channel', x)
    def do_set_ch7_triggersignal(self, x):
        daq.setInt('/dev12064/sgchannels/6/awg/auxtriggers/0/channel', x)
    def do_set_ch8_triggersignal(self, x):
        daq.setInt('/dev12064/sgchannels/7/awg/auxtriggers/0/channel', x)

    def do_set_ch1_triggerslope(self, x):
        daq.setInt('/dev12064/sgchannels/0/awg/auxtriggers/0/slope', x)
    def do_set_ch2_triggerslope(self, x):
        daq.setInt('/dev12064/sgchannels/1/awg/auxtriggers/0/slope', x)
    def do_set_ch3_triggerslope(self, x):
        daq.setInt('/dev12064/sgchannels/2/awg/auxtriggers/0/slope', x)
    def do_set_ch4_triggerslope(self, x):
        daq.setInt('/dev12064/sgchannels/3/awg/auxtriggers/0/slope', x)
    def do_set_ch5_triggerslope(self, x):
        daq.setInt('/dev12064/sgchannels/4/awg/auxtriggers/0/slope', x)
    def do_set_ch6_triggerslope(self, x):
        daq.setInt('/dev12064/sgchannels/5/awg/auxtriggers/0/slope', x)
    def do_set_ch7_triggerslope(self, x):
        daq.setInt('/dev12064/sgchannels/6/awg/auxtriggers/0/slope', x)
    def do_set_ch8_triggerslope(self, x):
        daq.setInt('/dev12064/sgchannels/7/awg/auxtriggers/0/slope', x)

    def upload_awg(self, channel, ccode):

        shfsg_utils.load_sequencer_program(daq, "dev12064", channel-1, ccode)
        daq.sync()
        time.sleep(0.05)

    def start_awg_chan1(self):
        daq.setInt('/dev12064/sgchannels/0/awg/enable', 1)
        daq.sync()

    def twotone_pulse(self, freq, length):

        seq = """
        const freq = """ + str(freq) + """;
        const len = """ + str(length) + """;

        wave i = sine(len, 1, 0, len*freq/2e9);
        wave q = sine(len, 1, -3.141593/2, len*freq/2e9);
        const delay = 416;

        while(true){
        waitDigTrigger(1);
        playZero(delay, 2e9);
        waitWave();
        playWave(1,2, i, 1, 2, q);
        playZero(10000);
        }"""

        chan_index = 0
        shfsg_utils.load_sequencer_program(daq, "dev12064", 0, seq)
        daq.setInt('/dev12064/sgchannels/0/awg/enable', 1)

        self.setup_triggering(length)

    awg_shfsg = daq.awgModule()
    awg_shfsg.set('device', 'DEV12064')
    awg_shfsg.execute()

    def setup_triggering(self, delay):

        daq.setInt('/dev12064/sgchannels/1/awg/single', 1)
        daq.setInt('/dev12064/sgchannels/1/awg/auxtriggers/0/channel', 8)
        daq.setInt('/dev12064/sgchannels/1/awg/auxtriggers/0/slope', 1)

        seq = """
        while (true) {
        waitDigTrigger(1);
        playZero(""" + str(delay) + """, 2e9);
        playWave(join(marker(8,1), marker(24,0)));
        }

    """

        import zhinst.deviceutils.shfsg as shfsg_utils

        awg_seqc = seq

        chan_index = 1
        shfsg_utils.load_sequencer_program(daq, "dev12064", chan_index, awg_seqc)
        daq.setInt('/dev12064/sgchannels/2/awg/time', 0)  # set sampling rate to 2GHz
        daq.sync()
        daq.setInt('/dev12064/sgchannels/1/awg/enable', 1)

    def set_cont_driving_modulation(self, freq, length, shots, delay):
        seq = """

        var f;


        const len =""" + str(length) + """;

        wave i = sine(len, 1, 0, """ + str(freq / 1e6) + """*len/4/500);
        wave q = sine(len, 1, -3.1415926/2, """ + str(freq / 1e6) + """*len/4/500);

        const marker_pos = 0;
        wave m_left = marker(""" + str(length - delay) + """, 0);

        wave m_right = marker(12, 1);
        wave w_marker = join(m_left, m_right);
        wave ii = i+w_marker;

        for(f=0; f<""" + str(shots) + """;f++){
        //resetOscPhase();
        playWave(1,2,ii, 1,2,q); 
        playZero(100000);}"""

        import zhinst.deviceutils.shfsg as shfsg_utils

        awg_seqc = seq

        chan_index = 0
        shfsg_utils.load_sequencer_program(daq, "dev12064", chan_index, awg_seqc)
