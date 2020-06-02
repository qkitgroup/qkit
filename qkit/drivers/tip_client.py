# QTLAB class for remote access of an TIP temperature control server,
# Author: HR @ KIT 2011
import qkit
from qkit.core.instrument_base import Instrument
import socket
import time
import types
from numpy import arange, size, linspace, sqrt, ones, delete, append, argmin, array, abs
import logging
import six

try:
    import cPickle as pickle
except:
    import pickle

class Error(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

# zero.1 version of a remote tip command

def loads(i):
    if six.PY2:
        return pickle.loads(i)
    else:
        return pickle.loads(i,encoding='latin1')

RANGE = {0: 0.02,
         1: 0.2,
         2: 2,
         3: 20,
         4: 200,
         5: 2e3,
         6: 20e3,
         7: 200e3,
         8: 2e6,
         9: 20e6
         }


class tip_client(Instrument):
    '''
        This is the remote tip client to connect to the TIP temperature control program

        Usage:
        Initialize with
        <name> = instruments.create('<name>', 'TIP_client', address='IP address', port='PORT')
    '''

    def __init__(self, name, address="localhost", port=9999):
        # logging.info(__name__ + ' : Initializing TIP client')
        Instrument.__init__(self, name, tags=['physical'])

        # Add some global constants
        self._address = address
        self._port = port

        self.reconnect(address, port)
        self.add_function('reconnect')
        self.add_function('send')
        self.add_function('recv')
        self.add_function('r_set_T')
        self.add_function('r_get_T')
        self.add_function('new_T')
        self.add_function('close')
        self.add_function('autorange')
        self.add_function('set_interval_scanning')
        self.add_function('set_interval_base')
        self.add_function('set_interval_off')
        self.add_function('measure')
        self.add_function('get_all')
        
        self.add_parameter('T',
                           flags=Instrument.FLAG_GETSET,
                           type=float,
                           units='K'
                           )
        self.add_parameter('P',
                           flags=Instrument.FLAG_GETSET,
                           type=float,
                           units=''
                           )
        self.add_parameter('I',
                           flags=Instrument.FLAG_GETSET,
                           type=float,
                           units=''
                           )
        self.add_parameter('D',
                           flags=Instrument.FLAG_GETSET,
                           type=float,
                           units=''
                           )
        self.add_parameter('interval', type=float,
                           flags=Instrument.FLAG_GETSET, units="s",
                           channels=(1, 5), channel_prefix='T%d_')
        self.add_parameter('range', type=int,
                           flags=Instrument.FLAG_GETSET,
                           channels=(1, 5), channel_prefix='T%d_')
        self.add_parameter('excitation', type=int,
                           flags=Instrument.FLAG_GETSET,
                           channels=(1, 5), channel_prefix='T%d_')
        self.add_parameter('temperature', type=float,
                           flags=Instrument.FLAG_GET, units="K",
                           channels=(1, 5), channel_prefix='T%d_')

        self.T = 0.0
    
    def reconnect(self, HOST=None, PORT=None):
        try:
            self.sock.close()
        except:
            pass
        if HOST is None: HOST = self._address
        if PORT is None: PORT = self._port
        
        try:
            # Create a socket (SOCK_STREAM means a TCP socket)
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Connect to server and send data
            self.sock.connect((HOST, PORT))
            print("TIP client connected to TIP server at %s port %d\n" % (HOST, PORT))
        except:
            raise

    # generic com comands

    def send(self, send_cmd):
        self.sock.send((send_cmd + "\n").encode('latin1'))

    def recv(self,bytes=False):
        # Receive data from the server and shut down
        rdata = self.sock.recv(8192 * 10)
        if bytes:
            return rdata
        return rdata.decode('latin1').strip()

    # get and set Temperature

    def r_set_T(self, T):
        self.T = T
        if T > 0.7: return None
        self.send("SET/PID/TCTRL/%s" % str(T))
        if not int(self.recv()) == 1:
            raise Error("communication error")

    def r_get_T(self):
        self.send("get/T//T")
        return float(self.recv())

    def new_T(self, T, dT_max=0.0005):
        def rms(Ts):
            return sqrt(sum(Ts * Ts) / len(Ts))

        Ts = ones(20)
        settling_time = time.time()
        print("T set to ", T)
        self.r_set_T(T)

        T_current = self.r_get_T()
        print(T_current)
        # qkit.flow.sleep(15)
        # print T_current
        while (True):
            T_current = self.r_get_T()
            Ts = delete(append(Ts, T_current), 0)
            rmsTs = rms(Ts)

            if abs(rmsTs - T) > dT_max:
                print("dT > dT_max(%.5f): %.5f at Tctl: %.5f Curr T: %.5f" % (dT_max, rmsTs - T, T, T_current))
                qkit.flow.sleep(2)
            else:
                break
        print("settling time:", time.time() - settling_time)

    def close(self):
        self.sock.close()

    def do_set_T(self, val):
        try:
            self.r_set_T(val)
            self.T = self.r_get_T()
            return self.T
        except ValueError:
            logging.warning('TIP connection probably lost. Nothing set.')
            return False

    def do_get_T(self):
        try:
            self.T = self.get_T4_temperature()
        except ValueError:
            logging.warning('TIP connection probably lost. Returning temperature 0 K.')
            self.T = 0
        return self.T

    def get_PID_params(self):
        self.send("GET/PID/ALL")
        return loads(self.recv(bytes=True))

    def do_get_P(self):
        self.send("GET/PID/P")
        return float(self.recv())

    def do_set_P(self, P):
        self.send("SET/PID/P/%.8e" % P)
        return bool(self.recv())

    def do_get_I(self):
        self.send("GET/PID/I")
        return float(self.recv())

    def do_set_I(self, I):
        self.send("SET/PID/I/%.8e" % I)
        return bool(self.recv())

    def do_get_D(self):
        self.send("GET/PID/D")
        return float(self.recv())

    def do_set_D(self, D):
        self.send("SET/PID/D/%.8e" % D)
        return bool(self.recv())

    # bridge settings for different channels

    def do_get_interval(self, channel):
        self.send("GET/T/%i/INTERVAL" % channel)
        return float(self.recv())

    def do_set_interval(self, interval, channel):
        '''
        set the measurement interval of the specified channel. Unit is seconds.
        '''
        self.send("SET/T/%i/INTERVAL/%.8e" % (channel, interval))
        return bool(self.recv())

    def do_get_range(self, channel):
        self.send("GET/T/%i/RANGE" % channel)
        return float(self.recv())

    def do_set_range(self, range, channel):
        '''
        Set the resistance range of the specified channel. Check RANGE dict for help.
        '''
        self.send("SET/T/%i/Range/%i" % (channel, range))
        return bool(self.recv())

    def do_get_excitation(self, channel):
        self.send("GET/T/%i/EX" % channel)
        return float(self.recv())

    def do_set_excitation(self, excitation, channel):
        '''
        set the measurement excitation of the specified channel.
        -1: Excitation off
        -1: (excitation off)
        0:3uV
        1:10uV
        2:30uV
        3:100uV
        4:300uV
        5:1 mV
        6:3 mV
        7:10 mV
        8:30 mV
        '''
        self.send("SET/T/%i/EX/%i" % (channel, excitation))
        return bool(self.recv())
    
    def do_get_temperature(self,channel):
        self.send("get/T/%i/T"%channel)
        return float(self.recv())
    
    def autorange(self):
        '''
        Does one single autorange cycle by looking at all resistance values. THIS IS NOT A PERMANENT SETTING!
        Prints if it changes something
        '''
        self.send('G/T/:/ALL')
        time.sleep(.1)
        x = loads(self.recv(bytes=True))
        for y in x:
            if (y['last_Res'] / RANGE[y['range']]) < 0.1 or (y['last_Res'] / RANGE[y['range']]) > 2:
                newrange = max(4,
                    argmin(abs(y['last_Res'] / array(list(RANGE.values())) - 1)))  # we take a minimum RANGE setting of 4
                print("%s has a R_meas/R_ref value of %.4f and is set to range %i but I would set it to %i." % (
                    y['name'], y['last_Res'] / RANGE[y['range']], y['range'], newrange))
                self.do_set_range(newrange, y['channel'])

    def set_range_cold(self):
        for i,v in enumerate([6,7,7,8,8]):
            self.do_set_range(v,i+1)
            
    def set_range_warm(self):
        for i,v in enumerate([4,4,5,5,6]):
            self.do_set_range(v,i+1)
            
    def set_interval_scanning(self):
        '''
        Sets the measurement intervals to repeatedly scan through all channels.
        '''
        for i in range(1, 6):
            self.do_set_interval(1, i)

    def set_interval_base(self):
        '''
        Sets the measurement intervals to monitor base and measure other channels from time to time
        '''
        self.do_set_interval(600, 1)
        self.do_set_interval(600, 2)
        self.do_set_interval(600, 3)
        self.do_set_interval(1, 4)
        self.do_set_interval(120, 5)

    def set_interval_off(self):
        '''
        Sets the measurement intervals to measure nothing.
        '''
        for i in range(1, 6):
            self.do_set_interval(0, i)

    def measure(self, channels=None):
        if channels is None:
            channels = range(1, 6)
        if type(channels) is int:
            channels = [channels]
        for c in channels:
            self.send("set/therm/%i/schedule" % c)
            self.recv()
    
    def get_all(self):
        for ch in range(1,6):
            for value in ['range','interval','excitation','temperature']:
                self.get("T%i_%s"%(ch,value))
        for value in ['P','I','D','T']:
            self.get(value)
