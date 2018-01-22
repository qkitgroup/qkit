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
        return qkit.last[-1]
    def get_last(self):
        return qkit.last[-2]
    def stop_measure(self):
        return qkit.flow.stop()
    def ex(self,func):
        if qkit.cfg.get("ris_debug",False):
            return eval(func)
        else:
            return False


class RISThread(object):
    def __init__(self):
        self.ris = ""
        logging.info(__name__+"starting RIS ...")
        thread = threading.Thread(target=self.run, name="ris", args=())
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution
    def run(self):
        self.ris = zerorpc.Server(QKIT_visible())
        host = qkit.cfg.get("ris_host","127.0.0.1")
        port = str(qkit.cfg.get("ris_port",5700))
        self.ris.bind("tcp://"+host+":"+port)
        self.ris.run()
    def stop(self):
            try:
                self.ris.stop()
            except:
                pass

if __name__ == "__main__":
    RIS = RISThread()
