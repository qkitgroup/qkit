# -*- coding: utf-8 -*-

# MMW@KIT
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

# install:
'''
    sudo apt-get update
    sudo apt-get install python-dev
    sudo apt-get install python-zerorpc
    sudo apt-get install python-rpi.gpio
'''


import zerorpc
import RPi.GPIO as GPIO
from qkit.config.services import cfg
import numpy
import time
import logging
import os
import json

class qplexkit(object):
    '''
    Qplexkit is a DC multiplexer for low level and low noise transport
    measurements of micro and nano circuits at low temperatures. It uses MDSM 
    connectors with 25 pins and enables to measure 12 different 4-wire 
    experiments with the same four lines in switching between them by means of 
    low temperature applicable latching relays. For low-ohmic experiments it 
    provides additionally two switchable current divider at low temperatures 
    to achieve better SNRs. The control unit at room temperature uses a 
    Respberry Pi Model B+ and is embedded to Qkit - a quantum measurement suite
    in python.
    
    
    ##########################################################################
    #                            Cryostat circuit                            #
    ##########################################################################
    
                                                                    line 1               line 2                                                                  CURRENT DIVIDER
                                                                 │      ₒ   │         │   ₒ      │                                                                
                                                                 │    ╔═╧═╗ │         │ ╔═╧═╗    │                                                                
                                                                 ├─■■─╢15 ╟─┤         ├─╢16 ╟─■■─┤                                                                
                                                                 │    ╚═══╝ │         │ ╚═══╝    │                                                                
                                                                 │     11   │         │  12      │                                                                
                                                                 █          █         █          █                                                                
                                                                 │          │         │          │                                                                
                                                                 └──────────┴────╥────┴──────────┘                                                                
                                                                                 ║                                                                                
                                                                                 ║                                                                                DC MULTIPLEXER
                                                                               ╔═╩═╗                                                                              
                                         ╔═════════════════════════════════════╣ 0 ╠═════════════════════════════════════╗                                        relay layer A: <lay> = 0
                                         ║                                     ╚╤═╤╝                                     ║                                        
                                       ╔═╩═╗                                     0                                     ╔═╩═╗                                      
                     ╔═════════════════╣ 1 ╠═════════════════╗                                       ╔═════════════════╣ 2 ╠═════════════════╗                    relay layer B: <lay> = 1
                     ║                 ╚═══╝                 ║                                       ║                 ╚═══╝                 ║                    
                   ╔═╩═╗                 1                 ╔═╩═╗                                   ╔═╩═╗                 2                 ╔═╩═╗                  
           ╔═══════╣ 3 ╠═══════╗                   ╔═══════╣ 4 ╠═══════╗                   ╔═══════╣ 5 ╠═══════╗                   ╔═══════╣ 6 ╠═══════╗          relay layer C: <lay> = 2
           ║       ╚═══╝       ║                   ║       ╚═══╝       ║                   ║       ╚═══╝       ║                   ║       ╚═══╝       ║          
         ╔═╩═╗       3       ╔═╩═╗               ╔═╩═╗       4       ╔═╩═╗               ╔═╩═╗       5       ╔═╩═╗               ╔═╩═╗       6       ╔═╩═╗        
      ╔══╣ 7 ╠══╗         ╔══╣ 8 ╠══╗         ╔══╣ 9 ╠══╗         ╔══╣10 ╠══╗         ╔══╣11 ╠══╗         ╔══╣12 ╠══╗         ╔══╣13 ╠══╗         ╔══╣14 ╠══╗     relay layer D: <lay> = 3
      ║  ╚═══╝  ║         ║  ╚═══╝  ║         ║  ╚═══╝  ║         ║  ╚═══╝  ║         ║  ╚═══╝  ║         ║  ╚═══╝  ║         ║  ╚═══╝  ║         ║  ╚═══╝  ║     
    ┌─╨─┐  7  ┌─╨─┐     ┌─╨─┐  8  ┌─╨─┐     ┌─╨─┐  /  ┌─╨─┐     ┌─╨─┐  /  ┌─╨─┐     ┌─╨─┐  9  ┌─╨─┐     ┌─╨─┐ 10  ┌─╨─┐     ┌─╨─┐  /  ┌─╨─┐     ┌─╨─┐  /  ┌─╨─┐   <self._rels[<rel>]>: physical relay number
    │ 0 │     │ 1 │     │ 2 │     │ 3 │     │ 4 │     │ 5 │     │ 6 │     │ 7 │     │ 8 │     │ 9 │     │10 │     │11 │     │12 │     │13 │     │14 │     │15 │   <exp>              : logical experiment number
    └───┘     └───┘     └───┘     └───┘     └───┘     └───┘     └───┘     └───┘     └───┘     └───┘     └───┘     └───┘     └───┘     └───┘     └───┘     └───┘
      0         1         2         3         4         /         5         /         6         7         8         9        10         /        11         /     <self._exps(<exp>)>: physical experiment number
    0000      0001      0010      0011      0100      0101      0110      0111      1000      1001      1010      1011      1100      1101      1110      1111    bin(<exp>)         : equals path through relays ABCD (0:left, 1:right)
    
    DC MULTIPLEX
    Each logical latching relay (double solid lined) switches all four
    measurement lines to select the wanted experiment (singel solid line). The 
    logical relay numbers 9, 10, 11, 12 are dummy relais that do not exist 
    physically, but simplify the control logic by using bit operations of this 
    obtained symmertic setup.
    
    CURRENT DIVIDER
    Above the DC multiplexer, latching relays (double solid lined) may connect 
    a pair of two current lines with a 10Ω resistance (black box). Together 
    with the down-streamed cables, filters etc (illustrated as resistances 
    above) this forms switchable current dividers whose attenuation factor 
    depends on the ratio of these resistances and attenuates both signal and 
    noise. Since the added Nyquist noise depends on the square root of the 
    temperature, this low temperature current divider provides better signal to
    noise ratios compared to those operating at room temperature.
    
    
    ##########################################################################
    #                        Room temperature circuit                        #
    ##########################################################################
    
    ───┬───────────┬───────────┬───────────┬───────────┬───────────┬───────────┬───────────┬───────────┬───────────┬───────────┬───────────┬───────────┬───────────┬────────── HIGH
       │           │           │           │           │           │           │           │           │           │           │           │           │           │           
    ───Є─────┬─────Є─────┬─────Є─────┬─────Є─────┬─────Є─────┬─────Є─────┬─────Є─────┬─────Є─────┬─────Є─────┬─────Є─────┬─────Є─────┬─────Є─────┬─────Є─────┬─────Є─────┬──── LOW
     ₒ │   ₒ │   ₒ │   ₒ │   ₒ │   ₒ │   ₒ │   ₒ │   ₒ │   ₒ │   ₒ │   ₒ │   ₒ │   ₒ │   ₒ │   ₒ │   ₒ │   ₒ │   ₒ │   ₒ │   ₒ │   ₒ │   ₒ │   ₒ │   ₒ │   ₒ │   ₒ │   ₒ │     
    ┌┴─┴┐ ┌┴─┴┐ ┌┴─┴┐ ┌┴─┴┐ ┌┴─┴┐ ┌┴─┴┐ ┌┴─┴┐ ┌┴─┴┐ ┌┴─┴┐ ┌┴─┴┐ ┌┴─┴┐ ┌┴─┴┐ ┌┴─┴┐ ┌┴─┴┐ ┌┴─┴┐ ┌┴─┴┐ ┌┴─┴┐ ┌┴─┴┐ ┌┴─┴┐ ┌┴─┴┐ ┌┴─┴┐ ┌┴─┴┐ ┌┴─┴┐ ┌┴─┴┐ ┌┴─┴┐ ┌┴─┴┐ ┌┴─┴┐ ┌┴─┴┐    
    │ 0 │ │ 1 │ │ 2 │ │ 3 │ │ 4 │ │ 5 │ │ 6 │ │ 7 │ │ 8 │ │ 9 │ │10 │ │11 │ │12 │ │13 │ │14 │ │15 │ │16 │ │17 │ │18 │ │19 │ │20 │ │21 │ │22 │ │23 │ │24 │ │25 │ │ 0 │ │ 1 │    non-latching relay (controled by logical pin number)
    └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘    
      └──┬──┘     └──┬──┘     └──┬──┘     └──┬──┘     └──┬──┘     └──┬──┘     └──┬──┘     └──┬──┘     └──┬──┘     └──┬──┘     └──┬──┘     └──┬──┘     └──┬──┘     └──┬──┘      
         │           │           │           │           │           │           │           │           │           │           │           │           │           │         
         ≈           ≈           ≈           ≈           ≈           ≈           ≈           ≈           ≈           ≈           ≈           ≈           ≈           ≈         connection to cryostat circuit
         │   ╔═══╗   │   ╔═══╗   │   ╔═══╗   │   ╔═══╗   │   ╔═══╗   │   ╔═══╗   │   ╔═══╗   │   ╔═══╗   │   ╔═══╗   │   ╔═══╗   │   ╔═══╗   │   ╔═══╗   │   ╔═══╗   │         
         └───╢ 0 ╟───┴───╢ 1 ╟───┴───╢ 2 ╟───┴───╢ 3 ╟───┴───╢ 4 ╟───┴───╢ 5 ╟───┴───╢ 6 ╟───┴───╢ 7 ╟───┴───╢ 8 ╟───┴───╢11 ╟───┴───╢12 ╟───┴───╢15 ╟───┴───╢16 ╟───┘         logical relay number (see Cryostat circuit)
             ╚═══╝       ╚═══╝       ╚═══╝       ╚═══╝       ╚═══╝       ╚═══╝       ╚═══╝       ╚═══╝       ╚═══╝       ╚═══╝       ╚═══╝       ╚═══╝       ╚═══╝             
    
    To safe relay switch lines for low temperature relays (double solid lined),
    they are arranged ring-shaped where each line is connected to the relay 
    coil '+' on the one side and to the relay '-' on the other side. At room 
    temperature they are open by default and can be connected either with HIGH 
    or LOW by two non-latching relays (single solid lined) that are controlled 
    by GPIOs of a Raspberry Pi 3 Model B.
    '''
    
    def __init__(self):
        '''
        Initiates variables to default configuration and sets raspberry up.
        
        Input:
            None
        Output:
            None
        '''
        # class variables
        self._switch_time = 10e-3
        self._rels = {0:0, 1:1, 2:2, 3:3, 4:4, 5:5, 6:6, 7:7, 8:8, 9:11, 10:12, 11:15, 12:16}             # logical relay number [physical relay number]
        self._rel_num = len(self._rels)
        self._exps = {0:0, 1:1, 2:2, 3:3, 4:4, 5:6, 6:8, 7:9, 8:10, 9:11, 10:12, 11:14}                   # logical experiment number [physical experiment number]
        self._pin = [(((0+2*i)%26, (3+2*i)%26),((2+2*i)%26, (1+2*i)%26)) for i in range(self._rel_num)]   # logical pin configuration [relay number][relay value]
        self._gpio_num = len(numpy.unique(self._pin))
        self._gpio = {i:i+2 for i in range(self._gpio_num)}                                               # logical GPIO number [logical pin number]
        
        ## prepare raspberry pi
        try:
            # set board mode to Broadcom
            GPIO.setmode(GPIO.BCM)
            # setup GPIO
            for pin in list(set(numpy.concatenate(numpy.concatenate(self._gpio)))):
                GPIO.setup(pin, GPIO.OUT)
        except:
            logging.error('qplexkit: Cannot setup Raspberry Pi')
            raise RuntimeError('qplexkit: Cannot setup Raspberry Pi')
        
        # actual settings
        self._ccr_file = cfg['qplexkit_ccr_file']
        try:
            self._ccr = self.read_ccr()
        except ValueError:
            logging.info('qplexkit: Reset qplexkit and create new json-file')
            self._ccr = 0
            self.create_ccr()
            self.reset()
        
        
        
    def set_switch_time(self, val):
        '''
        Sets duration of GPIO pulse to <val>.
        
        Input:
            val (flt)
        Output:
            None
        '''
        self._switch_time = val
        return
    
    
    def get_switch_time(self):
        '''
        Gets duration of GPIO pulse <val>.
        
        Input:
            None
        Output:
            val (flt)
        '''
        return self._switch_time
    
    
    def set_experiment(self, exp, **kwargs):
        '''
        Sets experiment to <exp> in setting relevant relays if necessary.
        
        Input:
            exp (int): physical experiment number ∈ [0,11]
            **kwargs: <ccr> (int): condition code register <ccr> of relay states
        Output:
            None
        '''
        _ccr = kwargs.get('ccr', self._ccr)
        try:
            _exp = self._exps[exp]                                             # logical experiment number
            logging.info('Set experiment to {:d}({:d})'.format(_exp, exp))
            for lay in range(4):
                rel = 2**lay-1+(_exp >> 4-lay)                                 # logical relay number
                val = bool((_exp >> 3-lay)%2)                                  # logical relay value
                if self.get_relay(rel=rel, ccr=_ccr) ^ val:                    # if not already set correctly
                    self.set_relay(rel, val, **kwargs)
        except (ValueError, KeyError) as e:
            logging.error('qplexkit: Cannot set experiment {:d}: {:s}'.format(exp, e))
        return
    
    
    def get_experiment(self, **kwargs):
        '''
        Sets experiment to <exp> in setting relevant relays if necessary.
        
        Input:
            **kwargs: <ccr> (int): condition code register <ccr> of relay states
        Output:
            exp (int): physical experiment number ∈ [0,11]
        '''
        _ccr = kwargs.get('ccr', self._ccr)
        exp = 4*['0']
        for lay in range(4):
            exp[lay] = str((_ccr >> int(17-2**lay-sum([2**(lay-a)*int(exp[a-1]) for a in range(1,4)])))%2)
            #exp[lay] = str((_ccr >> int(15-2**lay-2**(lay-1)*int(exp[0])-2**(lay-2)*int(exp[1])-2**(lay-3)*int(exp[2])))%2)
        return self._exps.keys()[self._exps.values().index(int(''.join(exp), 2))]
    
    
    def set_current_divider(self, line, val, **kwargs):
        '''
        Sets current divider of <line> to <val> by setting relevant the relay if necessary.
        
        Input:
            line (int) : line number ∈ [1,2]
            val (bool) : current divider state
            **kwargs   : <ccr> (int): condition code register <ccr> of relay states
        Output:
            None
        '''
        if bool(val) ^ self.get_relay(rel=14+line, **kwargs):
            return self.set_relay(rel=14+line, val=val, **kwargs)
        else:
            return
    
    
    def get_current_divider(self, line, **kwargs):
        '''
        Gets <val> of current divider of <line>.
        
        Input:
            line (int) : line number ∈ [1,2]
            **kwargs   : <ccr> (int): condition code register <ccr> of relay states
        Output:
            val (bool) : current divider state
        '''
        return self.get_relay(rel=14+line, **kwargs)
    
    
    def set_relay(self, rel, val, **kwargs):
        '''
        Sets relay number <rel> to <val> in sending pulse signals of duration <switch_time> on GPIOs corresponding to <rel> with polarity corresponding to <val>
        
        Input:
            rel (int)  : logical relay number <rel> ∈ [0:16]
            val (bool) : relay polarity
            **kwargs   : <switch_time> (float) : duration of voltage pulse to switch relays
                         <ccr> (int)           : condition code register <ccr> of relay states
                         <ccr_file> (str)      : json-file to write <ccr>
        Output:
            None
        '''
        _rel         = self._rels.keys()[self._rels.values().index(rel)]       # physical relay number
        _switch_time = kwargs.get('switch_time', self._switch_time)
        _pin_low     = self._pin[_rel][int(val)][0]                            # logical GPIO number set to HIGH
        _pin_high    = self._pin[_rel][int(val)][1]                            # logical GPIO number set to HIGH
        _gpio_low    = self._gpio[_pin_low]                                    # physical GPIO number set to HIGH
        _gpio_high   = self._gpio[_pin_high]                                   # physical GPIO number set to LOW
        logging.info('qplexkit: Set relay {:d}({:d}) to {:d} with logical pins {:d}({:d}) and {:d}({:d})'.format(_rel, rel, val, _pin_low, _gpio_low, _pin_high, _gpio_high))
        GPIO.output(_gpio_low, 1)
        logging.info('qplexkit: Set GPIO{:d} high'.format(_gpio_low))
        GPIO.output(_gpio_high, 1)
        logging.info('qplexkit: Set GPIO{:d} high'.format(_gpio_high))
        time.sleep(_switch_time)
        GPIO.output(_gpio_high, 0)
        logging.info('qplexkit: Set GPIO{:d} low'.format(_gpio_high))
        GPIO.output(_gpio_low, 0)
        logging.info('qplexkit: Set GPIO{:d} low'.format(_gpio_low))
        # save changes in ccr
        self.set_ccr(rel=rel, val=val, **kwargs)
        self.write_ccr(timestamp=True, **kwargs)
        return
    
    
    def get_relay(self, rel, **kwargs):
        '''
        Gets value <val> of relay <rel> from a given condition code register <ccr>
        
        Input:
            rel (int)  : logical relay number <rel> ∈ [0:16]
            **kwargs   : <ccr> (int) : condition code register <ccr> of relay states
        Output:
            val (bool) : relay polarity
        '''
        return self.get_ccr(rel, **kwargs)
    
    
    def set_ccr(self, rel, val, **kwargs):
        '''
        Sets condition code register <ccr> from a given relay <rel> with value <val>
        
        Input:
            rel (int)  : logical relay number <rel> ∈ [0:16]
            val (bool) : relay polarity
            **kwargs   : <ccr> (int) : condition code register <ccr> of relay states
        Output:
            None
        '''
        _ccr = list('{:017b}'.format(kwargs.get('ccr', self._ccr)))
        _ccr[rel] = str(int(val))
        self._ccr = int(''.join(_ccr), 2)
        return self._ccr
    
    
    def get_ccr(self, rel, **kwargs):
        '''
        Gets value <val> of relay <rel> from a given condition code register <ccr>
        
        Input:
            rel (int)  : logical relay number <rel> ∈ [0:16]
            **kwargs   : <ccr> (int) : condition code register <ccr> of relay states
        Output:
            val (bool) : relay polarity
        '''
        return bool(int(kwargs.get('ccr', self._ccr) >> int(16-rel))%2)
    
    
    def write_ccr(self, timestamp=True, **kwargs):
        '''
        Writes a given condition code register <ccr> (and a current timestamp if wanted <timestamp>) to a json-file <ccr_file>.
        
        Input:
            timestamp (bool) : default=True
            **kwargs         : <ccr> (int)      : condition code register <ccr> of relay states
                               <ccr_file> (str) : json-file to write <ccr>
        Output:
            None
        format:
            [{"time": "yyyy-MM-dd HH:mm:ss", "ccr": <ccr>}] (if timestamp)
            [<ccr>]
        '''
        try:
            _ccr      = kwargs.get('ccr', self._ccr)
            _ccr_file = kwargs.get('ccr_file', self._ccr_file)
            with open(_ccr_file, 'r+') as f:
                try:
                    data = json.load(f)
                except ValueError as e:
                    logging.error('qplexkit: Cannot load json-file to append ccr: {:s}'.format(e))
                    data = []
                f.seek(0)
                if timestamp:
                    data.append({'ccr':_ccr, 'time':time.strftime('%Y-%m-%d %H:%M:%S')})
                else:
                    data.append(_ccr)
                json.dump(data, f)
        except IOError as e:
            logging.error('qplexkit: Cannot find json-file {:s}: {:s}'.format(_ccr_file, e))
        return
    
    
    def read_ccr(self, **kwargs):
        '''
        Reads the latest condition code register <ccr> from a json-file <ccr_file>.
        
        Input:
            **kwargs : <ccr_file> (str) : json-file to write <ccr>
        Output:
            ccr (int)
        '''
        _ccr_file = kwargs.get('ccr_file', self._ccr_file)
        with open(_ccr_file, 'r+') as f:
            try:
                _ccr = json.load(f)[-1]
                if isinstance(_ccr, dict):
                    ccr = _ccr['ccr']
                elif isinstance(_ccr, int):
                    ccr = _ccr
                else:
                    logging.error('qplexkit: Cannot handle data from json-file {:s}'.format(_ccr_file))
                    raise ValueError('Cannot read condition code register')
            except (ValueError, KeyError) as e:
                logging.error('qplexkit: Cannot find condition code register: {:s}'.format(e))
                ccr = None
                raise ValueError('Cannot read condition code register')
        return ccr
    
    
    def create_ccr(self, **kwargs):
        '''
        Creates a json-file <ccr_file> and writes a condition code register <ccr>.
        
        Input:
            **kwargs : <ccr> (int)      : condition code register <ccr> of relay states
                       <ccr_file> (str) : json-file to write <ccr>
        Output:
            None
        '''
        _ccr      = kwargs.get('ccr', self._ccr)
        _ccr_file = kwargs.get('ccr_file', self._ccr_file)
        if not os.path.isfile(_ccr_file):
            with open(_ccr_file, 'w+') as f:
                json.dump([{'ccr':_ccr, 'time':time.strftime('%Y-%m-%d %H:%M:%S')}], f)
        return
    
    
    def reset(self):
        '''
        Reset every relay to False and condition code register to 0
        
        Input:
            None
        Output:
            None
        '''
        logging.info('qplexkit: Reset every relay to False')
        for _rel, rel in self._rels.items():                                   # physical, logical relay number
            self.set_relay(rel, 0)
        self._ccr = 0
        self.write_ccr()
        return

_adress = cfg['qplexkit_adress']
s = zerorpc.Server(qplexkit())
s.bind(_adress)
s.run()
