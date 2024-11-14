
# tested on a ZNA67 with a mm Wave extender, thus these parameter limits are set.
# started HR@KIT 2023
# (The inital driver code is substantially based on the QKIT Keysight VNA driver, since 
# the R&S device has for the most part very similar commands.) 
# GPL v2
# Fixme: - several (commented) functions are Keysight related and not working on the ZNA 
#        - not all set parameter limits are real device limits
#        - flow control is not working
#        - some functions and variables are workarounds for the keysight devices and not needed anymore


import qkit
from qkit.core.instrument_base import Instrument
from qkit import visa
import logging
import numpy

class RS_VNA_ZNAXX(Instrument):
    """
    This is the python driver for the ZNA67 Vector Network Analyzer

    Usage:
    Initialise with
    <name> = instruments.create('<name>', address='<GPIB address>', reset=<bool>)

    """

    def __init__(self, name, address, channel_index=1):
        """
        Initializes

        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address
        """
        
        logging.info(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])

        self._address = address
        self.reconnect()
        self._freqpoints = 0
        self._ci = channel_index 
        self._pi = 2 # port_index, similar to self._ci
        self._start = 0
        self._stop = 0
        self._nop = 0
        self._cwfreq = None #MK This parameter tracks the center-freq when switching to nop=1 (cw mode)
        self._hold = None
        self._sweep = None
        self._edel = None
        self._active_trace = None

        # Implement parameters
        self.add_parameter('nop', type=int,
            flags=Instrument.FLAG_GETSET,
            minval=1, maxval=100001,
            tags=['sweep'])

        self.add_parameter('bandwidth', type=float,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=1e11,
            units='Hz', tags=['sweep']) 

        self.add_parameter('averages', type=int,
            flags=Instrument.FLAG_GETSET,
            minval=1, maxval=65536, tags=['sweep'])
        
        
        self.add_parameter('count', type=int,
            flags=Instrument.FLAG_GETSET,
            minval=1, maxval=2e6, tags=['sweep'])
        
        self.add_parameter('Average', type=bool,
            flags=Instrument.FLAG_GETSET)   
                    
        self.add_parameter('centerfreq', type=float,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=130e9,
            units='Hz', tags=['sweep'])

        self.add_parameter('cwfreq', type=float,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=130e9,
            units='Hz', tags=['sweep'])
            
        self.add_parameter('startfreq', type=float,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=130e9,
            units='Hz', tags=['sweep'])            
            
        self.add_parameter('stopfreq', type=float,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=130e9,
            units='Hz', tags=['sweep'])                        
            
        self.add_parameter('span', type=float,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=130e9,
            units='Hz', tags=['sweep'])        
            
        self.add_parameter('power', type=float,
            flags=Instrument.FLAG_GETSET,
            minval=-100, maxval=20, offset=True,
            units='dBm', tags=['sweep'])

        self.add_parameter('startpower', type=float,
            flags=Instrument.FLAG_GETSET,
            minval=-100, maxval=20,
            units='dBm')

        self.add_parameter('stoppower', type=float,
            flags=Instrument.FLAG_GETSET,
            minval=-100, maxval=20,
            units='dBm')

        self.add_parameter('cw', type=bool,
            flags=Instrument.FLAG_GETSET)
            
        self.add_parameter('channel_index', type=int,
            flags=Instrument.FLAG_GETSET)

        self.add_parameter('sweeptime', type=float,   #added by MW
            flags=Instrument.FLAG_GET,
            minval=0, maxval=1e3,
            units='s', tags=['sweep'])
            
        self.add_parameter('sweeptime_averages', type=float,   #JB
            flags=Instrument.FLAG_GET,
            minval=0, maxval=1e3,
            units='s', tags=['sweep'])
        """ 
        self.add_parameter('measurement_parameter', type=str,
                           flags=Instrument.FLAG_GETSET)
        
        self.add_parameter('edel', type=float, # legacy name for parameter. This corresponds to the VNA's port extension values.
            flags=Instrument.FLAG_GETSET, 
            minval=-10, maxval=10,
            units='s', tags=['sweep'],
            channels=(1, self._pi), channel_prefix = 'port%d_') # the channel option for qtlab's Instument class is used here to easily address the two VNA ports
        """ 
        self.add_parameter('edel_status', type=bool, # legacy name for parameter. This corresponds to the VNA's port extension values.
            flags=Instrument.FLAG_GETSET)
                  
        self.add_parameter('sweep_mode', type=str,  #JDB This parameter switches on/off hold. The hold function below does the same job, this is just for code compatibility to the agilent and anritsu drivers.
            flags=Instrument.FLAG_GETSET,tags=['sweep']) 
                    
        self.add_parameter('sweep_type', type=str,
            flags=Instrument.FLAG_GETSET,tags=['sweep'])
        """
        self.add_parameter('active_trace', type=int,
            flags=Instrument.FLAG_GETSET)
        """            
        #Triggering Stuff
        self.add_parameter('trigger_source', type=str,
            flags=Instrument.FLAG_GETSET)
        
        # Implement functions
        self.add_function('get_freqpoints')
        self.add_function('get_tracedata')
        self.add_function('avg_clear')
        #self.add_function('avg_status')
        self.add_function('get_hold')
        self.add_function('hold')
        self.add_function('get_sweeptime')
        self.add_function('get_sweeptime_averages')
        self.add_function('pre_measurement')
        self.add_function('start_measurement')
        self.add_function('ready')
        self.add_function('post_measurement')

        #self.do_set_active_trace(1)
        #self.get_all()
    
    def get_all(self):        
        self.get_nop()
        self.get_power()
        self.get_centerfreq()
        self.get_startfreq()
        self.get_stopfreq()
        self.get_span()
        self.get_bandwidth()
        self.get_trigger_source()
        self.get_Average()
        self.get_averages()
        self.get_freqpoints()   
        self.get_channel_index()
        self.get_sweeptime()
        self.get_sweeptime_averages()
        self.get_edel_status()
        self.get_cw()
        for port in range(self._pi):
            self.get('port%d_edel' % (port+1))
        
    ###
    #Communication with device
    ###
    def reset_vna(self):
        """
        Deletes all traces, measurements, and windows and resets the vna to factory
        defined default settings.
        Creates a S11 measurement named "CH1_S11_1".
        """
        self._visainstrument.write('SYST:PRES')
    
    def hold(self, status):
        """
        Stop sweeping
        This is can be achieved by using "ena emulation language" command swe:mode hold
        or by using init:cont 0/1 which is analog to the query command which isn’t 
        implemented in ena emulation
        """
        if status:
            #self._visainstrument.write('SENS%i:SWE:MODE HOLD'%self._ci)
            self._visainstrument.write('INIT%i:CONT 1'%self._ci) # needed if in single mode
            self._visainstrument.write('INIT%i:CONT 0'%self._ci)
        else:
            #self._visainstrument.write('SENS%i:SWE:MODE CONT'%self._ci)
            self._visainstrument.write('INIT%i:CONT 1'%self._ci)

    def get_hold(self):
        """
        second option is more robust, as the first can not differentiate between a running 
        and finished single sweep. sweep_counter() is always zero if in continuous mode while 
        the set number for count can not be zero
        """
        #return not(bool(int(self._visainstrument.query('INIT%i:CONT?'%self._ci))))
        return (self.do_get_sweep_counter() == self.do_get_count()) # more robust
        
    def avg_clear(self):
        '''
        restarts averaging
        '''
        self._visainstrument.write(':SENS%i:AVER:CLE' % self._ci)

    def avg_status(self): 
        '''
        check if averaging is set or not
        '''
        #return 0 == (int(self._visainstrument.query('STAT:OPER:COND?')) & (1<<4))
        return bool(int(self._visainstrument.query('SENS%i:AVER:STAT?' % self._ci)))

    def get_tracedata(self, format='AmpPha', single=False, averages=None):
        """
        Get the data of the current trace

        Input:
            format (string) : 'AmpPha': Amp in dB and Phase, 'RealImag',

        Output:
            'AmpPha':_ Amplitude and Phase
        """
        if single:
            print('No longer implemented. Use manual trigger source.')
        if averages is not None:

            print('Average parameter no longer supported.')

        self._visainstrument.write('FORM:DATA REAL,32')
        self._visainstrument.write('FORM:BORD SWAPPED') #SWAPPED
        data = self._visainstrument.query_binary_values('CALC%i:DATA? SDAT' %( self._ci))
        data_size = numpy.size(data)
        datareal = numpy.array(data[0:data_size:2])
        dataimag = numpy.array(data[1:data_size:2])
          
        if format == 'RealImag':
            if self.get_cw():
                return numpy.mean(datareal), numpy.mean(dataimag)
            else:
                return datareal, dataimag
        elif format == 'AmpPha':
            if self.get_cw():
                datacomplex = [numpy.mean(datareal + 1j*dataimag)]
                dataamp = numpy.abs(datacomplex)
                datapha = numpy.angle(datacomplex)
            else:
                dataamp = numpy.sqrt(datareal*datareal+dataimag*dataimag)
                datapha = numpy.arctan2(dataimag, datareal)
            return dataamp, datapha
        else:
            raise ValueError('get_tracedata(): Format must be AmpPha or RealImag')
    
    def get_segments(self):
        if self.get_sweep_type(query=False) == "SEGM":
            self._visainstrument.write('FORM:DATA REAL,64')
            self._visainstrument.write('FORM:BORD SWAPPED')
            segments =  [0]
            for x in numpy.reshape(self._visainstrument.query_binary_values("sense:segment:list? SSTOP",datatype="d"),(-1,8)):
                if x[0]>0.5: #the segment is active
                    segments.append(int(x[1])+segments[-1])
            return segments[1:]
        else:
            return []
      
    def get_freqpoints(self, query=False):
        if self.get_sweep_type(query=False) == "SEGM":
            self._visainstrument.write('FORM:DATA REAL,64')
            self._visainstrument.write('FORM:BORD SWAPPED')
            freqs = numpy.array([])
            for x in numpy.reshape(self._visainstrument.query_binary_values("sense:segment:list? SSTOP",datatype="d"),(-1,8)):
                if x[0]>0.5: #the segment is active
                    freqs = numpy.append(freqs,numpy.linspace(x[2],x[3],int(x[1])))
            self._freqpoints = freqs
            return self._freqpoints
        if query:
            self._freqpoints = numpy.array(self._visainstrument.query_ascii_values('SENS:X?'))
        if self.get_cw():
            self._freqpoints = numpy.atleast_1d(self.get_centerfreq())
        else:
            self._freqpoints = numpy.linspace(self._start,self._stop,self._nop)
        return self._freqpoints

    ###
    # SET and GET functions
    ###
    
    def do_set_sweep_mode(self, mode):
        """
        select the sweep mode from 'hold', 'cont', single' and "group"
        single means only one single trace, not all the averages even if averages
         larger than 1 and Average==True
        """
        mode=mode.lower()
        if mode == 'hold':
            self._visainstrument.write('SENS%i:SWE:MODE HOLD' % self._ci)
        elif mode == 'cont':
            self._visainstrument.write('SENS%i:SWE:MODE CONT' % self._ci)
        elif mode == 'single':
            self._visainstrument.write('SENS%i:SWE:MODE SING' % self._ci) # this should do the same as hold but doesn't work although it is documented as ena emulation command
        elif mode == 'group':
            #self._visainstrument.write('SENS%i:SWE:MODE GRO' % self._ci)
            self._visainstrument.write("INIT:CONT:ALL OFF")
            self._visainstrument.write("INIT:SCOP SING")
            self._visainstrument.write("INIT; *OPC")
        else:
            logging.warning('invalid mode')
            
    def do_get_sweep_mode(self):
        return str(self._visainstrument.query(':SENS%i:SWE:MODE?' % self._ci)).rstrip()
    
    def do_set_nop(self, nop):
        """
        Set Number of Points (nop) for sweep

        Input:
            nop (int) : Number of Points

        Output:
            None
        """
        logging.debug(__name__ + ' : setting Number of Points to %s ' % nop)
        self._visainstrument.write(':SENS%i:SWE:POIN %i' %(self._ci,nop))
        self._nop = nop
        self.get_freqpoints() #Update List of frequency points
        
    def do_get_nop(self):
        """
        Get Number of Points (nop) for sweep

        Input:
            None
        Output:
            nop (int)
        """

        self._nop = int(self._visainstrument.query(':SENS%i:SWE:POIN?' % self._ci))
        return self._nop 
    
    def do_set_Average(self, status):
        """
        Set status of Average

        Input:
            status (boolean)

        Output:
            None
        """
        logging.debug(__name__ + ' : setting Average to "%s"' % status)
        if status:
            status = 'ON'
            self._visainstrument.write('SENS%i:AVER:STAT %s' % (self._ci,status))
        elif not status:
            status = 'OFF'
            self._visainstrument.write('SENS%i:AVER:STAT %s' % (self._ci,status))
        else:
            raise ValueError('set_Average(): can only set True or False')

    def do_get_Average(self):
        """
        Get status of Average

        Input:
            None

        Output:
            Status of Averaging (boolean)
        """
        logging.debug(__name__ + ' : getting average status')
        return bool(int(self._visainstrument.query('SENS%i:AVER:STAT?' % self._ci)))
                    
    def do_set_averages(self, av, sync_sweep_counter=True):
        """
        Set number of averages

        Input:
            av (int) : Number of averages
            sync_sweep_counter (bool) : set number of sweeps to number of averages (reproduce keyside behavior)
        Output:
            None
        """
        logging.debug(__name__ + ' : setting Number of averages to %i ' % av)
        self._visainstrument.write('SENS%i:AVER:COUN %i' % (self._ci,av))
        self.avg_clear()
        
        if sync_sweep_counter:
            self.do_set_count(av,  sync_average=False)
            
    def do_get_averages(self):
        """
        Get number of averages

        Input:
            None
        Output:
            Number of averages
        """
        logging.debug(__name__ + ' : getting Number of Averages')
        return int(self._visainstrument.query('SENS%i:AVER:COUN?' % self._ci))

    def do_set_count(self, co, sync_average=True):
        """
        Sets the trigger count (groups)

        Input:
            co (int) : Count number
            sync_average (bool) : sets average to the same number, which also restarts averaging
        Output:
            None
        """
        logging.debug(__name__ + ' : setting count number to %i ' % co)
        self._visainstrument.write('SENS%i:SWE:COUN %i' % (self._ci,co))
        if sync_average:
            self.do_set_averages(co, sync_sweep_counter=False)

    def do_get_count(self):
        """
        Sets the trigger count (groups)

        Input:
            None
        Output:
            Count number
        """
        logging.debug(__name__ + ' : getting count number')
        return int(self._visainstrument.query('SENS%i:SWE:COUN?' % self._ci))

    def do_set_power(self, pow, port=1):
        """
        Set probe power

        Input:
            pow (float) : Power in dBm

        Output:
            None
        """
        logging.debug(__name__ + ' : setting power to %s dBm' % pow)
        self._visainstrument.write('SOUR%i:POW%i %.1f' % (self._ci, port, pow))

    def do_get_power(self, port=1):
        """
        Get probe power

        Input:
            None

        Output:
            pow (float) : Power in dBm
        """
        logging.debug(__name__ + ' : getting power')
        return float(self._visainstrument.query('SOUR%i:POW%i?' % (self._ci, port)))

    def do_set_startpower(self, pow):
        """
        Set probe power

        Input:
            pow (float) : Power in dBm

        Output:
            None
        """
        logging.debug(__name__ + ' : setting startpower to %s dBm' % pow)
        self._visainstrument.write('SOUR%i:POW:START %.1f' % (self._ci,pow))

    def do_get_startpower(self):
        """
        Get probe power

        Input:
            None

        Output:
            pow (float) : Power in dBm
        """
        logging.debug(__name__ + ' : getting startpower')
        return float(self._visainstrument.query('SOUR%i:POW:START?' % self._ci))

    def do_set_stoppower(self, pow):
        """
        Set probe power

        Input:
            pow (float) : Power in dBm

        Output:
            None
        """
        logging.debug(__name__ + ' : setting stoppower to %s dBm' % pow)
        self._visainstrument.write('SOUR%i:POW:STOP %.1f' % (self._ci,pow))

    def do_get_stoppower(self):
        """
        Get probe power

        Input:
            None

        Output:
            pow (float) : Power in dBm
        """
        logging.debug(__name__ + ' : getting stoppower')
        return float(self._visainstrument.query('SOUR%i:POW:STOP?' % self._ci))
                
    def do_set_centerfreq(self, cf):
        """
        Set the center frequency

        Input:
            cf (float) :Center Frequency in Hz

        Output:
            None
        """
        logging.debug(__name__ + ' : setting center frequency to %s' % cf)
        self._visainstrument.write('SENS%i:FREQ:CENT %f' % (self._ci,cf))
        self.get_startfreq()
        self.get_stopfreq()
        self.get_span()

    def do_get_centerfreq(self):
        """
        Get the center frequency

        Input:
            None

        Output:
            cf (float) :Center Frequency in Hz
        """
        logging.debug(__name__ + ' : getting center frequency')
        return  float(self._visainstrument.query('SENS%i:FREQ:CENT?' % self._ci))

    def do_set_cwfreq(self, cf):
        """ set cw frequency """
        if self.get_cw():
            self._visainstrument.write('SENS%i:FREQ:CENT %f' %(self._ci, cf))
            self._cwfreq = cf
        else:
            self._cwfreq = cf

    def do_get_cwfreq(self):
        """ get cw frequency """
        if self.get_cw():
            return  float(self._visainstrument.query('SENS%i:FREQ:CENT?' % self._ci))
        else:
            return self._cwfreq

    def do_set_span(self, span):
        """
        Set Span

        Input:
            span (float) : Span in KHz

        Output:
            None
        """
        logging.debug(__name__ + ' : setting span to %s Hz' % span)
        self._visainstrument.write('SENS%i:FREQ:SPAN %i' % (self._ci,span))
        self.get_startfreq()
        self.get_stopfreq()
        self.get_centerfreq()
        
    def do_get_span(self):
        """
        Get Span

        Input:
            None

        Output:
            span (float) : Span in Hz
        """
        return float(self._visainstrument.query('SENS%i:FREQ:SPAN?' % self._ci)) 
        


    def do_get_sweeptime_averages(self):###JB
# was ist das im vergleich zu do_get_sweeptime()
        """
        Get sweeptime

        Input:
            None

        Output:
            sweep time (float) times number of averages: sec
        """
        return self.get_sweeptime() * (self.get_averages() if self.get_Average() else 1)
        
    def do_get_sweeptime(self):  #added MW July 2013
        """
        Get sweeptime

        Input:
            None

        Output:
            sweep time (float) : sec
        """
        logging.debug(__name__ + ' : getting sweep time')
        self._sweep=float(self._visainstrument.query('SENS1:SWE:TIME?'))
        return self._sweep

    def do_set_edel(self, val, channel):  # MP 04/2017
        """
        Set electrical delay
        """
        logging.debug(__name__ + ' : setting port %s extension to %s sec' % (channel, val))
        self._visainstrument.write('SENS1:CORR:EXT:PORT%i:TIME %.12f' % (channel, val))

    def do_get_edel(self, channel):   # MP 04/2017
        """
        Get electrical delay
        """
        logging.debug(__name__ + ' : getting port %s extension' % channel)
        self._edel = float(self._visainstrument.query('SENS1:CORR:EXT:PORT%i:TIME?'% channel))
        return  self._edel   
        
    def do_set_edel_status(self, status):   # AS 04/2019
        """
        Set electrical delay
        """
        logging.debug(__name__ + ' : setting port extension status to %s' % status)
        self._visainstrument.write('SENS:CORR:EXT:STAT %i' % status)

    def do_get_edel_status(self):   # AS 04/2019

        """
        Get electrical delay

        """
        logging.debug(__name__ + ' :  port extension status')
        #return  self._visainstrument.query('SENS:CORR:EXT:STAT?').strip() == "1"
        return True

    def do_set_startfreq(self, val):
        """
        Set Start frequency

        Input:
            span (float) : Frequency in Hz

        Output:
            None
        """
        logging.debug(__name__ + ' : setting start freq to %s Hz' % val)
        self._visainstrument.write('SENS%i:FREQ:STAR %f' % (self._ci,val))
        self._start = val
        self.get_centerfreq()
        self.get_stopfreq()
        self.get_span()
        
    def do_get_startfreq(self):
        """
        Get Start frequency

        Input:
            None

        Output:
            span (float) : Start Frequency in Hz
        """
        logging.debug(__name__ + ' : getting start frequency')
        self._start = float(self._visainstrument.query('SENS%i:FREQ:STAR?' % self._ci))
        return  self._start

    def do_set_stopfreq(self, val):
        """
        Set STop frequency

        Input:
            val (float) : Stop Frequency in Hz

        Output:
            None
        """
        logging.debug(__name__ + ' : setting stop freq to %s Hz' % val)
        self._visainstrument.write('SENS%i:FREQ:STOP %f' % (self._ci,val))
        self._stop = val
        self.get_startfreq()
        self.get_centerfreq()
        self.get_span()

    def do_get_stopfreq(self):
        """
        Get Stop frequency

        Input:
            None

        Output:
            val (float) : Start Frequency in Hz
        """
        logging.debug(__name__ + ' : getting stop frequency')
        self._stop = float(self._visainstrument.query('SENS%i:FREQ:STOP?' % self._ci))
        return  self._stop

    def do_set_bandwidth(self, band):
        """
        Set Bandwidth

        Input:
            band (float) : Bandwidth in Hz

        Output:
            None
        """
        logging.debug(__name__ + ' : setting bandwidth to %s Hz' % band)
        self._visainstrument.write('SENS%i:BWID %i' % (self._ci,band))

    def do_get_bandwidth(self):
        """
        Get Bandwidth

        Input:
            None

        Output:
            band (float) : Bandwidth in Hz
        """
        logging.debug(__name__ + ' : getting bandwidth')
        # getting value from instrument
        return  float(self._visainstrument.query('SENS%i:BWID?'%self._ci))
    
    def do_set_cw(self, val):
        """
        Set instrument to CW (single frequency) mode and back
        """
        if val:
            if self._cwfreq is None:
                self._cwfreq = self.get_centerfreq()
            self.set_nop(1)
            self.set_sweep_type("LIN")
            self.set_cwfreq(self._cwfreq)
        else:
            self._visainstrument.write(':SENS%i:SWE:POIN 1001' % self._ci)
            self.set_startfreq(self._start)
            self.set_stopfreq(self._stop)

    def do_get_cw(self):
        """
        retrieve CW mode status
        """
        if (self.get_nop() == 1) and (self.get_sweep_type() == "LIN"): ret = True
        else: ret = False
        return ret

    def do_set_channel_index(self, val):
        """
        Set the index of the channel to address.

        Input:
            val (int) : 1 .. number of active channels (max 14)

        Output:
            None
        """
        logging.debug(__name__ + ' : setting channel index to "%i"' % val)
        noc = int(self._visainstrument.query('SYST:CHAN:CAT?')[-3])
        if val <= noc:
            self._ci = val 
        else:
            raise ValueError('set_channel_index(): index must be < No. channels')

    def do_get_channel_index(self):
        """
        Get the index of the channel to address.

        Input:
            None

        Output:
            channel_index (int) : 1-14
        """
        logging.debug(__name__ + ' : getting channel index')
        return self._ci

    def do_set_active_trace(self, trace):
        """
        Sets the active trace on the selected channel, which can then be readout
        :param trace: Number of the active trace
        :return: None
        """
        # TODO: catch error
        self._active_trace = trace
        self._visainstrument.write('CALC%i:PAR:MNUM %f' %(self._ci, trace))

    def do_get_active_trace(self):
        """
        :return: the active trace on the selected channel
        """
        self._active_trace = int(self._visainstrument.query('CALC%i:PAR:MNUM?'%(self._ci)).strip())
        return self._active_trace

    def do_get_sweep_type(self):
        """
        Get the Sweep Type

        Input:
            None

        Output:
            Sweep Type (string). One of
            LIN:    Frequency-based linear sweep
            LOG:    Frequency-based logarithmic sweep
            SEGM:   Segment-based sweep with frequency-based segments
            POW:    Power-based sweep with CW frequency
            CW:     Single frequency mode
        """
        logging.debug(__name__ + ' : getting sweep type')
        return str(self._visainstrument.query('SENS%i:SWE:TYPE?' % self._ci)).rstrip()
    
    def do_set_sweep_type(self, swtype):
        """
        Set the Sweep Type
        Input:
            swtype (string):    One of
                LIN:    Frequency-based linear sweep
                LOG:    Frequency-based logarithmic sweep
                SEGM:   Segment-based sweep with frequency-based segments
                POW:    Power-based sweep with CW frequency
                CW:     Time-based sweep with CW frequency

        Output:
            None
        """
        if swtype in ('LIN','LOG','SEGM','POW','CW'):
            logging.debug(__name__ + ' : Setting sweep type to %s' % swtype)
            if swtype == 'SEGM':
                self._visainstrument.write('SENS%i:SEGM:POW:CONT ON' %(self._ci))
                self._visainstrument.write('SENS%i:SEGM:ARB ON' %(self._ci))
                self._visainstrument.write('SENS%i:SEGM:X:SPAC OBAS' %(self._ci))
            return self._visainstrument.write('SENS%i:SWE:TYPE %s' %(self._ci,swtype))
        else:
            logging.error(__name__ + ' : Illegal argument %s' % swtype)
            return False
            
    def do_get_measurement_parameter(self):
        """
        Gets the measurement parameter, i.e. S11, S21, ...
        Output:
            Parameter as string "S11" ...
        """
        return self.query("CALC%i:MEAS:PAR?"%self._ci).strip()
    
    def do_set_measurement_parameter(self, mode):
        """
        Sets the measurement parameter, i.e. S11, S21, ...
        Input:
            mode: Parameter as string, e.g. "S11"
        """
        return self.write("CALC%i:MEAS:PAR %s"%(self._ci, mode))

    def do_set_trigger_source(self, source):
        """
        Set Trigger Mode

        Input:
            source (string) : EXTernal | IMMediate (internal) | MANual
        Output:
            None
        Default:
            IMMediate
        """
        logging.debug(__name__ + ' : setting trigger source to "%s"' % source)
        if source.upper() in ['EXT', 'IMM', 'MAN']:
            self._visainstrument.write('TRIG:SEQ:SOUR %s' % source.upper())
        else:
            raise ValueError('set_trigger_source(): must be EXTernal | IMMediate | MANual')

    def do_get_trigger_source(self):
        """
        Get Trigger Mode

        Input:
            None

        Output:
            source (string) : INTernal | MANual | EXTernal | BUS
        """
        logging.debug(__name__ + ' : getting trigger source')
        return str(self._visainstrument.query('TRIG:SEQ:SOUR?')).rstrip()

    def send_trigger(self):
        """
        Sends one trigger to all channels when trigger source is MANual
        """
        self._visainstrument.write('INIT:IMM')
          
    def query(self, msg):
        return self._visainstrument.query(msg)

    def write(self, msg):
        return self._visainstrument.write(msg)

    def pre_measurement(self):
        """
        Set everything needed for the measurement
        Averaging has to be enabled.
        Trigger count is set to number of averages
        """
        if not self.get_Average():
            self.set_Average(True)
            self.set_averages(1)
        self.set_count(self.do_get_averages())

    def post_measurement(self):
        """
        Bring the VNA back to a mode where it can be easily used by the operator.
        """
        self.set_sweep_mode("cont")

    def start_measurement(self):
        """
        This function is called at the beginning of each single measurement in the spectroscopy script.
        Here, it starts n sweeps, where n is the active channels trigger count.
        Also, the averages need to be reset.
        """
        self.avg_clear()
        self._visainstrument.write('*SRE 32')
        self._visainstrument.write('*ESE 1')
        self.set_sweep_mode("group")

    def ready(self):
        """
        This is a proxy function, returning True when the VNA is on HOLD after finishing the required number of averages .
        """
        
        try:  # the VNA sometimes throws an error here, we just ignore it
            return (1 == int(self._visainstrument.query('*ESR?'))) # ESR is set to 1 once sweep has finished. Needed, as the version below doesn't work for a single sweep measurement
            #return (self.do_get_sweep_counter() == self.do_get_count())
        except:
            return False
    
    def reconnect(self):
        self._visainstrument = visa.instrument(self._address)

    def add_segment(self,center,span,nop,power):
        self.write("SENS:SEGM1:ADD")
        if span >= 0:
            self.write("SENS:SEGM1:FREQ:CENT %f" % center)
            self.write("SENS:SEGM1:FREQ:SPAN %f"%span)
        else:
            start, stop = center+numpy.array((-1, 1))*span/2
            self.write("SENS:SEGM1:FREQ:STAR %f" % start)
            self.write("SENS:SEGM1:FREQ:STOP %f" % stop)
        self.write("SENS:SEGM1:SWE:POIN %i"%nop)
        self.write("SENS:SEGM1:POW %f"%power)
        self.write("SENS:SEGM1 ON")
        qkit.flow.sleep(1) # The VNA needs some time to digest this...
        
        
    def delete_all_segments(self):
        self.write("SENS:SEGM:DEL:ALL")

    def do_get_sweep_counter(self):
        '''

        Output:
            int: present state of sweep counter
        '''

        logging.debug(__name__ + ' : getting sweep counter')
        return int(self._visainstrument.query('CALC%i:DATA:NSWEEP:COUNT?' % self._ci))
    
    def do_autoscale(self):
        '''
        Rescale using auto-scale
        '''
        
        logging.debug(__name__ + ' : run auto-scale ')
        self.write("DISP:WIND:TRAC:Y:AUTO ONCE")

    def do_set_average_mode(self, mode):
        '''
        Set the average mode [ AUTO, FLATten, REDuce, MOVing ].
        '''
        if mode in ['AUTO', 'auto', 'flat', 'FLAT', 'RED', 'red', 'MOV', 'mov']:
            logging.debug(__name__ + ' : set average mode to %s' % mode)
            self.write("SENS%i:AVER:MODE %s" % (self._ci, mode))

    def do_get_marker(self):
        '''
        Get value for marker n.
        '''
        
