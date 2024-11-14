# Nitrogen refilling automation by JB@KIT 11/2015 jochen.braumueller@kit.edu
# model: XXX + custom controller box to monitor/switch off nitrogen refilling (R. Jehle)

# this file is named 'NitrogenControl.py' and runs on the raspberry in the controller box
# functionality: logging of switching events to 'nitrogen.log', controlled stop of refilling when
#   automatic refilling continues for more than 30? minutes

# model: Raspberry Pi running Raspian
# server scripts has to be run with su permission due to GPIO usage

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

# GPIO settings
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)   #use RPi.GPIO layout

OUTPUT = 21   #gpio9
SENSE = 23   #gpio11
SWITCH = 19   #gpio10
GPIO.setup(OUTPUT, GPIO.OUT)
GPIO.setup(SENSE, GPIO.IN)
GPIO.output(OUTPUT, GPIO.LOW)   #switch on by default THIS RELAY IS INVERSE!
GPIO.setup(SWITCH, GPIO.OUT)
GPIO.output(SWITCH, GPIO.LOW)   #manual switch is off per default

try:
    import SocketServer
except ImportError:
    import socketserver as SocketServer
from threading import Thread
from sendMail import *

#import os,sys
from time import sleep


def _send_mail(m = ''):
    
    strTime = time.strftime('%x %X')

    s = SendMail("UFO@kit.edu",strTime+" UFO monitoring - manual switch off of nitrogen refilling")   #sender, subject
    
    s.setRecipients("")
    #s.add_Line("Hello, I am feeling great. Cool gases. Nice pressures.")
    s.add_Line(strTime)
    s.add_Line("The control script monitoring nitrogen refilling performed a manual switch off of nitrogen refilling.")
    s.add_Line("Refilling was taking for more than 60 minutes.")
    s.add_Line("A possible reason for this is a nitrogen dewar running empty or a malfunction of the sensor in the nitrogen bath or the PID controller.")
    s.add_Line("")
    s.add_Line(" - What happened last night can happen again. - ")
    s.add_Line("")
    s.add_Line("Please reflect this event critically. Refilling can be turned on again via remote by running the script refilling_switch_on.py, typing")
    s.add_Line("python /home/pi/nitrogen/refilling_switch_on.py")
    s.add_Line("in a ssh shell connecting to pi-us87.")
    s.add_Line("")
    if m != '':
        s.add_Line("Additional message: " + str(m))
        s.add_Line("")
    s.add_Line("Best, UFO")
    
    s.sendEMail()
    print "Mail sent to recipients."
    

class TCPHandler_Nitrogen(SocketServer.BaseRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """
    
    def set_output(self, switch_to):
        if switch_to == 'on':
            GPIO.output(OUTPUT, GPIO.LOW)
            self.man_switch = True
            sleep(0.1)
            return True
        elif switch_to == 'off':
            GPIO.output(OUTPUT, GPIO.HIGH)
            self.man_switch = False
            sleep(0.1)
            _send_mail()
            return True
        else:
            return False
    def get_state(self):
        #for i in range(15): #As we have an AC component on the signal, we have to average...
        if GPIO.input(SENSE) == GPIO.HIGH:
            return True
            #sleep(.1)
        return False

            
    def handle(self):
        try:
            # self.request is the TCP socket connected to the client
            self.data = self.request.recv(1024).strip()
            if str(self.data) == 'get_status':
                print 'status request from', str(format(self.client_address[0]))
                if self.get_state():   #refilling active
                    status = '1'
                else:
                    status = '0'
                self.request.sendall(str(status))
            elif str(self.data) == 'output on':
                print 'output on request from', str(format(self.client_address[0]))
                self.request.sendall(str(self.set_output('on')))
            elif str(self.data) == 'output off':
                print 'output off request from', str(format(self.client_address[0]))
                self.request.sendall(str(self.set_output('off')))
            else:
                print 'request string not recognized'
                self.request.sendall(0)
        except Exception as m:
            print 'Error in TCP server handler:', m


class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):   #enable multiple access
    pass


if __name__ == "__main__":
    HOST, PORT = 'ip-address', 9989

    # Create the server, binding to localhost on port 9955
    server = ThreadedTCPServer((HOST, PORT), TCPHandler_Nitrogen)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    print 'Starting server...'
    
    try:
        server.serve_forever()
    finally:
        print 'shut down server'
        server.shutdown()

