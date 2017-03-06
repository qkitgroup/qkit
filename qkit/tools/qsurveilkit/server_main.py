#!/usr/bin/env python
# server_main.py

# logging/monitoring server main file, version 1.0 written by HR,JB@KIT 2011, 2016

'''
requires a 'settings.cfg' file in the working directory
'''

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


import ConfigParser
import sys#,time
import argparse
import atexit

#import random

#from threading import Thread

from worker import IO_worker
from data_class import DATA
import srv_thread as srv   # server thread to spread information

# --- instrument readout drivers ---
sys.path.append('../evaporate/lib')
from er_MKS_PDR900 import Pressure_Dev


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Derived from TIP v0.1 (HR@KIT 2011), updated and generalized by HR,JB@KIT 2016")

    parser.add_argument('ConfigFile', nargs='?', default='settings.cfg',
                        help='Configuration file name')
    args=parser.parse_args()
    
    Conf = ConfigParser.RawConfigParser()
    Conf.read(args.ConfigFile)
    
    DATA = DATA(Conf)
    DATA.config = Conf
    
    #specify data request objects
    # --- use objects names according to entry names in settings.cfg
    pLL = Pressure_Dev('LL')
    DATA.pLL.data_request_object = pLL.getPressure
    pMC = Pressure_Dev('MC')
    DATA.pMC.data_request_object = pMC.getPressure
    
    atexit.register(DATA.atexit)
    
    #DATA.pLL.store_value(3)
    
    
    try:
        IO = IO_worker(DATA) 
        IO.setDaemon(1)
        IO.start()
        
        srv.remote_service_operator(DATA)
        
    except KeyboardInterrupt:
        print "tip.py: Exiting tip.py"
        DATA.set_wants_abort()
        #dserv.server.shutdown()
        exit()
