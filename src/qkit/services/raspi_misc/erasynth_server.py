import serial
import time
import sys
import zerorpc


class ERASynth(object):
    def __init__(self, ttyname, verb=True):
        s = '/dev/tty'
        self.path = s + str(ttyname)
        self.ser = serial.Serial(self.path)
        self.ser.baudrate = 115200
        self.verbose = verb

        if(self.ser.is_open == True):
            s = ""
            while s.find("HTTP server started") == -1:
                s += self.ser.readline().decode("ascii")  # .rstrip()
                if(self.verbose):
                    # sys.stdout.write(s)
                    print(s)
            print("Device: " + self.path)
            print("Initialization complete")
        else:
            print("Error: Establishing connection failed!")
            print("Check permissions and connection.")

    def __del__(self):
        self.ser.close()

    def readln(self):
        s = self.ser.readline().decode("ascii").rstrip()
        if(self.verbose):
            print(s)
            return s
        else:
            return s

    def enableout(self):
        self.ser.write(b'>P01\r\n')
        return self.readln()

    def disableout(self):
        self.ser.write(b'>P00\r\n')
        return self.readln()

    def setfrequency(self, f):
        self.ser.write(b'>F' + str(int(f)).encode() + b'\r\n')
        return self.readln()

    def setamplitude(self, a):
        self.ser.write(b'>A' + str(a).encode() + b'\r\n')
        return self.readln()

    def setrefint(self):
        self.ser.write(b'>P10\r\n')  # Clock Ref internal
        return self.readln()

    def setrefext(self):
        self.ser.write(b'>P11\r\n')  # Clock Ref internal
        return self.readln()

    def setrefocxo(self):
        self.ser.write(b'>P51\r\n')  # OCXO
        return self.readln()

    def setreftcxo(self):
        self.ser.write(b'>P50\r\n')  # TCXO
        return self.readln()

    def readall(self):
        self.ser.write(b'>RA\r\n')  # Readl all as json
        return self.readln()

    def readdiag(self):
        self.ser.write(b'>RD\r\n')
        return self.readln()


s = zerorpc.Server(ERASynth("ACM0", False))
s.bind("tcp://0.0.0.0:4242")
s.run()

'''
synth1 = ERASynth('ACM0')

synth1.setfrequency(6,9)
synth1.setamplitude(-22.2335)
synth1.enableout()
time.sleep(3)
synth1.disableout()
'''
