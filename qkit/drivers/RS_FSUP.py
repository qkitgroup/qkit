# RS FSUP
# Andre Schneider <andre.schneider@student.kit.edu> 2014
# modified: JB <jochen.braumueller@kit.edu> 11/2016
# modified: Jan Brehm <jan.brehm@kit.edu> 02/2019
# modified: Nicolas Gosling <Nicolas.Gosling@partner.kit.edu> 04/21
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
import logging
from time import sleep
import numpy

class RS_FSUP(Instrument):
    '''
    This is the python driver for the Rhode&Schwarz FSUP Signal Source Analyzer.
    The command set is not complete.

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

        # Implement parameters

        self.add_parameter('averages', type=int,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=32767, tags=['sweep'])    

        self.add_parameter('centerfreq', type=float,
            flags=Instrument.FLAG_GETSET,
            minval=0, maxval=26.5e9,
            tags=['sweep'])

        self.add_parameter('nop', type=int,
            flags=Instrument.FLAG_GETSET,
            minval=155, maxval=30001,
            tags=['sweep'])
        self.add_parameter('freqspan', type=float,
            flags=Instrument.FLAG_GETSET,tags=['sweep'])                    

        self.add_parameter('powerunit', type=str,
            flags=Instrument.FLAG_GETSET,tags=['sweep']) 

        self.add_parameter('startfreq', type=float,
            flags=Instrument.FLAG_GETSET,tags=['sweep']) 

        self.add_parameter('stopfreq', type=float,
            flags=Instrument.FLAG_GETSET,tags=['sweep']) 

        self.add_parameter('sweeptime', type=float,
            flags=Instrument.FLAG_GETSET,tags=['sweep'])

        self.add_parameter('resolutionBW', type=float,
            flags=Instrument.FLAG_GETSET,tags=['sweep'])

        self.add_parameter('videoBW', type=float,
            flags=Instrument.FLAG_GETSET,tags=['sweep'])        
            
        self.add_parameter('sweeptime_averages', type=float,
            flags=Instrument.FLAG_GET,tags=['sweep'])

        self.add_parameter('sweeptime_auto', type=float,
            flags=Instrument.FLAG_GETSET,tags=['sweep'])    

        self.add_parameter('freqpoints', type=numpy.ndarray,
            flags=Instrument.FLAG_GET,tags=['sweep'])    

        self.add_parameter('active_traces', type=int, flags=Instrument.FLAG_GET)    
                
        # Implement functions
        self.add_function('set_continuous_sweep_mode')
        #self.add_function('set_freq_center')
        #self.add_function('set_freq_span')
        self.add_function('set_marker')
        self.add_function('start_measurement')
        self.add_function('ready')
        self.add_function('set_powerunit')
        self.add_function('get_marker_level')
        self.add_function('get_trace_name')
        self.add_function('get_y_unit')
        #self.add_function('avg_clear')
        #self.add_function('avg_status')
        
        self.get_all()
    
    def get_all(self):        
        self.get_marker_level(1)
        
        #self.get_zerospan()

    def do_set_averages(self, av):
        '''
        Set number of averages

        Input:
            av (int) : Number of averages

        Output:
            None
        '''

        self.write('AVER ON')
        self.write('AVER:AUTO OFF')
        self.write('AVER:COUN %i' % (av))
  


    def do_get_averages(self):
        '''
        Get number of averages

        Input:
            None
        Output:
            number of averages
        '''
        
        return int(self.ask('AVER:COUN?'))
    
    def do_get_freqpoints(self):
        '''
        returns an array with the frequencies of the points returned by get_trace()
        ideally suitable as x-axis for plots
        '''

        x_values=numpy.linspace(self.do_get_startfreq(), self.do_get_stopfreq(), self.do_get_nop())
        return x_values
        

    def do_set_resolutionBW(self, BW):
        '''
        sets the resolution bandwidth
        '''
        self.write('band %e'%(BW))

    def do_get_resolutionBW(self):
        '''
        gets the resolution bandwidth
        '''
        return float(self.ask('band?'))


    def get_y_unit(self, channel):
        '''
        gets the y-unit
        '''
        y_unit=self.ask('CALC:LIM1:UNIT?')[:-1]
        return str(y_unit.strip('"'))

    def do_set_videoBW(self, BW):
        '''
        sets the video bandwidth
        '''
        self.write('band:vid %e'%(BW))

    def do_get_videoBW(self):
        '''
        gets the video bandwidth
        '''
        return float(self.ask('band:vid?'))

    def do_set_sweeptime(self, sweeptime):
        '''
        sets the sweeptime
        sweeptime in seconds (e.g. 3s) or milliseconds (e.g. 50ms)
        '''
        self.write('swe:time %s'%sweeptime)
        
    def do_get_sweeptime(self):
        '''
        gets the sweeptime
        '''
        return float(self.ask('swe:time?'))

    def do_set_sweeptime_auto(self, autosweep):
        '''
        sets the sweeptime
        sweeptime in seconds (e.g. 3s) or milliseconds (e.g. 50ms)
        '''
        self.write('SWE:TIME:AUTO %s'%autosweep)
        
    def do_get_sweeptime_auto(self):
        '''
        gets the sweeptime
        '''
        return float(self.ask('SWE:TIME:AUTO?'))
    

    def do_get_sweeptime_averages(self):
        '''
        gets the sweeptime averages
        '''
        return self.do_get_sweeptime()*self.do_get_averages()

    def do_get_active_traces(self):
        '''
        gets the active channels A,B,AB for channel 1,2,1+2
        '''
        return 1

    def get_trace_name(self, trace):
        '''
        function for signal spectroscopy script to automatically generate names for trace data
        :param trace:
        :return: (string) name of trace
        '''
        return 'Spectrum'

    def do_set_centerfreq(self, centerfreq):
        '''
        sets the center frequency
        '''
        self.write('freq:cent %e'%(centerfreq))

    def do_get_centerfreq(self):
        '''
        gets the center frequency
        '''
        return float(self.ask('freq:cent?'))

    def do_set_freqspan(self, freqspan):
        '''
        sets the frequency span
        '''
        self.write('freq:span %e'%(freqspan))
    
    def do_get_freqspan(self):
        '''
        get the frequency span
        '''
        return float(self.ask('freq:span?'))

    def do_set_startfreq(self, freq):
        self.write('freq:start %e'%(freq))

    def do_get_startfreq(self):
        return float(self.ask('freq:start?'))

    def do_set_stopfreq(self, freq):
        self.write('freq:stop %e'%(freq))

    def do_get_stopfreq(self):
        return float(self.ask('freq:stop?'))
        
    def do_set_nop(self, nop):
        self.write('swe:poin %i'%(nop))

    def do_get_nop(self):
        return int(self.ask('swe:poin?'))

    def ready(self):
        '''
        This is a proxy function, returning True when the VNA has finished the required number of averages.
        '''
        status = int(self.ask('STAT:OPER:COND?')[0:-1])
        if status  == 0:
            return True
        else:
            return False
        
    def do_set_powerunit(self,unit):
        '''
        sets the unit for powers
        provide unit as a string! ("DBm")
        '''
        self.write('unit:pow %s'%(unit))
        
    def do_get_powerunit(self):
        '''
        gets the power unit for powers
        '''
        return self.ask('unit:pow?').strip()
    
    def set_marker(self,marker,frequency):
        '''
        sets marker number marker to frequency
        
        '''
        self.write('calc:mark%i:x %e'%(marker, frequency))
        self.enable_marker(marker)
        
    def get_marker(self,marker):
        '''
        gets frequency of marker
        
        '''
        return float(self.ask('calc:mark%i:x?'%(marker)))
    
    def get_marker_level(self,marker):
        '''
        gets power level of indicated marker
        
        '''
        return float(self.ask('calc:mark%i:y?'%(marker)))
        
    def set_continuous_sweep_mode(self,value):
        '''
        value='ON' Continuous sweep
        value='OFF' Single sweep
        '''
        self.write('INIT:CONT %s'%(value))
    
    def enable_marker(self,marker,state='ON'):
        '''
        ON or OFF
        '''
        self.write('CALC:MARK%i %s'%(marker,state))
    
    def sweep(self):
        '''
        perform a sweep and wait for it to finish
        '''
        self.write('INIT; *WAI')
    
    def get_trace(self, tracenumber=1):
        return self._visainstrument.query_ascii_values('trac:data? trace%i'%tracenumber)

    def start_measurement(self):
        """starts a new measurement"""
        self.write("INIT:CONT OFF")
        self.write("*CLS")
        self.write("INIT:IMM; *OPC")
        
    def get_tracedata(self,tracenumber=1):

        amp = numpy.array(self._visainstrument.query_ascii_values('trac:data? trace%i'%tracenumber))
        return amp
    
    def write(self, command):
        self._visainstrument.write(command)
    
    def ask(self,command):
        return self._visainstrument.query(command)

    def pre_measurement(self):
        pass

    def post_measurement(self):
        self.write("INIT:CONT ON")
    
