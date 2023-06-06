# wrapper for EdwardsActiveDigitalController by JB@KIT 03/2015
# pressure readout device @ UFO: G1, G2
# model: D39591000 (enhanced)

from qkit.core.instrument_base import Instrument
import socket

class EdwardsActiveDigitalController(Instrument):

    def __init__(self, name, host='pi-us74', port=9955):

        Instrument.__init__(self, name, tags=['physical'])
        
        self.add_parameter('condenser_pressure',
            type=float,
            flags=Instrument.FLAG_GET, units='mbar')
        self.add_parameter('still_pressure',
            type=float,
            flags=Instrument.FLAG_GET, units='mbar')
            
        self.HOST, self.PORT = host, port

    def do_get_condenser_pressure(self):
        try:
            # Create a socket (SOCK_STREAM means a TCP socket)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #connect
            sock.connect((self.HOST, self.PORT))
            sock.sendall('get_p_cond' + '\n')
            # Receive data from the server and shut down
            rec = sock.recv(1024)
            sock.close()
            return rec
        except Exception as detail:
            print "Error: ", detail
            return 0
            
    def do_get_still_pressure(self):
        try:
            # Create a socket (SOCK_STREAM means a TCP socket)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #connect
            sock.connect((self.HOST, self.PORT))
            sock.sendall('get_p_still' + '\n')
            # Receive data from the server and shut down
            rec = sock.recv(1024)
            sock.close()
            return rec
        except Exception as detail:
            print "Error: ", detail
            return 0
    
    def get_all(self):
        self.get('condenser_pressure')
        self.get('still_pressure')
 
