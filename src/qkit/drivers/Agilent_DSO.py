# Agilent DSO oscilloscope driver for qtlab
# Markus Jerger <markus.jerger@kit.edu>, 2011
# modified by Sebastian Probst <Sebastian.Probst@kit.edu>, 2012

from qkit.core.instrument_base import Instrument
from qkit import visa
import types
import logging
import numpy as np

class Agilent_DSO(Instrument):
    '''
    This driver is for Agilent digital storage oscilloscopes, in particular the
    DSO81204B 12GHz 40GS/s 4ch oscilloscope
    '''
    
    def __init__(self, name, address):
        '''
        
        Input:
            name (string)
            address (string): VISA address of the device
        '''
        
        Instrument.__init__(self, name, tags=['physical'])
        self._address = address
        self._visainstrument = visa.instrument(self._address)
        
        # number of channels
        self._numchs = 4
        
        # initialize virtual instrument
        self.add_parameter('points', flags = Instrument.FLAG_GETSET, 
            units = '', type = int, minval = 16, maxval = 524288)
        self.add_parameter('segments', flags = Instrument.FLAG_GETSET, 
            units = '', type = int)
        self.add_parameter('averages', flags = Instrument.FLAG_GETSET, 
            units = '', type = int, minval = 1, maxval = 4096)
        self.add_parameter('average_enabled', flags = Instrument.FLAG_GETSET, 
            units = '', type = bool)
                    
        self.add_parameter('samplerate', flags = Instrument.FLAG_GETSET, 
            units = 'Hz', type = float)
        self.add_parameter('bandwidth', flags = Instrument.FLAG_GETSET, 
            units = 'Hz', type = float)
        self.add_parameter('acqmode', flags = Instrument.FLAG_GET, 
            type = str)
        self.add_function('acqmode_realtime')
        self.add_function('acqmode_peakdetect')
        self.add_function('acqmode_highres')
        self.add_function('acqmode_segmented')
            
        self.add_parameter('refclock', flags = Instrument.FLAG_GETSET,
            type = bool)
        self.add_parameter('xoffset', flags = Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units = 's', type = float)
        self.add_parameter('xrange', flags = Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            units = 's', type = float)
        
        self.add_parameter('yoffset', flags = Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET, 
            units = 'V', type = float, channels=(1, self._numchs), channel_prefix='ch%d_')
        self.add_parameter('yrange', flags = Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET, 
            units = 'V', type = float, channels=(1, self._numchs), channel_prefix='ch%d_')
            
        self.add_function('reset')
        self.add_function('preset')
        self.add_function('clear_status')
        self.add_function('get_error')
        self.add_function('message')
        self.add_function('acq_digitize')
        self.add_function('acq_run')
        self.add_function('acq_single')
        self.add_function('acq_stop')
        self.add_function('get_triggered')
        self.add_function('get_done')
        self.add_function('get_completedpercent')
        self.add_function('get_averages_acquired')
        self.add_function('autoscale')
        self.add_function('get_data_old')
        self.add_function('get_data')
        self.add_function('restart_average')
        self.add_function('get_completed')
        self.add_function('get_meas_phase')
        self.add_function('get_meas_vamp')
        self.add_function('get_meas_vrms')
        self.add_function('get_meas_frequency')
        
        # to do: functions to setup maths on the oscilloscope
        # to do: histogram functions
        # to do: marker stuff
        # to do: measurements
        # to do: trigger setup functions

        # initialize physical instrument
        self._visainstrument.write(':SYST:HEAD OFF')
        self._visainstrument.write(':SYST:LONG OFF')
        self._visainstrument.write(':WAV:BYT LSBF') # faster
            
    # memory management: points, segments and averages
    def do_set_average_enabled(self,value):
        if value: self._visainstrument.write(':ACQ:AVER ON')
        else: self._visainstrument.write(':ACQ:AVER Off')
        
    def do_get_average_enabled(self):
        if 1 == self._visainstrument.ask(':ACQ:AVER?'): value=True
        else: value = False
        return value
    
    def do_get_points(self):
        return int(self._visainstrument.ask(':ACQ:POIN?'))
    def do_set_points(self, value):
        self._visainstrument.write(':ACQ:POIN %d'%value)
    def do_get_segments(self):
        return int(self._visainstrument.ask(':ACQ:SEGM:COUN?'))
    def do_set_segments(self, value):
        self._visainstrument.write(':ACQ:SEGM:COUN %d'%value)
    def do_get_averages(self):
        avgon = 1 == int(self._visainstrument.ask(':ACQ:AVER?'))
        if(avgon):
            return int(self._visainstrument.ask(':ACQ:AVER:COUN?'))
        else:
            return 1
    def do_set_averages(self, value):
        if(value > 1):
            self._visainstrument.write(':ACQ:AVER 1')
            self._visainstrument.write(':ACQ:AVER:COUN %d'%value)
        else:
            self._visainstrument.write(':ACQ:AVER 0')


    # acquisition options bandwidth
    def do_get_samplerate(self):
        srate = self._visainstrument.ask(':ACQ:SRATE?')
        if(srate == 'AUTO'):
            return 0
        else:
            return float(srate)
    def do_set_samplerate(self, value):
        if(value == 0): value = 'AUTO'
        if(value == inf): value = 'MAX'
        self._visainstrument.write(':ACQ:BAND %s'%string(value))    
    def do_get_bandwidth(self):
        band = self._visainstrument.ask(':ACQ:BAND?')
        if(band == 'AUTO'):
            return inf
        else:
            return float(band)
    def do_set_bandwidth(self, value):
        if value in [0,inf] : value = 'AUTO'   ##((value == 0) || (value == inf))
        self._visainstrument.write(':ACQ:BAND %s'%string(value))
    def do_get_acqmode(self):
        '''
            acquisition mode may be RTIM, PDET, HRES, SEGM
        '''
        return self._visainstrument.ask(':ACQ:MODE?')
    def acqmode_realtime(self):
        self._visainstrument.write(':ACQ:MODE RTIM')
    def acqmode_peakdetect(self):
        self._visainstrument.write(':ACQ:MODE PDET')
    def acqmode_highres(self):
        self._visainstrument.write(':ACQ:MODE HRES')
    def acqmode_segmented(self):
        self._visainstrument.write(':ACQ:MODE SEGM')
    
    # timebase functions
    def do_get_xoffset(self,):
        '''
            return the delay between trigger event and the delay reference point
        '''
        return float(self._visainstrument.ask(':TIM:POS?'))
    def do_set_xoffset(self, value):
        return self._visainstrument.write(':TIM:POS %e'%value)
    def do_get_xrange(self,):
        '''
            return the delay between trigger event and the delay reference point
        '''
        return float(self._visainstrument.ask(':TIM:RANG?'))
    def do_set_xrange(self, value):
        return self._visainstrument.write(':TIM:RANG %e'%value)    
    def do_get_refclock(self):
        '''
            use external 10MHz reference?
        '''
        return '1' == self._visainstrument.ask(':TIM:REFC?')
    def do_set_refclock(self, value):
        return self._visainstrument.write(':TIM:REFC %d'%int(value))
        
    # per channel functions
    def do_get_yoffset(self, channel):
        return float(self._visainstrument.ask(':CHAN%d:OFFS?'%channel))
    def do_set_yoffset(self, value, channel):
        return self._visainstrument.write(':CHAN%d:OFFS %e'%(channel, value))
    def do_get_yrange(self, channel):
        return float(self._visainstrument.ask(':CHAN%d:RANG?'%channel))
    def do_set_yrange(self, value, channel):
        return self._visainstrument.write(':CHAN%d:RANG %e'%(channel, value))
        
    # functions
    def reset(self):
        self._visainstrument.write('*RST')
    def preset(self):
        self._visainstrument.write(':PRES')
    def autoscale(self):
        self._visainstrument.write(':AUT')
    def clear_status(self):
        '''
            clear status bits and empty error queue
        '''
        self._visainstrument.write('*CLS')
    def get_error(self):
        '''
            return error code and message of the next error in the queue
            if the queue is empty or the last entry was reached, returns a 0 error code
            
            Returns:
                (int) error code, (string) error message
        '''
        reply = self._visainstrument.ask(':SYST:ERR? STR')
        errno, null, errmsg = str.partition(reply)
        return int(errno), errmsg[1:-1]
    def message(self, value):
        '''
            display a message on the advisory line
        '''
        self._visainstrument.write(':SYST:DSP %s'%str(value))
    def acq_digitize(self, channels = None, functions = None):
        '''
            runs the instument in digitizer mode
            measurement and math operations will not be executed
            (see chapter 6 of the programming manual for an example)
            Input:
                channels/functions - numbers of the channels or functions to acquire
        '''
        channels = ['CHAN%d'%x for x in channels]
        functions = ['FUNC%d'%x for x in functions]
        parameter = ', '.join(channels + functions)
        self._visainstrument.write(':DIG %s'%parameter)
    def acq_run(self):
        '''
            runs the instrument in standard mode
        '''
        self._visainstrument.write('*TRG')
    def acq_single(self):
        '''
            runs the instrument in single acquisition mode
        '''
        self._visainstrument.write(':SING')
    def acq_stop(self):
        '''
            stops the instrument
        '''
        self._visainstrument.write(':STOP')
    def get_triggered(self):
        '''
            returns True if the instrument was triggered since the last call
        '''
        return '1' == self._visainstrument.ask(':TER?')
    def get_done(self):
        '''
            returns True if the acquisition has finished
        '''
        return 1 == self._visainstrument.ask(':ADER?')
    def get_completedpercent(self):
        return float(self._visainstrument.ask(':WAV:COMP?'))
        
    def get_completed(self):
        return float(self._visainstrument.ask(':ACQ:COMP?'))

    def get_averages_acquired(self):
        return int(self._visainstrument.ask(':WAV:COUNT?'))
        
    def restart_average(self):
        self.do_set_average_enabled(False)
        self.do_set_average_enabled(True)
        
    def get_data_old(self, channel):
        '''
            retrieve waveform data from the oscilloscope
            
            Input:
                source - CHAN<N>, FUNC<N>, HIST, WMEM<N>
            Returns:
                data as a numpy array of floats
                preamble sent by the device
        '''
        # retrieve data preamble
        self._visainstrument.write(':WAV:VIEW ALL; :WAV:FORM WORD')
        values = self._visainstrument.ask(':WAV:PRE?')#.split(',')
        print len(values)
        print values
        values = values.split(',')
        print values
        def conv_to_float_if_possible(val):
            for x in val:
                if x.replace('.','',1).isdigit()==True : x=float(x)
            return val
        values = [conv_to_float_if_possible(value) for value in values]
        parts = [
            'format', 'type', 'points', 'count', 
            'Xincrement', 'Xorigin', 'Xreference',
            'Yincrement', 'Yorigin', 'Yreference', 'coupling', 
            'Xdisprange', 'Xdisporigin', 'Ydisprange', 'Ydisporigin',
            'date', 'time', 'framemodelno', 'acqmode', 'completion',
            'Xunits', 'Yunits', 'lowerBWlimit', 'upperBWlimit'
        ]
        print len(parts)
        print len(values)
        print values
        preamble = {}
        for i in range(len(parts)):
            preamble.update({parts[i]:values[i]})  #this is very strange values[0][i]
        ##preamble = dict(parts=values)
        
        
        # retrieve data from device
        self._visainstrument.write(':WAV:SOUR %s'%channel)
        raw_data = self._visainstrument.ask_for_values(':WAV:DATA?', '') # start,size; format ascii, single, double, big_endian
        ##print np.shape(raw_data)
        ##print raw_data
        ##data = np.fromstring(raw_data, np.int16) ###??? not float?
        data = 0
        
        return data, preamble
        
    def get_data(self, channel, format='ascii'): #format='word' doesn't work!!!
        '''
            retrieve waveform data from the oscilloscope
            
            Input:
                source - CHAN<N>, FUNC<N>, HIST, WMEM<N>
            Returns:
                data as a numpy array of floats
                preamble sent by the device
        '''
        self._visainstrument.write(':WAV:SOUR CHAN%i' %channel)
        self._visainstrument.write(':WAV:BYTEORDER LSBF')
        if format=='ascii': self._visainstrument.write(':WAV:FORM ASCii')
        if format=='word': self._visainstrument.write(':WAV:FORM WORD')
        xUnits = self._visainstrument.ask(':WAV:XUN?')
        xOrigin = float(self._visainstrument.ask(':WAV:XOR?'))
        xIncrement = float(self._visainstrument.ask(':WAV:XINC?'))
        #print xIncrement
        xPoints = int(self._visainstrument.ask(':WAV:POIN?'))
        #print xPoints
        
        xData = [xOrigin+xIncrement*i for i in range(xPoints)]
        
        yOrigin = float(self._visainstrument.ask(':WAV:YOR?'))
        yIncrement = float(self._visainstrument.ask(':WAV:YINC?'))
        if format=='word':
            yData = self._visainstrument.ask_for_values(':WAV:DATA?',format=1)
            yData = [yOrigin+yIncrement*float(i) for i in yData]
        if format=='ascii': yData = [float(i) for i in self._visainstrument.ask(':WAV:DATA?').split(',')]
        return xData, yData
        
    #measurement functions
    def get_meas_phase(self, channel1, channel2):
        return float(self._visainstrument.ask(':MEAS:PHAS? CHAN%d,CHAN%d'%(channel1,channel2)))
        
    def get_meas_vamp(self, channel1):
        return float(self._visainstrument.ask(':MEAS:VAMP? CHAN%d'%channel1))

    def get_meas_vrms(self,channel1,display=True,ac=True):
        '''
            Get RMS Voltage value of channel1
            display: Calculate RMS over whole display (true) or single cycle (false)
            AC: Remove DC component (true) or include it (false)
        '''        
        return float(self._visainstrument.ask(':MEAS:VRMS? %s,%s,CHAN%d'%('DISP' if display else 'CYCL','AC' if ac else 'DC',channel1)))
        
    def get_meas_area(self,channel1,display=True):
        '''
            Get RMS Voltage value of channel1
            display: Calculate RMS over whole display (true) or single cycle (false)
        '''        
        return float(self._visainstrument.ask(':MEAS:AREA? %s,CHAN%d'%('DISP' if display else 'CYCL',channel1)))
    
    def get_meas_frequency(self, channel1):
        return float(self._visainstrument.ask(':MEAS:FREQ? CHAN%d'%channel1))    
    
    def get_meas(self):
        return self._visainstrument.ask(':MEAS:RES?')
    
    def set_meas_statistics(self, parameter):
        self._visainstrument.write(':MEAS:STAT %s'%parameter)
    
    def ask(self, question):
        return self._visainstrument.ask('%s'%question)
    def write(self, question):
        return self._visainstrument.write('%s'%question)
