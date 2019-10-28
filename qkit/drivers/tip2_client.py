# QTLAB class for remote access of an TIP temperature control server version 2,
# Author: HR @ KIT 2019-

import time
import types
from numpy import arange, size, linspace, sqrt, ones, delete, append, argmin, array, abs
import logging
import zmq
import json
import qkit
from qkit.core.instrument_base import Instrument



class Error(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

# zero.1 version of a remote tip command


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


class tip2_client(Instrument):
    '''
        This is the remote tip client to connect to the TIP2 temperature control program

        Usage:
        Initialize with
        <name> = instruments.create('<name>', 'tip2_client', url = "tcp://localhost:5000")
    '''

    def __init__(self, name, url = "tcp://localhost:5000"):
        
        Instrument.__init__(self, name, tags=['physical'])

        # Add some global constants
        #self._address = address
        #self._port = port

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.setup_connection(url=url)
        self.default_device = ''
        self.control_device = ''

        self.add_function('set_param')
        self.add_function('get_param')
        self.add_function('get_device')
        self.add_function('get_devices')
        self.add_function('get_config')
        self.add_function('get_controled_thermometers')
        self.add_function('define_default_thermometer')

        self.add_function('r_get_T')
        self.add_function('r_get_R')
        self.add_function('new_T')
        self.add_function('close')
        
        
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
                           flags=Instrument.FLAG_GETSET, units="s")
        self.add_parameter('range', type=int,
                           flags=Instrument.FLAG_GETSET)
        self.add_parameter('excitation', type=int,
                           flags=Instrument.FLAG_GETSET)
        self.add_parameter('temperature', type=float,
                           flags=Instrument.FLAG_GET, units="K")
        self.add_parameter('resistance', type=float,
                           flags=Instrument.FLAG_GET, units="Ohm")

        self.T = 0.0
        self.default_device = ""
    

    def close(self):
        print ("closing zmq socket")
        self.socket.close()

    def setup_connection(self,url="tcp://localhost:5000"):
        print("Connecting to TIP server…")
        self.socket.connect(url)

    def set_param(self,device, param, value):
        self.socket.send_string("set/"+device+"/"+param+"/"+str(value))
        message = self.socket.recv_string()
        return (message)

    def get_param(self,device, param):
        self.socket.send_string("get/"+device+"/"+param)
        message = self.socket.recv_string()
        return (message)

    def get_device(self,device):
        self.socket.send_string("get/"+device+"/:")
        message = self.socket.recv_string()
        return json.loads(message)

    def get_devices(self):
        self.socket.send_string("get/:")
        message = self.socket.recv_string()
        return json.loads(message)

    def get_config(self):
        self.socket.send_string("get/::")
        message = self.socket.recv_string()
        return json.loads(message)

    def get_controled_thermometers(self):
        devices = self.get_devices()
        controlled_devices = []
        for dev in devices:
            if self._boolean(self.get_param(dev,'active')):
                if self._boolean(self.get_param(dev,'control_active')):
                    controlled_devices.append(dev)

        return controlled_devices
    
    def define_default_thermometer(self,thermometer):
        self.default_device = thermometer
    
    # get and set Temperature

    def r_set_T(self, T, thermometer = None):
        if thermometer is None: thermometer = self.default_device
        self.T = T
        if T > 1.0: return None
        self.set_param(self.default_device,'control_temperature',T)
        # if not int(self.recv()) == 1:
        #    raise Error("communication error")

    def r_get_T(self,thermometer = None):
        if thermometer is None: thermometer = self.default_device
        return float(self.get_param(thermometer,'temperature'))

    def r_get_R(self, thermometer = None):
        if thermometer is None: thermometer = self.default_device
        return float(self.get_param(thermometer,'resistance'))

    def new_T(self, T, dT_max=0.0005, thermometer = None):
        if thermometer is None: thermometer = self.default_device
        def rms(Ts):
            return sqrt(sum(Ts * Ts) / len(Ts))

        Ts = ones(20)
        settling_time = time.time()
        print ("T set to "+str(T))
        self.r_set_T(T)

        T_current = self.r_get_T()
        print (T_current)
        # qkit.flow.sleep(15)
        # print T_current
        while (True):
            T_current = self.r_get_T()
            Ts = delete(append(Ts, T_current), 0)
            rmsTs = rms(Ts)

            if abs(rmsTs - T) > dT_max:
                print ("dT > dT_max(%.5f): %.5f at Tctl: %.5f Curr T: %.5f" % (dT_max, rmsTs - T, T, T_current))
                qkit.flow.sleep(2)
            else:
                break
        print ("settling time: %s"%(time.time() - settling_time))

    

    def do_set_T(self, val):
        if thermometer is None: thermometer = self.default_device
        try:
            self.r_set_T(val)
            self.T = self.r_get_T()
            return self.T
        except ValueError:
            logging.warning('TIP connection probably lost. Nothing set.')
            return False

    def do_get_T(self,thermometer = None ):
        if thermometer is None: thermometer = self.default_device
        return float(self.get_param(thermometer,'temperature'))

    def do_get_P(self,thermometer = None):
        if thermometer is None: thermometer = self.default_device
        return float(self.get_param(thermometer,'control_P'))

    def do_set_P(self, P,thermometer = None):
        if thermometer is None: thermometer = self.default_device
        return float(self.set_param(thermometer,'control_I',P))

    def do_get_I(self,thermometer = None): 
        if thermometer is None: thermometer = self.default_device       
        return float(self.get_param(thermometer,'control_I'))

    def do_set_I(self, I,thermometer = None):
        if thermometer is None: thermometer = self.default_device
        return float(self.set_param(thermometer,'control_I',I))

    def do_get_D(self,thermometer = None):
        if thermometer is None: thermometer = self.default_device
        return float(self.get_param(thermometer,'control_D'))

    def do_set_D(self, D,thermometer = None):
        if thermometer is None: thermometer = self.default_device
        return float(self.set_param(thermometer,'control_I',D))

    # bridge settings for different channels

    def do_get_interval(self, thermometer = None):
        if thermometer is None: thermometer = self.default_device
        return float(self.get_param(thermometer,'interval'))

    def do_set_interval(self, interval, thermometer = None):
        '''
        set the measurement interval of the specified channel. Unit is seconds.
        '''
        if thermometer is None: thermometer = self.default_device
        return float(self.set_param(thermometer,'interval',interval))

    def do_get_range(self, thermometer = None):
        if thermometer is None: thermometer = self.default_device
        return float(self.get_param(thermometer,'device_range'))

    def do_set_range(self, range, thermometer = None):
        '''
        Set the resistance range of the specified channel. Check RANGE dict for help.
        '''
        if thermometer is None: thermometer = self.default_device
        self.send("SET/T/%i/Range/%i" % (channel, range))
        return bool(self.recv())

    def do_get_excitation(self, thermometer = None):
        if thermometer is None: thermometer = self.default_device
        return float(self.get_param(thermometer,'device_excitation'))

    def do_set_excitation(self, excitation, thermometer = None):
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
        if thermometer is None: thermometer = self.default_device
        self.send("SET/T/%i/EX/%i" % (channel, excitation))
        return bool(self.recv())
    
    def do_get_temperature(self, thermometer = None):
        if thermometer is None: thermometer = self.default_device
        return float(self.get_param(thermometer,'temperature'))
    

    def do_get_resistance(self, thermometer = None):
        if thermometer is None: thermometer = self.default_device
        return float(self.get_param(thermometer,'resistance'))

    def _boolean(self,s): return s.lower() in ("yes", "true", "t", "1")

    # def autorange(self):
    #     '''
    #     Does one single autorange cycle by looking at all resistance values. THIS IS NOT A PERMANENT SETTING!
    #     Prints if it changes something
    #     '''
    #     self.send('G/T/:/ALL')
    #     time.sleep(.1)
    #     #x = pickle.loads(self.recv())
    #     for y in x:
    #         if (y['last_Res'] / RANGE[y['range']]) < 0.01 or (y['last_Res'] / RANGE[y['range']]) > 50:
    #             newrange = max(4, RANGE.keys()[
    #                 argmin(abs(y['last_Res'] / array(RANGE.values()) - 1))])  # we take a minimum RANGE setting of 4
    #             print ("%s has a R_meas/R_ref value of %.4f and is set to range %i but I would set it to %i." % (
    #                 y['name'], y['last_Res'] / RANGE[y['range']], y['range'], newrange))
    #             self.do_set_range(newrange, y['channel'])

    