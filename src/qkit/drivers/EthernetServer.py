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

# TO DO
# - cleanup/timeout of registered listeners
#
#

from qkit.core.instrument_base import Instrument
import types
import logging
# comms and byte packing
import threading
import socket
import dpkt
import struct
# ip filter
import re

class EthernetServer(Instrument):
    '''
    This instrument passes packets between UDP and Ethernet, to talk to GHZdac devices.

    Usage:
    Initialize with
    <name> = qt.instruments.create('name', 'EthernetServer', interface='<interface name>', ethertype=<ethertype>, ip_host=<ip_host>, ip_port=<ip_port>)
    <interface name> = name of the raw packet network interface
    <ethertype> = 0x0003 (ETH_P_ALL, receive all packets) or any other EtherType value
    <ip_host>:<ip_port> = 127.0.0.1:413 to bind the UDP interface to
    '''

    # broadcast address
    MAC_BROADCAST = struct.pack('>6B', *[0xff, 0xff, 0xff, 0xff, 0xff, 0xff])
    # capture all packets ethertype
    ETH_P_ALL = 0x0003
    # maximum packet size
    RECV_SIZE = 2048

    def __init__(self, name, interface, ethertype = 0x0003, ip_host = '127.0.0.1', ip_port = 413, ip_filter = ''):
        '''
        Initializes the UDP-to-Ethernet bridge

        Input:
            name (string)    : name of the instrument
            interface (string) : raw ethernet network interface
            ethertype : ethernet frame type to receive
            ip_host:ip_port : UDP interface address
            ip_filter : regular expression used to match incoming packets against

        Output:
            None
        '''
        logging.debug(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])

        self._interface = interface
        self._ethertype = int(ethertype)
        self._ip_host = ip_host
        self._ip_port = int(ip_port)
        self.do_set_ip_filter(ip_filter)
        self._clients = {} # associate MAC addresses with udp clients
        self._devices = set() # mac addresses seen on the raw interface
        self._updateLock = threading.Lock()

        # add parameters
        self.add_parameter('interface', type=str, flags=Instrument.FLAG_GET)
        self.add_parameter('MAC', type=str, flags=Instrument.FLAG_GET)
        self.add_parameter('ethertype', type=int, flags=Instrument.FLAG_GET)
        self.add_parameter('ip_host', type=str, flags=Instrument.FLAG_GET)
        self.add_parameter('ip_port', type=int, flags=Instrument.FLAG_GET)
        self.add_parameter('ip_filter', type=str, flags=Instrument.FLAG_GETSET)
        self.add_parameter('devices', type=types.ListType, flags=Instrument.FLAG_GET)
        self.add_parameter('listeners', type=types.ListType, flags=Instrument.FLAG_GET)
        self.add_parameter('raw_rcvbuf', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('udp_rcvbuf', type=int, flags=Instrument.FLAG_GETSET)
        self.add_function('get_all')

        # open sockets
        self._init_udp()
        self._init_raw()

        # update ui
        self.get_all()

        # start daemons
        self._udp_receiver = self.udp_receiver(self)
        self._udp_receiver.daemon = True
        self._udp_receiver.start()
        self._raw_receiver = self.raw_receiver(self)
        self._raw_receiver.daemon = True
        self._raw_receiver.start()

    def __del__(self):
        '''
        clean up
        '''
        self._udp_socket.close()
        self._raw_socket.close()

    class udp_receiver(threading.Thread):
        '''
        receive client requests
        '''
        def __init__(self, node):
            threading.Thread.__init__(self, name = 'node_udp')
            self.node = node

        def run(self):
            logging.debug(self.name + ' : udp listener started.')
            while(True):
                # receive packet (ethernet packet in the payload of an UDP packet)
                (raw_packet, sender) = self.node._udp_socket.recvfrom(self.node.RECV_SIZE)
                packet = dpkt.ethernet.Ethernet(raw_packet)
                logging.debug(self.name + ' : udp packet received.')
                # source filtering
                if(not self.node._ip_filter(sender)):
                    logging.debug(self.name + ' : udp packet from %s discarded.'%sender[0])
                    continue
                # add this connection to the listeners of a specific device MAC
                if(packet.dst not in self.node._clients):
                    self.node._updateLock.acquire(True)
                    if(packet.dst not in self.node._clients):
                        self.node._clients[packet.dst] = set()
                    self.node._updateLock.release()
                if(sender not in self.node._clients[packet.dst]):
                    self.node._clients[packet.dst].add(sender)
                # dispatch to raw socket
                packet.src = self.node._MAC
                self.node._raw_socket.send(packet.pack())

    class raw_receiver(threading.Thread):
        '''
        receive raw network packets
        '''
        def __init__(self, node):
            threading.Thread.__init__(self, name = 'node_raw')
            self.node = node

        def run(self):
            logging.debug(self.name + ' : raw listener started.')
            while(True):
                # receive packet (ethernet packet)
                (raw_packet, sender) = self.node._raw_socket.recvfrom(self.node.RECV_SIZE)
                packet = dpkt.ethernet.Ethernet(raw_packet)
                logging.debug(self.name + ' : raw packet received.')
                self.node._devices.add(packet.src)
                # dispatch to all listeners
                for client_list in [self.node._clients.get(packet.src, None), self.node._clients.get(self.node.MAC_BROADCAST, None)]:
                    if(client_list == None): continue
                    for client in client_list:
                        self.node._udp_socket.sendto(raw_packet, client)

    def _init_udp(self):
        # open udp socket
        logging.debug(__name__ + ' : Listening for packets on %s:%d.'%(self._ip_host, self._ip_port))
        self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._udp_socket.bind((self._ip_host, self._ip_port))

    def _init_raw(self):
        # open raw socket
        if(self._ethertype == self.ETH_P_ALL):
            logging.info(__name__ + ' : EtherType set to ETH_P_ALL, this may generate high CPU load')
	    self._raw_socket = socket.socket(socket.PF_PACKET, socket.SOCK_RAW, self._ethertype)
        self._raw_socket.bind((self._interface, self._ethertype))
        self._MAC = self._raw_socket.getsockname()[4]

    def get_all(self):
        ''' call all getters to update the ui '''
        self.get_interface()
        self.get_MAC()
        self.get_ethertype()
        self.get_ip_host()
        self.get_ip_port()
        self.get_ip_filter()
        self.get_udp_rcvbuf()
        self.get_raw_rcvbuf()

        self.get_listeners()
        self.get_devices()

    def do_get_interface(self):
        ''' return name of the network interface used '''
        return self._interface

    def do_get_MAC(self):
        ''' return own MAC address '''
        return '%02x:%02x:%02x:%02x:%02x:%02x'%(struct.unpack('>6B', self._MAC))
 
    def do_get_ethertype(self):
        ''' return packet type received '''
        return self._ethertype

    def do_get_ip_host(self):
        ''' return hostname of the udp socket '''
        return self._ip_host

    def do_get_ip_port(self):
        ''' return port number of the udp socket '''
        return self._ip_port

    def do_set_ip_filter(self, expr):
        ''' udp source filter (regular) expression '''
        if(expr):
            self._ip_filter_expr = expr
            self._ip_filter = re.compile(expr).match
        else:
            self._ip_filter_expr = ''
            self._ip_filter = lambda s: True

    def do_get_ip_filter(self):
        ''' return udp source filter expression '''
        return self._ip_filter_expr

    def do_get_listeners(self):
        ''' return list of udp clients '''
        # gather list of clients in <ip>:<port> format
        listeners = []
        for client_list in self._clients.values():
            listeners.append(['%s:%d'%(x[0], x[1]) for x in list(client_list)])
        # remove duplicates
        return list(set(listeners))

    def do_get_devices(self):
        ''' return list of seen devices '''
        #return self._clients.keys()
        return list(self._devices)

    def do_set_raw_rcvbuf(self, bufsize):
        ''' set the receive buffer size of the raw socket '''
        self._raw_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, int(bufsize))

    def do_get_raw_rcvbuf(self):
        ''' get the receive buffer size of the raw socket '''
        return self._raw_socket.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)

    def do_set_udp_rcvbuf(self, bufsize):
        ''' set the receive buffer size of the raw socket '''
        self._udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, int(bufsize))

    def do_get_udp_rcvbuf(self):
        ''' get the receive buffer size of the raw socket '''
        return self._udp_socket.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)

