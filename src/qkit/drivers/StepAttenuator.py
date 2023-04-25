#AS 2016 @ KIT
#Use to control selfmade StepAttenuator which is controlled by a RaspberryPi.
from qkit.core.instrument_base import Instrument
import types
#import numpy as np
import socket


class StepAttenuator(Instrument):

    def __init__(self, name, host='pi-us126', port=9900):

        Instrument.__init__(self, name, tags=['physical'])
        
        self.add_parameter('attenuation',
            type=float, minval=0, maxval=31.5, units='dB',
            flags=Instrument.FLAG_GETSET)
            
        self.HOST, self.PORT = host, port
        self.get_attenuation()
    

    def do_set_attenuation(self, attenuation):
        try:
            # Create a socket (SOCK_STREAM means a TCP socket)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            sock.connect((self.HOST, self.PORT))
            sock.sendall('ATTEN %.3f\n'%attenuation)
            #receive confirmation from server and shut down connection
            rec = sock.recv(1024)
            #print str(rec)
            sock.close()
        except Exception as detail:
            print "Error: ", detail
            return False
        
        if rec == 'True':  
            return True
        else:
            return False
            
    def do_get_attenuation(self):
        try:
            # Create a socket (SOCK_STREAM means a TCP socket)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            sock.connect((self.HOST, self.PORT))
            sock.sendall('ATTEN?\n')
            #receive data from the server and shut down connection
            rec = sock.recv(1024)
            sock.close()
            return float(rec)
        except Exception as detail:
            print "Error: ", detail
            return False
 
