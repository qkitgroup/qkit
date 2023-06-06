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
import numpy as np
import logging
import time

nidaq = ctypes.windll.nicaiu

int32 = ctypes.c_long
int64 = ctypes.c_longlong
uInt32 = ctypes.c_ulong
uInt64 = ctypes.c_ulonglong
float64 = ctypes.c_double
TaskHandle = uInt64

DAQmx_Val_Cfg_Default = int32(-1)
DAQmx_Val_RSE = 10083
DAQmx_Val_NRSE = 10078
DAQmx_Val_Diff = 10106
DAQmx_Val_PseudoDiff = 12529
_config_map = {'DEFAULT': DAQmx_Val_Cfg_Default,
               'RSE': DAQmx_Val_RSE,
               'NRSE': DAQmx_Val_NRSE,
               'DIFF': DAQmx_Val_Diff,
               'PSEUDODIFF': DAQmx_Val_PseudoDiff,
               }

DAQmx_Val_Volts = 10348
DAQmx_Val_Rising = 10280
DAQmx_Val_FiniteSamps = 10178
DAQmx_Val_GroupByChannel = 0
DAQmx_Val_GroupByScanNumber = 1

DAQmx_Val_CountUp = 10128
DAQmx_Val_CountDown = 10124
DAQmx_Val_ExtControlled = 10326


def CHK(err):
    """
    Error checking routine raises an error, if it gets an error code.

    Parameters
    ----------
    err: int
        Error number.

    Returns
    -------
    None
    """
    if err < 0:
        buf_size = 500
        buf = ctypes.create_string_buffer(b'\000' * buf_size)
        nidaq.DAQmxGetErrorString(err, ctypes.byref(buf), buf_size)
        raise RuntimeError('Nidaq call failed with error %d: %s' % (err, repr(buf.value)))

def buf_to_list(buf):
    """
    Decodes a buffer to a python list

    Parameters
    ----------
    buf: str
        Buffer to be decoded and split to a list.

    Returns
    -------
    list: list
        List generated from buffer.
    """
    return buf.raw.decode('ascii').rstrip('\x00').split(', ')

def get_device_names():
    """
    Gets a list of available NI DAQ devices.

    Parameters
    ----------
    None

    Returns
    -------
    names: list(str)
        list of available NI DAQ devices
    """
    bufsize = 1024
    buf = ctypes.create_string_buffer(b'\000' * bufsize)
    nidaq.DAQmxGetSysDevNames(ctypes.byref(buf), bufsize)
    return buf_to_list(buf)

def reset_device(dev):
    """
    Resets device.

    Parameters
    ----------
    dev: str
        Device name to be reset.

    Returns
    -------
    None
    """
    nidaq.DAQmxResetDevice(dev.encode('ascii'))

def get_physical_input_channels(dev):
    """
    Gets all physical input channels of a device.

    Parameters
    ----------
    dev: str
        Device name of interest.

    Returns
    -------
    channels: list(str)
        Physical input channels.
    """
    bufsize = 1024
    buf = ctypes.create_string_buffer(b'\000' * bufsize)
    nidaq.DAQmxGetDevAIPhysicalChans(dev.encode('ascii'), ctypes.byref(buf), bufsize)
    return buf_to_list(buf)

def get_physical_output_channels(dev):
    """
    Gets all physical output channels of a device.

    Parameters
    ----------
    dev: str
        Device name of interest.

    Returns
    -------
    channels: list(str)
        Physical output channels.
    """
    bufsize = 1024
    buf = ctypes.create_string_buffer(b'\000' * bufsize)
    nidaq.DAQmxGetDevAOPhysicalChans(dev.encode('ascii'), ctypes.byref(buf), bufsize)
    return buf_to_list(buf)

def get_physical_counter_channels(dev):
    """
    Gets all physical counter channels of a device.

    Parameters
    ----------
    dev: str
        Device name of interest.

    Returns
    -------
    channels: list(str)
        Physical counter channels.
    """
    bufsize = 1024
    buf = ctypes.create_string_buffer(b'\000' * bufsize)
    nidaq.DAQmxGetDevCIPhysicalChans(dev.encode('ascii'), ctypes.byref(buf), bufsize)
    return buf_to_list(buf)

def write(devchan, data, freq=1e4, minv=-10.0, maxv=10.0, timeout=10.0):
    """
    Writes analog output values <data> to channel <devchan> with sample frequency <freq>.

    Parameters
    ----------
    devchan: str
        Device/output_channel specifier, such as 'Dev1/ao0'.
    data: int/float/np.array
        Voltage data to write in Volts.
    freq: float
        Sample frequency in Hertz.
    minv: float
        Minimum voltage in Volts.
    maxv: float
        Maximum voltage in Volts.
    timeout: float
        Time to wait for completion in seconds.

    Returns
    -------
    written: int
        Number of values written
    """
    if isinstance(data, float) or isinstance(data, int):
        data = np.array([data], dtype=np.float64)
    elif isinstance(data, np.ndarray) and data.dtype is not np.float64:
        data = np.array(data, dtype=np.float64)
    elif data.size > 0:
        data = np.array(data, dtype=np.float64)
    samples = data.size
    AO_TaskHandle = TaskHandle(0)
    written = int32()
    try:
        CHK(nidaq.DAQmxCreateTask(b"", ctypes.byref(AO_TaskHandle)))
        CHK(nidaq.DAQmxCreateAOVoltageChan(AO_TaskHandle,
                                           devchan.encode('ascii'),
                                           b"",
                                           float64(minv),
                                           float64(maxv),
                                           DAQmx_Val_Volts,
                                           None))
        if data.size == 1:
            CHK(nidaq.DAQmxWriteAnalogScalarF64(AO_TaskHandle,
                                                1,
                                                float64(timeout),
                                                float64(data),
                                                None))
            written = int32(1)
        else:
            CHK(nidaq.DAQmxCfgSampClkTiming(AO_TaskHandle,
                                            b"",
                                            float64(freq),
                                            DAQmx_Val_Rising,
                                            DAQmx_Val_FiniteSamps,
                                            uInt64(samples)))
            CHK(nidaq.DAQmxWriteAnalogF64(AO_TaskHandle,
                                          samples,
                                          0,
                                          float64(timeout),
                                          DAQmx_Val_GroupByChannel,
                                          data.ctypes.data,
                                          ctypes.byref(written),
                                          None))
            CHK(nidaq.DAQmxStartTask(AO_TaskHandle))
    except Exception as e:
        logging.error('NI DAQ call failed (correct channel configuration selected?): %s', str(e))
    finally:
        if AO_TaskHandle.value != 0:
            nidaq.DAQmxStopTask(AO_TaskHandle)
            nidaq.DAQmxClearTask(AO_TaskHandle)
    return written.value

def read(devchan, samples=1, freq=1e4, minv=-10.0, maxv=10.0, timeout=10.0, config=DAQmx_Val_Cfg_Default):
    """
    Reads analog input values <data> of channel <devchan> with sample frequency <freq>.

    Parameters
    ----------
    devchan: str
        Device/input_channel specifier, such as 'Dev1/ai0'.
    samples: int
        Number of samples to read up to max_samples.
    freq: float
        Sample frequency in Hertz.
    minv: float
        Minimum voltage in Volts.
    maxv: float
        Maximum voltage in Volts.
    timeout: float
        Time to wait for completion in seconds.
    config: str/int
        Channel configuration.

    Returns
    -------
    data: float/np.array/None
        Read voltage data in Volts on success or None on error.
    """
    if isinstance(config, str):
        if config in _config_map:
            config = _config_map[config]
        else:
            return None
    if not type(config) in (int32, int64, uInt32, uInt64):
        return None
    if samples == 1:
        retsamples = 1
        samples = 2
    else:
        retsamples = samples
    data = np.zeros(samples, dtype=np.float64)
    AI_TaskHandle = TaskHandle(0)
    read = int32()
    try:
        CHK(nidaq.DAQmxCreateTask(b"", ctypes.byref(AI_TaskHandle)))
        CHK(nidaq.DAQmxCreateAIVoltageChan(AI_TaskHandle,
                                           devchan.encode('ascii'),
                                           b"",
                                           config,
                                           float64(minv),
                                           float64(maxv),
                                           DAQmx_Val_Volts,
                                           None))
        if retsamples > 1:
            CHK(nidaq.DAQmxCfgSampClkTiming(AI_TaskHandle,
                                            b"",
                                            float64(freq),
                                            DAQmx_Val_Rising,
                                            DAQmx_Val_FiniteSamps,
                                            uInt64(samples)))
            CHK(nidaq.DAQmxStartTask(AI_TaskHandle))
            CHK(nidaq.DAQmxReadAnalogF64(AI_TaskHandle,
                                         samples,
                                         float64(timeout),
                                         DAQmx_Val_GroupByChannel,
                                         ctypes.c_int64(data.ctypes.data),
                                         samples,
                                         ctypes.byref(read),
                                         None))
        else:
            CHK(nidaq.DAQmxReadAnalogScalarF64(AI_TaskHandle,
                                               float64(timeout),
                                               ctypes.c_int64(data.ctypes.data),
                                               None))
            read = int32(1)
    except Exception as e:
        print(str(e))
        logging.error('NI DAQ call failed: %s', str(e))
    finally:
        if AI_TaskHandle.value != 0:
            nidaq.DAQmxStopTask(AI_TaskHandle)
            nidaq.DAQmxClearTask(AI_TaskHandle)
    if read.value > 0:
        if retsamples == 1:
            return data[0]
        else:
            return data[:read.value]
    else:
        return None

def read_counter(devchan, samples=1, freq=1.0, timeout=1.0, src=""):
    """
    Reads counter values <data> of channel <devchan> with sample frequency <freq>.

    Parameters
    ----------
    devchan: str
        Device/input_channel specifier, such as 'Dev1/ctr0'.
    samples: int
        Number of samples to read up to max_samples.
    freq: float
        Sample frequency in Hertz.
    timeout: float
        Time to wait for completion in seconds.
    src: str
        Specified source pin.

    Returns
    -------
    data: float/np.array/None
        Read counter data on success or None on error.
    """
    Crt_TaskHandle = TaskHandle(0)
    try:
        CHK(nidaq.DAQmxCreateTask(b"", ctypes.byref(Crt_TaskHandle)))
        initial_count = int32(0)
        CHK(nidaq.DAQmxCreateCICountEdgesChan(Crt_TaskHandle,
                                              devchan.encode('ascii'),
                                              b"",
                                              DAQmx_Val_Rising,
                                              initial_count,
                                              DAQmx_Val_CountUp))
        if src is not None and src != "":
            CHK(nidaq.DAQmxSetCICountEdgesTerm(Crt_TaskHandle,
                                               devchan.encode('ascii'),
                                               src))
        nread = int32()
        data = np.zeros(samples, dtype=np.float64)
        if samples > 1:
            CHK(nidaq.DAQmxCfgSampClkTiming(Crt_TaskHandle,
                                            b"",
                                            float64(freq),
                                            DAQmx_Val_Rising,
                                            DAQmx_Val_FiniteSamps,
                                            uInt64(samples)))
            CHK(nidaq.DAQmxStartTask(Crt_TaskHandle))
            CHK(nidaq.DAQmxReadAnalogF64(Crt_TaskHandle,
                                         int32(samples),
                                         float64(timeout),
                                         DAQmx_Val_GroupByChannel,
                                         ctypes.c_int64(data.ctypes.data),
                                         samples,
                                         ctypes.byref(read),
                                         None))
        else:
            CHK(nidaq.DAQmxStartTask(Crt_TaskHandle))
            time.sleep(1.0 / freq)
            nread = int32(0)
            CHK(nidaq.DAQmxReadCounterF64(Crt_TaskHandle,
                                          int32(samples),
                                          float64(timeout),
                                          ctypes.c_int64(data.ctypes.data),
                                          int32(samples),
                                          ctypes.byref(nread),
                                          None))
            nread = int32(1)
    except Exception as e:
        logging.error('NI DAQ call failed: %s', str(e))
    finally:
        if Crt_TaskHandle.value != 0:
            nidaq.DAQmxStopTask(Crt_TaskHandle)
            nidaq.DAQmxClearTask(Crt_TaskHandle)
    if nread.value == 1:
        return int(data[0])
    else:
        return data

def sync_write_read(O_devchan, I_devchan, waveform, rate=1e3, minv=-10.0, maxv=10.0, timeout=10.0, config=DAQmx_Val_Cfg_Default):
    """
    Writes values <waveform> to an output channel <O_devchan> and reads synchronized an input channel <I_devchan> with rate <rate>.

    Parameters
    ----------
    O_devchan: strs
        Device/output_channel specifier, such as 'Dev1/ao0'.
    I_devchan: str
        Device/input_channel specifier, such as 'Dev1/ai0'.
    waveform: list/np.array
        Voltage data to write to O_devchan in Volts.
    rate: float
        Write/read rate in Hertz.
    minv: float
        Minimum voltage in Volts.
    maxv: float
        Maximum voltage in Volts.
    timeout: float
        Time to wait for completion in seconds.
    config: str/int
        Channel configuration.

    Returns
    -------
    data: np.array
        Sense data.
    """
    if type(config) is str:
        if config in _config_map:
            config = _config_map[config]
        else:
            return None
    if not type(config) in (int, int32, uInt32, uInt64):
        return None
    debug = False
    oversamples = 10
    sampswritten = int32()
    sampsread = int32()
    # cast data to np.array
    waveform = np.array(waveform, dtype=np.float64)
    samples = waveform.size
    # Due to Nyquist theorem: sampling rate and samples have to be doubled for reading
    # align fix: After the trigger we read (samples+1) samples and throw away the first
    # (trigger sample) later
    AI_rate = oversamples * rate
    AI_samples = oversamples * samples
    readbuf = np.zeros(AI_samples + 1, dtype=np.float64)
    # Check if the StartTrigger option is available
    DAQmx_Val_Bit_TriggerUsageTypes_Start = 8
    triggerAvailable = ctypes.c_int32()
    CHK(nidaq.DAQmxGetDevAITrigUsage(I_devchan.encode('ascii'), ctypes.byref(triggerAvailable)))
    if not ((int(triggerAvailable.value) & DAQmx_Val_Bit_TriggerUsageTypes_Start) == DAQmx_Val_Bit_TriggerUsageTypes_Start):
        raise RuntimeError('Error: Input trigger for synchronization is not available on this device')
    # create task handles for input and output
    AI_TaskHandle = TaskHandle(0)
    AO_TaskHandle = TaskHandle(1)
    # prepare Analog Input
    CHK(nidaq.DAQmxCreateTask(str(AI_TaskHandle.value),
                              ctypes.byref(AI_TaskHandle)))
    CHK(nidaq.DAQmxCreateAIVoltageChan(AI_TaskHandle,
                                       I_devchan.encode('ascii'),
                                       b"",
                                       config,
                                       float64(minv),
                                       float64(maxv),
                                       DAQmx_Val_Volts,
                                       None))
    CHK(nidaq.DAQmxCfgSampClkTiming(AI_TaskHandle,
                                    b"",
                                    float64(AI_rate),
                                    DAQmx_Val_Rising,
                                    DAQmx_Val_FiniteSamps,
                                    uInt64(AI_samples + 1)))
    if debug:
        print('Debug: Analog Input AI_TaskHandle prepared')
    # prepare Analog Output
    CHK(nidaq.DAQmxCreateTask(str(AO_TaskHandle.value),
                              ctypes.byref(AO_TaskHandle)))
    CHK(nidaq.DAQmxCreateAOVoltageChan(AO_TaskHandle,
                                       O_devchan.encode('ascii'),
                                       b"",
                                       float64(minv),
                                       float64(maxv),
                                       DAQmx_Val_Volts,
                                       None))
    CHK(nidaq.DAQmxCfgSampClkTiming(AO_TaskHandle,
                                    b"",
                                    float64(rate),
                                    DAQmx_Val_Rising,
                                    DAQmx_Val_FiniteSamps,
                                    uInt64(samples)))
    if debug:
        print('Debug: Analog Output AO_TaskHandle prepared')
    # register internal trigger, AI_TaskHandle starts with AO_TaskHandle
    # /Dev1/ao/StartTrigger is the reference name to the output start trigger
    triggerName = '/'+O_devchan.split('/')[0]+'/ao/StartTrigger'
    CHK(nidaq.DAQmxCfgDigEdgeStartTrig(AI_TaskHandle,
                                       triggerName.encode('ascii'),
                                       DAQmx_Val_Rising))
    CHK(nidaq.DAQmxWriteAnalogF64(AO_TaskHandle,
                                  samples,
                                  0,
                                  float64(timeout),
                                  DAQmx_Val_GroupByChannel,
                                  ctypes.c_int64(waveform.ctypes.data),
                                  ctypes.byref(sampswritten),
                                  None))
    if debug:
        print('Debug: read_write() Analog-Output buffer written:', waveform, sampswritten)
    # start the tasks, sampling of (samples +1) at AI_TaskHandle is started when AO_TaskHandle started
    CHK(nidaq.DAQmxStartTask(AI_TaskHandle))
    CHK(nidaq.DAQmxStartTask(AO_TaskHandle))
    CHK(nidaq.DAQmxWaitUntilTaskDone(AI_TaskHandle,
                                     float64(timeout)))
    CHK(nidaq.DAQmxReadAnalogF64(AI_TaskHandle,
                                 AI_samples + 1,
                                 float64(timeout),
                                 DAQmx_Val_GroupByChannel,
                                 ctypes.c_int64(readbuf.ctypes.data),
                                 AI_samples + 1,
                                 ctypes.byref(sampsread),
                                 None))
    if debug:
        print('Debug: read_write() Analog-Input buffer read:', readbuf, readbuf.size)
    # stop the whole thing, fixme: use try...except !
    if AO_TaskHandle.value != 0:
        nidaq.DAQmxStopTask(AO_TaskHandle)
        nidaq.DAQmxClearTask(AO_TaskHandle)
    if AI_TaskHandle.value != 0:
        nidaq.DAQmxStopTask(AI_TaskHandle)
        nidaq.DAQmxClearTask(AI_TaskHandle)
    # again align fix: throw away the first sample and average over the read samples
    # to get the shape than put in
    returnbuf = np.zeros(samples)
    aveis = np.arange(oversamples)
    if debug:
        print(len(readbuf), len(returnbuf), aveis)
    for i in np.arange(samples):
        for ii in aveis:
            returnbuf[i] += readbuf[oversamples * i + ii]
    return returnbuf / float(oversamples)


if __name__ == '__main__':
    # some tests
    buf = np.linspace(0, 5, 10)
    print(sync_write_read('Dev1/ai0', 'Dev1/ao0', buf, rate=100000))

