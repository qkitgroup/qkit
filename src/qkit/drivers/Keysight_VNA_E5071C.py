# Agilent_VNA_E5071C driver, P. Macha, modified by M. Weides July 2013, J. Braumueller 2015
# Adapted to Keysight VNA by A. Schneider and L. Gurenhaupt 2016
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

import qkit
from qkit.core.instrument_base import Instrument
from qkit import visa
import types
import logging
from time import sleep
import numpy

class Keysight_VNA_E5071C(Instrument):
    '''
    This is the python driver for the Anritsu MS4642A Vector Network Analyzer

    Usage:
    Initialise with
    <name> = instruments.create('<name>', address='<GPIB address>', reset=<bool>)
    
    '''

    def __init__(self, name, address, channel_index = 1):
        '''
        Initializes 

        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address
        '''
        
        logging.info(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])

        self._address = address
        self._visainstrument = visa.instrument(self._address)
        if visa.qkit_visa_version > 1:
            # we have to define the read termination chars manually for the newer version
            idn = self._visainstrument.query('*IDN?')
            self._visainstrument.read_termination = idn[len(idn.strip()):]
            
        self._zerospan = False
        self._freqpoints = 0
        self._ci = channel_index
        self._pi = 2 # port_index, similar to self._ci
        self._active_trace = 0
        self._start = 0
        self._stop = 0
        self._nop = 0

        # Implement parameters
        self.add_parameter('nop', type=int,
            flags=Instrument.FLAG_GETSET,
            minval=2, maxval=20001,
            tags=['sweep'])
            
        self.add_parameter('bandwidth',     type=float, minval=0,   maxval=1e9, units='Hz')
        self.add_parameter('averages',      type=int,   minval=1,   maxval=1024)
        self.add_parameter('Average',       type=bool)
        self.add_parameter('centerfreq',    type=float, minval=0, maxval=20e9,  units='Hz')
        self.add_parameter('cwfreq',        type=float, minval=0, maxval=20e9,  units='Hz')
        self.add_parameter('startfreq',     type=float, minval=0, maxval=20e9,  units='Hz')
        self.add_parameter('stopfreq',      type=float, minval=0, maxval=20e9,  units='Hz')
        self.add_parameter('span',          type=float, minval=0, maxval=20e9,  units='Hz')
        self.add_parameter('power',         type=float, minval=-85, maxval=10,  units='dBm')
        self.add_parameter('startpower',    type=float, minval=-85, maxval=10,  units='dBm')
        self.add_parameter('stoppower',     type=float, minval=-85, maxval=10,  units='dBm')
        self.add_parameter('cw',            type=bool)
        self.add_parameter('zerospan',      type=bool)
        self.add_parameter('channel_index', type=int)
        self.add_parameter('sweeptime',     type=float, minval=0, maxval=1e3,   units='s',flags=Instrument.FLAG_GET)
        self.add_parameter('sweeptime_averages', type=float,minval=0, maxval=1e3,units='s',flags=Instrument.FLAG_GET)
        self.add_parameter('edel',          type=float,minval=-10, maxval=10,units='s',channels=(1, self._pi), channel_prefix = 'port%d_') # the channel option for qtlab's Instument class is used here to easily address the two VNA ports
        self.add_parameter('edel_status',   type=bool) # legacy name for parameter. This corresponds to the VNA's port extension values.
        self.add_parameter('sweep_mode',    type=str)  #JDB This parameter switches on/off hold. The hold function below does the same job, this is just for code compatibility to the agilent and anritsu drivers.
        self.add_parameter('sweep_type',    type=str)
        self.add_parameter('active_trace',  type=int)
        
        #Triggering Stuff
        self.add_parameter('trigger_source', type=str)
        
        # Implement functions
        self.add_function('get_freqpoints')
        self.add_function('get_tracedata')
        self.add_function('init')
        self.add_function('avg_clear')
        self.add_function('avg_status')
        self.add_function('def_trig')
        self.add_function('get_hold')
        self.add_function('hold')
        self.add_function('get_sweeptime')
        self.add_function('get_sweeptime_averages')
        self.add_function('pre_measurement')
        self.add_function('start_measurement')
        self.add_function('ready')
        self.add_function('post_measurement')

        self.get_all()
    
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
        self.get_zerospan()
        self.get_sweeptime()
        self.get_sweeptime_averages()
        self.get_edel_status()
        self.get_cw()
        self.get_cwfreq()
        for port in range(self._pi):
            self.get('port%d_edel' % (port+1))
        
    ###
    #Communication with device
    ###
    
    
    def hold(self, status):
        self.write(":TRIG:SOUR INT")
        if status:
            self.write(':INIT%i:CONT OFF'%(self._ci))
        else:
            self.write(':INIT%i:CONT ON'%(self._ci))

    def get_hold(self):
        return self.ask(':INIT%i:CONT?'%(self._ci))
    
    def init(self):
        if self._zerospan:
          self.write('INIT1;*wai')
        else:
          if self.get_Average():
            for i in range(self.get_averages()):
              self.write('INIT1;*wai')
          else:
              self.write('INIT1;*wai')

    def def_trig(self):
        self.write(':TRIG:AVER ON')
        self.write(':TRIG:SOUR bus')
        
    def avg_clear(self):
        self.write(':SENS%i:AVER:CLE' %(self._ci))

    def avg_status(self):
        return 0 == (int(self.ask('STAT:OPER:COND?')) & (1<<4))
        
    def get_tracedata(self, format = 'AmpPha', single=False, averages=1.):
        '''
        Get the data of the current trace

        Input:
            format (string) : 'AmpPha': Amp in dB and Phase, 'RealImag',

        Output:
            'AmpPha':_ Amplitude and Phase
        '''
        
        if single==True:
            #print('single shot readout')
            self.write('TRIG:SOUR INT') #added MW July 2013. start single sweep.
            self.write('INIT%i:CONT ON'%(self._ci)) #added MW July 2013. start single sweep.
            self.hold(True)
            sleep(float(self.ask('SENS1:SWE:TIME?')))
        
        #sleep(0.1) # required to avoid timing issues    MW August 2013   ???
        
        self.write('FORM:DATA REAL')
        self.write('FORM:BORD SWAPPED')
        data = self.ask_for_values('CALC%i:SEL:DATA:SDAT?'%(self._ci), fmt = 3)
        data_size = numpy.size(data)
        datareal = numpy.array(data[0:data_size:2])
        dataimag = numpy.array(data[1:data_size:2])
        
        if format == 'RealImag':
          if self._zerospan:
            return numpy.mean(datareal), numpy.mean(dataimag)
          else:
            return datareal, dataimag
        elif format == 'AmpPha':
          if self._zerospan or self.get_cw(False):
            datacomplex = [numpy.mean(datareal + 1j*dataimag)]
            dataamp = numpy.abs(datacomplex)
            datapha = numpy.angle(datacomplex)
          else:
            dataamp = numpy.sqrt(datareal*datareal+dataimag*dataimag)
            datapha = numpy.arctan2(dataimag,datareal)
          return dataamp, datapha
        else:
          raise ValueError('get_tracedata(): Format must be AmpPha or RealImag')
      
    def get_freqpoints(self, query = False):
      if query:
           self.write("FORM:DATA REAL; FORM:BORD SWAPPED;")
           self._freqpoints = self.ask_for_values(':SENS%i:FREQ:DATA?'%(self._ci), format = visa.double)
      elif self.get_cw():
           self._freqpoints = numpy.atleast_1d(self.get_cwfreq())
      else:
           self._freqpoints = numpy.linspace(self._start,self._stop,self._nop)
      return self._freqpoints

    ###
    # SET and GET functions
    ###
    
    def do_set_sweep_mode(self, mode):
        '''
        select the sweep mode from 'hold', 'cont', single'
        single means only one single trace, not all the averages even if averages
         larger than 1 and Average==True
        '''
        if mode == 'hold':
            self.write(':INIT%i:CONT OFF'%(self._ci))
        elif mode == 'cont':
            self.write(':INIT%i:CONT ON'%(self._ci))
        elif mode == 'single':
            self.write(':INIT%i:CONT ON'%(self._ci))
            self.write(':INIT%i:CONT OFF'%(self._ci))
        else:
            logging.warning('invalid mode')
            
    def do_get_sweep_mode(self):
        return int(self.ask(':INIT%i:CONT?'%(self._ci)))
    
    def do_set_nop(self, nop):
        '''
        Set Number of Points (nop) for sweep

        Input:
            nop (int) : Number of Points

        Output:
            None
        '''

        logging.debug(__name__ + ' : setting Number of Points to %s ' % (nop))
        if self._zerospan:
          print('in zerospan mode, nop is 1')
        else:
          cw = self.get_cw()
          if(nop == 1) and (not cw):
              logging.info(__name__ + 'nop == 1 is only supported in CW mode.')
              self.set_cw(True)
          else:
              self.write(':SENS%i:SWE:POIN %i' %(self._ci,nop))
          """
          Comment below is copy from Anritsu driver
          if(cw):
            self.write(':SENS%i:SWE:CW:POIN %i' %(self._ci,nop))
          else:
            self.write(':SENS%i:SWE:POIN %i' %(self._ci,nop))
          """
          self._nop = nop
          self.get_freqpoints() #Update List of frequency points
        
    def do_get_nop(self):
        '''
        Get Number of Points (nop) for sweep

        Input:
            None
        Output:
            nop (int)
        '''
        logging.debug(__name__ + ' : getting Number of Points')
        if self._zerospan or self.get_cw():
          self._nop = 1
        else:
          self._nop = int(self.ask(':SENS%i:SWE:POIN?' %(self._ci)))
        return self._nop
    
    def do_set_Average(self, status):
        '''
        Set status of Average

        Input:
            status (boolean)

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting Average to "%s"' % (status))
        if status:
            status = 'ON'
            self.write('SENS%i:AVER:STAT %s' % (self._ci,status))
        elif status == False:
            status = 'OFF'
            self.write('SENS%i:AVER:STAT %s' % (self._ci,status))
        else:
            raise ValueError('set_Average(): can only set True or False')
    def do_get_Average(self):
        '''
        Get status of Average

        Input:
            None

        Output:
            Status of Averaging (boolean)
        '''
        logging.debug(__name__ + ' : getting average status')
        return bool(int(self.ask('SENS%i:AVER:STAT?' %(self._ci))))
        
    def do_set_averages(self, av):
        '''
        Set number of averages

        Input:
            av (int) : Number of averages

        Output:
            None
        '''
        if self._zerospan == False:
            logging.debug(__name__ + ' : setting Number of averages to %i ' % (av))
            self.write('SENS%i:AVER:COUN %i' % (self._ci,av))
        else:
            self.write('SWE%i:POIN %.1f' % (self._ci,av))
            
    def do_get_averages(self):
        '''
        Get number of averages

        Input:
            None
        Output:
            number of averages
        '''
        logging.debug(__name__ + ' : getting Number of Averages')
        if self._zerospan:
          return int(self.ask('SWE%i:POIN?' % self._ci))
        else:
          return int(self.ask('SENS%i:AVER:COUN?' % self._ci))
          
    def do_set_power(self,pow):
        '''
        Set probe power

        Input:
            pow (float) : Power in dBm

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting power to %s dBm' % pow)
        if self.get_cw():
            self.set_startpower(pow)
            self.set_stoppower(pow)
        else:
            self.write('SOUR%i:POW:PORT1:LEV:IMM:AMPL %.1f' % (self._ci,pow))
    def do_get_power(self):
        '''
        Get probe power

        Input:
            None

        Output:
            pow (float) : Power in dBm
        '''
        logging.debug(__name__ + ' : getting power')
        if self.get_cw():
            return self.get_startpower()
        else:
            return float(self.ask('SOUR%i:POW:PORT1:LEV:IMM:AMPL?' % (self._ci)))

    def do_set_startpower(self,pow):
        '''
        Set probe power

        Input:
            pow (float) : Power in dBm

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting startpower to %s dBm' % pow)
        self.write('SOUR%i:POW:START %.1f' % (self._ci,pow))
    def do_get_startpower(self):
        '''
        Get probe power

        Input:
            None

        Output:
            pow (float) : Power in dBm
        '''
        logging.debug(__name__ + ' : getting startpower')
        return float(self.ask('SOUR%i:POW:START?' % (self._ci)))

    def do_set_stoppower(self,pow):
        '''
        Set probe power

        Input:
            pow (float) : Power in dBm

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting stoppower to %s dBm' % pow)
        self.write('SOUR%i:POW:STOP %.1f' % (self._ci,pow))
    def do_get_stoppower(self):
        '''
        Get probe power

        Input:
            None

        Output:
            pow (float) : Power in dBm
        '''
        logging.debug(__name__ + ' : getting stoppower')
        return float(self.ask('SOUR%i:POW:STOP?' % (self._ci)))
        
    def do_set_centerfreq(self,cf):
        '''
        Set the center frequency

        Input:
            cf (float) :Center Frequency in Hz

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting center frequency to %s' % cf)
        if self.get_cw(False):
          self.set_cwfreq(cf)
        self.write('SENS%i:FREQ:CENT %f' % (self._ci,cf))
        self.get_startfreq()
        self.get_stopfreq()
        self.get_span()
    def do_get_centerfreq(self):
        '''
        Get the center frequency

        Input:
            None

        Output:
            cf (float) :Center Frequency in Hz
        '''
        logging.debug(__name__ + ' : getting center frequency')
        return  float(self.ask('SENS%i:FREQ:CENT?'%(self._ci)))

    def do_set_cwfreq(self, cf):
        ''' set cw frequency '''
        self.write('SENS%i:FREQ:CW %f' % (self._ci,cf))
    
    def do_get_cwfreq(self):
        ''' get cw frequency '''
        return float(self.ask('SENS%i:FREQ:CW?'%(self._ci)))
        
    def do_set_span(self,span):
        '''
        Set Span

        Input:
            span (float) : Span in KHz

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting span to %s Hz' % span)
        self.write('SENS%i:FREQ:SPAN %i' % (self._ci,span))
        self.get_startfreq()
        self.get_stopfreq()
        self.get_centerfreq()
        
    def do_get_span(self):
        '''
        Get Span
        
        Input:
            None

        Output:
            span (float) : Span in Hz
        '''
        #logging.debug(__name__ + ' : getting center frequency')
        span = self.ask('SENS%i:FREQ:SPAN?' % (self._ci) ) #float( self.ask('SENS1:FREQ:SPAN?'))
        return span

    def do_get_sweeptime_averages(self):###JB
        '''
        Get sweeptime
        
        Input:
            None

        Output:
            sweep time (float) times number of averages: sec
        '''
        return self.get_sweeptime() * (self.get_averages() if self.get_Average() else 1)
        
    def do_get_sweeptime(self):  #added MW July 2013
        '''
        Get sweeptime
        
        Input:
            None

        Output:
            sweep time (float) : sec
        '''
        logging.debug(__name__ + ' : getting sweep time')
        self._sweep=float(self.ask('SENS1:SWE:TIME?'))
        return self._sweep


    def do_set_edel(self, val,channel):  # MP 04/2017

        '''
        Set electrical delay

        '''
        logging.debug(__name__ + ' : setting port %s extension to %s sec' % (channel, val))
        self.write('SENS1:CORR:EXT:PORT%i:TIME %.12f' % (channel, val))
        
    
    def do_get_edel(self, channel):   # MP 04/2017

        '''
        Get electrical delay

        '''
        logging.debug(__name__ + ' : getting port %s extension' % channel)
        self._edel = float(self.ask('SENS1:CORR:EXT:PORT%i:TIME?'% channel))
        return  self._edel
        
    def do_set_edel_status(self, status):   # AS 04/2019

        '''
        Set electrical delay

        '''
        logging.debug(__name__ + ' : setting port extension status to %s' % (status))
        self.write('SENS:CORR:EXT:STAT %i' % (status))
        
    
    def do_get_edel_status(self):   # AS 04/2019

        '''
        Get electrical delay

        '''
        logging.debug(__name__ + ' :  port extension status')
        return  self.ask('SENS:CORR:EXT:STAT?').strip() == "1"
        
        
    def do_set_startfreq(self,val):
        '''
        Set Start frequency

        Input:
            span (float) : Frequency in Hz

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting start freq to %s Hz' % val)
        self.write('SENS%i:FREQ:STAR %f' % (self._ci,val))
        self._start = val
        self.get_centerfreq()
        self.get_stopfreq()
        self.get_span()
        
    def do_get_startfreq(self):
        '''
        Get Start frequency
        
        Input:
            None

        Output:
            span (float) : Start Frequency in Hz
        '''
        logging.debug(__name__ + ' : getting start frequency')
        self._start = float(self.ask('SENS%i:FREQ:STAR?' % (self._ci)))
        return  self._start

    def do_set_stopfreq(self,val):
        '''
        Set STop frequency

        Input:
            val (float) : Stop Frequency in Hz

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting stop freq to %s Hz' % val)
        self.write('SENS%i:FREQ:STOP %f' % (self._ci,val))
        self._stop = val
        self.get_startfreq()
        self.get_centerfreq()
        self.get_span()
    def do_get_stopfreq(self):
        '''
        Get Stop frequency
        
        Input:
            None

        Output:
            val (float) : Start Frequency in Hz
        '''
        logging.debug(__name__ + ' : getting stop frequency')
        self._stop = float(self.ask('SENS%i:FREQ:STOP?' %(self._ci) ))
        return  self._stop

    def do_set_bandwidth(self,band):
        '''
        Set Bandwidth

        Input:
            band (float) : Bandwidth in Hz

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting bandwidth to %s Hz' % (band))
        self.write('SENS%i:BWID:RES %i' % (self._ci,band))
    def do_get_bandwidth(self):
        '''
        Get Bandwidth

        Input:
            None

        Output:
            band (float) : Bandwidth in Hz
        '''
        logging.debug(__name__ + ' : getting bandwidth')
        # getting value from instrument
        return  float(self.ask('SENS%i:BWID:RES?'%self._ci))
    
    def do_set_cw(self, val):
        '''
        Set instrument to CW (single frequency) mode and back
        '''
        if val:
            self.set_cwfreq(self.get_centerfreq())
            self.set_nop(2)
            self.set_startpower(self.get_power())
            self.set_stoppower(self.get_power())
            return self.write(':SENS%i:SWE:TYPE POW' %(self._ci))
        else:
            return self.write(':SENS%i:SWE:TYPE LIN' %(self._ci))
        
    def do_get_cw(self):
        '''
        retrieve CW mode status from device
        '''
        sweep_type = str(self.ask(':SENS%i:SWE:TYPE?'%(self._ci))).rstrip()
        if sweep_type == 'POW': ret = True
        else: ret = False
        return ret

    def do_set_zerospan(self,val):
        '''
        Zerospan is a virtual "zerospan" mode. In Zerospan physical span is set to
        the minimal possible value (2Hz) and "averages" number of points is set.

        Input:
            val (bool) : True or False

        Output:
            None
        '''
        #logging.debug(__name__ + ' : setting status to "%s"' % status)
        if val not in [True, False]:
            raise ValueError('set_zerospan(): can only set True or False')
        if val:
          self._oldnop = self.get_nop()
          self._oldspan = self.get_span()
          if self.get_span() > 0.002:
            Warning('Setting ZVL span to 2Hz for zerospan mode')
            self.set_span(0.002)
            
        av = self.get_averages()
        self._zerospan = val
        if val:
            self.set_Average(False)
            self.set_averages(av)
            if av<2:
              av = 2
        else:
          self.set_Average(True)
          self.set_span(self._oldspan)
          self.set_nop(self._oldnop)
          self.get_averages()
        self.get_nop()
        
    def do_get_zerospan(self):
        '''
        Check weather the virtual zerospan mode is turned on

        Input:
            None

        Output:
            val (bool) : True or False
        '''
        return self._zerospan


    def do_set_trigger_source(self,source):
        '''
        Set Trigger Mode

        Input:
            source (string) : INTernal | MANual | EXTernal | REMote

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting trigger source to "%s"' % source)
        if source.upper() in ['INT', 'MAN', 'EXT', 'BUS']:
            self.write('TRIG:SEQ:SOUR %s' % source.upper())
        else:
            raise ValueError('set_trigger_source(): must be INTernal | MANual | EXTernal | REMote')

    def do_get_trigger_source(self):
        '''
        Get Trigger Mode

        Input:
            None

        Output:
            source (string) : INTernal | MANual | EXTernal | BUS
        '''
        logging.debug(__name__ + ' : getting trigger source')
        return str(self.ask('TRIG:SEQ:SOUR?')).rstrip()
        

    def do_set_channel_index(self,val):
        '''
        Set the index of the channel to address.

        Input:
            val (int) : 1 .. number of active channels (max 16)

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting channel index to "%i"' % int)
        nop = self._visainstrument.read('DISP:COUN?')
        if val < nop:
            self._ci = val
        else:
            raise ValueError('set_channel_index(): index must be < nop channels')
    def do_get_channel_index(self):
        '''
        Get active channel

        Input:
            None

        Output:
            channel_index (int) : 1-16
        '''
        logging.debug(__name__ + ' : getting channel index')
        return self._ci
    
    def do_set_active_trace(self, trace):
        """
        Sets the active trace, which can then be readout
        :param trace: Number of the active trace
        :return: None
        """
        # TODO: catch error
        self._active_trace = trace
        self.write('CALC{}:PAR{}:SEL'.format(self._ci, trace))

    def do_get_active_trace(self):
        """
        :return: the active trace on the VNA
        """
        # TODO: ask device
        return self._active_trace

    def do_get_sweep_type(self):
        '''
        Get the Sweep Type

        Input:
            None

        Output:
            Sweep Type (string). One of
            LIN:    Frequency-based linear sweep
            LOG:    Frequency-based logarithmic sweep
            SEGM:   Segment-based sweep with frequency-based segments
            POW:    Power-based sweep with either Power-based sweep with a 
                CW frequency, or Power-based sweep with swept-frequency
        '''
        logging.debug(__name__ + ' : getting sweep type')
        
        return str(self.ask('SENS%i:SWE:TYPE?' %(self._ci))).rstrip()
    
    def do_set_sweep_type(self,swtype):
        '''
        Set the Sweep Type
        Input:
            swtype (string):    One of
                LIN:    Frequency-based linear sweep
                LOG:    Frequency-based logarithmic sweep
                SEGM:   Segment-based sweep with frequency-based segments
                POW:    Power-based sweep with either Power-based sweep with a 
                    CW frequency, or Power-based sweep with swept-frequency

        Output:
            None            
        '''
        if swtype in ('LIN','LOG','SEGM','POW'):
            
            logging.debug(__name__ + ' : Setting sweep type to %s'%(swtype))
            return self.write('SENS%i:SWE:TYPE %s' %(self._ci,swtype))
            
        else:
            logging.debug(__name__ + ' : Illegal argument %s'%(swtype))
    
    def write(self,msg):
        return self._visainstrument.write(msg)
    
    if qkit.visa.qkit_visa_version == 1:
        def ask(self, msg):
            return self._visainstrument.ask(msg)
    
        def ask_for_values(self, msg, **kwargs):
            return self._visainstrument.ask_for_values(kwargs)
    else:
        def ask(self, msg):
            return self._visainstrument.query(msg)
    
        def ask_for_values(self, msg, format=None, fmt=None):
            dtype = format if format is not None else fmt if fmt is not None else qkit.visa.single
            dtype = qkit.visa.dtypes[dtype]
            return self._visainstrument.query_binary_values(msg,datatype=dtype,container=numpy.array)
     
    def pre_measurement(self):
        '''
        Set everything needed for the measurement
        '''
        self.write(":TRIG:SOUR BUS")#Only wait for software triggers
        self.write(":TRIG:AVER ON")# Tell the instrument to do the specific number of averages on every trigger.
        
        
    def post_measurement(self):
        '''
        After a measurement, the VNA is in hold mode, and it can be difficult to start a measurement again from front panel.
        This function brings the VNA back to normal measuring operation.
        '''
        self.write(":TRIG:SOUR INT") #Only wait for software triggers
        self.write(":TRIG:AVER OFF")# Tell the instrument to do the specific number of averages on every trigger.
        self.hold(False)
        
      
    def start_measurement(self):
        '''
        This function is called at the beginning of each single measurement in the spectroscopy script.
        Here, it resets the averaging
        '''
        self.avg_clear()
        self.write('*TRG') #go

    
    def ready(self):
        '''
        This is a proxy function, returning True when the VNA has finished the required number of averages.
        '''
        return (int(self.ask(':STAT:OPER:COND?')) & 32)==32
