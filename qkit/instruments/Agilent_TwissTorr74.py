# Agilent Twisstorr74 class, to perform the communication between the Wrapper and the device
#
import serial
import logging
import atexit
from qkit.core.instrument_base import Instrument

class AgilentTwissTorr74(Instrument):

    def __init__(self, name, address, reset=False):
        #Instrument.__init__(self, name, tags=['physical'])
            
        logging.info(__name__ + ': Initializing instrument Twisstorr')
        #self.setup(address)

        
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

    def get_temperature(self):
        # get temperature
        temperature=[0x02,0x80,0x32,0x30,0x34,0x30,0x03,0x38,0x35]
        return self.output(temperature)
    
    def get_pumpstatus(self):
        # get pump status
        status = [0x02,0x80,0x32,0x30,0x35,0x30,0x03,0x38,0x34]
    def get_rotationspeed(self):
        # get rotationspeed
        rotationspeed=[0x02,0x80,0x31,0x32,0x30,0x30,0x03,0x38,0x30]
        

        
    def _std_open(self, device, baudrate, timeout):
        return serial.Serial(device, baudrate, timeout=timeout)

    def remote_cmd(self, cmd):
        self.ser.write(cmd)
        
        time.sleep(0.1)
        #value = self.ser.readline().strip("\x06")
        rem_char = self.ser.inWaiting()
        
        value = self.ser.read(rem_char).strip(self.ack)
        #print "##"+value+"##"+value.strip()+"###"
        return value #value.strip()
    
    def output(data):
        N=np.size(data)
        format = ">"
        for i in range(N):
            format = format + "B" # 
        return struct.pack(format, *data)#
    def ret_value(data):
        N=len(data)
        format = ">"
        for i in range(N):
            format = format + "B" # 
        return struct.unpack(format, data)


