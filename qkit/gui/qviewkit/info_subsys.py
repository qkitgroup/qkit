# zmq  qkit info client, runs in a separate thread
# HR@KIT/2017


import zmq
import qkit
from qkit.core.lib.com.signals import SIGNALS

from threading import Thread
import time,sys

from qkit.core.lib.com.info_client import info_client


class info_thread(Thread):
   def __init__(self, data):
      Thread.__init__(self)
      self.data = data
      self.ifc = info_client()
      self.ifc.listen_to_all()
      self.data.set_info_thread_continue(True)
      
   def run(self):
      while self.data.info_thread_continue:
        socks = dict(self.ifc.poller.poll(1000))# wait 1s
        if self.ifc.socket in socks and socks[self.ifc.socket] == zmq.POLLIN:
            tid, message = self.ifc.get_message()
            print(message,tid)
            if int(tid)  == SIGNALS.get('close-gui'):
                print("received close gui signal")
                self.data.set_info_thread_continue(False)
                self.data.close_all()

        time.sleep(0.01)



if __name__ == "__main__":
    if len(sys.argv) > 1:
        host =  int(sys.argv[1])
        port =  int(sys.argv[2])
        ifc = info_client(host,port)
    else:
        ifc = info_client()
    ifc.listen_to_all()
    for i in range(10):
        ifc.print_message()
