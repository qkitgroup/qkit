# NI_DAQ.py, National Instruments Data AcQuisition instrument driver
# Reinier Heeres <reinier@heeres.eu>, 2009
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
# DAQ=qt.instruments.create('DAQ', 'NI_DAQ_IV',id='Dev1')
import qkit
from qkit.core.instrument_base import Instrument
import types
import nidaq_syncIV as nidaq
import numpy as np
import time


def _get_channel(devchan):
    if not '/' in devchan:
        return devchan
    parts = devchan.split('/')
    if len(parts) != 2:
        return devchan
    return parts[1]


class NI_DAQ_IV(Instrument):

    def __init__(self, name, id):
        self.__name__ = __name__ # 'NI_DAQ' #
        Instrument.__init__(self, name, tags=['physical'])

        self._id = id

        for ch_in in self._get_input_channels():
            ch_in = _get_channel(ch_in)
            self.add_parameter(ch_in,
                               flags=Instrument.FLAG_GET,
                               type=float,
                               units='V',
                               tags=['measure'],
                               get_func=self.do_get_input,
                               channel=ch_in)
        self._plc = 50.
        self._sense_nplc = None
        self._bias_values = {} # dict with {channel: value}
        for i, ch_out in enumerate(self._get_output_channels()):
            ch_out = _get_channel(ch_out)
            self.add_parameter(ch_out,
                               flags=Instrument.FLAG_SET,
                               type=float,
                               units='V',
                               tags=['sweep'],
                               set_func=self.do_set_output,
                               channel=ch_out)
            self.set_bias_value(val=0, channel=i)

        for ch_ctr in self._get_counter_channels():
            ch_ctr = _get_channel(ch_ctr)
            self.add_parameter(ch_ctr,
                               flags=Instrument.FLAG_GET,
                               type=int,
                               units='#',
                               tags=['measure'],
                               get_func=self.do_get_counter,
                               channel=ch_ctr)
            self.add_parameter(ch_ctr + "_src",
                               flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
                               type=str,
                               set_func=self.do_set_counter_src,
                               channel=ch_ctr)

        self.add_parameter('chan_config',
                           flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
                           type=str,
                           option_list=('Default', 'RSE', 'NRSE', 'Diff', 'PseudoDiff'))

        self.add_parameter('count_time',
                           flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
                           type=float,
                           units='s')

        self.add_function('reset')
        self.add_function('read')
        self.add_function('write')
        self.add_function('sync_output_input')


        self.O_devchan = self._id+'/ao0'
        self.I_devchan = self._id+'/ai0'

        self.reset()
        self.set_chan_config('RSE')
        self.set_count_time(0.1)
        self.get_all()

    def write(self, devchan, data, freq=10000.0, minv=-10.0, maxv=10.0, timeout=10.0):
        return nidaq.write(devchan, data, freq=freq, minv=minv, maxv=maxv, timeout=timeout)

    def read(self, devchan, samples=1, freq=10000.0, minv=-10.0, maxv=10.0, timeout=10.0):
        return nidaq.read(devchan, samples=samples, freq=freq, minv=minv, maxv=maxv, timeout=timeout,
                          config=self._chan_config)

    ####################################################################################################################
    ### functions needed for transport.py and virtual_tunnel_electronics.py                                          ###
    ####################################################################################################################

    def get_measurement_mode(self, channel=0):
        return 1  # 4-wire

    def get_bias_mode(self, channel=0):
        return 1  # voltage bias

    def get_sense_mode(self, channel=0):
        return 1  # voltage bias

    def get_bias_range(self, channel=0):
        return -1  # 5V

    def get_sense_range(self, channel=0):
        return -1  # 5V

    def get_bias_delay(self, channel=0):
        return 0

    def get_sense_delay(self, channel=0):
        return 0

    def get_sense_average(self, channel=0):
        return 1

    def get_plc(self):
        return self._plc

    def set_sense_nplc(self, val, channel=0):
        self._sense_nplc = val

    def get_sense_nplc(self, channel=0):
        return self._sense_nplc

    def set_bias_value(self, val, channel=0):
        self._bias_values[channel] = val
        nidaq.write('{:s}/ao{:d}'.format(self._id, channel), val)

    def get_bias_value(self, channel=0):
        return self._bias_values[channel]

    def get_sense_value(self, channel=0):
        return nidaq.read('{:s}/ai{:d}'.format(self._id, channel), config=self._chan_config)

    def set_status(self, status, channel=0):
        pass
        #if not status:
        #    self.set_bias_value(val=0, channel=channel)

    def get_sweep_mode(self):
        return 0  (VV-mode)

    def get_sweep_channels(self):
        return (1,2)#(self.O_devchan, self.I_devchan)

    def get_sweep_bias(self):
        return 1  # voltage

    def set_step_time(self, step_time):
        self._step_time = step_time

    def set_sweep_mode(self, *args, **kwargs):
        pass

    def get_sweep_mode(self):
        return 0

    def set_sweep_parameters(self, sweep):
        start = float(sweep[0])
        stop = float(sweep[1])
        step = float(sweep[2])
        nop = int(round(abs((stop-start)/step)+1))
        self.waveform = np.linspace(start, np.sign(stop)*(np.floor(np.abs(np.round(float(stop-start)/step)))*step)+start, nop) # stop is rounded down to multiples of step
        self.rate = self._plc/self._sense_nplc
        self.set_bias_value(start)
        time.sleep(1./self.rate)

    def get_tracedata(self):
        in_data = self.waveform
        out_data = nidaq.sync_write_read(self.O_devchan, self.I_devchan, in_data, rate=self.rate)
        return self.waveform, out_data



    ####################################################################################################################
    ### old version                                                                                                  ###
    ####################################################################################################################

    def get_all(self):
        ch_in = [_get_channel(ch) for ch in self._get_input_channels()]
        self.get(ch_in)

    def reset(self):
        '''Reset device.'''
        nidaq.reset_device(self._id)

    def _get_input_channels(self):
        return nidaq.get_physical_input_channels(self._id)

    def _get_output_channels(self):
        return nidaq.get_physical_output_channels(self._id)

    def _get_counter_channels(self):
        return nidaq.get_physical_counter_channels(self._id)

    def do_get_input(self, channel):
        devchan = '%s/%s' % (self._id, channel)
        return nidaq.read(devchan, config=self._chan_config)

    def do_set_output(self, val, channel):
        devchan = '%s/%s' % (self._id, channel)
        return nidaq.write(devchan, val)

    def do_set_chan_config(self, val):
        self._chan_config = val

    def do_set_count_time(self, val):
        self._count_time = val

    def do_get_counter(self, channel):
        devchan = '%s/%s' % (self._id, channel)
        src = self.get(channel + "_src")
        if src is not None and src != '':
            src = '/%s/%s' % (self._id, src)
        return nidaq.read_counter(devchan, src=src, freq=1 / self._count_time)

    def do_set_counter_src(self, val, channel):
        return True

    def sync_output_input(self, O_devchan, I_devchan, waveform, rate=1000, **kwargs):
        return nidaq.sync_write_read(O_devchan, I_devchan, waveform, rate=rate)


def detect_instruments():
    '''Refresh NI DAQ instrument list.'''

    for name in nidaq.get_device_names():
        qkit.instruments.create('NI%s' % name, 'NI_DAQ', id=name)
