# nidaq.py, python wrapper for NIDAQ DLL
# Reinier Heeres <reinier@heeres.eu>, 2008
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

import ctypes
import types
import numpy
import logging
import time

nidaq = ctypes.windll.nicaiu

int32 = ctypes.c_long
uInt32 = ctypes.c_ulong
uInt64 = ctypes.c_ulonglong
float64 = ctypes.c_double
TaskHandle = uInt32

DAQmx_Val_Cfg_Default = int32(-1)

DAQmx_Val_RSE               = 10083
DAQmx_Val_NRSE              = 10078
DAQmx_Val_Diff              = 10106
DAQmx_Val_PseudoDiff        = 12529

_config_map = {
    'DEFAULT': DAQmx_Val_Cfg_Default,
    'RSE': DAQmx_Val_RSE,
    'NRSE': DAQmx_Val_NRSE,
    'DIFF': DAQmx_Val_Diff,
    'PSEUDODIFF': DAQmx_Val_PseudoDiff,
}

DAQmx_Val_Volts             = 10348
DAQmx_Val_Rising            = 10280
DAQmx_Val_FiniteSamps       = 10178
DAQmx_Val_GroupByChannel    = 0
DAQmx_Val_GroupByScanNumber = 1
DAQmx_Val_ChanPerLine       = 0
DAQmx_Val_ChanForAllLines   = 1

DAQmx_Val_CountUp           = 10128
DAQmx_Val_CountDown         = 10124
DAQmx_Val_ExtControlled     = 10326

def CHK(err):
    '''Error checking routine'''

    if err < 0:
        buf_size = 100
        buf = ctypes.create_string_buffer('\000' * buf_size)
        nidaq.DAQmxGetErrorString(err, ctypes.byref(buf), buf_size)
        raise RuntimeError('Nidaq call failed with error %d: %s' % \
            (err, repr(buf.value)))

def buf_to_list(buf):
    name = ''
    namelist = []
    for ch in buf:
        if ch in '\000 \t\n':
            name = name.rstrip(',')
            if len(name) > 0:
                namelist.append(name)
                name = ''
            if ch == '\000':
                break
        else:
            name += ch

    return namelist

def get_device_names():
    '''Return a list of available NIDAQ devices.'''

    bufsize = 1024
    buf = ctypes.create_string_buffer('\000' * bufsize)
    nidaq.DAQmxGetSysDevNames(ctypes.byref(buf), bufsize)
    return buf_to_list(buf)

def reset_device(dev):
    '''Reset device "dev"'''
    nidaq.DAQmxResetDevice(dev)

def get_physical_input_channels(dev):
    '''Return a list of physical input channels on a device.'''

    bufsize = 1024
    buf = ctypes.create_string_buffer('\000' * bufsize)
    nidaq.DAQmxGetDevAIPhysicalChans(dev, ctypes.byref(buf), bufsize)
    return buf_to_list(buf)

def get_physical_output_channels(dev):
    '''Return a list of physical output channels on a device.'''

    bufsize = 1024
    buf = ctypes.create_string_buffer('\000' * bufsize)
    nidaq.DAQmxGetDevAOPhysicalChans(dev, ctypes.byref(buf), bufsize)
    return buf_to_list(buf)

def get_digital_output_channels(dev):
    '''Return a list of physical output channels on a device.'''

    bufsize = 1024
    buf = ctypes.create_string_buffer('\000' * bufsize)
    nidaq.DAQmxGetDevDOLines(dev, ctypes.byref(buf), bufsize)
    return buf_to_list(buf)

def get_physical_counter_channels(dev):
    '''Return a list of physical counter channels on a device.'''

    bufsize = 1024
    buf = ctypes.create_string_buffer('\000' * bufsize)
    nidaq.DAQmxGetDevCIPhysicalChans(dev, ctypes.byref(buf), bufsize)
    return buf_to_list(buf)

def read(devchan, samples=1, freq=10000.0, minv=-10.0, maxv=10.0,
            timeout=10.0, config=DAQmx_Val_Cfg_Default):
    '''
    Read up to max_samples from a channel. Seems to have trouble reading
    1 sample!

    Input:
        devchan (string): device/channel specifier, such as Dev1/ai0
        samples (int): the number of samples to read
        freq (float): the sampling frequency
        minv (float): the minimum voltage
        maxv (float): the maximum voltage
        timeout (float): the time in seconds to wait for completion
        config (string or int): the configuration of the channel

    Output:
        A numpy.array with the data on success, None on error
    '''

    if type(config) is types.StringType:
        if config in _config_map:
            config = _config_map[config]
        else:
            return None
    if type(config) is not types.IntType:
        return None

    if samples == 1:
        retsamples = 1
        samples = 2
    else:
        retsamples = samples

    data = numpy.zeros(samples, dtype=numpy.float64)

    taskHandle = TaskHandle(0)
    read = int32()
    try:
        CHK(nidaq.DAQmxCreateTask("", ctypes.byref(taskHandle)))
        CHK(nidaq.DAQmxCreateAIVoltageChan(taskHandle, devchan, "",
            config,
            float64(minv), float64(maxv),
            DAQmx_Val_Volts, None))

        if retsamples > 1:
            CHK(nidaq.DAQmxCfgSampClkTiming(taskHandle, "", float64(freq),
                DAQmx_Val_Rising, DAQmx_Val_FiniteSamps,
                uInt64(samples)));
            CHK(nidaq.DAQmxStartTask(taskHandle))
            CHK(nidaq.DAQmxReadAnalogF64(taskHandle, samples, float64(timeout),
                DAQmx_Val_GroupByChannel, data.ctypes.data,
                samples, ctypes.byref(read), None))
        else:
            CHK(nidaq.DAQmxReadAnalogScalarF64(taskHandle, float64(timeout),
                data.ctypes.data, None))
            read = int32(1)

    except Exception, e:
        logging.error('NI DAQ call failed: %s', str(e))
    finally:
        if taskHandle.value != 0:
            nidaq.DAQmxStopTask(taskHandle)
            nidaq.DAQmxClearTask(taskHandle)

    if read > 0:
        if retsamples == 1:
            return data[0]
        else:
            return data[:read.value]
    else:
        return None

def write(devchan, data, freq=10000.0, minv=-10.0, maxv=10.0,
                timeout=10.0):
    '''
    Write values to channel

    Input:
        devchan (string): device/channel specifier, such as Dev1/ao0
        data (int/float/numpy.array): data to write
        freq (float): the the minimum voltage
        maxv (float): the maximum voltage
        timeout (float): the time in seconds to wait for completion

    Output:
        Number of values written
    '''

    if type(data) in (types.IntType, types.FloatType):
        data = numpy.array([data], dtype=numpy.float64)
    elif isinstance(data, numpy.ndarray):
        if data.dtype is not numpy.float64:
            data = numpy.array(data, dtype=numpy.float64)
    elif len(data) > 0:
        data = numpy.array(data, dtype=numpy.float64)
    samples = len(data)

    taskHandle = TaskHandle(0)
    written = int32()
    try:
        CHK(nidaq.DAQmxCreateTask("", ctypes.byref(taskHandle)))
        CHK(nidaq.DAQmxCreateAOVoltageChan(taskHandle, devchan, "",
            float64(minv), float64(maxv), DAQmx_Val_Volts, None))

        if len(data) == 1:
            CHK(nidaq.DAQmxWriteAnalogScalarF64(taskHandle, 1, float64(timeout),
                float64(data[0]), None))
            written = int32(1)
        else:
            CHK(nidaq.DAQmxCfgSampClkTiming(taskHandle, "", float64(freq),
                DAQmx_Val_Rising, DAQmx_Val_FiniteSamps, uInt64(samples)))
            CHK(nidaq.DAQmxWriteAnalogF64(taskHandle, samples, 0, float64(timeout),
                DAQmx_Val_GroupByChannel, data.ctypes.data,
                ctypes.byref(written), None))
            CHK(nidaq.DAQmxStartTask(taskHandle))
    except Exception, e:
        logging.error('NI DAQ call failed (correct channel configuration selected?): %s', str(e))
    finally:
        if taskHandle.value != 0:
            nidaq.DAQmxStopTask(taskHandle)
            nidaq.DAQmxClearTask(taskHandle)

    return written.value

def read_counter(devchan="/Dev1/ctr0", samples=1, freq=1.0, timeout=1.0, src=""):
    '''
    Read counter 'devchan'.
    Specify source pin with 'src'.
    '''

    taskHandle = TaskHandle(0)
    try:
        CHK(nidaq.DAQmxCreateTask("", ctypes.byref(taskHandle)))
        initial_count = int32(0)
        CHK(nidaq.DAQmxCreateCICountEdgesChan(taskHandle, devchan, "",
                DAQmx_Val_Rising, initial_count, DAQmx_Val_CountUp))
        if src is not None and src != "":
            CHK(nidaq.DAQmxSetCICountEdgesTerm(taskHandle, devchan, src))

        nread = int32()
        data = numpy.zeros(samples, dtype=numpy.float64)
        if samples > 1:
            CHK(nidaq.DAQmxCfgSampClkTiming(taskHandle, "", float64(freq),
                DAQmx_Val_Rising, DAQmx_Val_FiniteSamps,
                uInt64(samples)));
            CHK(nidaq.DAQmxStartTask(taskHandle))
            CHK(nidaq.DAQmxReadAnalogF64(taskHandle, int32(samples), float64(timeout),
               DAQmx_Val_GroupByChannel, data.ctypes.data,
               samples, ctypes.byref(read), None))
        else:
            CHK(nidaq.DAQmxStartTask(taskHandle))
            time.sleep(1.0 / freq)
            nread = int32(0)
            CHK(nidaq.DAQmxReadCounterF64(taskHandle, int32(samples), float64(timeout),
                data.ctypes.data, int32(samples), ctypes.byref(nread), None))
            nread = int32(1)

    except Exception, e:
        logging.error('NI DAQ call failed: %s', str(e))

    finally:
        if taskHandle.value != 0:
            nidaq.DAQmxStopTask(taskHandle)
            nidaq.DAQmxClearTask(taskHandle)

    if nread.value == 1:
        return int(data[0])
    else:
        return data

def create_counter_task(devchan, samples=1, freq=1, timeout=1, src=""):
    taskHandle = TaskHandle(0)

    try:
        CHK(nidaq.DAQmxCreateTask("", ctypes.byref(taskHandle)))
        initial_count = int32(0)
        CHK(nidaq.DAQmxCreateCICountEdgesChan(taskHandle, devchan, "",
                DAQmx_Val_Rising, initial_count, DAQmx_Val_CountUp))
        if src is not None and src != "":
            CHK(nidaq.DAQmxSetCICountEdgesTerm(taskHandle, devchan, src))

        if samples > 1:
            CHK(nidaq.DAQmxCfgSampClkTiming(taskHandle, "", float64(freq),
                DAQmx_Val_Rising, DAQmx_Val_FiniteSamps,
                uInt64(samples)));

    except Exception, e:
        logging.error('NI DAQ call failed: %s', str(e))
        if taskHandle.value != 0:
            nidaq.DAQmxStopTask(taskHandle)
            nidaq.DAQmxClearTask(taskHandle)

    return taskHandle

def read_counters(devchans=["/Dev1/ctr0","/Dev1/ctr1"], samples=1, freq=1.0, timeout=1.0, src=None):
    tasks = []
    devsrc = None
    ret = []
    for i, dev in enumerate(devchans):
        if src is not None:
            devsrc = src[i]
        result = create_counter_task(dev, samples, freq, timeout, devsrc)
        if result != -1:
            tasks.append(result)

    try:
        for task in tasks:
            CHK(nidaq.DAQmxStartTask(task))

        time.sleep(float(samples) / freq)

        for task in tasks:
            data = numpy.zeros(samples, dtype=numpy.float64)
            if samples > 1:
                CHK(nidaq.DAQmxReadAnalogF64(task, int32(samples), float64(timeout),
                        DAQmx_Val_GroupByChannel, data.ctypes.data,
                        samples, ctypes.byref(read), None))
                ret.append(data)
            else:
                nread = int32(0)
                CHK(nidaq.DAQmxReadCounterF64(task, int32(samples), float64(timeout),
                    data.ctypes.data, int32(samples), ctypes.byref(nread), None))
                nread = int32(1)
                ret.append(data[0])

    except Exception, e:
        logging.error('NI DAQ call failed: %s', str(e))

    finally:
        for task in tasks:
            if task.value != 0:
                nidaq.DAQmxStopTask(task)
                nidaq.DAQmxClearTask(task)

    return ret

def write_dig_port8(channel, val, timeout=1.0):
    '''
    Set digital output of channels.
    The value is sent to the specified channels, LSB to MSB.
    '''

    taskHandle = TaskHandle(0)
    try:
        CHK(nidaq.DAQmxCreateTask("", ctypes.byref(taskHandle)))
        CHK(nidaq.DAQmxCreateDOChan(taskHandle, channel, '', DAQmx_Val_ChanForAllLines))

        nwritten = int32(0)

#        val = numpy.array((val,), dtype=numpy.int16)
#       This requires shifting bits if writing to part of a port
#        CHK(nidaq.DAQmxWriteDigitalU16(taskHandle, int32(1), int32(1),
#            float64(1.0), int32(DAQmx_Val_GroupByChannel), val.ctypes.data, ctypes.byref(nwritten), None))

        vals = numpy.array([(val >> i) & 1 for i in range(8)], dtype=numpy.int8)
        nbytes = int32(0)
        CHK(nidaq.DAQmxGetWriteDigitalLinesBytesPerChan(taskHandle, ctypes.byref(nbytes)))
        CHK(nidaq.DAQmxWriteDigitalLines(taskHandle, int32(1), int32(1),
            float64(1.0), int32(DAQmx_Val_GroupByChannel), vals.ctypes.data, ctypes.byref(nwritten), None))

        CHK(nidaq.DAQmxStartTask(taskHandle))

    except Exception, e:
        logging.error('NI DAQ call failed: %s', str(e))

    finally:
        if taskHandle.value != 0:
            nidaq.DAQmxStopTask(taskHandle)
            nidaq.DAQmxClearTask(taskHandle)
