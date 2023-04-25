# zmq based info_service 
# HR@KIT/2017,2018


import zmq
import time
import logging
import qkit
from qkit.core.lib.com.signals import SIGNALS


class info_service(object):
    def __init__(self,host = None, port = None):
        if host:
            self.host = host
        else:
            self.host = qkit.cfg.get('info_host','localhost')
            
        if port:
            self.port = port
        else:
            self.port = qkit.cfg.get('info_port',5600)
            
        self.start_service(self.host,self.port)
    def start_service(self,host,port):
        socket_bound = False
        for newport in range(port,port+20):
            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.PUB)
            try:
                self.socket.bind("tcp://*:%s" % newport)
                qkit.cfg['info_port'] = newport
                qkit.cfg['info_host'] = host
                socket_bound = True
                break
            except zmq.ZMQError:
                self.context.destroy()
        if not socket_bound:
            logging.warning("Info service: address/port in use: ZMQError. \nMaybe more than 20 instances of QKIT are running?")
            logging.warning("Not starting info service.")
            
        #zmq.ZMQError.errno
        # wait until zmq is settled
        time.sleep(0.3)
    
        
    def dist(self,topic, message = ""):
        "distribute a message"
        if SIGNALS.has_key(topic):
            sig = SIGNALS.get(topic)
            self.socket.send("%d:%s" % (sig, message))
        else:
            print("please specify a correct topic, specs are in SIGNALS.py")

    def info(self,message):
        self.dist('info',message)
        
    def emit(self,topic,message):
        "distribute a message to a topic(), message can be omitted"
        self.dist(topic,message)
        
    

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        msg =  sys.argv[1]
    else: msg = ""
    
    ifs = info_service()
    
    ifs.info(msg)
    ifs.dist('reload',"quick!!! "+msg)
    
