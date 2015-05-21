# QTLAB class for remote access of an TIP temperature control server,
# Author: HR @ KIT 2011
from instrument import Instrument
import qt
import socket
import time
import types
from numpy import arange, size, linspace, sqrt,ones,delete,append

# generic error class
# raise Error("Error)
class Error(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

# zero.1 version of a remote tip command

class tip_client(Instrument):
    '''
        This is the remote tip client to connect to the TIP temperature control program

        Usage:
        Initialize with
        <name> = instruments.create('<name>', 'TIP_client', address='IP address', port='PORT')
    '''
    def __init__(self,name, address = "localhost", port = 9999):
        #logging.info(__name__ + ' : Initializing TIP client')
        Instrument.__init__(self, name, tags=['physical'])

        # Add some global constants
        self._address = address
        self._port = port

        self.setup(address,port)
        self.add_function('setup')
        self.add_function('send')
        self.add_function('recv')
        self.add_function('r_set_T')
        self.add_function('r_get_T')
        self.add_function('new_T')
        self.add_function('close')
        
        self.add_parameter('T',
            flags=Instrument.FLAG_GETSET,
            type=types.FloatType,
            units='K'
        )
        
        self.T = 0.0
        #self._T = 0.0
        
    def setup(self,HOST,PORT):
        try:
            # Create a socket (SOCK_STREAM means a TCP socket)
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Connect to server and send data
            self.sock.connect((HOST, PORT))
            print("TIP client connected to TIP server at %s port %d\n"%(HOST,PORT))
        except:
            raise
    # generic com comands
    def send(self,send_cmd):
        self.sock.send(send_cmd + "\n")
        
    def recv(self):
        # Receive data from the server and shut down
        rdata = self.sock.recv(8192)
        string = rdata
        return string.strip()
        
    # get and set Temperature
    
    def r_set_T(self,T):
        self.T = T
        if T>0.7:return None
        self.send("set T %s" % str(T))
        if not int(self.recv()) == 1:
            raise Error("communication error")
            
    def r_get_T(self):
        self.send("get T")
        return float(self.recv())

    def new_T(self,T,dT_max=0.0005):
        def rms(Ts):
            return sqrt(sum(Ts*Ts)/len(Ts)) 
        Ts=ones(20)
        settling_time = time.time()
        print "T set to ",T,
        self.r_set_T(T)
        
        T_current =self.r_get_T()
        print T_current
        #qt.msleep(15)
        #print T_current
        while(True):
            T_current = self.r_get_T()
            Ts=delete(append(Ts,T_current),0)
            rmsTs=rms(Ts)
            
            if abs(rmsTs-T) > dT_max:
                print "dT > dT_max(%.5f): %.5f at Tctl: %.5f Curr T: %.5f"%(dT_max,rmsTs-T,T,T_current)
                qt.msleep(2)
            else:
                break
        print "settling time:", time.time()-settling_time
        
    def close(self):
        self.sock.close()
        
    def do_set_T(self,val):
        self.r_set_T(val)
        self.T = self.r_get_T()
        return self.T
    def do_get_T(self):
        self.T = self.r_get_T()
        return self.T