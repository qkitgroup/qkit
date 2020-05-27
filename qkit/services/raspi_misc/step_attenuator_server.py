# AS@KIT

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

# install:
'''
    sudo apt-get update
    sudo apt-get install python-dev
    sudo apt-get install python-rpi.gpio
'''


import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)   #use RPi.GPIO layout

#P = [19,   21, 23, 22, 24, 26] #rpi 2 #GPIO 10,9,11,25,8,7
P = [33,    35, 37, 36, 38, 40] #rpi 3 #GPIO 13,19,26,16,20,21
A = [0.5,   1,  2,  4,  8,  16]#Attenuation

GPIO.setup(P, GPIO.OUT, initial=GPIO.HIGH) #initialize to high to have maximum attenuation at start.

attenuation = sum(A)
A.reverse() #this is needed for the loop later
#P.reverse() #now they correspond to each other again

try:
    import SocketServer
except ImportError:
    import socketserver as SocketServer
from threading import Thread
from time import sleep


class TCPHandler_StepAttenuator(SocketServer.BaseRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def set_attenuation(self, att):
        global attenuation
        try:
            att=round(float(att),3) #the round is to avoid floating point precision issues. Would only affect udB settings.
        except Exception as m:
            print 'Conversion of attenuation to float failed: ', m
        
        set_values = [1]*len(A)
        att2 = att
        for i,a in enumerate(A):
            if att2 >= a:
                set_values[i]=0
                att2-=a
        if att2 != 0:
            print "Got request to set to %s dB, but I then would have %.4f dB left"%(att,att2)
            return False
        
        GPIO.output(P,set_values)
        attenuation = att
        print "Setting attenuation to %.3fdB: "%(att)+str(set_values)
        return True
            
    def handle(self):
        global attenuation
        try:
            # self.request is the TCP socket connected to the client
            self.data = str(self.request.recv(1024).strip()).upper()
            if "ATTEN" in self.data and "?" in self.data:
                print 'get attenuation request from', str(format(self.client_address[0]))
                self.request.sendall(str(attenuation))
            elif "ATTEN" in self.data:
                print 'Set attenuation request from', str(format(self.client_address[0]))
                att = float(filter(lambda x: str.isdigit(x) or x==".",self.data)) #extracts digits and decimal point
                self.request.sendall(str(self.set_attenuation(att)))
            else:
                print 'request string not recognized: %s'%self.data
                self.request.sendall(0)
        except Exception as m:
            print 'Error in TCP server handler:', m


class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):   #enable multiple access
    pass


if __name__ == "__main__":
    HOST, PORT = 'ip-address', 9900

    # Create the server, binding to localhost on port 9955
    server = ThreadedTCPServer((HOST, PORT), TCPHandler_StepAttenuator)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    try:
        server.serve_forever()
    finally:
        print 'shut down server'
        server.shutdown()

