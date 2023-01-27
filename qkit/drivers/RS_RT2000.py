# R&S RT2000 Oscilloscope Driver
# Joao Barbosa <j.barbosa.1@research.gla.ac.uk>, 2021

from qkit.core.instrument_base import Instrument
from qkit import visa
import logging
import numpy as np
from time import sleep

class RS_RT2000(Instrument):
    '''
    Driver class for Rhode&Schwarz RT2000 Oscilloscope
    Usage:
        scope=qkit.instruments.create("scope", "RS_RT2000", address=<TCPIP address>)
        scope.gets_()
        scope.sets_()
        scope.some_function()
        ...
    '''
    def __init__(self, name, address, meas_channel=1) -> None:
        logging.info(__name__ + ' : Initializing instrument')
        super().__init__(name, tags=["physical"])

        self._address=address
        self._visainstrument = visa.instrument(self._address)
        self._visainstrument.read_termination="\n"
        self._nchannels = 4
        self.manual_trigger_delay=0

        if meas_channel>4 or meas_channel<1: 
            raise ValueError("Channels between 1 and {}".format(self._nchannels))
        self._meas_channel= int(meas_channel) #integer for single channel meas, list for multi channel meas

        self.add_parameter("nop",flag = Instrument.FLAG_GETSET,
            units="", type=int, minval=1000, maxval=1e9)
        self.add_parameter("resolution", flag=Instrument.FLAG_GETSET,
            units="s", type=float, minval=1e-12, maxval=0.5)

        self.add_parameter("xscale",flag=Instrument.FLAG_GETSET,
            units="s/div", type=float, minval=100e-12,maxval=10000)
        self.add_parameter("xrange",flag=Instrument.FLAG_GETSET,
            units="s",type=float, minval=1e-12, maxval=50e3)

        self.add_parameter("yscale",flag=Instrument.FLAG_GETSET,
            units="V/div", type=float)
        self.add_parameter("averages",flag=Instrument.FLAG_GETSET,
            units="", type=int, minval=1)
        
        
        self.add_function("wait")
        self.add_function("clear")
        self.add_function("reset")
        self.add_function("preset")
        self.add_function("ready")
        self.add_function("set_resolution_dependence")
        self.add_function("set_meas_channel")
        self.add_function("set_channel")
        self.add_function("clear_errors")
        self.add_function("acq_continuous")
        self.add_function("acq_single")
        self.add_function("acq_stop")
        self.add_function("_pre_measurement")
        self.add_function("_start_measurement")
        self.add_function("_post_measurement")

        self.clear()

    def wait(self):
        self.write("*WAI")
        return

    def clear(self):
        #sometimes connection stops working and every query times out
        self._visainstrument.clear()
        return

    def reset(self):
        self.write("*RST")
        return

    def preset(self):
        self.write("SYST:PRES")
        return 

    def ready(self):
        return self.ask("*OPC?") #TODO
        #sleep(0.5)
        #return

    def set_resolution_dependence(self, value):
        '''
        Sets either the resolution or the number of points to be constant
        when adjusting the time scale or the time range.
        '''
        if value in ["nop", "NOP", "points"]:
            self.write("ACQ:POIN:AUTO RECL")
        elif value in ["resolution", "res"]:
            self.write("ACQ:POIN:AUTO RES")
        else:
            raise ValueError("Resolution or points dependency only. Use 'res' or 'nop'. Default is resolution.")
        return
    
    def set_meas_channel(self, channel=[1], multichannel=False):
        ch=[x+1 for x in range(self._nchannels)]
        
        self._meas_channel=[]
        for i in ch:
            if(i not in channel): self.write("CHAN{}:STAT 0".format(i))
            else:
                self.write("CHAN{}:STAT 1".format(i))
                self._meas_channel.append(i)

                self.write("TRIG:SOUR CHAN{}".format(i))
                self.write("TRIG:MODE AUTO")
                self.write("SING")
        return

    def set_channel(self, status=1):
        if(status): status=1
        else: status = 0
        self.write("CHAN{}:STAT {}".format(self._meas_channel,status))
        return

    def clear_errors(self):
        return self.ask("SYST:ERR:ALL?")

    def acq_continuous(self):
        return self.write("RUN")
        
    def acq_single(self):
        return self.write("SING")

    def acq_stop(self):
        return self.write("STOP")



    def do_get_nop(self):
        return int(self.ask("ACQ:POIN?"))
    def do_set_nop(self, value):
        self.write("ACQ:POIN {}".format(int(value)))
        return 

    def do_get_resolution(self):
        return self.ask("ACQ:RES?")
    def do_set_resolution(self, value):
        self.write("ACQ:RES {}".format(value))
        return

    def do_get_averages(self):
        return self.ask("ACQ:COUN?")
    def do_set_averages(self, value):
        self.write("ACQ:COUN {}".format(int(value)))
        return 

    def do_get_yscale(self):
        return self.ask("CHAN{}:SCAL?".format(self._meas_channel))
    def do_set_yscale(self, value):
        self.write("CHAN{}:SCAL {}".format(self._meas_channel,value))
        return

    def do_get_xscale(self):
        return self.ask("TIM:SCAL?")
    def do_set_xscale(self, value):
        self.write("TIM:SCAL {}".format(float(value)))
        return

    def do_get_xrange(self):
        return self.ask("TIM:RANG?")
    def do_set_xrange(self,value):
        self.write("TIM:RANG {}".format(value))
        return
    
    def get_data(self, format="ascii"):
        '''
        Gets the tracedata for all active channels on the scope. Set active channels with set_meas_channel([ch1,ch2,...])
        '''
        
        data_channels=np.zeros((len(self._meas_channel),self.do_get_nop()))
        data_time_channels=np.zeros((len(self._meas_channel),self.do_get_nop()))
        for ind,ch in enumerate(self._meas_channel):    
            data_time_channels[ind]=self.get_time_data(channel=ch)
            data_channels[ind]=self.ask_for_values("CHAN{}:DATA?".format(ch))

        return data_time_channels, data_channels

    def get_time_data(self,channel=None):
        #All channels have same time scale (for now), so just probe one of the active ones
        if not channel:
            xheader=self.ask("CHAN{}:DATA:HEAD?".format(self._meas_channel[0]))
        else:
            xheader=self.ask("CHAN{}:DATA:HEAD?".format(channel))
        xheader=xheader.split(",")

        time_array=np.linspace(float(xheader[0]),float(xheader[1]),num=int(xheader[2]))
        return time_array
        
    def _pre_measurement(self):
        self.write("TRIG:SOUR CHAN{}".format(self._meas_channel[0])) #source of trigger (software)
        self.write("TRIG:MODE NORM") # waits for trigger to acquire waveform
        
    
    def _start_measurement(self):
        #Get single trace (with average count)
        self.acq_single() #check later
        sleep(0.01)
        self.write("TRIG:FORC") #forces trigger and acquires waveform
        
    def _start_measurement_manual_trigger(self):
        # Trigger is done through a signal on one of the scope channels
        self.acq_continuous() #
        sleep(0.01)
        sleep(self.manual_trigger_delay)

    def _post_measurement(self):
        #return back to analog channel triggering
        self.clear()
        self.write("TRIG:SOUR CHAN{}".format(self._meas_channel[0]))
        #self.write("TRIG:FIND")
        self.write("TRIG:MODE AUTO")
        self.write("SING")

    def write(self,msg):
        return self._visainstrument.write(msg)
    
    if visa.qkit_visa_version == 1:
        def ask(self, msg):
            return self._visainstrument.ask(msg)
    
        def ask_for_values(self, msg, **kwargs):
            return self._visainstrument.ask_for_values(kwargs)
    else:
        def ask(self, msg):
            return self._visainstrument.query(msg)
    
        def ask_for_values(self, msg, format=None, fmt=None):
            dtype = format if format is not None else fmt if fmt is not None else visa.single
            dtype = visa.dtypes[dtype]
            return self._visainstrument.query_binary_values(msg,datatype=dtype,container=np.array)