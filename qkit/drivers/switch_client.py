# QKIT driver for remote access of an microwave switch control server
# Author: S1 @ KIT 2020

import zmq

from qkit.core.instrument_base import Instrument


class switch_client(Instrument):
    """
        This is the remote switch client to connect to the v2 switch raspberry

        Usage:
        Initialize with
        <name> = instruments.create('<name>', 'switch_client', url = "tcp://localhost:5000")
    """
    
    def __init__(self, name, url="tcp://localhost:5000"):
        
        Instrument.__init__(self, name, tags=['physical'])
        
        # Add some global constants
        # self._address = address
        # self._port = port
        
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.setup_connection(url=url)
        self.default_device = ''
        self.control_device = ''
        
        self.add_function('set_pulse_length')
        self.add_function('get_pulse_length')
        self.add_function('enable')
        self.add_function('disable')
        self.add_function('switch_to')
    
    def close(self):
        print("closing zmq socket")
        self.socket.close()
    
    def setup_connection(self, url="tcp://localhost:5000"):
        print("Connecting to switch server...")
        self.socket.connect(url)
    
    def enable(self, switch, port):
        self.socket.send_string("enable/%i/%i" % (switch, port))
        return self.socket.recv_string()
    
    def disable(self, switch, port):
        self.socket.send_string("disable/%i/%i" % (switch, port))
        return self.socket.recv_string()
    
    def switch_to(self, switch, port):
        self.socket.send_string("set/%i/%i" % (switch, port))
        return self.socket.recv_string()
    
    def set_pulse_length(self, pulse_length, switch=None):
        if switch is None:
            self.socket.send_string("set/length/%.3f" % pulse_length)
        else:
            self.socket.send_string("set/length/%.3f/%i" % (pulse_length, switch))
        return self.socket.recv_string()
    
    def get_pulse_length(self):
        self.socket.send_string("get/length")
        return self.socket.recv_string()
    
    def reset(self, switch):
        self.socket.send_string("reset/%i" % switch)
        return self.socket.recv_string()
    
    def get_position(self,switch):
        self.socket.send_string("get/%i" % switch)
        return self.socket.recv_string()
