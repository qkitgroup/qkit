#!/usr/bin/env python
#TIP main, version 0.2 written by HR@KIT Feb 2011
# TIP Is not Precious
import ConfigParser
import lib.tip_pidcontrol as tip_pidcontrol
import sys,time
import argparse

from lib.tip_dev import *

from lib.tip_data import DATA

# server thread to spread information
import server.tip_srv_thread as tip_srv


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TIP Is not Perfect // HR@KIT 2011")

    parser.add_argument('ConfigFile', nargs='?', default='settings.cfg',
                        help='Configuration file name')
    args=parser.parse_args()
    
    Conf = ConfigParser.RawConfigParser()
    Conf.read(args.ConfigFile)
    
    DATA = DATA(Conf)
    DATA.config = Conf

    PID = tip_pidcontrol.pidcontrol(DATA)
    DATA.PID = PID

    IO = IO_worker(DATA) 
    IO.setDaemon(1)
    IO.start()
    
    tipserv = tip_srv.tip_srv(DATA)
    tipserv.loop()

