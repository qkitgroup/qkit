#!/usr/bin/env python
# srv_thread.py

# RP(Y)C factory object  for QKIT, written by HR,JB@KIT 2016

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


import time
import sys
import logging
#import numpy

import rpyc
from rpyc.utils.server import ThreadedServer

DEBUG = False 
def logstr(logstring):
    if DEBUG:
        print(str(logstring))

#global wants_abort
wants_abort = False

# the following trick allows to pass an Object (DATA) to a factory class (rpc.Service)
# witout overriding the __init__() function. Basically a closure defines the namespace
# and passes the object.
 
def CustomizedService(DATA):
    class Plasma1Service(rpyc.Service):
    
        def on_connect(self):
            # code that runs when a connection is created
            print 'New connection with %s initiated.'%str(self._conn._config['endpoints'][1])
    
        def on_disconnect(self):
            # code that runs when the connection has already closed
            print 'Connection to %s closed.'%str(self._conn._config['endpoints'][1])
            
        def exposed_get_history(self,p,range):   #range in hours
            if DATA.debug: print 'history request from client %s'%str(self._conn._config['endpoints'][1])
            return getattr(DATA,str(p)).get_history(range)
            
        def exposed_get_last_value(self,p):
            if DATA.debug: print 'value request'
            return [getattr(DATA,str(p)).get_timestamp(),getattr(DATA,str(p)).get_last_value()]
            
    return Plasma1Service

def remote_service_operator(DATA):
        """
        starts the (threaded) service which exposes the 
        RPYC_service factory class to remote RPYC clients.
            
        This is the function which should be called in the main function,
        there is no need for hiding it in a class.
        """
        CS  = CustomizedService(DATA)
        t = ThreadedServer(CS, port = DATA.localhost.port)#, protocol_config = {"allow_public_attrs" : True})
        t.start()

class MyTestObject(object):
    def __init__(self):
        self.a = 'string'
        
if __name__ == "__main__":
    """
    logic of operation:
    * init DATA
    * start remote service operator
    * start data_srv 
    """
    o = MyTestObject()
    o.test=lambda: 1
    rso = remote_service_operator(o)
