# QTLab example instrument communicating by TCP/IP
# Reinier Heeres, 2009

from instrument import Instrument
import types
import socket

class example_tcpip(Instrument):

    def __init__(self, name, host, port):
        Instrument.__init__(self, name, tags=['measure'])

        self.add_parameter('position', type=types.FloatType,
                flags=Instrument.FLAG_GETSET)

        self.add_function('reset')
        self.add_function('step')

        self._host = host
        self._port = port
        self._connect()

        self.reset()

    def _connect(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((self._host, self._port))

    def send(self, data):
        if self._socket is None:
            self._connect()
        self._socket.send(data)

    def ask(self, data, bufsize=1024):
        self.send(data)
        self._socket.recv(bufsize)

    def do_get_position(self):
        ret = self.ask('POS?')
        return float(ret)

    def do_set_position(self, pos):
        self.send('POS %f' % pos)

    def reset(self):
        pass

    def step(self, channel, stepsie=0.1):
        '''Step channel <channel>'''
        print 'Stepping channel %d by %f' % (channel, stepsize)

