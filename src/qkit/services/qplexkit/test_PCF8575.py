# -*- coding: utf-8 -*-

# MMW@KIT
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

"""
References
----------
https://pypi.org/project/pcf8575/

Installation
------------
sudo apt-get update
sudo apt-get install python-rpi.gpio
sudo apt-get install libffi-dev
pip install pcf8575
"""

import sys
sys.path.append("/home/superuser/qkit/src")
import zmq
from qkit.config.services import cfg
import time
import logging
import os
import json

try:
    from pcf8575 import PCF8575
except ModuleNotFoundError:
    logging.warning('qplexkit: Module PCF8575 for I2C-expander not found. Use dummy instead that just supports software debugging but no control of the qplexkit at all.')
    class PCF8575(object):
        def __init__(self, i2c_bus_no, address):
            print(i2c_bus_no, address)
            self.port = 16 * [True]


class qplexkit(object):
    def __init__(self):
        self.pcf = PCF8575(i2c_bus_no=1, address=0x21)

    def set_port(self, port, status):
        self.pcf.port[port] = status
        print(f'set port {port} to {status}')
        return

    def get_port(self, port):
        print(f'get port {port}')
        return self.pcf.port[port]


qpk = qplexkit()

msg2cmd = {'set_port': qpk.set_port,
           'get_port': qpk.get_port,
           'get_attr': lambda attr, *args, **kwargs: getattr(qpk, attr),
           }


''' run zmq-server '''
if __name__ == "__main__":
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f'''tcp://*:{cfg['qplexkit']['server_port']}''')

    while True:
        fun, args, kwargs = socket.recv_json()
        socket.send_json(msg2cmd[fun](*args, **kwargs))


