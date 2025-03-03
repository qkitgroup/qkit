"""
This instrument contains multiple classes for communicating with a RS232 serial port

The main class handles the qkit integration and stores one of the other classes, 
which each offer a different way of connecting to the serial port. These include:
- Direct connection via USB to SerialPort cable connected to the measurement pc (requires pyserial)
- Via ethernet using a RS232-LAN adapter configured as a TCP server (requires socket)
- Via ethernet using a RasbPi (requires zmq)

The listed site-packages are initially only accessed alongside establishment of their respesctive connection class 
to keep the requirements to the python environment as low as possible

Author: Marius Frohn <uzrfo@student.kit.edu>
Version: 1.0; (07/2024) 
"""

from qkit.core.instrument_base import Instrument
import logging, time

class SerialPortCommunication(Instrument):
    """
    This main class is a wrapper for the underlying actually chosen communication type and handles qkit integration.
    Thus additionally required packages are only imported if the respective connection is indeed demanded. 

    Initialize with
    <SPC_name> = instruments.create('<SPC_name>', 'SerialPortCommunication', *args for creating connection*)
    """
    def __init__(self, name: str, connection_type: str, **connection_config):
        Instrument.__init__(self, name, tags=[])
        self.connection = None
        if connection_type == "Direct":
            self.connection = SerialPortDirect(**connection_config)
        elif connection_type == "Server":
            self.connection = SerialPortServer(**connection_config)
        elif connection_type == "Rasbpi":
            self.connection = SerialPortRasbpi(**connection_config)
        else:
            logging.error("Could not resolve connection type '{}'. Must be 'Direct', 'Server' or 'Rasbpi'".format(connection_type))
            print("Could not resolve connection type '{}'. Must be 'Direct', 'Server' or 'Rasbpi'".format(connection_type))
            raise ValueError
        self.add_function("communicate")
    def communicate(self, message: list[int], expect_return: int) -> list[int]:
        """
        Passes the communication command to the underlying connection type
        """
        if self.connection is None:
            logging.error("Something went wrong during connection creation")
            return []
        else:
            return self.connection.communicate(message, expect_return)


class SerialPortDirect:
    """
    Helper class handling communication via serial port
    Possible port names can be found before initialization with get_ports()

    Baudrate, parity & stopbits are currently hardcoded to fit the needs of IVVI_BiasDAC, 
    feel free to make this class more adjustable, if necessary
    """
    import serial, serial.serialutil

    @staticmethod
    def get_ports():
        """
        Shortcut for serial.tools.list_ports.main()
        Implemented as static function so one can determine to be used port name before instrument creation

        Input:
            None
        
        Output:
            (None): prints information about currently available serial ports
        """
        import serial.tools.list_ports
        serial.tools.list_ports.main()
    
    def __init__(self, port: str = "COM3", timeout: float = 3, timeskip: float = 0.01):
        self.timeskip = timeskip
        try:
            self.ser = self.serial.Serial(port=port, baudrate=115200, parity=self.serial.PARITY_ODD, stopbits=self.serial.STOPBITS_ONE, timeout=timeout, write_timeout=timeout)
        except self.serial.serialutil.SerialException:
            print("Error while trying to open serial port '{}' for IVVI. Port not connected?".format(port))
            raise self.serial.serialutil.SerialException
        self.ser.close()
    
    def __del__(self):
        self.ser.close()
    
    def communicate(self, message: list[int], expect_return: int) -> list[int]:
        """
        Main communication protocol of the serial port connection with integrated error flag interpretation

        Input:
            message (list[int]) : to be sent message
        
        Output:
            (list[int]) : received response, stripped off size & error flag bytes 
        """
        self.ser.open()
        if self.ser.in_waiting > 0:
            # clear input if something still in waiting for whetever reason
            self.ser.read(self.ser.in_waiting)
            time.sleep(self.timeskip)
        self.ser.write(bytes(message))
        time.sleep(self.timeskip)
        readback = []
        for i in range(100):
            readback += list(self.ser.read(self.ser.in_waiting))
            if len(readback) >= expect_return:
                break
            time.sleep(self.timeskip)
        self.ser.close()
        return readback

class SerialPortServer:
    """
    Helper class for accessing a TCP server to do the communication with the serial port.

    For now, this is used for a PUSR rs232-ethernet converter 
    (see https://www.pusr.com/products/1-port-rs232-to-ethernet-converters-usr-tcp232-302.html).
    To configure one of these converters for your desired purpose, download & install the configuration software, 
    then find your device and set it to static IP with what address + port you want and put it into 'TCP server' mode.
    """
    import socket
    def __init__(self, address: str = "129.13.93.50", port: int = 12345, max_message_len: int = 64, timeskip: int = 0.01):
        self.sock = self.socket.socket(self.socket.AF_INET, self.socket.SOCK_STREAM)
        self.sock.connect((address, port))
        self.max_msg_len = max_message_len
        self.timeskip = timeskip
    def __del__(self):
        self.sock.shutdown()
        self.sock.close()
    def communicate(self, message: list[int], expect_return: int) -> list[int]:
        # clear old message 
        self.sock.sendall(bytes(message))
        time.sleep(self.timeskip)
        readback = []
        for i in range(100):
            readback += list(self.sock.recv(self.max_msg_len))
            if len(readback) >= expect_return:
                break
            time.sleep(self.timeskip)
        return readback

class SerialPortRasbpi:
    """
    Helper class handling communication via ethernet using a RasbPi as server

    This mess originated from obsolete version of IVVI_BiasDAC driver, 
    I have no idea if this works or is usable for other cases than IVVI
    """
    import zmq

    def __init__(self, address='10.22.197.115'):
        self._address = address
        self._port = 6543
        self.REQUEST_TIMEOUT = 2500
        self.REQUEST_RETRIES = 3
        self._open_zmq_connection()

    def __del__(self):
        self._close_zmq_connection()

    def _open_zmq_connection(self):
        """
        Connects to the raspberry via zmq/tcp

        Input:
            None

        Output:
            None
        """
        self.context = self.zmq.Context(1)
        print("Connecting to Raspberry Pi")
        self.client = self.context.socket(self.zmq.REQ)
        self.client.connect("tcp://%s:%s" % (self._address,self._port)) # raspi address
        self.poll = self.zmq.Poller()
        self.poll.register(self.client, self.zmq.POLLIN)
        
    def _close_zmq_connection(self):
        """
        Closes the zmq connection

        Input:
            None

        Output:
            None
        """
        logging.debug(__name__ + ' : Closing ethernet connection')
        self.context.term()

    def communicate(self, message: list[int], expect_return: int) -> list[int]:
        """
        Main communication protocol of the ethernet connection with integrated error flag interpretation

        Input:
            message (list[int]) : to be sent message
        
        Output:
            (list[int]) : received response, stripped off size & error flag bytes 
        """
        logging.debug(__name__ + ' : do communication with instrument')
        message = ("{} "*message[0]).format(*message)
        retries_left = self.REQUEST_RETRIES
        while retries_left:
            self.client.send(message)
            expect_reply = True
            while expect_reply:
                socks = dict(self.poll.poll(self.REQUEST_TIMEOUT))
                if socks.get(self.client) == self.zmq.POLLIN:
                    data_out_string = self.client.recv()
                    if not data_out_string:
                        break
                    else:
                        retries_left = 0
                        expect_reply = False
                else:
                    print("No response from server, retrying")
                    # Socket is confused. Close and remove it.
                    self.client.setsockopt(self.zmq.LINGER, 0)
                    self.client.close()
                    self.poll.unregister(self.client)
                    retries_left -= 1
                    if retries_left == 0:
                        print("Server seems to be offline, abandoning")
                        break
                    print("Reconnecting and resending " + message)
                    # Create new connection
                    self._open_zmq_connection()
        return [int(s) for s in data_out_string.split(' ')]
        