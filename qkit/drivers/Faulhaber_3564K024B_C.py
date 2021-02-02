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
        self.set_bounds(bounds=(-1, 1600000))

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
        self.ins.write('{:s}\r'.format(cmd).encode())
        return self.ins.read(size=size).decode().split('\r\n')[0] # strip('\r\n') # 

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
        self._write({True: 'EN', False: 'DI'}[status])

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
        self._write({0: 'ADR', 1: 'ADL'}[val])

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
        return self._query('pos')

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
        def _move_to():
            rel = int(np.sign(float(self._query('pos')) - pos))
            self.set_direction({1: 1, -1: 0}[rel])
            self.set_status(True)
            while {1: float(self._query('POS')) > pos, -1: float(self._query('POS')) < pos}[rel] and not self.aborting:
                time.sleep(t)
            self.set_status(False)
        
        self.aborting = False
        self.thread = threading.Thread(target=_move_to)
        self.thread.start()

    def set_bounds(self, bounds=(0, 1510000)):
        """
        Sets the position range to <boudns>.

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

    def run(self, bounds=(0, 1500000), t=1e-2):
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
        def run_endless():
            while self.running:
                self.set_direction(0)
                time.sleep(0.5)
                self.set_status(True)
                while float(self._query('POS')) < bounds[1] and not self.aborting:
                    time.sleep(t)
                self.set_status(False)
                if self.aborting: break
                self.set_direction(1)
                time.sleep(0.5)
                self.set_status(True)
                while float(self._query('POS')) > bounds[0] and not self.aborting:
                    time.sleep(t)
                self.set_status(False)
                self.set_direction(1)

        self.running, self.aborting = True, False
        self.thread = threading.Thread(target=run_endless)
        self.thread.start()

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
        self.ins.read(size=100)
        return float(self._query('pos'))
    
    def get_status(self):
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