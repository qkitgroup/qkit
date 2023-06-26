# refilling_switch_off.py by JB@KIT 12/2015 jochen.braumueller@kit.edu
# client script to be run on the control machine (Raspberry Pi) to switch on nitrogen refilling, server script needs to be running
# use: only from remote as emergency

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
        # Create a socket (SOCK_STREAM means a TCP socket)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect to server and send data
        sock.connect((HOST, PORT))
        sock.sendall(data_string + "\n")
        # Receive data from the server and shut down
        received = str(sock.recv(1024))
    finally:
        sock.close()
        #print 'hallo', received
        return received

if __name__ == "__main__":

    print 'Switching off nitrogen refilling...'
    x = server_request('output off')
    s = time.ctime() + ':   manual off by separate client script - switch off'
    try:
        with open('monitor.log','a') as f: f.write(s + '\n')   #append to log
    except Exception:
        print 'Warning: No log entry written.'
    print 'Testing...'
    time.sleep(1)
    if not bool(int(server_request('get_status')[0])):
        print 'Successful.'
    else:
        print 'WARNING: Switching off not successful'
