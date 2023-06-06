# nitrogen_controller.py by JB@KIT 04/2015 jochen.braumueller@kit.edu
# client script to be run on the control machine (Raspberry Pi) to monitor and control the server (nitrogen_server.py)
# use: execute after starting the server

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

import socket
import sys
import time
import os.path

HOST, PORT = 'ip-address', 9989

def server_request(data_string):
    
    try:
        received = None
        # Create a socket (SOCK_STREAM means a TCP socket)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect to server and send data
        sock.connect((HOST, PORT))
        sock.sendall(data_string + "\n")
        # Receive data from the server and shut down
        received = str(sock.recv(1024))
    finally:
        sock.close()
        return received
        

if __name__ == "__main__":

    if not os.path.isfile('monitor.log'):
        file = open('monitor.log','w')
        file.close()
        
    print 'Start nitrogen refilling controller...'
    with open('monitor.log','a') as f: f.write('\n' + time.ctime() + '   Start nitrogen refilling control script.\n')
    
    controller_status_hist = False
    manual_status = True
    t_start = time.time() + 24*3600
    while True:
        try:
            received = server_request('get_status')
            controller_status = bool(int(received[0]))
            if controller_status != controller_status_hist:   #status change
                s = time.ctime() + ':   status change   ' + received
                print s
                with open('monitor.log','a') as f: f.write(s + '\n')   #append to log
                controller_status_hist = controller_status
                
                if controller_status:   #switched on
                    t_start = time.time()   #reset timer

            if (time.time() - t_start) > 60 * 60 and controller_status and manual_status:   # >60min refilling
                x = server_request('output off')
                s = time.ctime() + ':   refilling longer than 60min -> switch off'
                print s
                with open('monitor.log','a') as f: f.write(s + '\n')   #append to log
                manual_status = False
            if not manual_status and not controller_status:   #when automation wants to switch off
                x = server_request('output on')
                s = time.ctime() + ':   automation switch off -> deactivate manual off'
                print s
                with open('monitor.log','a') as f: f.write(s + '\n')   #append to log
                manual_status = True
            time.sleep(10)
        except Exception as e:
            print e