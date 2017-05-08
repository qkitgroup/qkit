# remote_python.py, TCP/IP client/server to allow eval()ing in a remote
# python interpreter running a gtk mainloop
# Reinier Heeres <reinier@heeres.eu>, 2009
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

import logging
from lib.network import tcpserver, tcpclient
import qt

PORT = 12000

class PythonServer(tcpserver.GlibTCPHandler):
    """
    Run a TCP/IP server that runs/evaluates all data it receives in the
    python interpreter using eval() calls.
    The result is written back to the socket.
    """

    def handle(self, data):
        data = data.strip()
        if len(data) == 0:
            return

        try:
            retval = eval(data, globals(), globals())
        except Exception, e:
            retval = str(e)

        self.socket.send(str(retval))

class PythonClient(tcpclient.TCPClient):
    """
    Client to connect to a TCP/IP Python eval server (or anything else
    actually).
    """

    def __init__(self, host, port=PORT):
        tcpclient.TCPClient.__init__(self, host, port)

    def cmd(self, cmd):
        self.send(cmd)
        data = self.recv(8192, 1)
        return data

    def live(self):
        print 'Entering remote python live mode, enter CTRL-d to quit'
        while True:
            try:
                input = raw_input('>>>')
            except EOFError:
                return
            reply = self.cmd(input)
            print reply

def start_server(port=PORT):
    try:
        qt.server_python = tcpserver.GlibTCPServer(('', port), \
                PythonServer)
    except Exception, e:
        logging.warning('Failed to start python server: %s', str(e))
