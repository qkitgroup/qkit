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

from instrument import Instrument
import visa
import types
import logging
import numpy
import struct
import time
#import hashlib

class Tabor_WX1284C(Instrument):
    '''
    This is the python driver for the Tabor Electronics Arbitrary Waveform Generator WX1284C
    
    Usage:
    Initialize with
    <name> = instruments.create('name', 'Tabor_WX1284C', address='<GPIB address>',
        reset=<bool>, numpoints=<int>)
    think about:    clock, waveform length
    TODO:
    I) adjust commands 
    1) Get All
    2) Remove test_send??
    3) Add docstrings
    4) Add 4-channel compatibility
    '''

    def __init__(self, name, address, chpair=None, reset=False, clock=6e9, numpoints=1000, numchannels = 4):    #<--
        '''
        Initializes the AWG WX1284C
        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address
            reset (bool)     : resets to default values, default=false
            numpoints (int)  : sets the number of datapoints
            chpair (int)     : number of channel pair (1 for channels 1&2, 2 for channels 3&4)
        Output:
            None
        '''
        logging.debug(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])

        self._address = address
        self._visainstrument = visa.instrument(self._address,term_chars = "\r\n")
        self._visainstrument.timeout=2
        self._values = {}
        self._values['files'] = {}
        self._clock = clock
        self._numpoints = numpoints
        
        if chpair not in [None, 1, 2]:
            raise ValueError("chpair should be 1, 2 or None.")
                
        if chpair and numchannels!=2:
            raise ValueError("numchannels should be 2.")
            
        if chpair is None and numchannels !=4:
            raise ValueError("numchannels should be 4.")
            
        self._numchannels = numchannels
        self._choff = 0                                                            #<--
        
        if chpair == 2:
            self._choff = 2
            
        # Add parameters
        #self.add_parameter('waveform', type=types.StringType,
        #   flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
        #   channels=(1, self._numchannels), channel_prefix='ch%d_')
        if numchannels == 4:                                                #<--
            self.add_parameter('runmode', type=types.StringType,
                flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
                channels=(1, 2), channel_prefix='p%d_')
        else:
            self.add_parameter('runmode', type=types.StringType,
                flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET)
        self.add_parameter('output', type=types.BooleanType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, self._numchannels), channel_prefix='ch%d_')
        self.add_parameter('marker_output', type=types.BooleanType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, self._numchannels), channel_prefix='ch%d_')
        self.add_parameter('trigger_impedance', type=types.FloatType,       #changed, checked in manual
            flags=Instrument.FLAG_GETSET,# | Instrument.FLAG_GET_AFTER_SET,
            minval=50, maxval=10e3, units='Ohm')
        self.add_parameter('trigger_level', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=-5, maxval=5, units='Volts')
        self.add_parameter('clock', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=1e6, maxval=1.25e9, units='Hz')
        self.add_parameter('reference_source', type=types.StringType,
            flags=Instrument.FLAG_GETSET)
        self.add_parameter('reference_source_freq', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=10e6, maxval=100e6, units='Hz')
        self.add_parameter('common_clock', type=types.BooleanType,
                flags=Instrument.FLAG_GETSET| Instrument.FLAG_GET_AFTER_SET)
        self.add_parameter('numpoints', type=types.IntType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            minval=100, maxval=1e9, units='Int')
        #self.add_parameter('filename', type=types.StringType,
        #   flags=Instrument.FLAG_SET, channels=(1, self._numchannels),
        #   channel_prefix='ch%d_')
        #self.add_parameter('direct_output', type=types.BooleanType,
        #   flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
        #   channels=(1, self._numchannels), channel_prefix='ch%d_')
        self.add_parameter('amplitude', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, self._numchannels), minval=0, maxval=2, units='Volts', channel_prefix='ch%d_')
        self.add_parameter('offset', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, self._numchannels), minval=-2, maxval=2, units='Volts', channel_prefix='ch%d_')
        self.add_parameter('marker_high', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, self._numchannels), minval=-2, maxval=2, units='Volts', channel_prefix='ch%d_')
        self.add_parameter('status', type=types.BooleanType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=(1, self._numchannels),channel_prefix='ch%d_')
        
    
        if numchannels == 4:
            self.add_parameter('trigger_mode', type=types.StringType,
                flags=Instrument.FLAG_GETSET,
                channels=(1, 2), channel_prefix='p%d_')
            self.add_parameter('trigger_delay', type=types.FloatType,
                flags=Instrument.FLAG_GETSET,
                channels=(1, 2), channel_prefix='p%d_')
            self.add_parameter('sequence_mode', type=types.StringType,
                flags=Instrument.FLAG_GETSET,
                channels=(1, 2), channel_prefix='p%d_')
            self.add_parameter('trigger_source', type=types.StringType,
                flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
                channels=(1, 2), channel_prefix='p%d_')
            self.add_parameter('trigger_time', type=types.FloatType,
                flags=Instrument.FLAG_GETSET,
                channels=(1, 2), channel_prefix='p%d_')     
            self.add_parameter('sync_output', type=types.BooleanType,
                flags=Instrument.FLAG_GETSET| Instrument.FLAG_GET_AFTER_SET,
                channels=(1, 2), channel_prefix='p%d_')
            self.add_parameter('trigger_slope', type=types.StringType,
                flags=Instrument.FLAG_GETSET| Instrument.FLAG_GET_AFTER_SET,
                channels=(1, 2), channel_prefix='p%d_')
            
        else:
            self.add_parameter('trigger_mode', type=types.StringType,
                flags=Instrument.FLAG_GETSET)
            self.add_parameter('trigger_delay', type=types.FloatType,
                flags=Instrument.FLAG_GETSET)
            self.add_parameter('sequence_mode', type=types.StringType,
                flags=Instrument.FLAG_GETSET)
            self.add_parameter('trigger_source', type=types.StringType,
                flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET)
            self.add_parameter('trigger_time', type=types.FloatType,
                flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET)
            self.add_parameter('sync_output', type=types.BooleanType,
                flags=Instrument.FLAG_GETSET| Instrument.FLAG_GET_AFTER_SET)
            self.add_parameter('trigger_slope', type=types.StringType,
                flags=Instrument.FLAG_GETSET| Instrument.FLAG_GET_AFTER_SET)
        #self.add_parameter('seq_length', type=types.IntType, flags = Instrument.FLAG_GETSET)
        #self.add_parameter('seq_position', type=types.IntType, flags = Instrument.FLAG_GET)

        # Add functions
        self.add_function('reset')
        self.add_function('fix')
        self.add_function('wait')
        self.add_function('get_all')
        self.add_function('set_seq_length')
        self.add_function('clear_waveforms')
        #self.add_function('set_trigger_mode')
        
        self.add_function('ask') #for debug
        self.add_function('write') #for debug
        self.add_function('define_sequence')
        self.add_function('close')
        
        
        if numchannels==2:
            self.add_function('preset_readout')
            self.add_function('preset_manipulation')
        
        #self.add_function('set_sequence_mode')
        #self.add_function('set_trigger_impedance_1e3')
        #self.add_function('set_trigger_impedance_50')
        
        # sequence manipulation functions (do not display all waveforms in the user interface)
        self.add_function('wfm_send')
        self.add_function('wfm_send2')
        #self.add_function('wfm_import')
        #self.add_function('get_seq_loop')
        #self.add_function('set_seq_loop')
        #self.add_function('get_seq_goto')
        #self.add_function('set_seq_goto')

        # Make Load/Delete Waveform functions for each channel
        #for ch in range(1,4):
        #   self._add_load_waveform_func(ch)
        #   self._add_del_loaded_waveform_func(ch)

        if reset:
            self.reset()
        else:
            self.get_all()
        self._visainstrument.write(":INST1;:MARK:SOUR USER;:INST3;:MARK:SOUR USER")
        
        print("The device is set up with %i channels. You use the channels %s" %(numchannels, str(range(self._choff+1, numchannels + self._choff+1))))

    # Functions
    def fix(self,verbose=True):
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
                print e
                continue
    def check(self):
        #this function is used to check whether the command was successfull
        rv = self._visainstrument.ask(":SYST:ERR?")
        if rv[0]=="0": return True
        else: raise ValueError("Device responded with error ->%s<-"%rv)
    def reset(self):        #checked 
        '''
        Resets the instrument to default values
        Input:
            None
        Output:
            None
        '''
        logging.info(__name__ + ' : Resetting instrument')
        self._visainstrument.write('*RST')
        self._visainstrument.write(":INST1;:MARK:SOUR USER;:INST3;:MARK:SOUR USER")
    
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
        for i in range(1,self._numchannels + 1):                      #<--
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
            self.get_trigger_impedance()
        except Exception:
            logging.warning('command trigger impedance not supported')
        self.get_trigger_level()
        self.get_clock()
        if self._numchannels == 4:
            for i in (1,2):                              #<--
                self.get('p%d_runmode' % i)
                self.get('p%d_trigger_mode' % i)
                self.get('p%d_sequence_mode' % i)
                self.get('p%d_sync_output' %i)
                self.get('p%d_trigger_time' %i)
                self.get('p%d_trigger_delay' %i)
                self.get('p%d_trigger_source' %i)
                self.get('p%d_trigger_slope' %i)
        for i in range(1,self._numchannels + 1):                      #<--
            self.get('ch%d_amplitude' % i)
            self.get('ch%d_offset' % i)
            self.get('ch%d_marker_high' % i)
            self.get('ch%d_marker_output' % i)
            self.get('ch%d_status' % i)
            self.get('ch%d_output' % i)
        if self._numchannels == 2:                         #<--
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
        
        
        
    def ask(self,cmd):
        return self._visainstrument.ask(cmd)
    
    def write(self,cmd):
        return self._visainstrument.write(cmd)
    
    def clear_waveforms(self): #done
        '''
        Clears the waveform on all channels.
        Input:
            None
        Output:
            None
        '''
        logging.debug(__name__ + ' : Clear waveforms from channels')
        for idx in range(self._choff+1,self._numchannels + 1):              #<--
            self._visainstrument.write(':INST%i; :TRAC:DEL:ALL'%idx)

    def run(self): #done
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
        self._visainstrument.write(':ENAB')

    def stop(self): #done
        '''
        Terminates the output of a waveform or a sequence. This is equivalent to pressing
        Run/Delete/Stop button on the front panel.
        Input:
            None
        Output:
            None
        '''
        logging.debug(__name__ + ' : Stop/Terminate output of a waveform or sequence')
        self._visainstrument.write('ABOR')

    def wait(self, max_timeouts = 1, quiet = False):#ok
        '''
        Wait until the previous command has completed.
        
        Input:
            timeouts - maximum number of timeouts that may occur. note that the command 
                does not execute at all if zero maximum timeouts are requested.
            quiet - if True, do not show messages when a timeout occurs
        '''
        if(max_timeouts > 0):
            self._visainstrument.write('*STB?')
        for i in range(max_timeouts):
            try:
                time.sleep(0.025)
                self._visainstrument.read()
                return
            except:
                if(not quiet): print('still waiting for the awg to become ready')
                time.sleep(1)

    def do_set_output(self, state, channel): #done
        '''
        This command sets the output state of the AWG.
        Input:
            channel (int) : the source channel
            state (bool) : True or False
        Output:
            None
        '''     
        return self.set("ch%i_status"%channel,state)
        
    def do_get_output(self, channel): #done
        '''
        This command gets the output state of the AWG.
        Input:
            channel (int) : the source channel
        Output:
            state (bool) : True or False
        '''
        return self.get('ch%d_status'%channel)
        
    def do_set_marker_output(self,state,channel):
        channel +=self._choff                                                 #<--
        logging.debug(__name__ + ' : Set marker %i output state %s'%(channel,state))
        self._visainstrument.write(':INST%s;:MARK:SEL%i;:MARK:STAT %i' % (channel,((int(channel)-1)%2+1),state))
        self.check()
        
    def do_get_marker_output(self,channel):
        channel +=self._choff                                                  #<--
        logging.debug(__name__ + ' : Get marker %i output state '%(channel))
        outp = self._visainstrument.ask(':INST%s;:MARK:SEL%i;:MARK:STAT?' % (channel,((int(channel)-1)%2+1)))
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
        channel +=self._choff                                 #<--
        mode = mode.upper()
        if not mode in ("FIX","USER","SEQ","ASEQ","MOD","PULS","PATT"):
            raise ValueError("The selected mode is not supported, your choice was %s, but I have FIX,USER,SEQ,ASEQ,MOD,PULS,PATT"%mode)
        return self._visainstrument.write(":INST%s;:FUNC:MODE %s"%((2*channel-1 if self._numchannels == 4 else channel),mode))
    
    def do_get_runmode(self,channel=1):
        '''
        returns the output mode of the AWG.
        '''
        channel +=self._choff                                                        #<--
        return self._visainstrument.ask(":INST%s;:FUNC:MODE?"%(2*channel-1 if self._numchannels == 4 else channel))
        
        
    def do_set_sequence_mode(self,mode,channel=1):      #<--?????
        '''
        Sequence Mode:
        AUTO - repeatedly run through the whole sequence (ignoring trigger)
        ONCE - play whole sequence once at trigger
        STEP - play one step per trigger event
        '''
        channel +=self._choff                                     #<--
        mode = mode.upper()
        if not mode in ("AUTO","ONCE","STEP"):
            raise ValueError("The selected sequence mode is not supported, your choice was %s, but I have AUTO,ONCE,STEP"%mode)
        return self._visainstrument.write(":INST%s;:SEQ:ADV %s"%((2*channel-1 if self._numchannels == 4 else channel),mode))
        
    def do_get_sequence_mode(self,channel=1):             #<--???????
        channel +=self._choff                                                  #<--

        return self._visainstrument.ask(":INST%s;:SEQ:ADV?"%(2*channel-1 if self._numchannels == 4 else channel))



    def do_set_trigger_mode(self, runmode,channel=1): #done
        '''
        Set the Trigger Mode of the device to Continuous, Triggered or Gated.
        Input:
            runmode (str) : The Trigger mode which can be set to 'CONT', 'TRIG', 'GAT'.
        Output:
            None
        '''
        channel +=self._choff                                                 #<--
        logging.debug(__name__ + ' : Set runmode to %s' % runmode)
        runmode = runmode.upper()
        if (runmode == 'TRIG'):
            self._visainstrument.write(':INST%s;:INIT:CONT 0;GATE 0'%(2*channel-1 if self._numchannels == 4 else channel))   #<--?????
        else:
            if (runmode == 'CONT'):
                self._visainstrument.write(':INST%s;:INIT:CONT 1'%(2*channel-1 if self._numchannels == 4 else channel))
            else:
                if (runmode == 'GATE'):
                    self._visainstrument.write(':INST%s;:INIT:CONT 0; GATE 1'%(2*channel-1 if self._numchannels == 4 else channel))
                else:
                    logging.error(__name__ + ' : Unable to set trigger mode to %s, expected "CONT", "TRIG" or "GATE"' % runmode)

    def do_get_trigger_mode(self,channel=1): #done
        '''
        Get the Trigger Mode of the device
        Output:
            runmode (str) : The Trigger mode which can be set to 'CONT', 'TRIG' or 'GAT'.
        '''
        channel +=self._choff                                                          #<--
        cont = self._visainstrument.ask(':INST%s;:INIT:CONT ?'%(2*channel-1 if self._numchannels == 4 else channel))          #<--?????
        
        if (cont == 'OFF'):
            gate = self._visainstrument.ask(':INST%s;:INIT:GATE ?'%(2*channel-1 if self._numchannels == 4 else channel))
            if (gate == 'OFF'):
                return 'TRIG'
            else:
                return 'GATE'
        else:
            return 'CONT'

    def do_get_trigger_delay(self,channel=1):           #<--?????
        '''
        gets the trigger delay for the specified pair of channels. Internally, the delay is counted in samples, but this function returns seconds.
        '''
        channel +=self._choff                                                                     #<--
        return float(self._visainstrument.ask(":INST%s;:TRIG:DEL?"%(2*channel-1 if self._numchannels == 4 else channel)))/float(self.get_clock())
        
    def do_set_trigger_delay(self,delay,channel=1):     #<--?????
        '''
        gets the trigger delay for the specified pair of channels. Internally, the delay is counted in samples, but this function returns seconds.
        '''
        channel +=self._choff                                #<--
        clock = self.get_clock()
        self._visainstrument.write(":INST%s;:TRIG:DEL%i"%((2*channel-1 if self._numchannels == 4 else channel),round(delay*clock)))
        
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

        return self._visainstrument.write(":INST%s;:TRIG:SOUR:ADV %s"%((2*channel-1 if self._numchannels == 4 else channel),source))
    
    def do_get_trigger_source(self, channel=1):
        '''
        returns the source of the trigger signal external or internal (timer)
        Input:
            None
        Output:
            EXT: external trigger input
            TIM: internal trigger
        '''                                    
        channel +=self._choff                                              #<--
        logging.debug(__name__ + ' : Get source of channel %s' % (2*channel-1 if self._numchannels == 4 else channel))
        return self._visainstrument.ask(":INST%s;:TRIG:SOUR:ADV?" %(2*channel-1 if self._numchannels == 4 else channel))
        
    def do_set_trigger_time(self, time, channel=1):
        '''
        sets the repitition time of the trigger signal
        Input:
            time
        Output:
            None    
        '''
        channel +=self._choff    
        
        return self._visainstrument.write(":INST%s;:TRIG:TIM:TIME %e"%((2*channel-1 if self._numchannels == 4 else channel),time))
        
    def do_get_trigger_time(self, channel = 1):
        '''
        gets the repitition time of the trigger signal
        Input:
            None
        Output:
            time    
        '''
        channel +=self._choff                                              #<--
        logging.debug(__name__ + ' : Get time of channel %s' % (2*channel-1 if self._numchannels == 4 else channel))
        return self._visainstrument.ask(":INST%s;:TRIG:TIM:TIME?" % (2*channel-1 if self._numchannels == 4 else channel))
    
    def do_set_sync_output(self, state, channel = 1):
        '''
        sends a sync pulse to sync out, can be used for synchronisation with chpair 2
        Input:
            True or False
        Output:
            None
        '''
        channel+=self._choff
        self._visainstrument.write(":OUTP:SYNC:SOUR%s"%(2*channel-1 if self._numchannels == 4 else channel))
        self._visainstrument.write(":OUTP:SYNC%i"%state)
        
    
    def do_get_sync_output(self, channel=1):
        '''
        checks if there is a synchronisation pulse
        Input:
            None
        Output:
            On or Off
        '''
        channel +=self._choff
        if self._visainstrument.ask(":OUTP:SYNC:SOUR ?")==str(channel):
            if self._visainstrument.ask(":OUTP:SYNC ?")=="ON":
                return True
        return False

    
    def set_trig_impedance(self, impedance): #done
        '''
        Sets the trigger impedance to 50 Ohm or 10 kOhm
        Input:
            '50' or '10k'
        Output:
            None
        '''
        logging.debug(__name__  + ' : Set trigger impedance')
        if ((impedance == '50') | (impedance == '10k')):
            self._visainstrument.write('TRIG:INP:IMP %s' % impedance)
        else:
            logging.error(__name__ + ' : Unable to set impedance to %s Ohm, expected "50" or "10k"' % impedance)

    # Parameters

    def do_get_trigger_impedance(self): #done
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
        imp = self._visainstrument.ask('TRIG:INP:IMP ?')
        if imp == "10K": imp = 1e4
        return  imp

    def do_set_trigger_impedance(self, mod): #done
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

    def do_get_trigger_level(self): #done
        '''
        Reads the trigger level from the instrument
        Input:
            None
        Output:
            None
        '''
        logging.debug(__name__  + ' : Get trigger level from instrument')
        return float(self._visainstrument.ask('TRIG:LEV ?'))

    def do_set_trigger_level(self, level): #done
        '''
        Sets the trigger level of the instrument
        Input:
            level (float) : trigger level in volts
        '''
        logging.debug(__name__  + ' : Trigger level set to %.2f' % level)
        self._visainstrument.write('TRIG:LEV %.2f' % level)

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
            self._visainstrument.write(":INST%i;:TRIG:SLOP%s"%((2*channel-1 if self._numchannels == 4 else channel),slope))
            
    def do_get_trigger_slope(self, channel=1):
        '''
        with which slope does the trigger start?
        Input:
            channel
        Output:
            slope
        '''
        return self._visainstrument.ask(":INST%i;:TRIG:SLOP?"%(2*channel-1 if self._numchannels == 4 else channel))
        
    
    
    def do_get_numpoints(self):
        '''
        Returns the number of datapoints in each wave
        Input:
            None
        Output:
            numpoints (int) : Number of datapoints in each wave
        '''
        return self._numpoints

    def do_set_numpoints(self, numpts):
        '''
        Sets the number of datapoints in each wave.
        This acts on all channels.
        Input:
            numpts (int) : The number of datapoints in each wave
        Output:
            None
        '''
        logging.debug(__name__ + ' : Trying to set numpoints to %s' % numpts)
        if numpts != self._numpoints:
            logging.warning(__name__ + ' : changing numpoints. This will clear all waveforms!')

        response = raw_input('type "yes" to continue')
        if response is 'yes':
            logging.debug(__name__ + ' : Setting numpoints to %s' % numpts)
            self._numpoints = numpts
            self.clear_waveforms()
        else:
            print 'aborted'

    def do_get_clock(self): #done
        '''
        Returns the clockfrequency, which is the rate at which the datapoints are
        sent to the designated output
        Input:
            None
        Output:
            clock (int) : frequency in Hz
        '''
        self._clock = self._visainstrument.ask(":FREQ:RAST?")
        return self._clock

    def do_set_clock(self, clock): #done
        '''
        Sets the rate at which the datapoints are sent to the designated output channel
        Input:
            clock (int) : frequency in Hz (75e6 to 1.25e9)
        Output:
            None
        '''
        #logging.warning(__name__ + ' : Clock set to %s. This is not fully functional yet. To avoid problems, it is better not to change the clock during operation' % clock)
        self._clock = clock
        self._visainstrument.write(':FREQ:RAST%f' % clock)
    
    def do_get_amplitude(self, channel): #done
        '''
        Reads the amplitude of the designated channel from the instrument
        Input:
            channel (int) : 1, 2, 3 or 4: the number of the designated channel
        Output:
            amplitude (float) : the amplitude of the signal in Volts
        '''
        channel +=self._choff                                                           #<--
        logging.debug(__name__ + ' : Get amplitude of channel %s from instrument'
            % channel)
        return float(self._visainstrument.ask(':INST%s;:VOLT ?' % channel))

    def do_set_amplitude(self, amp, channel): #done
        '''
        Sets the amplitude of the designated channel of the instrument
        Input:
            amp (float)   : amplitude in Volts (0.050 V to 2.000 V)
            channel (int) : 1, 2, 3 or 4: the number of the designated channel
        Output:
            None
        '''
        channel +=self._choff                                                   #<--
        logging.debug(__name__ + ' : Set amplitude of channel %s to %.6f'
            % (channel, amp))
        if amp < 50e-3:
            amp = 50e-3
            print 'amplitude was set to 0.05 V, which is smallest possible voltage'
        if amp > 2:
            amp = 2.
            print 'amplitude was set to 2 V, which is highest possible voltage'
            
        self._visainstrument.write(':INST%s;:VOLT%.3f' % (channel, amp))

    def do_get_offset(self, channel): #done
        '''
        Reads the offset of the designated channel of the instrument
        Input:
            channel (int) : 1, 2, 3 or 4: the number of the designated channel
        Output:
            offset (float) : offset of designated channel in Volts
        '''                                               
        channel +=self._choff                                              #<--
        logging.debug(__name__ + ' : Get offset of channel %s' % channel)
        return float(self._visainstrument.ask(':INST%s;:VOLT:OFFS ?' % channel))

    def do_set_offset(self, offset, channel): #done
        '''
        Sets the offset of the designated channel of the instrument
        Input:
            offset (float) : offset in Volts (-1.000 V to 1.000 V)
            channel (int)  : 1, 2, 3 or 4: the number of the designated channel
        Output:
            None
        '''
        
        channel +=self._choff                    #<--
        if offset < -1.000:
            offset = -1.000
            print 'Offset was set to -1.000 V, which is smallest possible voltage'
        if offset > 1.000:
            offset = 1.000
            print 'Offset was set to 1.000 V, which is highest possible voltage'
            
        logging.debug(__name__ + ' : Set offset of channel %s to %.3f' % (channel, offset))
        self._visainstrument.write(':INST%s;:VOLT:OFFS%.3f' % (channel, offset))

    def do_get_marker_high(self, channel): #done
        '''
        Gets the high level for marker1 on the designated channel.
        Note that Channels 1&2 and 3&4 share the same two markers.
        Input:
            channel (int) : 1, 2, 3 or 4: the number of the designated channel
        Output:
            high (float) : high level in Volts
        '''
        channel +=self._choff                                                #<--
        logging.debug(__name__ + ' : Get upper bound of marker %i of channel %s' %(((int(channel)-1)%2+1),channel))
        return float(self._visainstrument.ask(':INST%s;:MARK:SEL%i;:MARK:VOLT:HIGH ?' % (channel,((int(channel)-1)%2+1))))

    def do_set_marker_high(self, high, channel): #done
        '''
        Sets the high level for marker1 on the designated channel.
        Note that Channels 1&2 and 3&4 share the same two markers.
        
        Input:
            high (float)   : high level in Volts
            channel (int)  : 1, 2, 3 or 4: the number of the designated channel
        Output:
            None
         '''
        channel +=self._choff                                        #<--
        logging.debug(__name__ + ' : Set upper bound of marker%i of channel %s to %.3f'% (((int(channel)-1)%2+1),channel, high))
        self._visainstrument.write(':INST%s;:MARK:SEL%i;:MARK:VOLT:HIGH%.2f' % (channel,((int(channel)-1)%2+1),high))
        self.check()
    
    def do_get_status(self, channel): #done
        '''
        Gets the status of the designated channel.
        Input:
            channel (int) : 1, 2, 3 or 4: the number of the designated channel
        Output:
            status (bool)
        '''
        channel +=self._choff                                                  #<--
        logging.debug(__name__ + ' : Get status of channel %s' % channel)
        outp = self._visainstrument.ask(':INST%s;:OUTP ?' % channel)
        if ((outp=='0')|(outp == 'OFF')):
            return False
        elif ((outp=='1')|(outp == 'ON')):
            return True
        else:
            logging.debug(__name__ + ' : Read invalid status from instrument %s' % outp)
            return 'an error occurred while reading status from instrument'
        self.get("ch%i_output"%channel-self._choff)                             #<--

    def do_set_status(self, status, channel):  #done
        '''
        Sets the status of designated channel.
        Input:
            status (bool) : True or False
            channel (int)   : 1, 2, 3 or 4: the number of the designated channel
        Output:
            None
        '''
        channel +=self._choff                                                 #<--
        logging.debug(__name__ + ' : Set status of channel %s to %s' % (channel, status))
        if status:
            self._visainstrument.write(':INST%s;:OUTP ON' % channel)
        else:
            self._visainstrument.write(':INST%s;:OUTP OFF' % channel)
        self.get("ch%i_output"%(channel-self._choff))                           #<--

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
            self._visainstrument.write(':ROSC:SOUR %s' %source)
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
        return str(self._visainstrument.ask(':ROSC:SOUR ?'))
        
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
            self._visainstrument.write(':ROSC:FREQ %s' %str(freq))
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
        return float(self._visainstrument.ask(':ROSC:FREQ ?'))
        
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
            self._visainstrument.write(':INST:COUPLE:STAT ON')
        else:
            logging.debug(__name__ + ' : Set clocks to be separate.')
            self._visainstrument.write(':INST:COUPLE:STAT OFF')
            
    def do_get_common_clock(self):
        '''
        Check whether a common clock for both channel pairs is used.
        Input:
            None
        Output:
            (bool)
        '''
        logging.debug(__name__ + ' : Check common clock.')
        return int(self._visainstrument.ask(':INST:COUPLE:STAT ?'))

    def send_waveform(self, w, m1, m2, channel, seg):
        return self.wfm_send(w, m1, m2, channel, seg)
        
    def wfm_send(self, w, m1, m2, channel, seg):
        '''
        Sends a complete waveform. All parameters need to be specified.
        Takes a waveform as generated by generate_waveform from qkit and first converts it to data usable by the AWG 
        then sends it to the memory of the specified channel into the specified segment.
        
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
        #logging.debug(__name__ + ' : Sending waveform %s to instrument' % filename)
        # Check for errors
        
        if channel > self._numchannels:
            raise ValueError("There are only channels 1 and 2.")
        
        channel +=self._choff                   #<--
        
        
        dim = len(w)
        
        if len(w)%16 != 0:
            raise ValueError #wfm length has to be divisible by 16
        
        if(m1 == None): m1 = numpy.zeros_like(w)
        if(m2 == None): m2 = numpy.zeros_like(w)
        if (not((len(w)==len(m1)) and ((len(m1)==len(m2))))):
            raise ValueError("error, the length of your waveform and markes does not match")

        self._visainstrument.write(':TRAC:DEF%i,%i' % (seg,len(w)))
            
        #Set specified channel and number of memory segment 
        self._visainstrument.write(':INST%s;:TRAC:SEL%i' % (channel, seg))
        
        #set set single trace transfer mode
        self._visainstrument.write(':TRAC:MODE SING') 
        # LG@KIT 12-06-2015 out commented
        
        #self._values['files'][filename]={}
        #self._values['files'][filename]['w']=w
        #self._values['files'][filename]['m1']=m1
        #self._values['files'][filename]['m2']=m2
        #self._values['files'][filename]['clock']=clock
        #self._values['files'][filename]['numpoints']=len(w)

        ws = ''
        for i in range(0,len(w)):
            ws = ws + struct.pack('<H', 8191*w[i]+8192+m1[i]*2**14+m2[i]*2**15)

        self._visainstrument.write(':TRAC#%i%i%s' %(int(numpy.log10(len(ws))+1), len(ws), ws))
        print "transfering waveform with %i bytes."%len(ws)

    def wfm_send2(self, w1, w2, m1=None, m2=None, channel=1, seg=1):                #<--
        '''
        Sends two complete waveforms for channel pairs 1&2 or 3&4. All parameters need to be specified.
        Takes a waveform as generated by generate_waveform from qkit and first converts it to data usable by the AWG 
        then sends it to the memory of the specified channel into the specified segment.
        
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
        #logging.debug(__name__ + ' : Sending waveform %s to instrument' % filename)
        # Check for errors
        #s0 = time.time()
        channel +=self._choff                                                       #<--
        if len(w1) != len(w2): raise ValueError("Waveform length is not equal.")
        if len(w1)%16 != 0: raise ValueError("Wfm length has to be divisible by 16")
        
        if(m1 == None): m1 = numpy.zeros_like(w1)
        if(m2 == None): m2 = numpy.zeros_like(w1)
        if (not((len(w1)==len(m1)) and ((len(m1)==len(m2))))):
            raise ValueError("error, the length of your waveform and markes does not match")

        self._visainstrument.write(':TRAC:DEF%i,%i' % (seg,len(w1)))
            
        #Set specified channel and number of memory segment 
        self._visainstrument.write(':INST%s;:TRAC:SEL%i' % (channel, seg))
        
        #set set combined trace transfer mode
        self._visainstrument.write(':TRAC:MODE COMB') 
        
        ###old method
        #ws = ''
        #for i in range(0,len(w1),16):
        #   for j in range(16):
        #       ws = ws + struct.pack('<H', 8191*w2[i+j]+8192+m1[i+j]*2**14+m2[i+j]*2**15)
        #   for j in range(16):
        #       ws = ws + struct.pack('<H', 8191*w1[i+j]+8192+m1[i+j]*2**14+m2[i+j]*2**15)
        
        ###new method
        wfm = numpy.append(numpy.reshape(numpy.array(8191*w2+8192+m1*2**14+m2*2**15,dtype=numpy.dtype('<H')),(-1,16)),numpy.reshape(numpy.array(8191*w1+8192+m1*2**14+m2*2**15,dtype=numpy.dtype('<H')),(-1,16)),axis=1).flatten()
        #ws =struct.pack('<'+'H'*len(wfm),*wfm)
        ws =str(buffer(wfm))
        
        #s1 = time.time()
        self._visainstrument.write(':TRAC#%i%i%s' %(int(numpy.log10(len(ws))+1), len(ws), ws))
        #print "transfering waveform with %i bytes."%len(ws)
        #print "Pre: %.2fs, Send: %.2fs"%(s1-s0,time.time()-s1)
        

    def define_sequence(self,channel, segments=None,loops=None,jump_flags=None):
        '''
        specifies the sequence table for sequenced mode.
        channel: segments table can be created for each pair of channels separately
        segments (array of ints or int): which segments in the awg do you want to output? (1-32000) If a simple int is specified, range(1,i+1) will be used
        loops (array of ints): How often should each segment be repeated? (1-16M)
        jump_flags (array of 0,1): if set to 1, the sequencer will wait at this sequence element until an event happens.
        '''
        channel +=self._choff                                    #<--
        if segments==None:
            print "Amount of segments not specified, try to get it from AWG"
            for i in range(1,32000):
                if int(self._visainstrument.ask(":TRAC:DEF%i?"%i).split()[-1])==0:
                    segments = i-1
                    #print "I guess you have %i segments"%(i-1)
                    break
            if segments==None:
                raise ValueError("Could not find number of segments...")
        if type(segments)==int:
            #the segement table needs at least 3 entries. So if it would be shorter, we just take it multiple times.
            if segments == 1 : segments = [1,1,1]
            elif segments == 2 : segments = [1,2,1,2]
            else: segments = range(1,segments+1)
            #print segments
        if loops == None: loops = numpy.ones(len(segments))
        if jump_flags == None: jump_flags = numpy.zeros(len(segments))
        if not len(loops)==len(segments) or not len(jump_flags) == len(segments):
            raise ValueError("Length of segments (%i) does not match length of loops (%i) or length of jump_flags(%i)"%(len(segments),len(loops),len(jump_flags)))
        if len(segments)<3: raise ValueError("Sorry, you need at least 3 segments. Your command has %i segments"%(len(segments)))
                    
        #Set specified channel
        self._visainstrument.write(':INST%s' % (channel))
        ws = ''
        for i in range(len(segments)):
            #ws = ws + struct.pack('<Q', 2**32*loops[i]+2**16*segments[i]+jump_flags[i])
            ws = ws + struct.pack('<LHH', loops[i],segments[i],jump_flags[i])
        self._visainstrument.write(':SEQ#%i%i%s' %(int(numpy.log10(len(ws))+1), len(ws), ws))
        #print "transfering sequence table with %i bytes."%len(ws)
    
    def set_seq_length(self,length,chpair=1):
        self.define_sequence((2*chpair-1 if self._numchannels == 4 else chpair),length)
        
    def close(self):
        self._visainstrument.close()
        
#   def wfm_resend(self, channel, w=[], m1=[], m2=[], clock=[]):
        '''
        Resends the last sent waveform for the designated channel
        Overwrites only the parameters specified
        Input: (mandatory)
            channel (int) : 1, 2, 3 or 4, the number of the designated channel
        Input: (optional)
            w (float[numpoints]) : waveform
            m1 (int[numpoints])  : marker1
            m2 (int[numpoints])  : marker2
            clock (int) : frequency
        Output:
            None
        '''
        # filename = self._values['recent_channel_%s' % channel]['filename']
        # logging.debug(__name__ + ' : Resending %s to channel %s' % (filename, channel))


        # if (w==[]):
            # w = self._values['recent_channel_%s' % channel]['w']
        # if (m1==[]):
            # m1 = self._values['recent_channel_%s' % channel]['m1']
        # if (m2==[]):
            # m2 = self._values['recent_channel_%s' % channel]['m2']
        # if (clock==[]):
            # clock = self._values['recent_channel_%s' % channel]['clock']

        # if not ( (len(w) == self._numpoints) and (len(m1) == self._numpoints) and (len(m2) == self._numpoints)):
            # logging.error(__name__ + ' : one (or more) lengths of waveforms do not match with numpoints')

        # self.send_waveform(w,m1,m2,filename,clock)
        # self.do_set_filename(filename, channel)

    # def wfm_import(self, file, path, format = 'WFM'):
        '''
        Import a waveform from the AWG mass storage device into the waveform list.
        
        Input:
            file - file name of the waveform file
            path - path name of the waveform file
            type - type of the waveform file. default format is WFM.
        '''
        # self._visainstrument.write('MMEM:IMP "%s", "%s", %s'%(file, path, format))

    # def wfm_assign(self, channel, position, file):
        '''
        Assign a named waveform to a channel and sequencer position
        
        Input:
            channel - channel id (starting from 1)
            position - sequence element index (starting from 1)
            file - file name shown in the waveform window
        '''
        # self._visainstrument.write('SEQ:ELEM%d:WAV%d "%s"'%(position, channel, file))
        
    # def do_get_seq_length(self):
        '''
        Return the length of the currently loaded sequence in SEQ mode.
        '''
        # return int(self._visainstrument.ask('SEQ:LENG?'))
        
    # def do_set_seq_length(self, length):
        '''
        Set the length of the output sequence in SEQ mode.
        '''
        # self._visainstrument.write('SEQ:LENG %d'%int(length))
        
    # def do_get_seq_position(self):
        '''
        Get the current position of the sequencer in SEQ mode.
        '''
        # return int(self._visainstrument.ask('AWGC:SEQ:POS?'))
            
    # def set_seq_loop(self, position, count):
        '''
        Set how often the sequencer item at position is looped during playback.
        
        Input:
            position - sequence element index (starting from 1)
            count - loop count. may be inf(ty)
        '''
        # if(count == numpy.infty):
            # self._visainstrument.write('SEQ:ELEM%d:LOOP:INF 1'%position)
        # else:
            # self._visainstrument.write('SEQ:ELEM%d:LOOP:INF 0'%position)
            # self._visainstrument.write('SEQ:ELEM%d:LOOP:COUN %d'%(position, count))

    # def get_seq_loop(self, position):
        '''
        Get how often the sequencer item at position is looped during playback.
        
        Input:
            position (int) - sequence element index (starting from 1)
        Output: 
            loop count (int)
        '''
        # if(self._visainstrument.ask('SEQ:ELEM%d:LOOP:INF?'%position) == 1):
            # return numpy.infty
        # else:
            # return int(self._visainstrument.ask('SEQ:ELEM%d:LOOP:COUN?'%position))
            
    # def set_seq_goto(self, position, target):
        '''
        Sets the target for an unconditional jump from the sequence element at position
        
        Input:
            position (int) - sequence element index (starting from 1)
            target (int) - jump target (also starting from 1). None disables goto for the element.
        '''
        # if(target == None):
            # self._visainstrument.write('SEQ:ELEM%d:GOTO:STAT %d'%(position, 0))
        # else:
            # self._visainstrument.write('SEQ:ELEM%d:GOTO:STAT %d'%(position, 1))
            # self._visainstrument.write('SEQ:ELEM%d:GOTO:IND %d'%(position, target))
        
    # def get_seq_goto(self, position):
        '''
        Get the tharget for an unconditional jump from the sequence element at position
        
        Input:
            position (int) - sequence element index (starting from 1)
        '''
        # if(int(self._visainstrument.ask('SEQ:ELEM%d:GOTO:STAT?'%position)) == 0):
            # return None
        # else:
            # return int(self._visainstrument.ask('SEQ:ELEM%d:GOTO:IND?'%position))




