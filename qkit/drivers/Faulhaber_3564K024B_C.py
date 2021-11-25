import qkit
from qkit.core.instrument_base import Instrument
import logging
import serial
import time, numpy as np
import threading


class Faulhaber_3564K024B_C(Instrument):
    """
    This is the driver for the Faulhaber 3564K024B C stepping motor.
    """

    def __init__(self, name, address):
        """
        Initializes serial communication with the instrument Faulhaber 3564K024B C.

        Parameters
        ----------
        name: string
            Name of the instrument (driver).
        address: string
            Serial address for the communication with the instrument.

        Returns
        -------
        None
        """
        Instrument.__init__(self, name, tags=['physical'])
        logging.info(__name__ + ': Initializing instrument Faulhaber 3564K024B C')
        # Serial port configuration
        baudrate = 9600
        timeout = 0.1
        self.ins = serial.Serial(address, baudrate, timeout=timeout)
        self.running, self.aborting = False, False
        self.lock = threading.Lock()
        
        self.mode = 'SOR0'
        self.set_mode(self.mode)
        self.position = None
        self.speed = 10000
        self.direction = 0
        self.bounds = (-1, 1500000)
        self.set_bounds(bounds=self.bounds)

    def _write(self, cmd):
        """
        Sends a serial command <cmd> to the Device.

        Parameters
        ----------
        cmd: str
            Command that is send to the instrument.

        Returns
        -------
        None
        """
        with self.lock:
            return self.ins.write('{:s}\r'.format(cmd).encode())

    def _query(self, cmd, size=100):
        """
        Sends a serial command <cmd> and returns the read answer <ans>.

        Parameters
        ----------
        cmd: str
            Command that is send to the instrument.

        Returns
        -------
        answer: str
            Answer that is returned at read after the sent <cmd>.
        """
        with self.lock:
            self.ins.write('{:s}\r'.format(cmd).encode())
            return self.ins.read(size=size).decode().split('\r\n')[0] # strip('\r\n') # 
    
    def set_mode(self, mode):
        """
        Sets the motor operation mode <mode>.

        Parameters
        ----------
        mode: str
            Motor operation mode. Can be:
            'SOR': source for velocity by the 
                0: interface (default)
                1: voltage at the analog input
                2: pwm signal at the analog input
                3: current setpoint at the analog input
                4: current setpoint at the analog input with the direction by polarity
            'CONTMOD': continuous mode
            'STEPMOD': step motor mode
            'APCMOD': analog position control mode
            'ENCMOD': encoder mode
            'HALLSPEED': hall sensor as speed sensor
            'ENCSPEED': encoder as speed sensor
            'GEARMOD': gearing mode
            'VOLTMOD': set voltage mode
            'IXRMOD': set IxR mode

        Returns
        -------
        None
        """
        self.mode = mode
        self._write(mode)
        
    def set_speed(self, speed, direction=None):
        """
        Sets motor rotation speed to <speed> and the operating mode to <SOR0>, which is needed.

        Parameters
        ----------
        speed: int
            Motor roation speed (1rpm equals about 1500). Must be in [0, 30 000].

        Returns
        -------
        None
        """
        try:
            self.speed = speed
            if direction != None:
                self.direction = direction
            self.set_direction(val=self.direction)
            self._write('SOR0')
            self._write('V{:s}{:d}'.format({0: '+', 1: '-'}[direction], self.speed))
        except:
            self.set_speed(speed=speed, direction=direction)

    def set_status(self, status):
        """
        Sets motor status to <status>.

        Parameters
        ----------
        status: int
            Motor status. Possible values are 0 (off) and 1 (on).

        Returns
        -------
        None
        """
        try:
            if self.mode == 'SOR0':
                self.set_speed(speed={True: self.speed, False: 0}[status], direction=self.direction)
            self._write({True: 'EN', False: 'DI'}[status])
        except:
            self.set_status(status=status)

    def set_direction(self, val):
        """
        Sets motor rotation direction to <val>.

        Parameters
        ----------
        val: int
            Motor rotation direction. Possible values are 0 (right) and 1 (left).

        Returns
        -------
        None
        """
        self.direction = val
        try:
            self._write({0: 'ADR', 1: 'ADL'}[val])
        except:
            self.set_direction(val=val)

    def get_position(self):
        """
        Gets the motor position <ans>.

        Parameters
        ----------
        None

        Returns
        -------
        ans: int
            Motor position.
        """
        try:
            self.position = float(self._query('pos'))
        except ValueError:
            print('''Faulhaber_3564K024B_C: couldn't get position.''')
        finally:
            return self.position

    def set_zero_position(self):
        """
        Sets the motor's actual position to 0.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self._write('HO')

    def move_to(self, pos, t=1e-2):
        """
        Moves the motor to the positions <pos>.

        Parameters
        ----------
        pos: int
            Motor position.
        t: float
            Query interval for actual position.

        Returns
        -------
        pos: int
            Actual position
        """
        if self.mode == 'SOR1':
            def _move_to():
                rel = int(np.sign(self.get_position() - pos))
                self.set_direction({1: 1, -1: 0}[rel])
                self.set_status(True)
                while {1: self.get_position() > pos, -1: self.get_position() < pos}[rel] and not self.aborting:
                    time.sleep(t)
                self.set_status(False)
        elif self.mode == 'SOR0':
            print('''use 'SOR1' mode instead''')
            raise NotImplementedError(''''move_to' not yet implemented for 'SOR0' mode.''' )
        
        self.aborting = False
        self.thread_move_to = threading.Thread(target=_move_to)
        self.thread_move_to.start()

    def set_bounds(self, bounds=(0, 1510000)):
        """
        Sets the position range to <bounds>.

        Parameters
        ----------
        bounds: tuple(int)
            Motor position range.

        Returns
        -------
        None
        """
        self._write('LL{:+d}'.format(bounds[0]))
        self._write('LL{:+d}'.format(bounds[1]))
        self._write('APL1')
    
    def get_bounds(self):
        """
        Gets the position range <bounds>.

        Parameters
        ----------
        None

        Returns
        -------
        bounds: tuple(int)
            Motor position range.
        """
        return (float(self._query('GNL')), float(self._query('GPL')))

    def run(self, bounds=None, speed=None, t=1e-2):
        """
        Runs alternating one turn to the right and to the left bound in an endless loop or until it is stopped by 'self.stop()'

        Parameters
        ----------
        bounds: tuple
            left and right bound

        Returns
        -------
        None
        """
        if bounds == None:
            bounds = self.bounds
        if speed == None:
            speed = self.speed
        
        if self.mode == 'SOR1':
            def run_endless():
                while self.running:
                    self.set_direction(0)
                    time.sleep(0.5)
                    self.set_status(True)
                    while self.get_position() < bounds[1] and not self.aborting:
                        time.sleep(t)
                    self.set_status(False)
                    if self.aborting: break
                    self.set_direction(1)
                    time.sleep(0.5)
                    self.set_status(True)
                    while self.get_position() > bounds[0] and not self.aborting:
                        time.sleep(t)
                    self.set_status(False)
                    self.set_direction(1)
        elif self.mode == 'SOR0':
            def run_endless():
                while True:  # ugly bugfix, but I don't know, how to solve the problem of a restart (MMW)
                    while self.running:
                        self.set_status(True)
                        self.set_speed(speed=speed, direction=0)
                        while self.get_position() < bounds[1] and not self.aborting:
                            time.sleep(t)
                        self.set_speed(speed=speed, direction=1)
                        while self.get_position() > bounds[0] and not self.aborting:
                            time.sleep(t)
                        self.set_speed(speed=0, direction=1)
                        self.set_status(False)
                    time.sleep(1)
        
        self.running, self.aborting = True, False
        self.thread_run = threading.Thread(target=run_endless)
        self.thread_run.start()

    def stop(self):
        """
        Stops the endless loop initiated by 'self.run()' after the next cycle, when the motor is at its start position.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.running = False
    
    def abort(self):
        """
        Stops 'self.move_to()' or the endless loop initiated by 'self.run()' immediately.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.running, self.aborting = False, True
        time.sleep(0.5)
        with self.lock:
            self.ins.read(size=100)
        return self.get_position()
    
    def get_running_status(self):
        """
        Gets the status of endless loop initiated by 'self.run()' and eventually stopped by 'self.stop()' or 'self.abort()'.

        Parameters
        ----------
        None

        Returns
        -------
        status: boolean
            Running state.
        """
        return self.running and not self.aborting

    def close(self):
        """
        Closes the serial connecttion with the instrument.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.ins.close()