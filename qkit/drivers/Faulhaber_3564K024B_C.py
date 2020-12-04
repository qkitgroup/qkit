import qkit
from qkit.core.instrument_base import Instrument
import logging
import serial
import time
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
        self.running = False

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
        return self._write({True: 'EN', False: 'DI'}[status])

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
        return self._write({0: 'ADR', 1: 'ADL'}[val])

    def run(self):
        """
        Runs alternating one turn to the right and to the left in an endless loop or until it is stoppen by 'self.stop()'

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        def run_endless():
            self.set_status(True)
            while self.running:
                self.set_direction(0)
                time.sleep(25)
                self.set_direction(1)
                time.sleep(25)
            self.set_status(False)

        self.running = True
        self.thread = threading.Thread(target=run_endless)
        self.thread.start()

    def stop(self):
        """
        Stops the endless loop initiated by 'self.run()'

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.running = False

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