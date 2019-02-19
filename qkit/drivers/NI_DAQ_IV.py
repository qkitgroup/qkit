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
import qkit.instruments.nidaq_syncIV as nidaq
import numpy
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

        for ch_out in self._get_output_channels():
            ch_out = _get_channel(ch_out)
            self.add_parameter(ch_out,
                               flags=Instrument.FLAG_SET,
                               type=float,
                               units='V',
                               tags=['sweep'],
                               set_func=self.do_set_output,
                               channel=ch_out)

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

        self.reset()
        self.set_chan_config('RSE')
        self.set_count_time(0.1)
        self.get_all()

        self._dAdV = 1
        self._dAdV_B = 1
        self._dVdA = 1
        self._amp = 1

    def set_dAdV(self, dAdV=1):
        self._dAdV = dAdV

    def set_dAdV_B(self, dAdV_B=1):
        self._dAdV_B = dAdV_B

    def get_dAdV_B(self):
        return self._dAdV_B

    def set_amplification(self, amp=1):
        self._amp = amp

    def set_dVdA(self, dVdA=1):
        self._dVdA = dVdA

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

    def get_bias_mode(self, channel=1):
        return 'curr'

    def set_status(self, status, channel=1):
        return True

    def set_devchan(self, O_devchan='Dev1/ao0', I_devchan='Dev1/ai0'):
        self.O_devchan = O_devchan
        self.I_devchan = I_devchan

    def set_step_time(self, step_time):
        self._step_time = step_time

    def set_sweep_parameters(self, sweep, channel=1):
        self._step = sweep[2]
        self.waveform = numpy.arange(sweep[0], sweep[1], sweep[2])
        self.rate = 1. / self._step_time
        self.set_ao0(sweep[0] / self._dAdV)

    def take_IV(self, channel=1):
        in_data = self.waveform / self._dAdV
        out_data = nidaq.sync_write_read(self.O_devchan, self.I_devchan, in_data, rate=self.rate) / self._amp
        return self.waveform, out_data

    """
    def ramp_current(self, target, step, wait=0.1, channel=1):
        '''
        Ramps current from current value to <target>
        
        Input:
            target (float)
            step (float)
            wait (float)
        Output:
            None
        '''
        start = self.get_ao1()*self._dAdV_B
        if(target < start): step = -step
        for i in numpy.concatenate((numpy.arange(start, target, step)[1:], [target])):
            self.set_ao1(i/self._dAdV_B)
            time.sleep(wait)
    """

    def write(self, devchan, data, freq=10000.0, minv=-10.0, maxv=10.0, timeout=10.0):
        return nidaq.write(devchan, data, freq=freq, minv=minv, maxv=maxv, timeout=timeout)

    def read(self, devchan, samples=1, freq=10000.0, minv=-10.0, maxv=10.0, timeout=10.0):
        return nidaq.read(devchan, samples=samples, freq=freq, minv=minv, maxv=maxv, timeout=timeout,
                          config=self._chan_config)


def detect_instruments():
    '''Refresh NI DAQ instrument list.'''

    for name in nidaq.get_device_names():
        qkit.instruments.create('NI%s' % name, 'NI_DAQ', id=name)
