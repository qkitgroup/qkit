# This instrument transmits and receives raw ethernet packets to and from 
# a network interface. It is used to communicate with GHZdac devices.
# Markus Jerger <jerger@kit.edu>, 2011
#
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

from qkit.core.instrument_base import Instrument
import socket
import struct
import threading
try:
    import Queue
except ImportError:
    import queue as Queue

import types
import logging

class EthernetNode(Instrument):
    '''
    This instrument sends and receives ethernet packets (layer 2), to talk to GHZdac devices.

    Usage:
    Initialize with
    <name> = instruments.create('name', 'EthernetNode', interface='<interface name>', ethertype=<ethertype>)
    <interface name> = eth1
    <ethertype> = 0x0003 (ETH_P_ALL, receive all packets) or any other EtherType value
    '''

    # capture all packets ethertype
    ETH_P_ALL = 0x0003

    def __init__(self, name, interface, ethertype):
        '''
        Initializes the Oxford Instruments Kelvinox IGH Dilution Refrigerator.

        Input:
            name (string)    : name of the instrument
            interface (string) : label of the network interface used

        Output:
            None
        '''
        logging.debug(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])

        self._interface = interface
        self._ethertype = int(ethertype)
        self._queues = {}
        self._monitor = None # will receive all packets if set to a Queue object
        self._receiver = self.receiver(name = 'node_rx', args = (self))
        self._receiver.daemon = True
        self._updateLock = threading.Lock()

        #Add parameters
        self.add_parameter('interface', type=str, flags=Instrument.FLAG_GET)
        self.add_parameter('ethertype', type=int, flags=Instrument.FLAG_GET)
        self.add_parameter('MACs', type=types.ListType, flags=Instrument.FLAG_GET)
        self.add_parameter('rcvbuf', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('monitoring', type.bool, flags.Instrument.FLAG_GETSET)

        # Add functions
        self.add_function('register')
        self.add_function('unregister')
        self.add_function('monitor')
        self.add_function('send')

        # open socket
        self._init()


    class listener(threading.Thread):
        '''
        listen for incoming connections
        '''

    class receiver(threading.Thread):
        '''
        receives network packets and sorts them into the appropriate queue
        '''
        def run(self, node):
            while(True):
                # receive packet
                (packet, sender) = node._socket.recvfrom(2048)
                # sort into queue
                node._updateLock.acquire(blocking = True)
                queue = node._queues.get(sender)
                if(queue != None)
                    queue.put(packet)
                if(node._monitor != None):
                    node._monitor.put((sender, packet))
                node._updateLock.release()

    def _init(self):
        # open receiving socket
	    if(self._ethertype == self.ETH_P_ALL):
            logging.info(__name__ + ' : EtherType set to ETH_P_ALL, this may generate high CPU load')
	    self._socket = socket.socket(socket.PF_PACKET, socket.SOCK_RAW, self._ethertype)
        self._socket.bind((self._interface, self._ethertype))

        # determine default buffer size
        self.get_rcvbuf()

    def _MAC(self, MACin):
        '''
            convert mac address to byte string
            expected input format is 01:23:45:67:89:AB
        '''
        # split input and convert the parts to ints
        MAC = [int(byte, base = 16) for byte in str(MACin).split(':')]
        # merge the parts into a byte string
        return struct.pack('>6B', *MAC)

    def register(self, MAC):
        '''
        register a new DAC device with the server

        Input:
            MAC address
        Output:
            queue object
        '''
        MACkey = self._MAC(MAC)
        self._updateLock.acquire(blocking = True)
        if(not self._queues.has_key(MACkey)):
            logging.info(__name__ + ' : registering new device %s.'%MAC)
            self._queues[MACkey] = Queue.Queue()
        self._updateLock.release()
        return self._queues[MACkey]

    def unregister(self, MAC):
        '''
        unregister a DAC device from the server

        Input:
            MAC address
        Output:
            none
        '''
        MACkey = self._MAC(MAC)
        self._updateLock.acquire(blocking = True)
        if(self._queues.has_key(MACkey)):
            logging.info(__name__ + ' : unregistering device %s.'%MAC)
            self._queues.pop(MACkey)
        self._updateLock.release()

    def monitor(self):
        '''
        return monitor Queue
        '''
        return self._monitor

    def send(self, MAC, data)
        MACkey = self._MAC(MAC)
        self._socket.send(data)


    def do_get_interface(self):
        ''' return name of the network interface used '''
        return self._interface

    def do_get_ethertype(self):
        ''' return packet type received '''
        return self._ethertype

    def do_get_MACs(self):
        ''' return list of registered devices '''
        return self._queues.keys()

    def do_set_rcvbuf(self, bufsize):
        ''' set the receive buffer size of the socket; note that the size of the individual receive queues is unrelated '''
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, int(bufsize))

    def do_get_rcvbuf(self):
        ''' get the receive buffer size of the socket '''
        return self._socket.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)

    def do_set_monitoring(self, status):
        ''' enable or disable monitoring '''
        if(status == True):
            logging.debug(__name__ + ' : monitoring enabled')
            self._monitor = threading.Queue()
        else:
            logging.debug(__name__ + ' : monitoring disabled')
            self._monitor = None

    def do_get_monitoring(self):
        ''' check if monitoring is enabled '''
        return self._monitor != None
