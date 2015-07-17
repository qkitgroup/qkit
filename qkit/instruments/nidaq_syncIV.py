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

DAQmx_Val_CountUp           = 10128
DAQmx_Val_CountDown         = 10124
DAQmx_Val_ExtControlled     = 10326

def CHK(err):
    '''Error checking routine'''

    if err < 0:
        buf_size = 100
        buf = ctypes.create_string_buffer('\000' * buf_size)
        nidaq.DAQmxGetErrorString(err, ctypes.byref(buf), buf_size)
        raise RuntimeError('Nidaq call failed with error %d: %s' %(err, repr(buf.value)))

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
    #print config
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
        print str(e)
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



def sync_write_read(O_devchan,I_devchan,waveform,**kwargs):
    #,rate=1000,minv=-10.0, maxv=10.0,timeout=10.0):
    '''
    Write values to one channel and read synchronized at another channel

    Input:
        I_devchan (string): device/channel specifier, such as Dev1/ai0
        O_devchan (string): device/channel specifier, such as Dev1/ao0
        waveform (numpy.array): data to write to O_devchan
        rate (float): the write/read rate in Hz
        minv (float): the minimum voltage
        maxv (float): the maximum voltage
        timeout (float): the time in seconds to wait for completion

    Output:
        Numpy array containing data read.
    '''
    # fixme: check this
    rate=kwargs.get('rate',1000)
    minv=kwargs.get('minv',-10.0)
    maxv=kwargs.get('maxv',10.0)
    timeout=kwargs.get('timeout',100.0)

    debug = False
    oversamples = 10
    sampswritten=int32()
    sampsread=int32()

    #
    # make sure data is a numpy array, single values should be passed  
    # as an array (or list) with a minium of two numbers like this: [3,3]
    #
    waveform=numpy.array(waveform,dtype=numpy.float64)
    samples = waveform.size
    
    # Due to Nyquist theorem: sampling rate and samples have to be doubled for reading
    # align fix: After the trigger we read (samples+1) samples and throw away the first 
    # (trigger sample) later
    AI_rate = oversamples* rate
    AI_samples =oversamples* samples
    readbuf = numpy.zeros(AI_samples+1,dtype=numpy.float64)
    #~ readbuf = numpy.zeros(AI_samples,dtype=numpy.float64)

    #
    # Check if the StartTrigger option is available
    # 
    DAQmx_Val_Bit_TriggerUsageTypes_Start = 8
    triggerAvailable = ctypes.c_int32()
    CHK(nidaq.DAQmxGetDevAITrigUsage(I_devchan, ctypes.byref(triggerAvailable)))
    if not ((int(triggerAvailable.value) & DAQmx_Val_Bit_TriggerUsageTypes_Start) == DAQmx_Val_Bit_TriggerUsageTypes_Start):
        raise RuntimeError("Error: Input trigger for synchronization is not available on this device")

    #   
    # create task handles for input and output
    #
    AI = TaskHandle(0)
    AO = TaskHandle(1)
    
    #
    # prepare Analog Input
    #
    CHK(nidaq.DAQmxCreateTask("0", ctypes.byref(AI)))
    CHK(nidaq.DAQmxCreateAIVoltageChan(AI, I_devchan, "",
                                        DAQmx_Val_Cfg_Default,
                                        float64(minv), float64(maxv),
                                        DAQmx_Val_Volts, None))
    CHK(nidaq.DAQmxCfgSampClkTiming(AI, "", float64(AI_rate),
                                        DAQmx_Val_Rising, DAQmx_Val_FiniteSamps,
                                        uInt64(AI_samples+1)));
    #~ CHK(nidaq.DAQmxCfgSampClkTiming(AI, "", float64(AI_rate),
                                        #~ DAQmx_Val_Rising, DAQmx_Val_FiniteSamps,
                                        #~ uInt64(AI_samples)));
    #
    # prepare Analog Output AO
    #
    CHK(nidaq.DAQmxCreateTask("1", ctypes.byref(AO)))
    CHK(nidaq.DAQmxCreateAOVoltageChan(AO, O_devchan, "",
                                        float64(minv), float64(maxv), 
                                        DAQmx_Val_Volts, None))
    CHK(nidaq.DAQmxCfgSampClkTiming(AO, "", float64(rate),
                                        DAQmx_Val_Rising, DAQmx_Val_FiniteSamps, 
                                        uInt64(samples)))
    #
    # register internal trigger, AI starts with AO
    # /Dev1/ao/StartTrigger is the reference name to the output start trigger
    #
    triggerName = '/Dev1/ao/StartTrigger'
    CHK(nidaq.DAQmxCfgDigEdgeStartTrig(AI,triggerName,DAQmx_Val_Rising))
    
    CHK(nidaq.DAQmxWriteAnalogF64(AO, samples, 0, float64(timeout),
                    DAQmx_Val_GroupByChannel, waveform.ctypes.data,
                    ctypes.byref(sampswritten), None))
    if debug:
        print "Debug: read_write() Analog-Output buffer written:",waveform,sampswritten

    #
    # start the tasks, sampling of (samples +1) at AI is started when AO startet
    #
    CHK(nidaq.DAQmxStartTask(AI))
    CHK(nidaq.DAQmxStartTask(AO))
    
    CHK(nidaq.DAQmxWaitUntilTaskDone(AI, float64(timeout)))
    CHK(nidaq.DAQmxReadAnalogF64(AI, AI_samples+1, float64(timeout),
                                 DAQmx_Val_GroupByChannel, readbuf.ctypes.data,
                                 AI_samples+1, ctypes.byref(sampsread), None))
    #~ CHK(nidaq.DAQmxReadAnalogF64(AI, AI_samples+1, float64(timeout),
                                 #~ DAQmx_Val_GroupByChannel, readbuf.ctypes.data,
                                 #~ AI_samples+1, ctypes.byref(sampsread), None))
    
    if debug:
        print "Debug: read_write() Analog-Input buffer read:", readbuf ,readbuf.size

    # stop the whole thing, fixme: use try...except !
    if AO.value != 0:
        nidaq.DAQmxStopTask(AO)
        nidaq.DAQmxClearTask(AO)

    if AI.value != 0:
        nidaq.DAQmxStopTask(AI)
        nidaq.DAQmxClearTask(AI)

    # again align fix: throw away the first sample and average over the read samples 
    # to get the shape than put in
    #for i in arange(len(b)): b[i] = (a[2*i]+a[2*i+1])/2.0
    #readbuf = numpy.delete(readbuf,0)
    returnbuf = numpy.zeros(samples)
    
    aveis = numpy.arange(oversamples)
    if debug:
        print len(readbuf), len(returnbuf), aveis
    for i in numpy.arange(samples):
            for ii in aveis:
                returnbuf[i] += readbuf[oversamples*i+ii]
    return returnbuf/float(oversamples)
    
if __name__ == '__main__':
    # some tests
    buf= numpy.linspace(0,5,10)
    print sync_write_read('Dev1/ai0','Dev1/ao0',buf,rate=100000)
    
