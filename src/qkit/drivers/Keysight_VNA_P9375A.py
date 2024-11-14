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

from qkit.core.instrument_base import Instrument
from qkit import visa
import types
import logging
from time import sleep
import numpy

class Keysight_VNA_P9375A(Instrument):
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
        self._visainstrument.timeout = 10000
        self._zerospan = False
        self._freqpoints = 0
        self._ci = channel_index 
        self._active_trace = 1
        self._pi = 2 # port_index, similar to self._ci
        self._start = 0
        self._stop = 0
        self._nop = 0
        
        # Turn on "fixturing" such that data fetched is corrected for delay
        self._visainstrument.write("CALC:FSIM:STAT ON")

        # Implement parameters
        self.add_parameter('nop', type=int,
            flags=Instrument.FLAG_GETSET,
            minval=2, maxval=100001,
            tags=['sweep'])
            
        self.add_parameter('bandwidth', type=float,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=1e9,
            units='Hz', tags=['sweep']) 

        self.add_parameter('averages', type=int,
            flags=Instrument.FLAG_GETSET,
            minval=1, maxval=1024, tags=['sweep'])                    

        self.add_parameter('Average', type=bool,
            flags=Instrument.FLAG_GETSET)   
                    
        self.add_parameter('centerfreq', type=float,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=20e9,
            units='Hz', tags=['sweep'])

        self.add_parameter('cwfreq', type=float,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=20e9,
            units='Hz', tags=['sweep'])
            
        self.add_parameter('startfreq', type=float,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=20e9,
            units='Hz', tags=['sweep'])            
            
        self.add_parameter('stopfreq', type=float,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=20e9,
            units='Hz', tags=['sweep'])                        
            
        self.add_parameter('span', type=float,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=20e9,
            units='Hz', tags=['sweep'])        
            
        self.add_parameter('power', type=float,
            flags=Instrument.FLAG_GETSET,
            minval=-80, maxval=20,
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

        self.add_parameter('zerospan', type=bool,
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
    
        self.add_parameter('edel', type=float, # legacy name for parameter. This corresponds to the VNA's port extension values.
            flags=Instrument.FLAG_GETSET, 
            minval=-10, maxval=10,
            units='s', tags=['sweep'],
            channels=(1, self._pi), channel_prefix = 'port%d_') # the channel option for qtlab's Instument class is used here to easily address the two VNA ports
  
        self.add_parameter('edel_status', type=bool, # legacy name for parameter. This corresponds to the VNA's port extension values.
            flags=Instrument.FLAG_GETSET)
                   
        self.add_parameter('sweep_mode', type=str,  #JDB This parameter switches on/off hold. The hold function below does the same job, this is just for code compatibility to the agilent and anritsu drivers.
            flags=Instrument.FLAG_GETSET,tags=['sweep']) 
                    
        self.add_parameter('sweep_type', type=str,
            flags=Instrument.FLAG_GETSET,tags=['sweep'])

        self.add_parameter('active_trace', type=int,
            flags=Instrument.FLAG_GETSET)
        
        self.add_parameter('output', type=bool,
            flags=Instrument.FLAG_GETSET)   
        
        #Triggering Stuff
        self.add_parameter('trigger_source', type=str,
            flags=Instrument.FLAG_GETSET)
        
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
        self.get_output()
        for port in range(self._pi):
            self.get('port%d_edel' % (port+1))
        
    ###
    #Communication with device
    ###
    
    
    def hold(self, status):     # added MW July 13
        self._visainstrument.write(":TRIG:SOUR IMM")
        if status:
            self._visainstrument.write('INIT:CONT OFF')
            self._visainstrument.write('SENS:SWE:MODE HOLD') # set sweep mode to hold
            self._visainstrument.write('OUTP OFF') # set RF output off
        else:
            self._visainstrument.write('INIT:CONT ON')
            self._visainstrument.write('SENS:SWE:MODE CONT') # set sweep mode to hold
            self._visainstrument.write('OUTP ON') # set RF output on

    def get_hold(self):     # added MW July 13
        ###hold==False only if rf power is on,  sweep mode is continuous and trigger source is immediate (interal continuous triggering). 
        if int(self._visainstrument.query('INIT%i:CONT?'%(self._ci))) and self._visainstrument.query(':SENS%i:SWE:MODE?'%(self._ci)) == 'CONT\n' and int(self._visainstrument.query('OUTP?')):
            self._hold=False
        elif not int(self._visainstrument.query('INIT%i:CONT?'%(self._ci))) and self._visainstrument.query(':SENS%i:SWE:MODE?'%(self._ci)) == 'HOLD\n' and not int(self._visainstrument.query('OUTP?')):
            self._hold=True
        else:
            self._hold=None
        return self._hold 
    
    def init(self):
        if self._zerospan:
          self._visainstrument.write('INIT1;*wai')
        else:
          if self.get_Average():
            for i in range(self.get_averages()):            
              self._visainstrument.write('INIT1;*wai')
          else:
              self._visainstrument.write('INIT1;*wai')   

    def def_trig(self):
        self._visainstrument.write(':TRIG:AVER ON')
        self._visainstrument.write(':TRIG:SOUR bus')
        
    def avg_clear(self):
        #self._visainstrument.write(':TRIG:SING')
        #self._visainstrument.write(':SENSe%i:AVERage:CLEar'%(self._ci))
        self._visainstrument.write(':SENS%i:AVER:CLE' %(self._ci))

    def avg_status(self):
        return 0 == (int(self._visainstrument.query('STAT:OPER:COND?')) & (1<<4))
        #return int(self._visainstrument.query(':SENS%i:AVER:COUNT?' %(self._ci)))    
        
    def get_tracedata(self, format = 'AmpPha', single=False, averages=1.):
        
        
        '''
        Get the data of the current trace

        Input:
            format (string) : 'AmpPha': Amp in dB and Phase, 'RealImag',

        Output:
            'AmpPha':_ Amplitude and Phase
        '''
        
        
        if single==True:        #added MW July. 
            #print('single shot readout')
            self._visainstrument.write('TRIG:SOUR IMM') #added MW July 2013. start single sweep.
            self._visainstrument.write('INIT%i:CONT ON'%(self._ci)) #added MW July 2013. start single sweep.
            self.hold(True)
            sleep(float(self._visainstrument.query('SENS1:SWE:TIME?'))) 
        
        #sleep(0.1) # required to avoid timing issues    MW August 2013   ???
            
        #self._visainstrument.write(':FORMAT REALform; FORMat:BORDer SWAP;')
        #data = self._visainstrument.query_binary_values( "CALCulate:DATA? SDATA",format = visa.single)
        #data = self._visainstrument.query_binary_values(':FORMAT REAL,32;*CLS;CALC1:DATA:NSW? SDAT,1;*OPC',format=1)      
        #data = self._visainstrument.query_binary_values('FORM:DATA REAL; FORM:BORD SWAPPED; CALC%i:SEL:DATA:SDAT?'%(self._ci), format = visa.double)  
        self._visainstrument.write('FORM:DATA REAL')
        self._visainstrument.write('FORM:BORD SWAPPED') #SWAPPED
        #data = self._visainstrument.query_binary_values('CALC%d:SEL:DATA:SDAT?'%(self._ci), format = visa.double)              
        data = self._visainstrument.query_binary_values('CALC%i:MEAS:DATA:SDAT?'%(self._ci))
        data_size = numpy.size(data)
        datareal = numpy.array(data[0:data_size:2])
        dataimag = numpy.array(data[1:data_size:2])
          
        if format == 'RealImag':
          if self._zerospan:
            return numpy.mean(datareal), numpy.mean(dataimag)
          else:
            return datareal, dataimag
        elif format == 'AmpPha':
          if self._zerospan:
            datareal = numpy.mean(datareal)
            dataimag = numpy.mean(dataimag)
            dataamp = numpy.sqrt(datareal*datareal+dataimag*dataimag)
            for i in numpy.arange(len(datareal)):    #added MW July 2013
                if datareal[i]>=0 and dataimag[i] >=0:   #1. quadrant
                    datapha = numpy.arctan(dataimag[i]/datareal[i])
                elif  datareal[i] <0 and dataimag[i] >=0:  #2. quadrant
                    datapha = numpy.arctan(dataimag[i]/datareal[i])+ numpy.pi
                elif  datareal[i] <0 and dataimag[i] <0:  #3. quadrant
                    datapha = numpy.arctan(dataimag[i]/datareal[i])- numpy.pi
                elif  datareal[i] >=0 and dataimag[i]<0:   #4. quadrant
                    datapha = numpy.arctan(dataimag[i]/datareal[i])
                    
            return dataamp, datapha
          else:
            dataamp = numpy.sqrt(datareal*datareal+dataimag*dataimag)
            datapha = numpy.arctan2(dataimag,datareal)
            if self.get_cw():
                # in cw mode the vna performs a power sweep with 2 power values. the driver sets them to the same level,
                # but the returned data may cause a dimension problem.
                # therefore we only take one datapoint or average them.
                # Spectroscopy requires a sized object, so there must be [] around the values
                dataamp, datapha = numpy.array([numpy.mean(dataamp)]), numpy.array([numpy.mean(datapha)])
            return dataamp, datapha
        else:
          raise ValueError('get_tracedata(): Format must be AmpPha or RealImag') 
      
    def get_freqpoints(self, query = False):      
      if query == True:        
        self._freqpoints = self._visainstrument.query_binary_values('FORM:DATA REAL; FORM:BORD SWAPPED; :SENS%i:FREQ:DATA?'%(self._ci), format = visa.double)
      
        #self._freqpoints = numpy.array(self._visainstrument.query_binary_values('SENS%i:FREQ:DATA:SDAT?'%self._ci,format=1)) / 1e9
        #self._freqpoints = numpy.array(self._visainstrument.query_binary_values(':FORMAT REAL,32;*CLS;CALC1:DATA:STIM?;*OPC',format=1)) / 1e9
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

        Input:
            source (string) : HOLD | CONTinuous | SINGle 

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting sweep mode "%s"' % mode)
        if mode.upper() in ['HOLD', 'CONT', 'SING']:
            self._visainstrument.write('SENS:SWE:MODE %s' % mode.upper())        
        else:
            raise ValueError('set_trigger_source(): must be HOLD | CONTinuous | SINGle ')
        
           
    def do_get_sweep_mode(self):
        return self._visainstrument.query(':SENS%i:SWE:MODE?'%(self._ci))
    
    def do_set_output(self, status):
        '''
        sets the RF power on or off

        Input:
            status (boolean)

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting RF output to "%s"' % (status))
        if status:
            self._visainstrument.write('OUTP ON')
        elif status == False:
            self._visainstrument.write('OUTP OFF')
        else:
            raise ValueError('set_output(): can only set True or False')               
    def do_get_output(self):
        '''
        Get status of RF output

        Input:
            None

        Output:
            Status of RF output (boolean)
        '''
        logging.debug(__name__ + ' : getting average status')
        return bool(int(self._visainstrument.query('OUTP?')))
    
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
              self._visainstrument.write(':SENS%i:SWE:POIN %i' %(self._ci,nop))
          """
          Comment below is copy from Anritsu driver
          if(cw):
            self._visainstrument.write(':SENS%i:SWE:CW:POIN %i' %(self._ci,nop))
          else:
            self._visainstrument.write(':SENS%i:SWE:POIN %i' %(self._ci,nop))
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
          self._nop = int(self._visainstrument.query(':SENS%i:SWE:POIN?' %(self._ci)))    
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
            self._visainstrument.write('SENS%i:AVER:STAT %s' % (self._ci,status))
        elif status == False:
            status = 'OFF'
            self._visainstrument.write('SENS%i:AVER:STAT %s' % (self._ci,status))
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
        return bool(int(self._visainstrument.query('SENS%i:AVER:STAT?' %(self._ci))))
                    
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
            self._visainstrument.write('SENS%i:AVER:COUN %i' % (self._ci,av))
        else:
            self._visainstrument.write('SWE%i:POIN %.1f' % (self._ci,av))
            
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
          return int(self._visainstrument.query('SWE%i:POIN?' % self._ci))
        else:
          return int(self._visainstrument.query('SENS%i:AVER:COUN?' % self._ci))
                
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
            self._visainstrument.write('SOUR%i:POW1:LEV:IMM:AMPL %.1f' % (self._ci,pow))    
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
            return float(self._visainstrument.query('SOUR%i:POW1:LEV:IMM:AMPL?' % (self._ci)))

    def do_set_startpower(self,pow):
        '''
        Set probe power

        Input:
            pow (float) : Power in dBm

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting startpower to %s dBm' % pow)
        self._visainstrument.write('SOUR%i:POW:START %.1f' % (self._ci,pow))    
    def do_get_startpower(self):
        '''
        Get probe power

        Input:
            None

        Output:
            pow (float) : Power in dBm
        '''
        logging.debug(__name__ + ' : getting startpower')
        return float(self._visainstrument.query('SOUR%i:POW:START?' % (self._ci)))

    def do_set_stoppower(self,pow):
        '''
        Set probe power

        Input:
            pow (float) : Power in dBm

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting stoppower to %s dBm' % pow)
        self._visainstrument.write('SOUR%i:POW:STOP %.1f' % (self._ci,pow))    
    def do_get_stoppower(self):
        '''
        Get probe power

        Input:
            None

        Output:
            pow (float) : Power in dBm
        '''
        logging.debug(__name__ + ' : getting stoppower')
        return float(self._visainstrument.query('SOUR%i:POW:STOP?' % (self._ci)))
                
    def do_set_centerfreq(self,cf):
        '''
        Set the center frequency

        Input:
            cf (float) :Center Frequency in Hz

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting center frequency to %s' % cf)
        self._visainstrument.write('SENS%i:FREQ:CENT %f' % (self._ci,cf))
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
        return  float(self._visainstrument.query('SENS%i:FREQ:CENT?'%(self._ci)))

    def do_set_cwfreq(self, cf):
        ''' set cw frequency '''
        self._visainstrument.write('SENS%i:FREQ:CW %f' % (self._ci,cf))
    
    def do_get_cwfreq(self):
        ''' get cw frequency '''
        return float(self._visainstrument.query('SENS%i:FREQ:CW?'%(self._ci)))
        
    def do_set_span(self,span):
        '''
        Set Span

        Input:
            span (float) : Span in KHz

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting span to %s Hz' % span)
        self._visainstrument.write('SENS%i:FREQ:SPAN %i' % (self._ci,span))   
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
        span = self._visainstrument.query('SENS%i:FREQ:SPAN?' % (self._ci) ) #float( self.ask('SENS1:FREQ:SPAN?'))
        return span

    def do_get_sweeptime_averages(self):###JB
        '''
        Get sweeptime
        
        Input:
            None

        Output:
            sweep time (float) times number of averages: sec
        '''
        return self.get_sweeptime() * self.get_averages()
        
    def do_get_sweeptime(self):  #added MW July 2013
        '''
        Get sweeptime
        
        Input:
            None

        Output:
            sweep time (float) : sec
        '''
        logging.debug(__name__ + ' : getting sweep time')
        self._sweep=float(self._visainstrument.query('SENS1:SWE:TIME?'))
        return self._sweep


    def do_set_edel(self, val,channel):  # MP 04/2017

        '''
        Set electrical delay

        '''
        logging.debug(__name__ + ' : setting port %s extension to %s sec' % (channel, val))
        self._visainstrument.write('SENS1:CORR:EXT:PORT%i:TIME %.12f' % (channel, val))
            
    
    def do_get_edel(self, channel):   # MP 04/2017

        '''
        Get electrical delay

        '''
        logging.debug(__name__ + ' : getting port %s extension' % channel)
        self._edel = float(self._visainstrument.query('SENS1:CORR:EXT:PORT%i:TIME?'% channel))
        return  self._edel   
        
    def do_set_edel_status(self, status):   # MP 04/2017

        '''
        Set electrical delay

        '''
        logging.debug(__name__ + ' : setting port extension status to %s' % (status))
        self._visainstrument.write('SENS.CORR.EXT.STAT %i' % (status))
            
    
    def do_get_edel_status(self):   # MP 04/2017

        '''
        Get electrical delay

        '''
        logging.debug(__name__ + ' :  port extension status')
        return  self._visainstrument.query('SENS:CORR:EXT:STAT?')
        
        
    def do_set_startfreq(self,val):
        '''
        Set Start frequency

        Input:
            span (float) : Frequency in Hz

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting start freq to %s Hz' % val)
        self._visainstrument.write('SENS%i:FREQ:STAR %f' % (self._ci,val))   
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
        self._start = float(self._visainstrument.query('SENS%i:FREQ:STAR?' % (self._ci)))
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
        self._visainstrument.write('SENS%i:FREQ:STOP %f' % (self._ci,val))  
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
        self._stop = float(self._visainstrument.query('SENS%i:FREQ:STOP?' %(self._ci) ))
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
        self._visainstrument.write('SENS%i:BWID:RES %i' % (self._ci,band))
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
        return  float(self._visainstrument.query('SENS%i:BWID:RES?'%self._ci))                
    
    def do_set_cw(self, val):
        '''
        Set instrument to CW (single frequency) mode and back
        '''
        if val:
            self.set_cwfreq(self.get_centerfreq())
            self.set_nop(2)
            self.set_startpower(self.get_power())
            self.set_stoppower(self.get_power())
            return self._visainstrument.write(':SENS%i:SWE:TYPE POW' %(self._ci))
        else:
            return self._visainstrument.write(':SENS%i:SWE:TYPE LIN' %(self._ci))
        
    def do_get_cw(self):
        '''
        retrieve CW mode status from device
        '''
        sweep_type = str(self._visainstrument.query(':SENS%i:SWE:TYPE?'%(self._ci))).rstrip()
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
            source (string) : IMMediate | MANual | EXTernal

        Output:
            None
        '''
        logging.debug(__name__ + ' : setting trigger source to "%s"' % source)
        if source.upper() in ['IMM', 'MAN', 'EXT']:
            self._visainstrument.write('TRIG:SEQ:SOUR %s' % source.upper())        
        else:
            raise ValueError('set_trigger_source(): must be IMMediate | MANual | EXTernal')

    def do_get_trigger_source(self):
        '''
        Get Trigger Mode

        Input:
            None

        Output:
            source (string) : IMMediate  | MANual | EXTernal 
        '''
        logging.debug(__name__ + ' : getting trigger source')
        return str(self._visainstrument.query('TRIG:SEQ:SOUR?')).rstrip()
        

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
        self._visainstrument.write('CALC{}:PAR{}:SEL'.format(self._ci, trace))

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
        
        return str(self._visainstrument.query('SENS%i:SWE:TYPE?' %(self._ci))).rstrip()
    
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
            return self._visainstrument.write('SENS%i:SWE:TYPE %s' %(self._ci,swtype))
            
        else:
            logging.debug(__name__ + ' : Illegal argument %s'%(swtype))
          
    def write(self,msg):
      return self._visainstrument.write(msg)    
    def ask(self,msg):
      return self._visainstrument.query(msg)
     
    def pre_measurement(self):
        '''
        Set everything needed for the measurement
        '''
        # self._visainstrument.write(":TRIG:SOUR MAN") #Only wait for software triggers
        # self._visainstrument.write('INIT:CONT ON')
        self.do_set_Average(True)
        pass
        
        
    def post_measurement(self):
        '''
        After a measurement, the VNA is in hold mode, and it can be difficult to start a measurement again from front panel.
        This function brings the VNA back to normal measuring operation.
        '''
        # self._visainstrument.write('INIT:CONT ON')
        # self.do_set_Average(False)
        self.hold(False)
        pass
        
      
    def start_measurement(self):
        '''
        This function is called at the beginning of each single measurement in the spectroscopy script.
        Here, it resets the averaging
        '''
        self._visainstrument.write('SENS1:AVER:STAT OFF')
        self._visainstrument.write(':SENS1:AVER:CLE')
        self._visainstrument.write('SENS1:AVER:STAT ON')
        # self._visainstrument.write('INIT:IMM') #go
        # self._visainstrument.write('*TRG') #go

    
    def ready(self):
        '''
        This is a proxy function, returning True when the VNA has finished the required number of averages.
        '''
        return (int(self._visainstrument.query(':STAT:OPER:AVER1:COND?')) & 2) == 2
        # return (int(self._visainstrument.query('STAT:OPER:DEV?')) & 16) == 16
