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
    """
        This is the remote tip client to connect to the TIP2 temperature control program

        Usage:
        Initialize with
        <name> = instruments.create('<name>', 'tip2_client', url = "tcp://localhost:5000",setup = True)
        # If setup is True, the controled devices are automatically provided as parameters. Currently only supported for thermometers.
        # If there is anything going wrong with this automatic process, you can set setup=False and create the devices manually.
        # If you want to control the temperature of a device called 'mxc', you can do:
        name.get_mxc_temperature()
        name.enable_PID('mxc')
        name.r_set_T(0.050) # temperature in Kelvin
        
    """

    def __init__(self, name, url = "tcp://localhost:5000",setup = True):
        
        Instrument.__init__(self, name, tags=['physical'])

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.setup_connection(url=url)
        self.default_device = "mxc"
        self.control_device = ''
        self.T = 0.0

        self.add_function('set_param')
        self.add_function('get_param')
        self.add_function('get_device')
        self.add_function('get_devices')
        self.add_function('get_config')
        self.add_function('get_controled_thermometers')
        self.add_function('define_default_thermometer')
        self.add_function("setup_devices")

        self.add_function('r_get_T')
        self.add_function('r_get_R')
        self.add_function('new_T')
        self.add_function('close')
        
        
        # self.add_parameter('range', type=int,
        #                    flags=Instrument.FLAG_GETSET)
        # self.add_parameter('excitation', type=int,
        #                    flags=Instrument.FLAG_GETSET)
        if setup:
            self.setup_devices()

    def close(self):
        print ("closing zmq socket")
        self.socket.close()

    def setup_connection(self,url="tcp://localhost:5000"):
        print("Connecting to TIP server...")
        self.socket.connect(url)
    
    def setup_devices(self):
        for d in self.get_devices():
            i = self.get_device(d)
            if i['type'] == "thermometer":
                self.add_parameter("%s_temperature"%d,type=float,flags=Instrument.FLAG_GET,
                                   units=i['unit'],get_func=lambda d=d:self.get_param(d,'temperature'))
                self.add_parameter("%s_active"%d, type=bool, flags=Instrument.FLAG_GETSET,
                                   get_func=lambda d=d:self._boolean(self.get_param(d,"active")),
                                   set_func=lambda x,d=d: self.set_param(d,"active",str(x)))
                self.add_parameter("%s_interval" % d, type=float, flags=Instrument.FLAG_GETSET,
                                   get_func=lambda d=d: self.get_param(d, "interval"),
                                   set_func=lambda x, d=d: self.set_param(d, "interval", str(x)))
                self.get(["%s_temperature"%d,"%s_active"%d,"%s_interval" % d])
                if d==self.default_device:
                    self.add_parameter('P', flags=Instrument.FLAG_GETSET, type=float, units='')
                    self.add_parameter('I', flags=Instrument.FLAG_GETSET, type=float, units='')
                    self.add_parameter('D', flags=Instrument.FLAG_GETSET, type=float, units='')
    

    def set_param(self,device, param, value):
        self.socket.send_string("set/"+device+"/"+param+"/"+str(value))
        message = self.socket.recv_string()
        return message

    def get_param(self,device, param):
        self.socket.send_string("get/"+device+"/"+param)
        message = self.socket.recv_string()
        return message

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
    
    def enable_PID(self,channel):
        """
        Enables the PID control for the given channel.
        :param channel: Channel name, i.e. "mxc"
        :return:
        """
        rv = self.set_param(channel,"control_active",True)
        if not self._boolean(rv):
            raise ValueError("enable_PID not successful, device responded '%s'"%rv)
        self.default_device = channel
        
    def disable_PID(self,channel=None):
        if channel is None:
            channel = self.default_device
        self.set_param(channel, "control_active", False)
        return self.get_controled_thermometers()
    
    # get and set Temperature

    def r_set_T(self, T, thermometer = None, safety_checks = True):
        if thermometer is None:
            thermometer = self.default_device
        self.T = T
        if T > 1.0 and safety_checks:
            raise  ValueError(__name__+": r_set_T cancelled. Target temperature > 1K. Make sure what you are doing and disable safety checks.")
        self.set_param(thermometer,'control_temperature',T)

    def r_get_T(self,thermometer = None):
        if thermometer is None:
            thermometer = self.default_device
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
        while True:
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
        return float(self.set_param(thermometer,'control_P',P))

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
        return float(self.set_param(thermometer,'control_D',D))

    # bridge settings for different channels

    def do_get_range(self, thermometer = None):
        if thermometer is None: thermometer = self.default_device
        return float(self.get_param(thermometer,'device_range'))

    def do_set_range(self, range, thermometer = None):
        """
        Set the resistance range of the specified channel. Check RANGE dict for help.
        """
        if thermometer is None: thermometer = self.default_device
        self.send("SET/T/%i/Range/%i" % (thermometer, range))
        return bool(self.recv())

    def do_get_excitation(self, thermometer = None):
        if thermometer is None: thermometer = self.default_device
        return float(self.get_param(thermometer,'device_excitation'))

    def do_set_excitation(self, excitation, thermometer = None):
        """
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
        """
        if thermometer is None: thermometer = self.default_device
        self.send("SET/T/%i/EX/%i" % (thermometer, excitation))
        return bool(self.recv())
    
    def do_get_temperature(self, thermometer = None):
        if thermometer is None: thermometer = self.default_device
        return float(self.get_param(thermometer,'temperature'))
    

    def do_get_resistance(self, thermometer = None):
        if thermometer is None: thermometer = self.default_device
        return float(self.get_param(thermometer,'resistance'))

    def _boolean(self,s): return s.lower() in ("yes", "true", "t", "1")
