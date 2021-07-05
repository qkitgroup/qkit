# HP_3245A.py driver for Hewlett Packard 3245A Universal Source (current / voltage).
# Sergey Danilin @University of Glasgow, 01/2020

from qkit.core.instrument_base import Instrument
from qkit import visa
import types
import logging
import numpy as np

class HP_3245A(Instrument):
    '''
	This is the python driver for the Hewlett Packard 3245A Universal Source

	Usage: perform current or voltage sweep
	Initialise with
	<name> = qkit.instruments.create('<name>', 'HP_3245A', address='<GPIB address>', reset=<bool>)
	
	'''
    def __init__(self, name, address, reset = False):
        '''
        Initializes the HP 3245A source, and communicates with the wrapper.

        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address
            reset (bool)     : resets to default values

        Output:
            None
        '''
        # Initialize wrapper functions
        logging.info(__name__ + ' : Initializing instrument HP_3245A')
        Instrument.__init__(self, name, tags=['physical'])
                
        self._address = address
        self._visainstrument = visa.instrument(self._address)

        # Implement parameters
        self.add_parameter("current", type=float, units='A', flags=Instrument.FLAG_GETSET)
        self.add_parameter("voltage", type=float, units='V', flags=Instrument.FLAG_GETSET)

        self.add_function('reset')
        self.add_function('clear_memory')
        self.add_function('set_channel')
        self.add_function('set_terminal')
        self.add_function('set_output_type')
        self.add_function('set_impedance')
        self.add_function('set_resolution')
        self.add_function('set_autorange')
        #self.add_function('set_current')
        #self.add_function('set_voltage')

        self.reset()
                    
# functions to control the device

    def reset(self, ch = 'CHANA'):
        '''
        Resets the source or a spesified channel of it.
        Input: if none two channels of the source will be reset. If you specify the channel (string), then only that channel will be reset.
        Output: NOne
        '''
        logging.debug(__name__ + ' : resetting HP_3245A.')
        if ch in ['CHANA']:
            self.write('RESET ' + ch)
        elif ch in ['CHANB']:
            self.write('RESET ' + ch)
            logging.error('Channel B can not be reset. Entire source is reset.')
        else:
            logging.error('Unclear which channel to clear! Use CHANA for channel A, and CHANB for channel B.')
    
    def clear_memory(self):
        '''
        Clear the memory of the source.
        Input: None
        Output: None
        '''
        logging.debug(__name__ + ': clearing HP_3245A memory.')
        self.write('SCRATCH')
        
    def set_channel(self, ch):
        '''
        Switches the source to the requested channel for parameter changes and operation.
        Input: Channel name (string)
        Output: None
        '''
        if ch in ['CHANA','CHANB','0','100']:
            self.write('USE ' + ch)
        else:
            logging.error('Unclear which channel to set! Use CHANA for channel A, and CHANB for channel B.')
            
    def set_terminal(self, term):
        '''
        Selects the Front or Rear terminal for operation.
        Input: Terminal desired (string)
        Output: None
        '''
        if term in ['FRONT', 'REAR']:
            logging.debug(__name__ + ': the output is from ' + term + 'terminal.')
            self.write('TERM ' + term)
        else:
            logging.error('Unknown terminal! Use either FRONT or REAR.')
            
    def set_output_type(self, input_string):
        ''' Sets the source for DC voltage / current output or triggered DC voltage / current output.
        Input: string with the meaning  'DCV' - output DC voltages,
                                        'DCI' - output DC cirrents,
        Output: None'''
        
        if input_string in ['DCV', 'DCI']:
            logging.debug(__name__ + ' : setting output type to' + input_string)
            self.write('APPLY ' + input_string + ' 0')
            self._output_type = input_string
        else:
            logging.error('''Not allowed DC output type! Can be one of: 'DCV','DCI'.''')
            
    def set_impedance(self, impedance):
        ''' 
        Sets the output impedance of the source if it is in voltage source mode.
        Input: Desired output impedance (0 or 50 Ohm) (string '0' or '50')
        '''
        if self._output_type == 'DCV':
            if impedance in ['0', '50']:
                logging.debug(__name__ + ': setting output impedance to' + impedance)
                self.write('IMP ' + impedance)
            else:
                logging.error('Not allowed impedance! 0 or 50 Ohm.')
        else:
            print('The output mode is not DCV. The output impedance is 0 Ohm and can not be changed!')
            
    def set_resolution(self, res):
        '''
        Sets the resolution of the source.
        Input: Resolution desired ('HIGH' or 'LOW') in a string format.
        Output: None
        '''
        if res in ['HIGH', 'LOW']:
            logging.debug(__name__ + 'Setting the resolution to ' + res)
            self.write('DCRES ' + res)
        else:
            logging.error('Not allowed resolution is given!')
            
    def set_autorange(self):
        logging.debug(__name__ + 'setting the Autorange ON.')
        self.write('ARANGE ON')
        
    def do_set_current(self, current):

        '''
        Sets the current from the source
        
        Input: Current in Ampears
        
        Output: None
        '''
        logging.debug(__name__ + ' : setting current to %s A' % current)
        if (current < -1e-3):
            self.write('APPLY DCI -%.1fE-3' % (abs(current)/1e-3))
        elif (current >= -1e-3)&(current < -1e-6):
            self.write('APPLY DCI -%.1fE-6' % (abs(current)/1e-6))
        elif (current >= -1e-6)&(current < 0):
            self.write('APPLY DCI -%.1fE-9' % (abs(current)/1e-9))
        elif (current >= 0)&(current < 1e-6):
            self.write('APPLY DCI %.1fE-9' % (abs(current)/1e-9))
        elif (current >= 1e-6)&(current < 1e-3):
            self.write('APPLY DCI %.1fE-6' % (abs(current)/1e-6))
        else:
            self.write('APPLY DCI %.1fE-3' % (abs(current)/1e-3))
    
    def do_get_current(self):
        if self.ask('APPLY?') == "DCI":
            return self.ask('OUTPUT?')
        else:
            print("Not in current mode.")
            return

    def do_set_voltage(self, voltage):

        '''
        Sets the voltage from the source
        
        Input: Voltage in Volts
        
        Output: None
        '''
        logging.debug(__name__ + ' : setting voltage to %s V' % voltage)
        if (voltage < -1):
            self.write('APPLY DCV -%.1fE-0' % (abs(voltage)))
        elif (voltage >= -1)&(voltage < -1e-3):
            self.write('APPLY DCV -%.1fE-3' % (abs(voltage)/1e-3))
        elif (voltage >= -1e-3)&(voltage < 0):
            self.write('APPLY DCV -%.1fE-6' % (abs(voltage)/1e-6))
        elif (voltage >= 0)&(voltage < 1e-3):
            self.write('APPLY DCV %.1fE-6' % (abs(voltage)/1e-6))
        elif (voltage >= 1e-3)&(voltage < 1):
            self.write('APPLY DCV %.1fE-3' % (abs(voltage)/1e-3))
        else:
            self.write('APPLY DCV %.1fE-0' % (abs(voltage)))

    def do_get_voltage(self):
        if self.ask('APPLY?') == "DCV":
            return self.ask("OUTPUT?")
        else:
            print("Not in voltage mode.")
            return

    def write(self,msg):
        return self._visainstrument.write(msg)
    
    if qkit.visa.qkit_visa_version == 1:
        def ask(self, msg):
            return self._visainstrument.ask(msg)
    else:
        def ask(self, msg):
            return self._visainstrument.query(msg)
    

            