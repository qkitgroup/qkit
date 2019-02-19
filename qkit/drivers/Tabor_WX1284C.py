# Tabor_WX1284C.py driver, to perform the communication between the Wrapper and the device
# Lukas Gruenhaupt <gruenhaupt@gmail.com>, 04/2015
# Andre Schneider <andre.schneider@kit.edu>, 01/2016
#
# based on Tektronix_AWG7062.py class coded by
# Pieter de Groot <pieterdegroot@gmail.com>, 2008
# Martijn Schaafsma <qtlab@mcschaafsma.nl>, 2008
# Guenevere Prawiroatmodjo <guen@vvtp.tudelft.nl>, 2009
# Markus Jerger <jerger@kit.edu>, 2010
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
import numpy
import struct
import time

import pyvisa.constants as vc


class Tabor_WX1284C(Instrument):
    '''
    This is the python driver for the Tabor Electronics Arbitrary Waveform Generator WX1284C
    '''

    def __init__(self, name, address, chpair=None, reset=False, clock=6e9, numchannels = 4):
        '''
        Initializes the AWG WX1284C
        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address
            reset (bool)     : resets to default values, default=false
            chpair (int)     : number of channel pair (1 for channels 1&2, 2 for channels 3&4)
        Output:
            None
        '''
        logging.debug(__name__ + ' : Initializing instrument at '+address)
        Instrument.__init__(self, name, tags=['physical'])




        self._address = address
        if visa.qkit_visa_version == 1:
            self._visainstrument = visa.instrument(self._address,term_chars = "\r\n")
            self._visainstrument.timeout=2
        else:
            self._visainstrument = visa.instrument(self._address)
            self._visainstrument.timeout=2000L
            self._visainstrument.visalib.set_buffer(self._visainstrument.session, vc.VI_READ_BUF, 4000)
            self._visainstrument.visalib.set_buffer(self._visainstrument.session, vc.VI_WRITE_BUF, 32000)

            self._visainstrument.read_termination = '\n'
            self._visainstrument.write_termination = '\n'

                #intf_type = self._visainstrument.get_visa_attribute(vc.VI_ATTR_INTF_TYPE)

            if self._visainstrument.get_visa_attribute(vc.VI_ATTR_INTF_TYPE) in (vc.VI_INTF_USB, vc.VI_INTF_GPIB, vc.VI_INTF_TCPIP):
                self._visainstrument.set_visa_attribute(vc.VI_ATTR_WR_BUF_OPER_MODE, vc.VI_FLUSH_ON_ACCESS)
                self._visainstrument.set_visa_attribute(vc.VI_ATTR_RD_BUF_OPER_MODE, vc.VI_FLUSH_ON_ACCESS)
                if self._visainstrument.get_visa_attribute(vc.VI_ATTR_INTF_TYPE) == vc.VI_INTF_TCPIP:
                    self._visainstrument.set_visa_attribute(vc.VI_ATTR_TERMCHAR_EN, vc.VI_TRUE)

            self._visainstrument.clear()


        
        
        
        self._ins_VISA_INSTR = False#(self._visainstrument.resource_class == "INSTR") #check whether we have INSTR or SOCKET type
        
        self._values = {}
        self._values['files'] = {}
        self._clock = clock

        if chpair not in [None, 1, 2]:
            raise ValueError("chpair should be 1, 2 or None.")

        if chpair and numchannels!=2:
            raise ValueError("numchannels should be 2.")

        if chpair is None and numchannels !=4:
            raise ValueError("numchannels should be 4.")

        self._numchannels = numchannels
        self._choff = 0

        if chpair == 2:
            self._choff = 2

        if numchannels == 4:
            self.add_parameter('runmode', type=str,
                flags=Instrument.FLAG_GETSET,
                channels=(1, 2), channel_prefix='p%d_')
        else:
            self.add_parameter('runmode', type=str,
                flags=Instrument.FLAG_GETSET)
        
        self.add_parameter('output', type=bool,
            flags=Instrument.FLAG_GETSET,
            channels=(1, self._numchannels), channel_prefix='ch%d_')
        self.add_parameter('marker_output', type=bool,
            flags=Instrument.FLAG_GETSET,
            channels=(1, self._numchannels), channel_prefix='ch%d_')
        self.add_parameter('trigger_impedance', type=float,       #changed, checked in manual
            flags=Instrument.FLAG_GETSET,
            minval=50, maxval=10e3, units='Ohm')
        self.add_parameter('trigger_level', type=float,
            flags=Instrument.FLAG_GETSET,
            minval=-5, maxval=5, units='Volts')
        self.add_parameter('clock', type=float,
            flags=Instrument.FLAG_GETSET,
            minval=1e6, maxval=1.25e9, units='Hz')
        self.add_parameter('reference_source', type=str,
            flags=Instrument.FLAG_GETSET)
        self.add_parameter('reference_source_freq', type=float,
            flags=Instrument.FLAG_GETSET,
            minval=10e6, maxval=100e6, units='Hz')
        self.add_parameter('common_clock', type=bool,
                flags=Instrument.FLAG_GETSET)
        self.add_parameter('amplitude', type=float,
            flags=Instrument.FLAG_GETSET,
            channels=(1, self._numchannels), minval=0, maxval=2, units='Volts', channel_prefix='ch%d_')
        self.add_parameter('offset', type=float,
            flags=Instrument.FLAG_GETSET,
            channels=(1, self._numchannels), minval=-2, maxval=2, units='Volts', channel_prefix='ch%d_')
        self.add_parameter('marker_high', type=float,
            flags=Instrument.FLAG_GETSET,
            channels=(1, self._numchannels), minval=-2, maxval=2, units='Volts', channel_prefix='ch%d_')
        self.add_parameter('status', type=bool,
            flags=Instrument.FLAG_GETSET,
            channels=(1, self._numchannels),channel_prefix='ch%d_')
        self.add_parameter('sync_position', type=float,
                flags=Instrument.FLAG_GETSET,units='s')

        if numchannels == 4:
            self.add_parameter('trigger_mode', type=str,
                flags=Instrument.FLAG_GETSET,
                channels=(1, 2), channel_prefix='p%d_')
            self.add_parameter('trigger_delay', type=float,
                flags=Instrument.FLAG_GETSET,
                channels=(1, 2), channel_prefix='p%d_')
            self.add_parameter('sequence_mode', type=str,
                flags=Instrument.FLAG_GETSET,
                channels=(1, 2), channel_prefix='p%d_')
            self.add_parameter('trigger_source', type=str,
                flags=Instrument.FLAG_GETSET,
                channels=(1, 2), channel_prefix='p%d_')
            self.add_parameter('trigger_time', type=float,
                flags=Instrument.FLAG_GETSET,
                channels=(1, 2), channel_prefix='p%d_')
            self.add_parameter('sync_output', type=bool,
                flags=Instrument.FLAG_GETSET,
                channels=(1, 2), channel_prefix='p%d_')
            self.add_parameter('trigger_slope', type=str,
                flags=Instrument.FLAG_GETSET,
                channels=(1, 2), channel_prefix='p%d_')

        else:
            self.add_parameter('trigger_mode', type=str,
                flags=Instrument.FLAG_GETSET)
            self.add_parameter('trigger_delay', type=float,
                flags=Instrument.FLAG_GETSET)
            self.add_parameter('sequence_mode', type=str,
                flags=Instrument.FLAG_GETSET)
            self.add_parameter('trigger_source', type=str,
                flags=Instrument.FLAG_GETSET)
            self.add_parameter('trigger_time', type=float,
                flags=Instrument.FLAG_GETSET)
            self.add_parameter('sync_output', type=bool,
                flags=Instrument.FLAG_GETSET)
            self.add_parameter('trigger_slope', type=str,
                flags=Instrument.FLAG_GETSET)

        # Add functions
        self.add_function('reset')
        self.add_function('fix')
        self.add_function('wait')
        self.add_function('get_all')
        self.add_function('set_seq_length')
        self.add_function('clear_waveforms')

        self.add_function('ask') #for debug
        self.add_function('write') #for debug
        self.add_function('define_sequence')
        self.add_function('close')


        if numchannels==2:
            self.add_function('preset_readout')
            self.add_function('preset_manipulation')

        self.add_function('wfm_send')
        self.add_function('wfm_send2')
        
        if reset:
            self.reset()
        else:
            self.get_all()    
        self.write(":INST1;:MARK:SOUR USER;:INST3;:MARK:SOUR USER")

        print("The device is set up with %i channels. You use the channels %s" %(numchannels, str(range(self._choff+1, numchannels + self._choff+1))))

    # Functions
    def fix(self,verbose=True):
        '''
        Communication with the device is sometimes problematic. This functions helps by clearing the queue and reading/resetting the error memory.
        '''
        if not self._ins_VISA_INSTR:
            tmo= self._visainstrument.timeout
            self._visainstrument.timeout = .1
            if verbose: print "Emptying Queue"
            try:
                for i in range(200):
                    rl = str(self._visainstrument.read())
                    if verbose: print "In Buffer %i: "%i+rl
            except visa.VisaIOError:
                if verbose: print "Timeout after %i iterations"%i
            self._visainstrument.timeout = tmo
        if verbose: print "Clearing Error Memory:"
        for i in range(200):
            try:
                if self.check():
                    return i
            except ValueError as e:
                logging.warning(e)
                continue

    def check(self):
        #this function is used to check whether the command was successfull
        try:
            rv = self.ask(":SYST:ERR?")
            if rv[0]=="0": return True
            else: raise ValueError(__name__ + "(" +self.get_name()+") : Device responded with error ->%s<-"%rv)
        except visa.VisaIOError:
            return False

    def reset(self):
        '''
        Resets the instrument to default values
        Input:
            None
        Output:
            None
        '''
        logging.info(__name__ + ' : Resetting instrument')
        self.write('*RST')
        self.write(":INST1;:MARK:SOUR USER;:INST3;:MARK:SOUR USER")

    def preset(self):
        '''
        resets the instrument and then sets all parameters to the values necessary for the time domain setup
        '''
        self.reset()
        self.set_trigger_impedance(50)
        self.set_trigger_level(.2)
        #self.set_p1_trigger_mode('TRIG')
        #self.set_p2_trigger_mode('TRIG')
        #self.set_p1_runmode('SEQ')
        #self.set_p2_runmode('USER')
        #self.set_p1_sequence_mode('STEP')
        #self.set_p2_sequence_mode('STEP')
        for i in range(1,self._numchannels + 1):
            self.set('ch%i_amplitude'%i,2)
            self.set('ch%i_marker_output'%i,True)
            self.set('ch%i_marker_high'%i,1)
        self.get_all()

    def get_all(self):
        '''
        Reads all implemented parameters from the instrument,
        and updates the wrapper.
        Input:
            None
        Output:
            None
        '''
        self.fix(False)
        logging.info(__name__ + ' : Reading all data from instrument')
        #self.check()
        try:
            pass
            #self.get_trigger_impedance()
        except Exception:
            logging.warning('command trigger impedance not supported')
        self.get_trigger_level()
        self.get_clock()
        if self._numchannels == 4:
            for i in (1,2):
                self.get('p%d_runmode' % i)
                self.get('p%d_trigger_mode' % i)
                self.get('p%d_sequence_mode' % i)
                self.get('p%d_sync_output' %i)
                self.get('p%d_trigger_time' %i)
                self.get('p%d_trigger_delay' %i)
                self.get('p%d_trigger_source' %i)
                self.get('p%d_trigger_slope' %i)
        for i in range(1,self._numchannels + 1):
            self.get('ch%d_amplitude' % i)
            self.get('ch%d_offset' % i)
            self.get('ch%d_marker_high' % i)
            self.get('ch%d_marker_output' % i)
            self.get('ch%d_status' % i)
            self.get('ch%d_output' % i)
        if self._numchannels == 2:
            self.get('runmode')
            self.get('trigger_mode')
            self.get('sequence_mode')
            self.get('sync_output')
            self.get('trigger_time')
            self.get('trigger_delay')
            self.get('trigger_source')
            self.get('trigger_slope')

    def preset_readout(self, tr_slope = 'NEG'):
        '''
        prepare the specified AWG for readout mode

        inputs:
            trigger edge
        output:
            None
        '''
        self.set_runmode('USER')
        self.set_ch1_output(True)
        self.set_ch2_output(True)
        self.set_trigger_mode('TRIG')
        self.set_trigger_source('EXT')
        for i in range(1,self._numchannels + 1):
            self.set('ch%i_amplitude'%i,2)
            self.set('ch%i_marker_output'%i,True)
            self.set('ch%i_marker_high'%i,1)
        try:
            self.set_trigger_slope(tr_slope)
        except Exception as m:
            print 'Trigger slope has to be POS or NEG. Setting to NEG.', m
            self.set_trigger_slope('NEG')

    def preset_manipulation(self):
        '''
        prepare the specified AWG for manipulation
        default repitition time is 2e-4
        Input:
            None
        Output:
            None
        '''
        self.set_runmode('SEQ')
        self.set_ch1_output(True)
        self.set_ch2_output(True)
        self.set_trigger_mode('TRIG')
        self.set_trigger_source('TIM')
        self.set_sync_output(True)
        self.set_trigger_time(2e-4)
        self.set_sequence_mode("STEP")
        for i in range(1,self._numchannels + 1):
            self.set('ch%i_amplitude'%i,2)
            self.set('ch%i_marker_output'%i,True)
            self.set('ch%i_marker_high'%i,1)


    def ask(self,cmd):
        for i in range(15):
            try:
                logging.debug(__name__ + "(" +self.get_name()+" ask command:"+cmd[:100]+":")
                return self._visainstrument.ask(cmd).strip()
            except visa.VisaIOError as e:
                logging.debug(__name__ + "(" +self.get_name()+"): VisaIOError, retry ->%s<-"%e)
        raise ValueError(__name__ + "(" +self.get_name()+"): ask('%s') not successful after 15 retries ->%s<-"%(cmd[0:100],e))

    def write(self,cmd):
        for i in range(15):
            try:
                logging.debug(__name__ + "(" +self.get_name()+" write command:"+cmd[:100]+":")
                return self._visainstrument.write(cmd)
            except visa.VisaIOError as e:
                logging.debug(__name__ + "(" +self.get_name()+") :VisaIOError, retry ->%s<-"%e)
        raise ValueError(__name__ + "(" +self.get_name()+") : write('%s') not successful after 15 retries ->%s<-"%(cmd[0:100],e))

    def write_raw(self,cmd):
        if visa.qkit_visa_version == 1:
            self.write(cmd)
        else:
            self._visainstrument.write_raw(cmd)


    def clear_waveforms(self):
        '''
        Clears the waveform on all channels.
        Input:
            None
        Output:
            None
        '''
        logging.debug(__name__ + ' : Clear waveforms from channels')
        for idx in range(self._choff+1,self._numchannels + 1):
            self.write(':INST%i; :TRAC:DEL:ALL'%idx)

    def run(self):
        '''
        Initiates the output of a waveform or a sequence. This is equivalent to pressing
        Run/Delete/Stop button on the front panel. The instrument can be put in the run
        state only when output waveforms are assigned to channels.
        Input:
            None
        Output:
            None
        '''
        logging.debug(__name__ + ' : Run/Initiate output of a waveform or sequence')
        self.write(':ENAB')

    def stop(self):
        '''
        Terminates the output of a waveform or a sequence. This is equivalent to pressing
        Run/Delete/Stop button on the front panel.
        Input:
            None
        Output:
            None
        '''
        logging.debug(__name__ + ' : Stop/Terminate output of a waveform or sequence')
        self.write('ABOR')

    def wait(self, max_timeouts = 1, quiet = False):
        '''
        Wait until the previous command has completed.

        Input:
            timeouts - maximum number of timeouts that may occur. note that the command
                does not execute at all if zero maximum timeouts are requested.
            quiet - if True, do not show messages when a timeout occurs
        '''
        if(max_timeouts > 0):
            self.write('*STB?')
        for i in range(max_timeouts):
            try:
                time.sleep(0.025)
                self._visainstrument.read()
                return
            except:
                if(not quiet): print('still waiting for the awg to become ready')
                time.sleep(1)

    def do_set_output(self, state, channel):
        '''
        This command sets the output state of the AWG.
        Input:
            channel (int) : the source channel
            state (bool) : True or False
        Output:
            None
        '''
        return self.set("ch%i_status"%channel,state)

    def do_get_output(self, channel):
        '''
        This command gets the output state of the AWG.
        Input:
            channel (int) : the source channel
        Output:
            state (bool) : True or False
        '''
        return self.get('ch%d_status'%channel)

    def do_set_marker_output(self,state,channel):
        channel +=self._choff
        logging.debug(__name__ + ' : Set marker %i output state %s'%(channel,state))
        self.write(':INST%s;:MARK:SEL%i;:MARK:STAT %i' % (channel,((int(channel)-1)%2+1),state))
        self.check()

    def do_get_marker_output(self,channel):
        channel +=self._choff
        logging.debug(__name__ + ' : Get marker %i output state '%(channel))
        outp = self.ask(':INST%s;:MARK:SEL%i;:MARK:STAT?' % (channel,((int(channel)-1)%2+1)))
        if ((outp=='0')|(outp == 'OFF')):
            return False
        elif ((outp=='1')|(outp == 'ON')):
            return True
        else:
            logging.debug(__name__ + ' : Read invalid status from instrument %s' % outp)
            raise ValueError('an error occurred while reading status from instrument')

    def do_set_runmode(self,mode,channel=1):
        '''
        Set the output mode of the AWG:
        FIX - Standard waveform shapes
        USER - Arbitrary waveforms
        SEQ - Sequenced mode
        ASEQ - Advanced seq. mode
        MOD - Modulated waveforms
        PULS
        PATT
        '''
        channel +=self._choff
        mode = mode.upper()
        if not mode in ("FIX","USER","SEQ","ASEQ","MOD","PULS","PATT"):
            raise ValueError("The selected mode is not supported, your choice was %s, but I have FIX,USER,SEQ,ASEQ,MOD,PULS,PATT"%mode)
        return self.write(":INST%s;:FUNC:MODE %s"%((2*channel-1 if self._numchannels == 4 else channel),mode))

    def do_get_runmode(self,channel=1):
        '''
        returns the output mode of the AWG.
        '''
        channel +=self._choff
        return self.ask(":INST%s;:FUNC:MODE?"%(2*channel-1 if self._numchannels == 4 else channel))


    def do_set_sequence_mode(self,mode,channel=1):
        '''
        Sequence Mode:
        AUTO - repeatedly run through the whole sequence (ignoring trigger)
        ONCE - play whole sequence once at trigger
        STEP - play one step per trigger event
        '''
        channel +=self._choff
        mode = mode.upper()
        if not mode in ("AUTO","ONCE","STEP"):
            raise ValueError("The selected sequence mode is not supported, your choice was %s, but I have AUTO,ONCE,STEP"%mode)
        return self.write(":INST%s;:SEQ:ADV %s"%((2*channel-1 if self._numchannels == 4 else channel),mode))

    def do_get_sequence_mode(self,channel=1):
        channel +=self._choff

        return self.ask(":INST%s;:SEQ:ADV?"%(2*channel-1 if self._numchannels == 4 else channel))



    def do_set_trigger_mode(self, runmode,channel=1):
        '''
        Set the Trigger Mode of the device to Continuous, Triggered or Gated.
        Input:
            runmode (str) : The Trigger mode which can be set to 'CONT', 'TRIG', 'GAT'.
        Output:
            None
        '''
        channel +=self._choff
        logging.debug(__name__ + ' : Set runmode to %s' % runmode)
        runmode = runmode.upper()
        if (runmode == 'TRIG'):
            self.write(':INST%s;:INIT:CONT 0;GATE 0'%(2*channel-1 if self._numchannels == 4 else channel))
        else:
            if (runmode == 'CONT'):
                self.write(':INST%s;:INIT:CONT 1'%(2*channel-1 if self._numchannels == 4 else channel))
            else:
                if (runmode == 'GATE'):
                    self.write(':INST%s;:INIT:CONT 0; GATE 1'%(2*channel-1 if self._numchannels == 4 else channel))
                else:
                    logging.error(__name__ + ' : Unable to set trigger mode to %s, expected "CONT", "TRIG" or "GATE"' % runmode)

    def do_get_trigger_mode(self,channel=1):
        '''
        Get the Trigger Mode of the device
        Output:
            runmode (str) : The Trigger mode which can be set to 'CONT', 'TRIG' or 'GAT'.
        '''
        channel +=self._choff
        cont = self.ask(':INST%s;:INIT:CONT ?'%(2*channel-1 if self._numchannels == 4 else channel))

        if (cont == 'OFF'):
            gate = self.ask(':INST%s;:INIT:GATE ?'%(2*channel-1 if self._numchannels == 4 else channel))
            if (gate == 'OFF'):
                return 'TRIG'
            else:
                return 'GATE'
        else:
            return 'CONT'

    def do_get_trigger_delay(self,channel=1):
        '''
        gets the trigger delay for the specified pair of channels. Internally, the delay is counted in samples, but this function returns seconds.
        '''
        channel +=self._choff
        return float(self.ask(":INST%s;:TRIG:DEL?"%(2*channel-1 if self._numchannels == 4 else channel)))/float(self.get_clock())

    def do_set_trigger_delay(self,delay,channel=1):
        '''
        gets the trigger delay for the specified pair of channels. Internally, the delay is counted in samples, but this function returns seconds.
        '''
        channel +=self._choff
        clock = self.get_clock()
        self.write(":INST%s;:TRIG:DEL%i"%((2*channel-1 if self._numchannels == 4 else channel),round(delay*clock)))

    def do_set_trigger_source(self, source, channel=1):
        '''
        sets the source of the trigger signal external or internal (timer)
        Input:
            EXT: external trigger input
            TIM: internal trigger
        Output:
            None
        '''
        channel +=self._choff
        source = source.upper()
        if source == "INT":
            source = "TIM"
            logging.warning("I assume you mean TIM. I fixed this for you :)")
        if not source in ("EXT","TIM"):
            raise ValueError("The selected source is not supported, your choice was %s, but I have EXT or TIM"%source)

        return self.write(":INST%s;:TRIG:SOUR:ADV %s"%((2*channel-1 if self._numchannels == 4 else channel),source))

    def do_get_trigger_source(self, channel=1):
        '''
        returns the source of the trigger signal external or internal (timer)
        Input:
            None
        Output:
            EXT: external trigger input
            TIM: internal trigger
        '''
        channel +=self._choff
        logging.debug(__name__ + ' : Get source of channel %s' % (2*channel-1 if self._numchannels == 4 else channel))
        return self.ask(":INST%s;:TRIG:SOUR:ADV?" %(2*channel-1 if self._numchannels == 4 else channel))

    def do_set_trigger_time(self, time, channel=1):
        '''
        sets the repitition time of the trigger signal
        Input:
            time
        Output:
            None
        '''
        channel +=self._choff

        return self.write(":INST%s;:TRIG:TIM:TIME %e"%((2*channel-1 if self._numchannels == 4 else channel),time))

    def do_get_trigger_time(self, channel = 1):
        '''
        gets the repitition time of the trigger signal
        Input:
            None
        Output:
            time
        '''
        channel +=self._choff
        logging.debug(__name__ + ' : Get time of channel %s' % (2*channel-1 if self._numchannels == 4 else channel))
        return self.ask(":INST%s;:TRIG:TIM:TIME?" % (2*channel-1 if self._numchannels == 4 else channel))

    def do_set_sync_output(self, state, channel = 1):
        '''
        sends a sync pulse to sync out, can be used for synchronisation with chpair 2
        Input:
            True or False
        Output:
            None
        '''
        channel+=self._choff
        self.write(":OUTP:SYNC:SOUR%s"%(2*channel-1 if self._numchannels == 4 else channel))
        self.write(":OUTP:SYNC%i"%state)


    def do_get_sync_output(self, channel=1):
        '''
        checks if there is a synchronisation pulse
        Input:
            None
        Output:
            On or Off
        '''
        channel +=self._choff
        if self._numchannels == 4:
            channel = 2*channel-1
        if int(self.ask(":OUTP:SYNC:SOUR ?"))==channel:
            if self.ask(":OUTP:SYNC ?")=="ON":
                return True
        return False
    
    def do_set_sync_position(self,position):
        '''
        Set the position of the SYNC output pulse.
        Input:
            position: start of the pulse after the start of the waveform in seconds. This is internally converted into samples and rounded to 32.
        '''
        samplepos = int(round(position * self.get_clock() /32))*32
        self.write(":OUTP:SYNC:POS%i"%samplepos)

    def do_get_sync_position(self):
        return float(self.ask(":OUTP:SYNC:POS?"))/self.get_clock()

    def set_trig_impedance(self, impedance):
        '''
        Sets the trigger impedance to 50 Ohm or 10 kOhm
        Input:
            '50' or '10k'
        Output:
            None
        '''
        logging.debug(__name__  + ' : Set trigger impedance')
        if ((impedance == '50') | (impedance == '10k')):
            self.write('TRIG:INP:IMP %s' % impedance)
        else:
            logging.error(__name__ + ' : Unable to set impedance to %s Ohm, expected "50" or "10k"' % impedance)


    def do_get_trigger_impedance(self):
        '''
        Reads the trigger impedance from the instrument
        Input:
            None
        Output:
            impedance: 10K or 50 (Ohm)
        '''
        #logging.error(__name__ + ' : getting trigger impedance does currently not work... (AS 01/2016)')
        #return 0
        logging.debug(__name__  + ' : Get trigger impedance from instrument')
        imp = self.ask('TRIG:INP:IMP ?')
        if imp == "10K": imp = 1e4
        return  imp

    def do_set_trigger_impedance(self, mod):
        '''
        Sets the trigger impedance of the instrument
        Input:
            mod (int) : Either 1e3 or 50 depending on the mode
        Output:
            None
        '''
        if (mod==10e3):
            self.set_trig_impedance('10k')
        elif (mod==50):
            self.set_trig_impedance('50')
        else:
            logging.error(__name__ + ' : Unable to set trigger impedance to %s, expected "10e3" or "50"' % mod)

    def do_get_trigger_level(self):
        '''
        Reads the trigger level from the instrument
        Input:
            None
        Output:
            None
        '''
        logging.debug(__name__  + ' : Get trigger level from instrument')
        return float(self.ask('TRIG:LEV ?'))

    def do_set_trigger_level(self, level):
        '''
        Sets the trigger level of the instrument
        Input:
            level (float) : trigger level in volts
        '''
        logging.debug(__name__  + ' : Trigger level set to %.2f' % level)
        self.write('TRIG:LEV %.2f' % level)

    def do_set_trigger_slope(self, slope, channel=1):
        '''
        Trigger starts with positive or negative slope of trigger signal
        Input:
            slope: 'POS', 'NEG' or 'EIT'
            channel
        Output:
            None
        '''
        slope=slope.upper()
        if slope in ["POS", "NEG", "EIT"]:
            channel+=self._choff
            self.write(":INST%i;:TRIG:SLOP%s"%((2*channel-1 if self._numchannels == 4 else channel),slope))

    def do_get_trigger_slope(self, channel=1):
        '''
        with which slope does the trigger start?
        Input:
            channel
        Output:
            slope
        '''
        return self.ask(":INST%i;:TRIG:SLOP?"%(2*channel-1 if self._numchannels == 4 else channel))

    def do_get_clock(self):
        '''
        Returns the clockfrequency, which is the rate at which the datapoints are
        sent to the designated output
        Input:
            None
        Output:
            clock (int) : frequency in Hz
        '''
        self._clock = self.ask(":FREQ:RAST?")
        return self._clock

    def do_set_clock(self, clock):
        '''
        Sets the rate at which the datapoints are sent to the designated output channel
        Input:
            clock (int) : frequency in Hz (75e6 to 1.25e9)
        Output:
            None
        '''
        self._clock = clock
        self.write(':FREQ:RAST%f' % clock)

    def do_get_amplitude(self, channel):
        '''
        Reads the amplitude of the designated channel from the instrument
        Input:
            channel (int) : 1, 2, 3 or 4: the number of the designated channel
        Output:
            amplitude (float) : the amplitude of the signal in Volts
        '''
        channel +=self._choff
        logging.debug(__name__ + ' : Get amplitude of channel %s from instrument'
            % channel)
        return float(self.ask(':INST%s;:VOLT ?' % channel))

    def do_set_amplitude(self, amp, channel):
        '''
        Sets the amplitude of the designated channel of the instrument
        Input:
            amp (float)   : amplitude in Volts (0.050 V to 2.000 V)
            channel (int) : 1, 2, 3 or 4: the number of the designated channel
        Output:
            None
        '''
        channel +=self._choff
        logging.debug(__name__ + ' : Set amplitude of channel %s to %.6f'
            % (channel, amp))
        if amp < 50e-3:
            amp = 50e-3
            print 'amplitude was set to 0.05 V, which is smallest possible voltage'
        if amp > 2:
            amp = 2.
            print 'amplitude was set to 2 V, which is highest possible voltage'

        self.write(':INST%s;:VOLT%.3f' % (channel, amp))

    def do_get_offset(self, channel):
        '''
        Reads the offset of the designated channel of the instrument
        Input:
            channel (int) : 1, 2, 3 or 4: the number of the designated channel
        Output:
            offset (float) : offset of designated channel in Volts
        '''
        channel +=self._choff
        logging.debug(__name__ + ' : Get offset of channel %s' % channel)
        return float(self.ask(':INST%s;:VOLT:OFFS ?' % channel))

    def do_set_offset(self, offset, channel):
        '''
        Sets the offset of the designated channel of the instrument
        Input:
            offset (float) : offset in Volts (-1.000 V to 1.000 V)
            channel (int)  : 1, 2, 3 or 4: the number of the designated channel
        Output:
            None
        '''

        channel +=self._choff
        if offset < -1.000:
            offset = -1.000
            print 'Offset was set to -1.000 V, which is smallest possible voltage'
        if offset > 1.000:
            offset = 1.000
            print 'Offset was set to 1.000 V, which is highest possible voltage'

        logging.debug(__name__ + ' : Set offset of channel %s to %.3f' % (channel, offset))
        self.write(':INST%s;:VOLT:OFFS%.3f' % (channel, offset))

    def do_get_marker_high(self, channel):
        '''
        Gets the high level for marker1 on the designated channel.
        Note that Channels 1&2 and 3&4 share the same two markers.
        Input:
            channel (int) : 1, 2, 3 or 4: the number of the designated channel
        Output:
            high (float) : high level in Volts
        '''
        channel +=self._choff
        logging.debug(__name__ + ' : Get upper bound of marker %i of channel %s' %(((int(channel)-1)%2+1),channel))
        return float(self.ask(':INST%s;:MARK:SEL%i;:MARK:VOLT:HIGH ?' % (channel,((int(channel)-1)%2+1))))

    def do_set_marker_high(self, high, channel):
        '''
        Sets the high level for marker1 on the designated channel.
        Note that Channels 1&2 and 3&4 share the same two markers.

        Input:
            high (float)   : high level in Volts
            channel (int)  : 1, 2, 3 or 4: the number of the designated channel
        Output:
            None
         '''
        channel +=self._choff
        logging.debug(__name__ + ' : Set upper bound of marker%i of channel %s to %.3f'% (((int(channel)-1)%2+1),channel, high))
        self.write(':INST%s;:MARK:SEL%i;:MARK:VOLT:HIGH%.2f' % (channel,((int(channel)-1)%2+1),high))
        self.check()

    def do_get_status(self, channel):
        '''
        Gets the status of the designated channel.
        Input:
            channel (int) : 1, 2, 3 or 4: the number of the designated channel
        Output:
            status (bool)
        '''
        channel +=self._choff
        logging.debug(__name__ + ' : Get status of channel %s' % channel)
        outp = self.ask(':INST%s;:OUTP ?' % channel)
        if ((outp=='0')|(outp == 'OFF')):
            return False
        elif ((outp=='1')|(outp == 'ON')):
            return True
        else:
            logging.debug(__name__ + ' : Read invalid status from instrument %s' % outp)
            return 'an error occurred while reading status from instrument'
        self.get("ch%i_output"%channel-self._choff)

    def do_set_status(self, status, channel):
        '''
        Sets the status of designated channel.
        Input:
            status (bool) : True or False
            channel (int)   : 1, 2, 3 or 4: the number of the designated channel
        Output:
            None
        '''
        channel +=self._choff
        logging.debug(__name__ + ' : Set status of channel %s to %s' % (channel, status))
        if status:
            self.write(':INST%s;:OUTP ON' % channel)
        else:
            self.write(':INST%s;:OUTP OFF' % channel)
        self.get("ch%i_output"%(channel-self._choff))

    def do_set_reference_source(self,source='EXT'):
        '''
        Sets the clock reference source.
        Input:
            source (string) : 'INT' or 'EXT'
        Output:
            None
        '''
        if source == 'EXT' or source == 'INT':
            logging.debug(__name__ + ' : Set clock reference source to %s' %source)
            self.write(':ROSC:SOUR %s' %source)
        else:
            logging.warning('Clock source needs to be one of INT or EXT. No changes made.')

    def do_get_reference_source(self):
        '''
        Gets the clock reference source.
        Input:
            None
        Output:
            (string) : 'INT' or 'EXT'
        '''
        logging.debug(__name__ + ' : Get clock reference source.')
        return str(self.ask(':ROSC:SOUR ?'))

    def do_set_reference_source_freq(self,freq=10e6):
        '''
        Sets the clock reference frequency.
        Input:
            freq (float) : 10e6, 20e6, 50e6, 100e6
        Output:
            None
        '''
        if freq in [10e6,20e6,50e6,100e6]:
            logging.debug(__name__ + ' : Set clock reference frequency to %.2g' %freq)
            self.write(':ROSC:FREQ %s' %str(freq))
        else:
            logging.warning('Clock source needs to be one of [10e6,20e6,50e6,100e6]. No changes made.')

    def do_get_reference_source_freq(self):
        '''
        Gets the clock reference frequency.
        Input:
            None
        Output:
            (string) : 10e6, 20e6, 50e6, 100e6
        '''
        logging.debug(__name__ + ' : Get clock reference frequency.')
        return float(self.ask(':ROSC:FREQ ?'))

    def do_set_common_clock(self,status=True):
        '''
        Use a common trigger clock for both channel pairs.
        Input:
            status (bool)
        Output:
            None
        '''
        if status:
            logging.debug(__name__ + ' : Set common clock.')
            self.write(':INST:COUPLE:STAT ON')
        else:
            logging.debug(__name__ + ' : Set clocks to be separate.')
            self.write(':INST:COUPLE:STAT OFF')

    def do_get_common_clock(self):
        '''
        Check whether a common clock for both channel pairs is used.
        Input:
            None
        Output:
            (bool)
        '''
        logging.debug(__name__ + ' : Check common clock.')
        return bool(self.ask(':INST:COUPLE:STAT ?')=='ON')

    def send_waveform(self, w, m1, m2, channel, seg):
        return self.wfm_send(w, m1, m2, channel, seg)

    def wfm_send(self, w, m1, m2, channel, seg):
        '''
        Sends a complete waveform. All parameters need to be specified.
        Takes a waveform as generated by generate_waveform from qkit and first converts it to data usable by the AWG
        then sends it to the memory of the specified channel into the specified segment.
        Minimum waveform size is 192 points. If a waveform is shorter, it will be appended automatically.

        See also: resend_waveform()
        Input:
            w (float[numpoints]) : waveform (amplitude range 0 <-max amp.> to 1 <max amp.>)
            m1 (int[numpoints])  : marker1 (either 1 or 0, i.e. marker on or off)
            m2 (int[numpoints])  : marker2 (either 1 or 0, i.e. marker on or off)
            use m1=None or m2=None to fill with zeros
            channel (int)        : channel 1, 2, 3, or 4 that waveform is sent to
            seg (int)            : # of data segment the waveform is sent to (1 to 16000)
        Output:
            None
        '''

        if channel > self._numchannels:
            raise ValueError("There are only channels 1 and 2.")

        channel +=self._choff

        dim = len(w)

        if len(w)%16 != 0:
            raise ValueError #wfm length has to be divisible by 16
        if len(w) < 192:
            w = numpy.append(w1, numpy.zeros(192 - len(w)))
            m1 = numpy.append(m1, numpy.zeros(192 - len(m1)))
            m2 = numpy.append(m2, numpy.zeros(192 - len(m2)))

        if(m1 == None): m1 = numpy.zeros_like(w)
        if(m2 == None): m2 = numpy.zeros_like(w)
        if (not((len(w)==len(m1)) and ((len(m1)==len(m2))))):
            raise ValueError("error, the length of your waveform and markes does not match")

        self.write(':TRAC:DEF%i,%i' % (seg,len(w)))

        #Set specified channel and number of memory segment
        self.write(':INST%s;:TRAC:SEL%i' % (channel, seg))

        #set set single trace transfer mode
        self.write(':TRAC:MODE SING')

        ws = ''
        for i in range(0,len(w)):
            ws = ws + struct.pack('<H', 8191*w[i]+8192+m1[i]*2**14+m2[i]*2**15)

        self.write_raw(':TRAC#%i%i%s' %(int(numpy.log10(len(ws))+1), len(ws), ws))

    def wfm_send2(self, w1, w2, m1=None, m2=None, channel=1, seg=1):
        '''
        Sends two complete waveforms for channel pairs 1&2 or 3&4. All parameters need to be specified.
        Takes a waveform as generated by generate_waveform from qkit and first converts it to data usable by the AWG
        then sends it to the memory of the specified channel into the specified segment.
        Minimum waveform size is 192 points. If the two waveforms are shorter, they will be appended automatically.

        See also: resend_waveform()
        Input:
            w (float[numpoints]) : waveform (amplitude range 0 <-max amp.> to 1 <max amp.>)
            m1 (int[numpoints])  : marker1 (either 1 or 0, i.e. marker on or off)
            m2 (int[numpoints])  : marker2 (either 1 or 0, i.e. marker on or off)
            channel (int)        : channels are paired (1&2, 3&4) selecting either of one pair is fine
            seg (int)            : # of data segment the waveform is sent to (1 to 16000)
        Output:
            None
        '''
        channel +=self._choff
        if len(w1) != len(w2): raise ValueError("Waveform length is not equal.")
        if len(w1)%16 != 0: raise ValueError("Wfm length has to be divisible by 16")
        if len(w1) < 192:
            w1 = numpy.append(w1, numpy.zeros(192 - len(w1)))
            w2 = numpy.append(w2, numpy.zeros(192 - len(w2)))
            m1 = numpy.append(m1, numpy.zeros(192 - len(m1)))
            m2 = numpy.append(m2, numpy.zeros(192 - len(m2)))

        if m1 is None : m1 = numpy.zeros_like(w1)
        if m2 is None : m2 = numpy.zeros_like(w1)
        if (not((len(w1)==len(m1)) and ((len(m1)==len(m2))))):
            raise ValueError("error, the length of your waveform and markes does not match")

        self.write(':TRAC:DEF%i,%i' % (seg,len(w1)))

        #Set specified channel and number of memory segment
        self.write(':INST%s;:TRAC:SEL%i' % (channel, seg))

        #set set combined trace transfer mode
        self.write(':TRAC:MODE COMB')

        wfm = numpy.append(numpy.reshape(numpy.array(8191*w2+8192+m1*2**14+m2*2**15,dtype=numpy.dtype('<H')),(-1,16)),numpy.reshape(numpy.array(8191*w1+8192+m1*2**14+m2*2**15,dtype=numpy.dtype('<H')),(-1,16)),axis=1).flatten()
        ws =str(buffer(wfm))

        self.write_raw(':TRAC#%i%i%s' %(int(numpy.log10(len(ws))+1), len(ws), ws))


    def define_sequence(self,channel, segments=None,loops=None,jump_flags=None):
        '''
        specifies the sequence table for sequenced mode.
        channel: segments table can be created for each pair of channels separately
        segments (array of ints or int): which segments in the awg do you want to output? (1-32000) If a simple int is specified, range(1,i+1) will be used
        loops (array of ints): How often should each segment be repeated? (1-16M)
        jump_flags (array of 0,1): if set to 1, the sequencer will wait at this sequence element until an event happens.
        '''
        channel +=self._choff
        if segments is None:
            print "Amount of segments not specified, try to get it from AWG"
            for i in range(1,32000):
                if int(self.ask(":TRAC:DEF%i?"%i).split()[-1])==0:
                    segments = i-1
                    break
            if segments is None:
                raise ValueError("Could not find number of segments...")
        if type(segments)==int:
            #the segement table needs at least 3 entries. So if it would be shorter, we just take it multiple times.
            if segments == 1 : segments = [1,1,1]
            elif segments == 2 : segments = [1,2,1,2]
            else: segments = range(1,segments+1)
        if loops == None: loops = numpy.ones(len(segments))
        if jump_flags == None: jump_flags = numpy.zeros(len(segments))
        if not len(loops)==len(segments) or not len(jump_flags) == len(segments):
            raise ValueError("Length of segments (%i) does not match length of loops (%i) or length of jump_flags(%i)"%(len(segments),len(loops),len(jump_flags)))
        if len(segments)<3: raise ValueError("Sorry, you need at least 3 segments. Your command has %i segments"%(len(segments)))

        #Set specified channel
        self.write(':INST%s' % (channel))
        ws = ''
        for i in range(len(segments)):
            ws = ws + struct.pack('<LHH', loops[i],segments[i],jump_flags[i])
        self.write_raw(':SEQ#%i%i%s' %(int(numpy.log10(len(ws))+1), len(ws), ws))

    def set_seq_length(self,length,chpair=1):
        self.define_sequence((2*chpair-1 if self._numchannels == 4 else chpair),length)

    def close(self):
        self._visainstrument.close()
