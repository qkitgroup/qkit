# Agilent Twisstorr74 class, to perform the communication between the Wrapper and the device
#

import qkit
from qkit.core.instrument_base import Instrument
import logging
import time
import serial
import struct
import time,sys
import atexit
import numpy as np

class Agilent_TwissTorr74(Instrument):

    def __init__(self, name, address, reset=False):
        Instrument.__init__(self, name, tags=['physical'])
            
        logging.info(__name__ + ': Initializing instrument Twisstorr')
        self.setup(address)
    
    def setup(self, device="COM4"):
        # open serial port, 9600, 8,N,1, timeout 1s
        baudrate = 9600
        timeout = 0.1

        # Serial port configuration
        ser=serial.Serial()
        ser.baudrate=baudrate
        ser.timeout=timeout
        self.ser = self._std_open(device,baudrate,timeout)
        atexit.register(self.ser.close)

        #ser.port='COM4' # com4
        # load inficon comands
        #self.cmds = self.twisstorr_cmds()

    def close(self):
        # open serial port, 9600, 8,N,1, timeout 1s
        self.ser.close()
        
    def _set_remote_serial(self):
        # start
        remote_to_serial= [0x02,0x80,0x30,0x30,0x38,0x31,0x30,0x03,0x42,0x41]
        comand=self.ret_output(remote_to_serial)
        value_bin=self.remote_cmd(comand)
        value_hex=self.ret_value(value_bin)
        value_chr=map(lambda x: chr(value_hex[x]),range(len(value_hex)))
        return value_hex    

    def _set_speed_reading_after_stop(self):
        # start
        reading_speed_after_stop= [0x02,0x80,0x31,0x36,0x37,0x31,0x30,0x03,0x42,0x32]
        comand=self.ret_output(reading_speed_after_stop)
        value_bin=self.remote_cmd(comand)
        value_hex=self.ret_value(value_bin)
        value_chr=map(lambda x: chr(value_hex[x]),range(len(value_hex)))
        return value_hex      

    def _active_stop(self):
        # active stop
        active_stop= [0x02,0x80,0x31,0x30,0x37,0x31,0x31,0x03,0x42,0x35]
        comand=self.ret_output(active_stop)
        value_bin=self.remote_cmd(comand)
        value_hex=self.ret_value(value_bin)
        value_chr=map(lambda x: chr(value_hex[x]),range(len(value_hex)))
        return value_hex      

    def set_start(self):
        # start
        start= [0x02,0x80,0x30,0x30,0x30,0x31,0x31,0x03,0x42,0x33]
        comand=self.ret_output(start)
        value_bin=self.remote_cmd(comand)
        value_hex=self.ret_value(value_bin)
        value_chr=map(lambda x: chr(value_hex[x]),range(len(value_hex)))
        return value_hex    
    
    def set_stop(self):
        # stop
        stop= [0x02,0x80,0x30,0x30,0x30,0x31,0x30,0x03,0x42,0x32]
        comand=self.ret_output(stop)
        value_bin=self.remote_cmd(comand)
        value_hex=self.ret_value(value_bin)
        value_chr=map(lambda x: chr(value_hex[x]),range(len(value_hex)))
        return value_hex

    def get_temperature(self):
        # get temperature
        temperature=[0x02,0x80,0x32,0x30,0x34,0x30,0x03,0x38,0x35]
        comand=self.ret_output(temperature)
        
        value_bin=self.remote_cmd(comand)
        value_hex=self.ret_value(value_bin)
        value_chr=map(lambda x: chr(value_hex[x]),range(len(value_hex)))
        if value_hex[0:5]==(2, 128, 50, 48, 52):
            Temperature=float(''.join(value_chr[5:12]))
        else:
            print('response from Turbo not in window 205 on RS 235')
            print(value_hex)
        return 'Pump Temperature: '+ str(Temperature)

    def get_pumpstatus(self):
        # get pump status
        status = [0x02,0x80,0x32,0x30,0x35,0x30,0x03,0x38,0x34]
        comand=self.ret_output(status)
        value_bin=self.remote_cmd(comand)
        value_hex=self.ret_value(value_bin)
        value_chr=map(lambda x: chr(value_hex[x]),range(len(value_hex)))
        Pumpstatus ={
                  0: "Stop",
                  1: "Waiting initlk",
                  2: "Starting",
                  3: "Auto-tuning",
                  4: "Braking",
                  5: "Normal",
                  6: "Fail"
                }
        return 'Pump status is: '+str(Pumpstatus[int(''.join(value_chr[5:12]))])

    def get_rotationspeed(self):
        # get rotationspeed
        rotationspeed=[0x02,0x80,0x32,0x32,0x36,0x30,0x03,0x38,0x35]
        comand=self.ret_output(rotationspeed)
        value_bin=self.remote_cmd(comand)
        value_hex=self.ret_value(value_bin)
        value_chr=map(lambda x: chr(value_hex[x]),range(len(value_hex)))
        return 'The rotationspeed of the pump is: '+str(float(''.join(value_chr[5:12]))/60.0)+' Hz'

    def get_rotationspeed_setting(self):
        # get rotationspeed
        rotationspeed=[0x02,0x80,0x31,0x32,0x30,0x30,0x03,0x38,0x30]
        comand=self.ret_output(rotationspeed)
        value_bin=self.remote_cmd(comand)
        value_hex=self.ret_value(value_bin)
        value_chr=map(lambda x: chr(value_hex[x]),range(len(value_hex)))
        return 'The rotationspeed of the pump is: '+str(float(''.join(value_chr[5:12])))+' Hz'

    def set_rotationspeed1100_setting(self):
        # set rotation frequency to 1100 Herz, does not work at the moment
        rotationspeed=[0x80,0x31,0x32,0x30,0x31,0x30,0x30,0x31,0x31,0x30,0x30,0x03,0x38,0x31]
        comand=self.ret_output(rotationspeed)
        value_bin=self.remote_cmd(comand)
        value_hex=self.ret_value(value_bin)
        value_chr=map(lambda x: chr(value_hex[x]),range(len(value_hex)))
        return ''.join(value_chr[5:12])

    def _std_open(self, device, baudrate, timeout):
        return serial.Serial(device, baudrate, timeout=timeout)

    def remote_cmd(self, cmd):
        self.ser.write(cmd)      
        time.sleep(0.1)
        rem_char = self.ser.inWaiting()
        
        value = self.ser.read(rem_char)
        #print "##"+value+"##"+value.strip()+"###"
        return value #value.strip()
    
    def ret_output(self,data):
        N=np.size(data)
        format = ">"
        for i in range(N):
            format = format + "B" # 
        return struct.pack(format, *data)#

    def ret_value(self,data):
        N=len(data)
        format = ">"
        for i in range(N):
            format = format + "B" # 
        return struct.unpack(format, data)

    def command(self, addr=0x80, window, rw, data=None):
        """
        Function building the command string sent to the device.

        Args:
            addr (hex): Unit address = 0x80 for RS-232, 0x80 + device number for RS-485
            window (str): String of 3 numeric character indicating the window number (defining the command)
            rw (str): Is the command used to read ('0') or write ('1') to the device
            data (str):  Alphanumeric ASCII string with the data to be written in case rw=1

        Returns:
            cmd (str): Complete string to be sent to the device including a CRC
        """

        start = '\x02'

        command_string = chr(addr) + window + rw
        if rw == 1:
            command_string += data
        end = '\x03'
        command_string += end

        crc = ord(command_string[1])^ord(command_string[2])
        for i in range(3,len(command_string)):
            crc = crc^ord(command_string[i])
        crch = hex(crc)
        crc1 = crch[-2]
        crc2 = crch[-1]

        cmd = start + command_string + crc1 + crc2

        return cmd

    def answer(self, answer):
        start = answer[0]
        address = answer[1]
        if answer[2] == chr(0x06):
            return answer[2]
        else:
            window = answer[2] + answer[3] + answer[4]
            rw = answer[5]
            for i in range(6,len(answer)-4):
                data += answer[i]
            return data

    def start(self):
        window = '000'
        rw = '1'
        data = '1'
        cmd = self.command(window=window, rw=rw, data=data)
        self.remote_cmd(cmd)

    def stop(self):
        window = "000"
        rw = '1'
        data = '0'
        cmd = self.command(window=window, rw=rw, data=data)
        self.remote_cmd(cmd)

    def set_softstart(self, status=False):
        window = "100"
        rw = '1'
        if status: data = "1"
        else: data = "0"
        cmd = self.command(window=window, rw=rw, data=data)
        self.remote_cmd(cmd)

    def set_rot_freq_setting(self, freq=1167):
        """
        Rotational frequency setting (Hz)

        Args:
            freq (int): Rotational frequency [1100..1167], default = 1167
        """
        window = "000"
        rw = '1'
        data = str(freq)
        cmd = self.command(window=window, rw=rw, data=data)
        self.remote_cmd(cmd)

    def get_rot_freq(self):
        """
        Get rotation frequency (Hz)

        Returns:
            freq (int): Rotation frequency in Hz
        """
        window = "226"
        rw = '0'
        cmd = self.command(window=window, rw=rw)
        answer = self.answer(self.remote_cmd(cmd))
        answer = int(answer)/60.
        return answer