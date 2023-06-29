# -*- coding: utf-8 -*-

# qplexkit/server.py is a zmq server that has to run on the Raspberry Pi to
# controll the homemade qplexkit used for DC multiplexing.
# Micha Wildermuth, micha.wildermuth@kit.edu 2023
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

import zmq
from zmq.auth.thread import ThreadAuthenticator
import logging
from qkit.services.qplexkit.qplexkit import qplexkit
from qkit.config.services import cfg

##################################################
### setup zeroMQ-server for qkit communication ###
##################################################
''' run qplexkit '''
qpk = qplexkit()

''' dictionary of '''
msg2cmd = {'set_switch_time': qpk.set_switch_time,
           'get_switch_time': qpk.get_switch_time,
           'set_experiment': qpk.set_experiment,
           'get_experiment': qpk.get_experiment,
           'set_current_divider': qpk.set_current_divider,
           'get_current_divider': qpk.get_current_divider,
           'set_amplifier': qpk.set_amplifier,
           'get_amplifier': qpk.get_amplifier,
           'set_relay': qpk.set_relay,
           'get_relay': qpk.get_relay,
           'get_relays': qpk.get_relays,
           'get_ccr': qpk.get_ccr,
           'read_ccr': qpk.read_ccr,
           'reset': qpk.reset,
           'get_attr': lambda attr, *args, **kwargs: getattr(qpk, attr),
           }

''' run zmq-server '''
if __name__ == "__main__":
    context = zmq.Context()
    # auth = ThreadAuthenticator(context, log=logging.getLogger())
    # auth.allow('localhost')
    # for ip in cfg['qplexkit']['allowed_ip_addresses']:
    #     auth.allow(ip)
    # socket.zap_domain = b'global'
    socket = context.socket(zmq.REP)
    socket.bind(f'''tcp://*:{cfg['qplexkit']['server_port']}''')

    while True:
        fun, args, kwargs = socket.recv_json()
        socket.send_json(msg2cmd[fun](*args, **kwargs))


###################################################
### setup zeroRPC-server for qkit communication ###
###################################################
"""
import zerorpc
_address = cfg['qplexkit_address']
s = zerorpc.Server(qplexkit())
s.bind(_address)
s.run()
"""