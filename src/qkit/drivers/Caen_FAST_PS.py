# Caen Fast-PS class, to perform the communication between the Wrapper and the device
# Marco Pfirrmann, marco.pfirrmann@kit.edu 2017
#
# based on the work on the Keithley_2636A driver by
# Pieter de Groot <pieterdegroot@gmail.com>, 2008
# Martijn Schaafsma <qtlab@mcschaafsma.nl>, 2008
# Hannes Rotzinger, hannes.rotzinger@kit.edu 2010
#
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
import types
import socket
import logging
import time
import numpy

class Caen_FAST_PS(Instrument):
    '''
    This is the driver for the Caen Fast-PS Power Supply

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Caen_fast_ps', address='<GPIB address>', reset=<bool>')
    '''

    def __init__(self, name, address, port = 10001):
        '''
        Initializes the Caen_fast_ps, and communicates with the wrapper.

        Input:
          name (string)    : name of the instrument
          address (string) : GPIB address
          reset (bool)     : resets to default values, default=False
        '''
        logging.info(__name__ + ' : Initializing instrument Caen_fast_ps')
        Instrument.__init__(self, name, tags=['physical'])

        self._host = address
        self._port = port
        self._soc = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self._soc.connect((self._host, self._port))
        
        self._ak_str = '#AK'

        
        self.add_parameter('voltage',
            flags=Instrument.FLAG_GET, units='V', minval=-20, maxval=20, type=float)
            
        self.add_parameter('setvoltage',
            flags=Instrument.FLAG_GETSET, units='V', minval=-20, maxval=20, type=float)
 
        self.add_parameter('current',
            flags=Instrument.FLAG_GET, units='A', minval=-10, maxval=10, type=float)
            
        self.add_parameter('setcurrent',
            flags=Instrument.FLAG_GETSET, units='A', minval=-10, maxval=10, type=float)

        self.add_parameter('status',
            flags=Instrument.FLAG_GET, type=bool)

        self.add_parameter('output_mode',
            flags=Instrument.FLAG_GETSET, type=str)

        self.add_parameter('current_ramp_rate',
            flags=Instrument.FLAG_GETSET, units='A/s', minval=2e-4, maxval=10, type=float)

        self.add_parameter('voltage_ramp_rate',
            flags=Instrument.FLAG_GETSET, units='A/s', minval=-10, maxval=10, type=float)

        self.add_parameter('floating_mode', flags=Instrument.FLAG_GETSET, type=str)
        
        self.add_function('ramp_current')
        self.add_function('ramp_voltage')
        self.add_function('on')
        self.add_function('off')

    def get_all(self):
        '''
        Reads all implemented parameters from the instrument,
        and updates the wrapper.

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : get all')
        self.get('voltage')
        self.get('current')
        self.get('status')
        self.get('output_mode')
        self.get('setcurrent')
        self.get('setvoltage')
        self.get('current_ramp_rate')
        self.get('voltage_ramp_rate')
 
    def do_get_voltage(self):
        '''
        Reads the voltage signal from the instrument

        Input:
            None

        Output:
            volt (float) : Voltage in Volts
        '''
        logging.debug(__name__ + ' : get voltage')
        recv = self._ask('MRV:?')
        return float(recv.split(':')[1])

    def do_get_setvoltage(self):
        '''
        Reads the setvoltage signal from the instrument

        Input:
            None

        Output:
            setvolt (float) : Voltage in Volts
        '''
        logging.debug(__name__ + ' : get setvoltage')
        recv = self._ask('MWV:?')
        return float(recv.split(':')[1])

    def do_set_setvoltage(self, setvoltage):
        '''
        Reads the setvoltage signal from the instrument

        Input:
            setvoltage (float) : setvoltage in volts

        Output:
            None
        '''
        logging.debug(__name__ + ' : set setvoltage to %s' % setvoltage)
        recv = self._ask('MWV:%s' %setvoltage)
        if recv == self._ak_str: return True
        else: return 'ERROR: ' + error_msg[recv.split(':')[1]]
        
    def do_get_current(self):
        '''
        Reads the current signal from the instrument

        Input:
            None

        Output:
            current (float) : current in amps
        '''
        logging.debug(__name__ + ' : get current')
        recv = self._ask('MRI:?')
        return float(recv.split(':')[1])
        

    def do_get_setcurrent(self):
        '''
        Reads the setcurrent signal from the instrument

        Input:
            None

        Output:
            setcurrent (float) : setcurrent in amps
        '''
        logging.debug(__name__ + ' : get setcurrent')
        recv = self._ask('MWI:?')
        return float(recv.split(':')[1])
    
    def do_set_setcurrent(self, setcurrent):
        '''
        Reads the setcurrent signal from the instrument

        Input:
            setcurrent (float) : setcurrent in amps

        Output:
            None
        '''
        logging.debug(__name__ + ' : set setcurrent to %s' % setcurrent)
        recv = self._ask('MWI:%s' %setcurrent)
        if recv == self._ak_str:
            current = self.get_current()  # stores the actual current value in instrument.parameters
            return True
        else:
            return 'ERROR: ' + error_msg[recv.split(':')[1]]

    def do_get_status(self):
        '''
        Reads the output status from the instrument

        Input:
            None

        Output:
            status (int) : Usually True/False for On/Off, other integers specify certain errors. Conversion not (yet?) implemented.
        '''
        logging.debug(__name__ + ' : get status')
        recv = self._ask('MST:?')
        ret = int(recv.split(':')[1])
        return ret

    def do_get_output_mode(self):
        '''
        Reads the output mode from the instrument

        Input:
            None

        Output:
            mode (str) : 'V' oder 'I'
        '''
        logging.debug(__name__ + ' : get mode')
        recv = self._ask('LOOP:?')
        ret = recv.split(':')[1]
        return ret

    def do_set_output_mode(self, mode):
        '''
        Sets the output mode from the instrument
        ## There seems to be an error somewhere. The mode is set correctly but the return response does not work propperly

        Input:
            mode (str) : 'V' oder 'I'

        Output:
            None
        '''
        logging.debug(__name__ + ' : set mode')
        self.off()
        recv = self._ask('LOOP:%s' %mode)
        self.on()
        if recv == self._ak_str: return True
        else: return 'ERROR: ' + error_msg[recv.split(':')[1]]
        
    def do_get_current_ramp_rate(self):
        '''
        Reads the setcurrent signal from the instrument

        Input:
            None

        Output:
            rate (float) : current_ramp_rate in A/s
        '''
        logging.debug(__name__ + ' : get current ramp rate')
        recv = self._ask('MSRI:?')
        ret = recv.split(':')[1]
        return ret
    
    def do_set_current_ramp_rate(self, rate):
        '''
        Reads the setcurrent signal from the instrument

        Input:
            rate (float) : current_ramp_rate in A/s

        Output:
            None
        '''
        logging.debug(__name__ + ' : set current ramp rate to %s' %rate)
        recv = self._ask('MSRI:%s' %rate)
        if recv == self._ak_str: return True
        else: return 'ERROR: ' + error_msg[recv.split(':')[1]]

    def do_get_voltage_ramp_rate(self):
        '''
        Reads the setcurrent signal from the instrument

        Input:
            None

        Output:
            rate (float) : voltage_ramp_rate in V/s
        '''
        logging.debug(__name__ + ' : get voltage ramp rate')
        recv = self._ask('MSRV:?')
        ret = recv.split(':')[1]
        return ret
    
    def do_set_voltage_ramp_rate(self, rate):
        '''
        Reads the setcurrent signal from the instrument

        Input:
            rate (float) : voltage_ramp_rate in V/s

        Output:
            None
        '''
        logging.debug(__name__ + ' : set voltage ramp rate to %s' %rate)
        recv = self._ask('MSRV:%s' %rate)
        if recv == self._ak_str: return True
        else: return 'ERROR: ' + error_msg[recv.split(':')[1]]
        
    def do_set_floating_mode(self, mode):
        """
        Enables(Deables) the floating mode. However, earth fuse must be removed (inserted.)
        Input:
            mode (str) : 'N' = non floating, 'F' = floating
        Output:
            None
        """
        logging.debug(__name__ + ' : set floating mode to {}'.format(mode))
        if mode == 'N':
            print("WARNING: Earth fuse has to be inserted")
        elif mode == 'F':
            print("WARNING: Earth fuse has to be removed")
        else:
            print('wrong input')
            return
        recv = self._ask('SETFLOAT:{}'.format(mode))
        if recv == self._ak_str:
            return True
        else:
            return 'ERROR: ' + error_msg[recv.split(':')[1]]

    def do_get_floating_mode(self):
        """
        returns the floating mode
        Input: None
        Output (STR): F = floating, N = non-floating
        """
        logging.debug(__name__ + ' : get floating mode')
        recv = self._ask('SETFLOAT:?')
        ret = recv.split(':')[1]
        return ret

    # shortcuts
    def off(self):
        '''
        Sets status to False

        Input:
            None

        Output:
            None
        '''
        recv = self._ask('MOFF')
        if recv == self._ak_str: return True
        else: return 'ERROR: ' + error_msg[recv.split(':')[1]]

    def on(self):
        '''
        Sets status to True

        Input:
            None

        Output:
            None
        '''
        recv = self._ask('MON')
        if recv == self._ak_str: return True
        else: return 'ERROR: ' + error_msg[recv.split(':')[1]]
    
    def ramp_finished(self):
        time.sleep(0.1)
        while int(self._ask('MST:?').split(':')[1], 16) & 2**12 == 2**12: #MP: gets 32bit status array; 12th from last bit indicates ramping process
            time.sleep(0.1)
        return True
    
    def ramp_current(self, current, ramp_rate = False, wait = True):
        '''
        Ramps current with given rate
        
        Input:
            current (float) : destination value in A
            ramp_rate (float) : ramp rate in A/s (optional)
            wait (bool) : wait until set current value is reached before returning its value (recommended)
        
        Output:
            None
        '''
        if ramp_rate: self.do_set_current_ramp_rate(ramp_rate)
        logging.debug(__name__ + ' : ramp current to %s' %current)
        recv = self._ask('MWIR:%s' %current)
        if recv == self._ak_str: 
            if wait:
                time.sleep(0.1)
                while not self.ramp_finished():
                    time.sleep(0.1)
                time.sleep(0.1)
            current = self.get_current()  # stores the actual current value in instrument.parameters
            return True
        else:
            return 'ERROR: ' + error_msg[recv.split(':')[1]]
    
    def ramp_voltage(self, voltage, ramp_rate = False, wait = True):
        '''
        Ramps voltage with given rate
        
        Input:
            voltage (float) : destination value in V
            ramp_rate (float) : ramp rate in V/s (optional)
            wait (bool) : wait until set current value is reached before returning its value (recommended)
        
        Output:
            None
        '''
        if ramp_rate: self.do_set_voltage_ramp_rate(ramp_rate)
        logging.debug(__name__ + ' : ramp voltage to %s' %voltage)
        recv = self._ask('MWVR:%s' %voltage)
        if recv == self._ak_str:
            if not wait:
                return True
            else:
                time.sleep(0.1)
                while not self.ramp_finished():
                    time.sleep(0.1)
                time.sleep(0.1)
                return str(self.do_get_voltage())
       
    def _ask(self, cmd):
        cmd = (cmd+'\r').encode('utf-8')
        self._soc.sendall(cmd)
        return self._soc.recv(1024).strip().decode('utf8')
       
    def set_coil(self, coil):
        '''
        Adapts the PID values to the specific coils in our lab
        
        Input:
            coil (int) : {0:default, 1:solenoid_red, 2:yoke_red, 3:solenoid_janice}

        Output:
            None
        '''
        PID_dict = {0:[0.0001, 0.0001, 0], 1:[0.0001, 0.0001, 0], 2:[0.0001, 0.1, 0], 3:[0.0001, 0.0001, 0]}
        PID = PID_dict[coil]
        recv = self._ask('MWG:43:%f' %PID[0])
        if recv != self._ak_str: return 'ERROR: ' + error_msg[recv.split(':')[1]]
        recv = self._ask('MWG:44:%f' %PID[1])
        if recv != self._ak_str: return 'ERROR: ' + error_msg[recv.split(':')[1]]
        recv = self._ask('MWG:45:%f' %PID[2])
        if recv != self._ak_str: return 'ERROR: ' + error_msg[recv.split(':')[1]]
        recv = self._ask('MSAVE')
        if recv != self._ak_str: return 'ERROR: ' + error_msg[recv.split(':')[1]]   
        
        
error_msg = {'01':"Unknown command",
             '02':"Unknown Parameter",
             '03':"Index out of range",
             '04':"Not Enough Arguments",
             '05':"Privilege Level Requirement not met",
             '06':"Saving Error on device",
             '07':"Invalid password",
             '08':"Power supply in fault",
             '09':"Power supply already ON",
             '10':"Setpoint is out of model limits",
             '11':"Setpoint is out of software limits",
             '12':"Setpoint is not a number",
             '13':"Module is OFF",
             '14':"Slew Rate out of limits",
             '15':"Device is set in local mode",
             '16':"Module is not in waveform mode",
             '17':"Module is in waveform mode",
             '18':"Device is set in remote mode",
             '19':"Module is already in the selected loop mode",
             '20':"Module is not in the selected loop mode",
             '99':"Unknown error"}
