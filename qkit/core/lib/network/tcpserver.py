# network.py, functions for tcp/ip client/server integration with glib.
# Based on network.py from Sugar, Copyright (C) 2006-2007 Red Hat, Inc.
# Extended by Reinier Heeres for the QT Lab environment, (C)2008
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import gobject
import SocketServer
import socket
import time
import re
import logging

class GlibTCPServer():
    """GlibTCPServer

    Integrate socket accept into glib mainloop.
    """

    allow_reuse_address = True
    request_queue_size = 20

    def __init__(self, server_address, handler_class, allowed_ip=None):
        self._handler_class = handler_class
        self._allowed_ips = []
        if allowed_ip:
            self.add_allowed_ip(allowed_ip)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(server_address)
        self.socket.setblocking(0)  # Set nonblocking

        # Watch the listener socket for data
        gobject.io_add_watch(self.socket, gobject.IO_IN, self._handle_accept)
        self.socket.listen(1)

    def close(self):
        self.socket.close()

    def _handle_accept(self, source, condition):
        """Process incoming data on the server's socket by doing an accept()
        via handle_request()."""

        if not (condition & gobject.IO_IN):
            return True

        sock, addr = self.socket.accept()
        if not self.allow_client(addr[0]):
            logging.warning('Not allowing connection from %s', addr)
            sock.close()
            return
        logging.info('Allowing connection from %s', addr)

        handler = self._handler_class(sock, addr, self)
        return True

    def close_request(self, request):
        """Called to clean up an individual request."""
        pass

    def add_allowed_ip(self, ip_regexp):
        print 'Adding %s' % ip_regexp
        self._allowed_ips.append(re.compile(ip_regexp))

    def allow_client(self, client):
        for regexp in self._allowed_ips:
            m = regexp.match(client)
            return True
        return False

class GlibTCPHandler():
    '''
    Class to do asynchronous request handling integrated with GTK mainloop.
    '''

    BUFSIZE = 4096

    def __init__(self, sock, client_address, server, packet_len=False):
        '''
        If packet_len is True, the first 2 bytes received are expected to
        contain the packet length. The receive function will block until the
        whole packet is ready.
        '''

        if not isinstance(sock, socket.socket):
            raise ValueError('Only stream sockets supported')

        self._packet_len = packet_len
        self.socket = sock
        self.client_address = client_address
        self.server = server

        self.socket.setblocking(0)
        self._in_hid = None
        self._hup_hid = None
        # There seems to be an issue on Windows with the following...
        # self._hup_hid = gobject.io_add_watch(self.socket, \
        #    gobject.IO_ERR | gobject.IO_HUP, self._handle_hup)

        self.enable_callbacks()

    def enable_callbacks(self):
        if self._in_hid is not None:
            return
        self._in_hid = gobject.io_add_watch(self.socket, \
            gobject.IO_IN, self._handle_recv)

    def disable_callbacks(self):
        if self._in_hid is None:
            return
        gobject.source_remove(self._in_hid)
        self._in_hid = None

    def _handle_recv(self, socket, number):
        try:
            data = socket.recv(self.BUFSIZE)
        except Exception, e:
            # No data anyway...
            return True

        if len(data) == 0:
            self._handle_hup()
            return False
        else:
            self.handle(data)
            return True

        return True

    def _handle_hup(self, *args):
        if self._in_hid is not None:
            gobject.source_remove(self._in_hid)
            self._in_hid = None
        if self._hup_hid is not None:
            gobject.source_remove(self._hup_hid)
            self._hup_hid = None
        return False

    def handle(self, data):
        '''Override this function to handle actual data.'''
        print 'Data: %s, self: %r' % (data, repr(self))
        time.sleep(0.1)

    def finish(self):
        return

