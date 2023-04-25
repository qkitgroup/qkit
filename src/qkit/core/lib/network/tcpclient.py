import socket
import select

class TCPClient():

    def __init__(self, host, port, packet_len=False):
        self._packet_len = packet_len
        self._socket = None
        self._connect(host, port)

    def _connect(self, host, port):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((host, port))

    def send(self, data):
        self._socket.send(data)

    def recv(self, maxsize, timeout=1):
        rlist = [self._socket.fileno()]
        elist = []
        lists = select.select(rlist, elist, elist, timeout)
        if len(lists[0]) == 0:
            return None

        data = self._socket.recv(maxsize)
        return data
