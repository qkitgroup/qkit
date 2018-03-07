# -*- coding: utf-8 -*-
"""
Remote interface client (RIC) to access the RI service or any zerorpc service


@author: HR@KIT 2018
"""
import qkit

#import logging # the logging mechanism does not work here, since qkit is not started

def __update_tab(ric):
    # try to be smart and add the remote functions to the __dict__ for tabbing in ipython
    rflist = ric._zerorpc_list()
    for f in rflist: 
        ric.__dict__.update({f:getattr(ric,f)})

def __getdoc():
    return _zerorpc_help
    
    
def start_ric(host = None,port = None):
    import zerorpc
    """
    starts a remote interface client (ric)
    to a 
        host = host (default =  localhost)
    at a 
        port  = port (default =  5700)
    
    ric is based on zerorpc, so every zerorpc server should be accessible
    
    """
    ric = zerorpc.Client(); 
    if not host:
        host = qkit.cfg.get("ris_host","127.0.0.1")
    if not port:
        port = qkit.cfg.get("ris_port",5700)
    print("starting ric client on host %s and port %s" % (host,port))
    ric.connect("tcp://" + host + ":" + str(port))
    
    qkit.ric = ric    
    __update_tab(ric)
    
    return ric

"""
list of internal functions
_zerorpc_list to list calls
_zerorpc_name to know who you’re talking to
_zerorpc_ping (redundant with the previous one)
_zerorpc_help to retrieve the docstring of a call
_zerorpc_args to retrieve the argspec of a call
_zerorpc_inspect to retrieve everything at once
"""