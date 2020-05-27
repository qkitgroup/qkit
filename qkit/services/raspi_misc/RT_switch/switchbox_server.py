# server for providing TwoPortSwitch_RT by JB@KIT 04/2015 jochen.braumueller@kit.edu
# two port switch at room temperature to in situ (re)calibrate the qubit manipulation IQ-mixer
# model: Raspberry Pi running Raspian, Radiall Switch R572.432.000 (latching, no 50Ohms termination at open port) integrated in rack slot
# use: run on Raspberry Pi mounted in rack

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

'''
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)   #use RPi.GPIO layout

SWITCH1 = 16   #gpio23
SWITCH2 = 18   #gpio24
GPIO.setup(SWITCH1, GPIO.OUT)
GPIO.setup(SWITCH2, GPIO.OUT)   #set as outputs
GPIO.output(SWITCH1, GPIO.LOW)
GPIO.output(SWITCH2, GPIO.LOW)   #set off
'''

switch_position = 0

try:
    import SocketServer
except ImportError:
    import socketserver as SocketServer
from threading import Thread

#import os,sys
from time import sleep


class TCPHandler_Switch2port(SocketServer.BaseRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def switch(self, p):
        if p == 1:
            GPIO.output(SWITCH1, GPIO.HIGH)
            sleep(0.3)
            GPIO.output(SWITCH1, GPIO.LOW)
            switch_position = 1
            return True
        elif p == 2:
            GPIO.output(SWITCH2, GPIO.HIGH)
            sleep(0.3)
            GPIO.output(SWITCH2, GPIO.LOW)
            switch_position = 2
            return True
        else:
            return False
            
    def handle(self):
        try:
            # self.request is the TCP socket connected to the client
            self.data = self.request.recv(1024).strip()
            if str(self.data) == 'get_position':
                print 'switch get position request from', str(format(self.client_address[0]))
                self.request.sendall(str(switch_position))
            elif str(self.data) == 'switch 1':
                print 'switch 1 request from', str(format(self.client_address[0]))
                self.request.sendall(str(self.switch(1)))
            elif str(self.data) == 'switch 2':
                print 'switch 1 request from', str(format(self.client_address[0]))
                self.request.sendall(str(self.switch(2)))
            else:
                print 'request string not recognized'
                self.request.sendall(0)
        except Exception as m:
            print 'Error in TCP server handler:', m


class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):   #enable multiple access
    pass


if __name__ == "__main__":
    HOST, PORT = 'ip-address', 9988

    # Create the server, binding to localhost on port 9955
    server = ThreadedTCPServer((HOST, PORT), TCPHandler_Switch2port)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    try:
        server.serve_forever()
    finally:
        print 'shut down server'
        server.shutdown()

