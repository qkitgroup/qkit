# -*- coding: utf-8 -*-
"""
Remote interface client (RIC) to access the RI service or any zerorpc service


@author: HR@KIT 2018
"""

import qkit
import zerorpc

ric = zerorpc.Client(); 
host = qkit.cfg.get("ris_host","127.0.0.1")
port = str(qkit.cfg.get("ris_port",5700))

ric.connect("tcp://"+host+":"+port)

# try to be smart and add the remote functions to the __dict__ for tabbing in ipython
rflist = ric._zerorpc_list()
for f in rflist: 
    ric.__dict__.update({f:getattr(ric,f)})

qkit.ric = ric
    
"""
list of internal functions
_zerorpc_list to list calls
_zerorpc_name to know who you’re talking to
_zerorpc_ping (redundant with the previous one)
_zerorpc_help to retrieve the docstring of a call
_zerorpc_args to retrieve the argspec of a call
_zerorpc_inspect to retrieve everything at once
"""