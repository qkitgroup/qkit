# -*- coding: utf-8 -*-
"""
Remote interface service (RIS) for QKIT

The service forks a zerorpc RPC server in a separate thread. 
zerorpc manages incoming RPC requests concurrently on functions defined in QKIT_visible()
@author: HR@KIT 2018

#################################################################################
WARNING: Be careful in exposing new functions here:

The call may interrupt a running measurement or cause other race conditions.
Make sure the function is either GIL threadsave (atomic or builtin functions) or 
properly made threadsave by threading.Lock or similar.
#################################################################################

"""
import qkit
import threading
import zmq
import zerorpc
import logging

class flow(object):
    def stop_measure(self):
        return qkit.flow.stop()
    def hallo(self):
        return "hallo"

class QKIT_visible(object):
    """ Various convenience methods. """
    def __init__(self):
        self.flow = flow
    def __call__(self, func):
        return eval(func)

    def get_cfg(self):
        "returns the qkit.cfg dict"
        return qkit.cfg
    def get_current(self):
        pass
        #return qkit.last[-1]
    def get_last(self):
        pass
        #return qkit.last[-2]
    def stop_measure(self):
        pass
        #return qkit.flow.stop()
    def ex(self,func):
        if qkit.cfg.get("ris_debug",False):
            return eval(func)
        else:
            return False
    
    def get_instruments(self):
        return qkit.instruments.get_instrument_names()
    def get_instrument_param(selfs,instrument,parameter):
        return qkit.instruments.get(instrument).get(parameter)
    def get_all_instrument_params(self):
        return_dict = {}
        for ins in qkit.instruments.get_instruments().values():
            param_dict = {}
            for param in ins.get_parameter_names():
                param_dict.update({param: [ins.get(param, query=False), ins.get_parameter_options(param).get('units', "")]})
            return_dict.update({ins.get_name(): param_dict})
        return return_dict


class RISThread(object):
    def __init__(self):
        self.ris = ""
        logging.info(__name__+"starting RIS ...")
        thread = threading.Thread(target=self.run, name="ris", args=())
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution
    def run(self):
        
        host = qkit.cfg.get("ris_host","127.0.0.1")
        port = int(qkit.cfg.get("ris_port",5700))
        socket_bound = False
        for newport in range(port,port+20):
            try:
                self.ris = zerorpc.Server(QKIT_visible())
                self.ris.bind("tcp://%s:%d"%(host,newport))
                host = qkit.cfg.get("ris_host","127.0.0.1")
                qkit.cfg["ris_host"] = host
                qkit.cfg["ris_port"] = newport
                socket_bound = True
                break
            except zmq.ZMQError as e:
                logging.debug(e)
                socket_bound = False
                self.ris.stop()
                del self.ris
        if not socket_bound:
            logging.warning("RIS: address/port in use: ZMQError. \nMaybe another 20 instances of QKIT are running?")
            logging.warning("Not starting RIS.")
            return False
        # run the thread
        self.ris.run()
    def stop(self):
            try:
                self.ris.stop()
            except:
                pass

if __name__ == "__main__":
    RIS = RISThread()
