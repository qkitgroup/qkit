# Oxford_Triton.py
# MP@KIT 09/2016
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
import socket
import logging


class Oxford_Triton(Instrument):
    '''
    This is the python driver for the Oxford Triton 200 fridge

    Usage:
    Initialise with
    <name> = instruments.create('<name>', host='<IP address>', port=<port>)
    For the bypass functionality, you need to specify the RaspberryPi as HOST,
    where a proxy server runs, passing all commands to the Triton control PC.

    '''
    
    def __init__(self, name, host, port):
        '''
        Initializes

        Input:
            name (string)    : name of the instrument
            address (string) : IP address
            port (int)       : port
        '''
        
        logging.info(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])
        
        self._host = host
        self._port = port
        self._soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._soc.connect((self._host, self._port))
        
        # Implement parameters
        self.add_parameter('temperature', type=float,
                           flags=Instrument.FLAG_GET,
                           minval=0, maxval=350,
                           units='K')
        
        self.add_parameter('resistance', type=float,
                           flags=Instrument.FLAG_GET,
                           minval=0, maxval=200000,
                           units='Ohm')
        
        self.add_parameter('pressure', type=float,
                           flags=Instrument.FLAG_GET,
                           minval=0, maxval=5,
                           units='mbar')
        
        self.add_parameter('valve', type=bool,
                           flags=Instrument.FLAG_GETSET)
        
        self.add_parameter('pulse_tube', type=bool,
                           flags=Instrument.FLAG_GETSET)
        
        self.add_parameter('still_power', type=float,
                           flags=Instrument.FLAG_GETSET,
                           minval=0, maxval=1,
                           units='uW')
        
        self.add_parameter('base_power', type=float,
                           flags=Instrument.FLAG_GETSET,
                           minval=0, maxval=300,
                           units='uW')
        
        self.add_parameter('warm_up_heater', type=bool,
                           flags=Instrument.FLAG_GETSET)
        
        self.add_parameter('pump', type=bool, flags=Instrument.FLAG_GETSET)
        self.add_parameter('bypass', type=bool, flags=Instrument.FLAG_GETSET)
        self.add_parameter('turbo_speed', type=int, flags=Instrument.FLAG_GET)
        self.add_parameter('turbo_power', type=int, flags=Instrument.FLAG_GET)
        
        # Implement functions
        self.add_function('get_all')
        self.add_function('start_pre_cooling')
        self.add_function('empty_pre_cooling')
        self.add_function('start_condensing')
        self.add_function('cool_down')
        self.add_function('warm_up')
        self.add_function('get_status')
        self.add_function('get_automatisation')
        self.add_function('stop_automatisation')
        self.add_function('get_base_control')
        self.add_function('set_base_control')
        
        self.get_all()
    
    def get_all(self):
        for i in range(7):
            self.get_temperature(channel=i + 1)
        for i in range(5):
            self.get_pressure(gauge=i + 1)
        for i in range(8):
            self.get_valve(valve=i + 1)
        self.get_still_power()
        self.get_base_power()
        self.get_warm_up_heater()
    
    ###
    # Communication with device
    ###
    
    def start_pre_cooling(self):
        '''
        Starts pre cooling

        Input:
            None

        Output:
            bool as confirmation
        '''
        logging.debug(__name__ + ' : start pre-cooling')
        ret = self._ask('SET:SYS:DR:ACTN:PCL')
        return ret
    
    def empty_pre_cooling(self):
        '''
        Emptys pre cooling

        Input:
            None

        Output:
            bool as confirmation
        '''
        logging.debug(__name__ + ' : empty pre-cool circuit')
        ret = self._ask('SET:SYS:DR:ACTN:EPCL')
        return ret
    
    def start_condensing(self):
        '''
        Starts condensing

        Input:
            None

        Output:
            bool as confirmation
        '''
        logging.debug(__name__ + ' : start condensing')
        ret = self._ask('SET:SYS:DR:ACTN:COND')
        return ret
    
    def cool_down(self):
        '''
        Starts full cool down

        Input:
            None

        Output:
            bool as confirmation
        '''
        logging.debug(__name__ + ' : cool down')
        ret = self._ask('SET:SYS:DR:ACTN:CLDN')
        return ret
    
    def warm_up(self):
        '''
        Starts warm up

        Input:
            None

        Output:
            bool as confirmation
        '''
        logging.debug(__name__ + ' : warm up')
        # self.set_warm_up_heater(True)
        ret = self._ask('SET:SYS:DR:ACTN:WARM')
        return ret
    
    def get_status(self):
        '''
        Get status

        Input:
            None

        Output:
            status (str)
        '''
        logging.debug(__name__ + ' : get status')
        return self._ask('READ:SYS:DR:STATUS').strip()[19:]
    
    def get_automatisation(self):
        '''
        Get name of running automatisation

        Input:
            None

        Output:
            automatisation (str)
        '''
        logging.debug(__name__ + ' : get name of running automatisation')
        return self._ask('READ:SYS:DR:ACTN').strip()[17:]
    
    def stop_automatisation(self):
        '''
        Stop automatisation

        Input:
            None

        Output:
            bool as confirmation
        '''
        logging.debug(__name__ + ' : stop automatisation')
        return self._ask('SET:SYS:DR:ACTN:STOP').strip()[26:] == 'VALID'
    
    def get_base_control(self):
        '''
        Get base temperature

        Input:
            None
        Output:
            status (bool)
            P (float)
            I (int)
            D (int)
            temperature (float)
        '''
        if self._ask('READ:DEV:T5:TEMP:LOOP:MODE').strip()[27:] == 'NOT_FOUND':
            status = self._ask('READ:DEV:T8:TEMP:LOOP:MODE').strip()[27:] == 'ON'
            t_set = float(self._ask('READ:DEV:T8:TEMP:LOOP:TSET').strip()[27:-1])
            P = float(self._ask('READ:DEV:T8:TEMP:LOOP:P').strip()[24:])
            I = float(self._ask('READ:DEV:T8:TEMP:LOOP:I').strip()[24:])
            D = float(self._ask('READ:DEV:T8:TEMP:LOOP:D').strip()[24:])
        if self._ask('READ:DEV:T8:TEMP:LOOP:MODE').strip()[27:] == 'NOT_FOUND':
            status = self._ask('READ:DEV:T5:TEMP:LOOP:MODE').strip()[27:] == 'ON'
            t_set = float(self._ask('READ:DEV:T5:TEMP:LOOP:TSET').strip()[27:-1])
            P = float(self._ask('READ:DEV:T5:TEMP:LOOP:P').strip()[24:])
            I = float(self._ask('READ:DEV:T5:TEMP:LOOP:I').strip()[24:])
            D = float(self._ask('READ:DEV:T5:TEMP:LOOP:D').strip()[24:])
        else:
            return 'False'
        return status, t_set, P, I, D
        logging.debug(__name__ + ' : getting base controle ')
        return float(self._ask(''))
    
    def set_base_control(self, temperature=0, P=12., I=1, D=0, status=True):
        '''
        Set base controle to temperature usint PID values

        Input:
            temperature (float), optional, default = 0
            P (float), optional, default = 12.
            I (int), optional, default = 100.
            D (int), optional, default = 0.
            status (bool), optional, default = True
        Output:
            bool as confirmation
        '''
        
        if status:
            thermometer = 8
            logging.debug(__name__ + ' : setting base temperature to %f using P %f I %i D%i' % (temperature, P, I, D))
            if temperature >= 2.2:
                thermometer = 5
                self.set_pulse_tube(False)
                self.set_still_power(0)
                self.set_valve(9, True)
                self.set_valve(4, True)
            return str(self._ask('SET:DEV:T%i:TEMP:LOOP:HTR:H1:MODE:ON:P:%f:I:%i:D:%i:TSET:%f' % (thermometer, P, I, D, temperature))).find('INVALID') == -1
        else:
            logging.debug(__name__ + ' : turn off base control')
            if self._ask('READ:DEV:T5:TEMP:LOOP:MODE').strip()[27:] == 'ON':
                return self._ask('SET:DEV:T5:TEMP:LOOP:MODE:OFF').strip()[35:] == 'VALID'
            if self._ask('READ:DEV:T8:TEMP:LOOP:MODE').strip()[27:] == 'ON':
                return self._ask('SET:DEV:T8:TEMP:LOOP:MODE:OFF').strip()[35:] == 'VALID'
            else:
                return 'False'
    
    ###
    # GET and SET functions
    ###
    
    
    def do_get_temperature(self, channel=8):
        '''
        Get temperature of thermometer at channel

        Input:
            channel (int), default = 8, RuOx at MC
        Output:
            temperature (float)
        '''
        logging.debug(__name__ + ' : getting temperature of channel %i' % channel)
        return float(self._ask('READ:DEV:T%i:TEMP:SIG:TEMP' % channel).strip()[26:-1])
    
    def do_get_resistance(self, channel=8):
        '''
        Get resistance of thermometer at channel

        Input:
            channel (int), default = 8, RuOx at MC
        Output:
            resistance (float)
        '''
        logging.debug(__name__ + ' : getting resistance of channel %i' % channel)
        return float(self._ask('READ:DEV:T%i:TEMP:SIG:RES' % channel).strip()[25:-3])
    
    def do_get_pressure(self, gauge=1):
        '''
        Get pressure at gauge

        Input:
            pressure_meter (int), default=1, tank
        Output:
            pressure (float)
        '''
        
        logging.debug(__name__ + ' : getting pressure at gauge %i' % gauge)
        return float(self._ask('READ:DEV:P%i:PRES:SIG:PRES' % gauge).strip()[26:-2])
    
    def do_get_valve(self, valve):
        '''
        Get valve status at valve

        Input:
            valve number (int)
        Output:
            status (bool)
        '''
        status_dict = {'CLOSE': 0, 'OPEN': 1, 'TOGGLE': 2}
        logging.debug(__name__ + ' : getting valve %s status' % valve)
        return status_dict[self._ask('READ:DEV:V%i:VALV:SIG:STATE' % valve).strip()[27:]]
    
    def do_set_valve(self, valve, status):
        '''
        Set valve status at valve_number to status

        Input:
            valve number (int)
            status (bool)
        Output:
            bool as confirmation
        '''
        status_dict = {0: 'CLOSE', 1: 'OPEN', 2: 'TOGGLE'}
        return self._ask('SET:DEV:V%i:VALV:SIG:STATE:%s' % (valve, status_dict[status])).strip()[27:] == status_dict[status]
    
    def do_get_pulse_tube(self):
        '''
        Get pulse tube status

        Input:
            None
        Output:
            status (bool)
        '''
        status_dict = {'OFF': 0, 'ON': 1}
        logging.debug(__name__ + ' : getting pulse tube status')
        try:
            return self._ask('READ:DEV:C1:PTC:SIG:STATE').strip()[26:]
        except Exception:
            return False
    
    def do_set_pulse_tube(self, status):
        '''
        Set pulst tube to status

        Input:
            status (bool)
        Output:
            bool as confirmation
        '''
        status_dict = {0: 'OFF', 1: 'ON'}
        logging.debug(__name__ + ' : setting pulse tube to %i' % status)
        return self._ask('SET:DEV:C1:PTC:SIG:STATE:%s' % status_dict[status]).strip()[27:] == status_dict[status]
    
    def do_get_still_power(self):
        '''
        Get still heater power

        Input:
            None
        Output:
            power (float)
        '''
        
        logging.debug(__name__ + ' : getting still power')
        return float(self._ask('READ:DEV:H2:HTR:SIG:POWR').strip()[25:-2])
    
    def do_set_still_power(self, power):
        '''
        Set still heater to power

        Input:
            power (float)
        Output:
            bool as confirmation
        '''
        
        logging.debug(__name__ + ' : setting still heater power to %f' % power)
        add = len(str(power).split('.')[0])
        return self._ask('SET:DEV:H2:HTR:SIG:POWR:%f' % power).strip()[37 + add:] == 'VALID'
    
    def do_get_base_power(self):
        '''
        Get base heater power

        Input:
            None
        Output:
            power (float)
        '''
        
        logging.debug(__name__ + ' : getting base power')
        return float(self._ask('READ:DEV:H1:HTR:SIG:POWR').strip()[25:-2])
    
    def do_set_base_power(self, power):
        '''
        Set base heater to power

        Input:
            power (float)
        Output:
            bool as confirmation
        '''
        
        logging.debug(__name__ + ' : setting base heater power to %f' % power)
        add = len(str(power).split('.')[0])
        return self._ask('SET:DEV:H1:HTR:SIG:POWR:%f' % power).strip()[37 + add:] == 'VALID'
    
    def do_get_warm_up_heater(self):
        '''
        Get status of warm up heater

        Input:
            None
        Output:
            status (bool)
        '''
        
        logging.debug(__name__ + ' : getting warm up heater status')
        return float(self._ask('READ:DEV:H3:HTR:SIG:POWR').strip()[25:-2]) != 0
    
    def do_set_warm_up_heater(self, status):
        '''
        Set warm up heater to status

        Input:
            status (bool)
        Output:
            bool as confirmation
        '''
        
        logging.debug(__name__ + ' : setting warm up heater to %i' % status)
        power = 0
        if status:
            power = 10000
        add = len(str(power).split('.')[0])
        self._ask('SET:DEV:H3:HTR:SIG:POWR:%f' % power).strip()[37 + add:]
        return self.get_warm_up_heater() is status
    
    def _ask(self, cmd):
        self._soc.sendall((cmd + '\n').encode())
        return self._soc.recv(1024).decode()
    
    def _do_set_pump(self, pump="COMP", state=False):
        '''
        Set pump on or off

        Input:
            pump: one of 'TURB1', 'FP', 'COMP'
            state (bool)
        '''
        logging.debug(__name__ + ' : setting pump {} to state {}'.format(pump, "ON" if state else "OFF"))
        return self._ask('SET:DEV:{}:PUMP:SIG:STATE:{}'.format(pump, "ON" if state else "OFF")).strip()[-6:] == ":VALID"
    
    def _do_get_pump(self, pump="COMP"):
        '''
        Get pump state (bool)

        Input:
            pump: one of 'TURB1', 'FP', 'COMP'
        Output:
            status (bool)
        '''
        logging.debug(__name__ + ' : Getting pump {} state'.format(pump))
        return self._ask('READ:DEV:{}:PUMP:SIG:STATE'.format(pump)).strip()[-2:] == "ON"
    
    def _do_set_bypass(self, state):
        '''
        Open or close bypass and switch compressor accordingly.
        Does a safety check wether P2<750mbar

        Input:
            state (bool): True: open bypass and switch off compressor,
                          False: close bypass and switch on compressor
        Output:
            None
        '''
        logging.debug(__name__ + ' : {} bypass'.format("open" if state else "close"))
        if state:  # opening, do safety check
            if self.do_get_pressure(gauge=2) > 750:
                raise ValueError('{} bypass not successful. P2 is above 750mbar.'.format("open" if state else "close"))
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self._host, 9989))
            sock.send(b"open\n")
            response = sock.recv(1024 * 8).strip().decode()
            if response == "Ok":
                self._do_set_pump("COMP", False)
            else:
                raise ValueError("Opening bypass not successful '{}' Compressor still on".format(response))
        else:  # closing
            self._do_set_pump("COMP", True)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self._host, 9989))
            sock.send(b"close\n")
            response = sock.recv(1024 * 8).strip().decode()
            if response == "Ok":
                return True
            else:
                return False
    
    def _do_get_bypass(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self._host, 9989))
        sock.send(b"get_status\n")
        response = sock.recv(1024 * 8).strip().decode()
        if response == "open":
            return True
        if response == "closed":
            return False
        else:
            raise valueError("get_bypass responded with '{}'".format(response))
    
    def _do_get_turbo_speed(self):
        logging.debug(__name__ + ' : Getting speed of the turbo pump')
        return int(self._ask('READ:DEV:TURB1:PUMP:SIG:SPD').strip()[28:-2])
    
    def _do_get_turbo_power(self):
        logging.debug(__name__ + ' : Getting power of the turbo pump')
        return int(self._ask('READ:DEV:TURB1:PUMP:SIG:POWR').strip()[29:-1])