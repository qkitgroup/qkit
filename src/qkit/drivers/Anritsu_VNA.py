# Anritsu_VNA.py 
# Pascal Macha <pascalmacha@googlemail.com>, 2010
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

import logging

import numpy

import qkit
from qkit import visa
from qkit.core.instrument_base import Instrument


class Anritsu_VNA(Instrument):
    """
    This is the python driver for the Anritsu MS4642A Vector Network Analyzer

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
        self._visainstrument = visa.instrument(self._address)
        self._zerospan = False
        self._freqpoints = 0
        self._ci = channel_index
        self._start = 0
        self._stop = 0
        self._nop = 0
        
        # Implement parameters
        self.add_parameter('nop', type=int, flags=Instrument.FLAG_GETSET, minval=1, maxval=100000)
        self.add_parameter('bandwidth', type=float, flags=Instrument.FLAG_GETSET, minval=0, maxval=1e9, units='Hz')
        self.add_parameter('averages', type=int, flags=Instrument.FLAG_GETSET, minval=1, maxval=1024)
        self.add_parameter('Average', type=bool, flags=Instrument.FLAG_GETSET)
        self.add_parameter('centerfreq', type=float, flags=Instrument.FLAG_GETSET, minval=0, maxval=20e9, units='Hz')
        self.add_parameter('cwfreq', type=float, flags=Instrument.FLAG_GETSET, minval=0, maxval=20e9, units='Hz')
        self.add_parameter('startfreq', type=float, flags=Instrument.FLAG_GETSET, minval=0, maxval=20e9, units='Hz')
        self.add_parameter('stopfreq', type=float, flags=Instrument.FLAG_GETSET, minval=0, maxval=20e9, units='Hz')
        self.add_parameter('span', type=float, flags=Instrument.FLAG_GETSET, minval=0, maxval=20e9, units='Hz')
        self.add_parameter('power', type=float, flags=Instrument.FLAG_GETSET, minval=-25, maxval=30, units='dBm')
        self.add_parameter('cw', type=bool, flags=Instrument.FLAG_GETSET)
        self.add_parameter('zerospan', type=bool, flags=Instrument.FLAG_GETSET)
        self.add_parameter('channel_index', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('source_attenuation', type=int, flags=Instrument.FLAG_GETSET, channels=(1, 2), minval=0, maxval=60, units='dB')
        self.add_parameter('source_power_start', type=float, flags=Instrument.FLAG_GETSET, channels=(1, 2), minval=-2.9e1, maxval=3e1, units='dBm')
        self.add_parameter('source_power_stop', type=float, flags=Instrument.FLAG_GETSET, channels=(1, 2), minval=-2.9e1, maxval=3e1, units='dBm')
        self.add_parameter('calibration_state', type=bool, flags=Instrument.FLAG_GETSET)
        self.add_parameter('sweep_type', type=str, flags=Instrument.FLAG_GETSET)
        self.add_parameter('power_nop', type=int, flags=Instrument.FLAG_GETSET, channels=(1, 2), minval=0, maxval=60, tags=['sweep'])
        self.add_parameter('avg_type', type=str, flags=Instrument.FLAG_GETSET)
        self.add_parameter('edel', type=float, flags=Instrument.FLAG_GETSET, minval=0, maxval=1e-3, units='s')
        self.add_parameter('sweeptime', type=float, flags=Instrument.FLAG_GET, minval=0, maxval=1e-3, units='s')
        self.add_parameter('sweeptime_averages', type=float, flags=Instrument.FLAG_GET, minval=0, maxval=1e-3, units='s')
        self.add_parameter('sweep_mode', type=str, flags=Instrument.FLAG_GETSET)
        self.add_parameter('trigger_source', type=str, flags=Instrument.FLAG_GETSET)
        
        # Implement functions
        self.add_function('get_freqpoints')
        self.add_function('get_tracedata')
        self.add_function('init')
        self.add_function('returnToLocal')
        self.add_function('pre_measurement')
        self.add_function('start_measurement')
        self.add_function('ready')
        self.add_function('post_measurement')
        self.add_function('avg_clear')
        self.add_function('avg_status')
        
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
        self.get_channel_index()
        self.get_cw()
        self.get_source_attenuation1()
        self.get_source_attenuation2()
        self.get_source_power_start1()
        self.get_source_power_start2()
        self.get_source_power_stop1()
        self.get_source_power_stop2()
        self.get_calibration_state()
        self.get_sweep_type()
        self.get_power_nop1()
        self.get_power_nop2()
        self.get_avg_type()
        self.get_edel()
    
    def init(self):
        if self._zerospan:
            self.write('INIT1;*wai')
        else:
            if self.get_Average():
                for i in range(self.get_averages()):
                    self.write('INIT1;*wai')
            else:
                self.write('INIT1;*wai')
    
    def hold(self, status):
        if status:
            self.set_sweep_mode("HOLD")
        else:
            self.set_sweep_mode("CONT")
    
    def avg_clear(self):
        self.write(':SENS%i:AVER:CLE' % self._ci)
    
    def returnToLocal(self):
        self.write('RTL')
    
    def avg_status(self):
        return int(self.ask(':SENS%i:AVER:SWE?' % self._ci))
    
    def get_tracedata(self, format='AmpPha', single=False):
        """
        Get the data of the current trace

        Input:
            format (string) : 'AmpPha': Amp in dB and Phase, 'RealImag',

        Output:
            'AmpPha':_ Amplitude and Phase
        """
        data = self.ask_for_values('FORM:DATA REAL; FORM:BORD SWAPPED; CALC%i:SEL:DATA:SDAT?' % self._ci, fmt=visa.double)
        data_size = numpy.size(data)
        datareal = numpy.array(data[0:data_size:2])
        dataimag = numpy.array(data[1:data_size:2])
        
        if format.upper() == 'REALIMAG':
            if self._zerospan:
                return numpy.mean(datareal), numpy.mean(dataimag)
            else:
                return datareal, dataimag
        elif format.upper() == 'AMPPHA':
            if self._zerospan:
                datareal = numpy.mean(datareal)
                dataimag = numpy.mean(dataimag)
                dataamp = numpy.sqrt(datareal * datareal + dataimag * dataimag)
                datapha = numpy.arctan(dataimag / datareal)
                return dataamp, datapha
            else:
                dataamp = numpy.sqrt(datareal * datareal + dataimag * dataimag)
                datapha = numpy.arctan2(dataimag, datareal)
                return dataamp, datapha
        else:
            raise ValueError('get_tracedata(): Format must be AmpPha or RealImag')
    
    def get_freqpoints(self, query=False):
        if query:
            self._freqpoints = self.ask_for_values('FORM:DATA REAL; FORM:BORD SWAPPED; :SENS%i:FREQ:DATA?' % self._ci, fmt=visa.double)
        else:
            self._freqpoints = numpy.linspace(self._start, self._stop, self._nop)
        return self._freqpoints
    
    def get_powerpoints(self):
        return numpy.linspace(self.get_source_power_start1(), self.get_source_power_stop1(), self.get_power_nop1())
    
    def do_set_sweep_mode(self, mode):
        """
        select the sweep mode from 'HOLD', 'CONT', SING'
        """
        if mode.upper() in ["HOLD", "CONT", "SING"]:
            self.write(':SENS:HOLD:FUNC ' + mode.upper())
        else:
            logging.warning('invalid mode')
    
    def do_get_sweep_mode(self):
        return self.ask(':SENS:HOLD:FUNC?')
    
    def do_set_nop(self, nop):
        """
        Set Number of Points (nop) for sweep

        Input:
            nop (int) : Number of Points

        Output:
            None
        """
        logging.debug(__name__ + ' : setting Number of Points to %s ' % nop)
        if self._zerospan:
            print('in zerospan mode, nop is 1')
        else:
            cw = self.get_cw()
            if (nop == 1) and (not cw):
                logging.info(__name__ + 'nop == 1 is only supported in CW mode.')
                self.set_cw(True)
            if cw:
                self.write(':SENS%i:SWE:CW:POIN %i' % (self._ci, nop))
            else:
                self.write(':SENS%i:SWE:POIN %i' % (self._ci, nop))
            self._nop = nop
            self.get_freqpoints()  # Update List of frequency points
    
    def do_get_nop(self):
        """
        Get Number of Points (nop) for sweep

        Input:
            None
        Output:
            nop (int)
        """
        logging.debug(__name__ + ' : getting Number of Points')
        if self._zerospan:
            return 1
        else:
            if self.get_cw():
                self._nop = int(self.ask(':SENS%i:SWE:CW:POIN?' % self._ci))
            else:
                self._nop = int(self.ask(':SENS%i:SWE:POIN?' % self._ci))
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
            self.write('SENS%i:AVER:STAT %s' % (self._ci, '1'))
            self.write('SENS%i:AVER:TYP SWE' % self._ci)
        else:
            self.write('SENS%i:AVER:STAT %s' % (self._ci, '0'))
    
    def do_get_Average(self):
        """
        Get status of Average

        Input:
            None

        Output:
            Status of Averaging (bool)
        """
        logging.debug(__name__ + ' : getting average status')
        return bool(int(self.ask('SENS%i:AVER:STAT?' % self._ci)))
    
    def do_set_averages(self, av):
        """
        Set number of averages

        Input:
            av (int) : Number of averages

        Output:
            None
        """
        if not self._zerospan:
            logging.debug(__name__ + ' : setting Number of averages to %i ' % av)
            self.write('SENS%i:AVER:COUN %i' % (self._ci, av))
        else:
            self.write('SWE:POIN %.1f' % av)
    
    def do_get_averages(self):
        """
        Get number of averages

        Input:
            None
        Output:
            number of averages
        """
        logging.debug(__name__ + ' : getting Number of Averages')
        if self._zerospan:
            return int(self.ask('SWE%i:POIN?' % self._ci))
        else:
            return int(self.ask('SENS%i:AVER:COUN?' % self._ci))
    
    def do_set_power(self, pow):
        """
        Set probe power

        Input:
            pow (float) : Power in dBm

        Output:
            None
        """
        logging.debug(__name__ + ' : setting power to %s dBm' % pow)
        self.write('SOUR%i:POW:PORT1:LEV:IMM:AMP %.2f' % (self._ci, pow))
    
    def do_get_power(self):
        """
        Get probe power

        Input:
            None

        Output:
            pow (float) : Power in dBm
        """
        logging.debug(__name__ + ' : getting power')
        return float(self.ask('SOUR%i:POW:PORT1:LEV:IMM:AMP?' % self._ci))
    
    def do_set_centerfreq(self, cf):
        """
        Set the center frequency

        Input:
            cf (float) :Center Frequency in Hz

        Output:
            None
        """
        logging.debug(__name__ + ' : setting center frequency to %s' % cf)
        self.write('SENS%i:FREQ:CENT %f' % (self._ci, cf))
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
        return float(self.ask('SENS%i:FREQ:CENT?' % self._ci))
    
    def do_set_cwfreq(self, cf):
        """ set cw frequency """
        self.write('SENS%i:FREQ:CW %f' % (self._ci, cf))
    
    def do_get_cwfreq(self):
        """ get cw frequency """
        return float(self.ask('SENS%i:FREQ:CW?' % self._ci))
    
    def do_set_span(self, span):
        """
        Set Span

        Input:
            span (float) : Span in KHz

        Output:
            None
        """
        logging.debug(__name__ + ' : setting span to %s Hz' % span)
        self.write('SENS%i:FREQ:SPAN %i' % (self._ci, span))
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
        # logging.debug(__name__ + ' : getting center frequency')
        span = self.ask('SENS%i:FREQ:SPAN?' % self._ci)  # float( self.ask('SENS1:FREQ:SPAN?'))
        return span
    
    def do_set_startfreq(self, val):
        """
        Set Start frequency

        Input:
            span (float) : Frequency in Hz

        Output:
            None
        """
        logging.debug(__name__ + ' : setting start freq to %s Hz' % val)
        self.write('SENS%i:FREQ:STAR %f' % (self._ci, val))
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
        self._start = float(self.ask('SENS%i:FREQ:STAR?' % self._ci))
        return self._start
    
    def do_set_stopfreq(self, val):
        """
        Set STop frequency

        Input:
            val (float) : Stop Frequency in Hz

        Output:
            None
        """
        logging.debug(__name__ + ' : setting stop freq to %s Hz' % val)
        self.write('SENS%i:FREQ:STOP %f' % (self._ci, val))
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
        self._stop = float(self.ask('SENS%i:FREQ:STOP?' % self._ci))
        return self._stop
    
    def do_get_sweeptime_averages(self):
        if self.get_Average():
            return self.get_sweeptime() * self.get_averages()
        else:
            return self.get_sweeptime()
    
    def do_get_sweeptime(self):
        
        """
        Get sweep time

        """
        
        logging.debug(__name__ + ' : getting sweep time')
        
        return float(self.get_nop()) / self.get_bandwidth()
    
    def do_get_edel(self):  # added by MW
        
        
        """
        Get electrical delay

        """
        logging.debug(__name__ + ' : getting electrical delay')
        return float(self.ask('SENS%i:CORR:EXT:PORT1?' % self._ci))
    
    def do_set_edel(self, val):  # added by MW
        
        """
        Set electrical delay

        """
        logging.debug(__name__ + ' : setting electrical delay to %s sec' % val)
        self.write('SENS%i:CORR:EXT:PORT1  %.12f' % (self._ci, val))
    
    def set_edel_auto(self):
        
        """
        Uses the VNA auto edel function for trace 1 and returns it.
        """
        
        logging.debug(__name__ + ' : setting electrical delay to auto')
        self.write(":CALC1:PAR1:REF:EXT:AUTO")
        return self.get_edel()
    
    def do_set_bandwidth(self, band):
        """
        Set Bandwidth

        Input:
            band (float) : Bandwidth in Hz

        Output:
            None
        """
        logging.debug(__name__ + ' : setting bandwidth to %s Hz' % band)
        self.write('SENS%i:BWID:RES %i' % (self._ci, band))
    
    def do_get_bandwidth(self):
        """
        Get Bandwidth

        Input:
            None

        Output:
            band (float) : Bandwidth in Hz
        """
        logging.debug(__name__ + ' : getting bandwidth')
        return float(self.ask('SENS%i:BWID:RES?' % self._ci))
    
    def do_set_cw(self, val):
        """
        Set instrument to CW (single frequency) mode and back
        """
        state = 1 if val == True else 0
        self.write(':SENS%i:SWE:CW %d' % (self._ci, state))
    
    def do_get_cw(self):
        """
        retrieve CW mode status from device
        """
        return bool(int(self.ask(':SENS%i:SWE:CW?' % self._ci)))
    
    def do_set_zerospan(self, val):
        """
        Zerospan is a virtual "zerospan" mode. In Zerospan physical span is set to
        the minimal possible value (2Hz) and "averages" number of points is set.

        Input:
            val (bool) : True or False

        Output:
            None
        """
        # logging.debug(__name__ + ' : setting status to "%s"' % status)
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
            if av < 2:
                av = 2
        else:
            self.set_Average(True)
            self.set_span(self._oldspan)
            self.set_nop(self._oldnop)
            self.get_averages()
        self.get_nop()
    
    def do_get_zerospan(self):
        """
        Check weather the virtual zerospan mode is turned on

        Input:
            None

        Output:
            val (bool) : True or False
        """
        return self._zerospan
    
    def do_set_trigger_source(self, source):
        """
        Set Trigger Mode

        Input:
            source (string) : AUTO | MANual | EXTernal | REMote

        Output:
            None
        """
        logging.debug(__name__ + ' : setting trigger source to "%s"' % source)
        if source.upper() in ["AUTO", "MAN", "EXT", "REM"]:
            self.write('TRIG:SOUR %s' % source.upper())
        else:
            raise ValueError('set_trigger_source(): must be AUTO | MANual | EXTernal | REMote')
    
    def do_get_trigger_source(self):
        """
        Get Trigger Mode

        Input:
            None

        Output:
            source (string) : AUTO | MANual | EXTernal | REMote
        """
        logging.debug(__name__ + ' : getting trigger source')
        return self.ask('TRIG:SOUR?')
    
    def do_set_channel_index(self, val):
        """
        Set the index of the channel to address.

        Input:
            val (int) : 1 .. number of active channels (max 16)

        Output:
            None
        """
        logging.debug(__name__ + ' : setting channel index to "%i"' % int)
        nop = self.read('DISP:COUN?')
        if val < nop:
            self._ci = val
        else:
            raise ValueError('set_channel_index(): index must be < nop channels')
    
    def do_get_channel_index(self):
        """
        Get active channel

        Input:
            None

        Output:
            channel_index (int) : 1-16
        """
        logging.debug(__name__ + ' : getting channel index')
        return self._ci
    
    def do_get_source_attenuation(self, channel):
        """
        Get status of source attenuation on port

        Input:
            None

        Output:
            Status of source attenuation (value in dB)
        """
        
        logging.debug(__name__ + ' : getting attenuation status')
        return int(self.ask('SOUR%i:POW:PORT%i:ATT?' % (self._ci, channel)))
    
    def do_set_source_attenuation(self, att, channel):
        """
        Set value of source attenuation

        Input:
            att (int)   :   Value of source attenuation must
                            must be one of (0,10,20,30,40,50,60)

        Output:
            None
        """
        if att in (0, 10, 20, 30, 40, 50, 60):
            logging.debug(__name__ + ' : setting attenuation on port %i to %idB ' % (channel, att))
            self.write('SOUR%i:POW:PORT%i:ATT %i' % (self._ci, channel, att))
        else:
            logging.debug(__name__ + ' : cannot set attenuation to %i ' % att)
    
    def do_get_source_power_start(self, channel):
        """
        Get starting value for power sweep

        Input:
            None

        Output:
            Starting value for the power sweep (float value in dBm)
        """
        
        logging.debug(__name__ + ' : getting starting power')
        return float(self.ask('SOUR%i:POW:PORT%i:LIN:POW:STAR?' % (self._ci, channel)))
    
    def do_set_source_power_start(self, pow, channel):
        """
        Set starting value for power sweep

        Input:
            pow (float)   :   Starting power (-29.9 to 30)

        Output:
            None
        """
        logging.debug(__name__ + ' : setting starting power on port %i to %.2f dBm ' % (channel, pow))
        self.write('SOUR%i:POW:PORT%i:LIN:POW:STAR %.2f' % (self._ci, channel, pow))
    
    def do_get_source_power_stop(self, channel):
        """
        Get stopping value for power sweep

        Input:
            None

        Output:
            Stopping value for the power sweep (float value in dBm)
        """
        
        logging.debug(__name__ + ' : getting stopping power')
        return float(self.ask('SOUR%i:POW:PORT%i:LIN:POW:STOP?' % (self._ci, channel)))
    
    def do_set_source_power_stop(self, pow, channel):
        """
        Set stopping value for power sweep

        Input:
            pow (float)   :   Stopping power (-29.9 to 30)

        Output:
            None
        """
        
        logging.debug(__name__ + ' : setting stopping power on port %i to %.2f dBm ' % (channel, pow))
        self.write('SOUR%i:POW:PORT%i:LIN:POW:STOP %.2f' % (self._ci, channel, pow))
    
    def do_set_calibration_state(self, status):
        """
        Set status of Calibration

        Input:
            status (boolean)

        Output:
            None
        """
        
        if status:
            logging.debug(__name__ + ' : Turning on calibration ')
            self.write('SENS%i:CORR:STAT ON' % self._ci)
        else:
            logging.debug(__name__ + ' : Turning off calibration ')
            self.write('SENS%i:CORR:STAT OFF' % self._ci)
    
    def do_get_calibration_state(self):
        """
        Get status of Calibration

        Input:
            None

        Output:
            Status of Calibration (bool)
        """
        logging.debug(__name__ + ' : getting calibration state status')
        return bool(int(self.ask('SENS%i:CORR:STAT?' % self._ci)))
    
    def do_get_sweep_type(self):
        """
        Get the Sweep Type

        Input:
            None

        Output:
            Sweep Type (string). One of
            LIN:    Frequency-based linear sweep
            LOG:    Frequency-based logarithmic sweep
            FSEG:   Segment-based sweep with frequency-based segments
            ISEG:   Index-based sweep with frequency-based segments
            POW:    Power-based sweep with either Power-based sweep with a
                CW frequency, or Power-based sweep with swept-frequency
            MFGC:   Multiple frequency gain compression
        """
        logging.debug(__name__ + ' : getting sweep type')
        
        return str(self.ask('SENS%i:SWE:TYP?' % self._ci))
    
    def do_set_sweep_type(self, swtype):
        """
        Set the Sweep Type
        Input:
            swtype (string):    One of
                LIN:    Frequency-based linear sweep
                LOG:    Frequency-based logarithmic sweep
                FSEG:   Segment-based sweep with frequency-based segments
                ISEG:   Index-based sweep with frequency-based segments
                POW:    Power-based sweep with either Power-based sweep with a
                    CW frequency, or Power-based sweep with swept-frequency
                MFGC:   Multiple frequency gain compression

        Output:
            None
        """
        if swtype in ('LIN', 'LOG', 'FSEG', 'ISEG', 'POW', 'MFGC'):
            
            logging.debug(__name__ + ' : Setting sweep type to %s' % swtype)
            return self.write('SENS%i:SWE:TYP %s' % (self._ci, swtype))
        
        else:
            logging.debug(__name__ + ' : Illegal argument %s' % swtype)
    
    def do_get_power_nop(self, channel):
        """
        Get number of points for a power sweep

        Input:
            None

        Output:
            Number of points for a power sweep (int)
        """
        
        logging.debug(__name__ + ' : getting power nop')
        return int(self.ask(':SOUR%i:POW:PORT%i:LIN:POW:POIN?' % (self._ci, channel)))
    
    def do_set_power_nop(self, n, channel):
        """
        Set number of points for a power sweep

        Input:
            n (int)   :   Number of points of the sweep

        Output:
            None
        """
        
        logging.debug(__name__ + ' : setting number of power sweep points on channel %i to %i ' % (channel, n))
        self.write(':SOUR%i:POW:PORT%i:LIN:POW:POIN %i' % (self._ci, channel, n))
    
    def do_get_avg_type(self):
        """
        Get the Averaging Type

        Input:
            None

        Output:
            Averaging Type (string). One of
            POIN:   Point by Point
            SWE:    Sweep by Sweep
            
        """
        logging.debug(__name__ + ' : getting averaging type')
        
        return str(self.ask('SENS%i:AVER:TYP?' % self._ci))
    
    def do_set_avg_type(self, avgtype):
        """
        Set the Averaging Type
        Input:
            avgtype (string). One of:
                POIN:   Point by Point
                SWE:    Sweep by Sweep

        Output:
            None
        """
        if avgtype in ('POIN', 'SWE'):
            
            logging.debug(__name__ + ' : Setting avg type to %s' % avgtype)
            return self.write('SENS%i:AVER:TYP %s' % (self._ci, avgtype))
        
        else:
            logging.debug(__name__ + ' : Illegal argument %s' % avgtype)
    
    def read(self, msg):
        return self._visainstrument.read(msg)
    
    def write(self, msg):
        return self._visainstrument.write(msg)
    
    if qkit.visa.qkit_visa_version == 1:
        def ask(self, msg):
            return self._visainstrument.ask(msg)
        
        def ask_for_values(self, msg, format=None, fmt=None):
            return self._visainstrument.ask_for_values(msg, fmt)
    else:
        def ask(self, msg):
            return self._visainstrument.query(msg)
        
        def ask_for_values(self, msg, format=None, fmt=None):
            return self._visainstrument.query_binary_values(msg, fmt)
    
    def pre_measurement(self):
        """
        Set everything needed for the measurement
        Averaging has to be enabled.
        """
        self.hold(False)
        if not self.get_Average():
            self.set_Average(True)
            self.set_averages(1)
    
    def post_measurement(self):
        """
        Bring the VNA back to a mode where it can be easily used by the operater.
        For this VNA and measurement method, no special things have to be done.
        """
        pass
    
    def start_measurement(self):
        """
        This function is called at the beginning of each single measurement in the spectroscopy script.
        Here, it resets the averaging.
        """
        self.avg_clear()
    
    def ready(self):
        """
        This is a proxy function, returning True when the VNA has finished the required number of averages.
        """
        return self.avg_status() == self.get_averages(query=False)
