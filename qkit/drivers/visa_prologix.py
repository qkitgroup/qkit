#!/usr/bin/env python
"""
GPIB_ETHERNET python class for prologix ethernet-to-gpib bridge, 
written by Hannes Rotzinger, hannes.rotzinger@kit.edu for qtlab, qtlab.sf.net

interfaces GPIB commands over ethernet

released under the GPL, whatever version

Changelog:
0.1 March 2010, initial version, very alpha, most of the functionality is far from bullet proof.

0.2 June 2012 added master/slave capability and multi-device support -- by Jochen Zimmer

"""

import socket
import time
import re

class instrument(object):
    """ for prologix gpib_ethernet bridge """

    N_prologix_adapters = 0  # number of adapters
    l_IPs = []         # IPs of the adapters controlled by this driver
    l_p_master = []    # master object for adapter i

    def __init__(self,gpib,**kwargs):

        self.sock = None
        
        # for compatibility with NI visa
        self.timeout = kwargs.get("timeout",5)
        self.chunk_size = kwargs.get("chunk_size",20*1024)
        self.values_format = kwargs.get("values_format",'ascii') # fixme: single, double
        self.term_char = kwargs.get("term_char",'\n')
        self.send_end = kwargs.get("send_end",True)
        self.delay = kwargs.get("delay",0)
        self.lock = kwargs.get("lock",False)
        
        # parse gpib address (throws an Error() if fails)
        self.gpib_addr=self._get_gpib_adr_from_string(gpib)
        
        # IP address and port of  PROLOGIX GPIB-ETHERNET
        self.ip = kwargs.get("ip","192.168.0.100")
        self.ethernet_port = kwargs.get("port", 1234)

        self.p_master = None

        for i in range(instrument.N_prologix_adapters):
            if self.ip == instrument.l_IPs[i]:
                # print "Found a slave: %s, %i" % (self.ip, self.gpib_addr)
                self.is_master = False
                self.p_master = instrument.l_p_master[i]
        if self.p_master == None:
            # print "Found a master: %s, %i" % (self.ip, self.gpib_addr)
            instrument.N_prologix_adapters += 1
            instrument.l_IPs.append(self.ip)
            self.is_master = True
            instrument.l_p_master.append(self)
            self.p_master = self

#       self.gpib_addr

        if self.is_master:
            # open connection
            self._open_connection()

            if self.send_end:
                    self.term_char = '\n'
                    self._set_EOI_assert()

            # disable the automatic saving of parameters in
            # the ethernet-gpib device,

            #self._set_saveconfig(False) ## deactivated because it caused an unknown error in the new devices
            
            # set set the ethernet gpib device to be the controller of#
            # the gpib chain
            self._set_controller_mode()
            # set the GPIB address of the device
            self._set_gpib_address()
            
            self._set_EOI_assert()
            self._set_read_timeout()
            self._set_read_after_write(False)
            #self._dump_internal_vars()

    # wrapper functions for py visa, generalized for master/slave
    def write(self,cmd):
        self.p_master._send("++addr " + str(self.gpib_addr) + "\n")
        return self.p_master._send(cmd)

    def read(self):
        self.p_master._send("++addr " + str(self.gpib_addr) + "\n")
        return self.p_master._recv()

    def read_values(self,format):
        self.p_master._send("++addr " + str(self.gpib_addr) + "\n")
        return self.p_master._recv()
        
    def ask(self,cmd):
        self.p_master._send("++addr " + str(self.gpib_addr) + "\n")
        return self.p_master._send_recv(cmd)

    def ask_for_values(self,cmd,format=None):
        self.p_master._send("++addr " + str(self.gpib_addr) + "\n")
        return self.p_master._send_recv(cmd)
        
    def clear(self):
        self.p_master._send("++addr " + str(self.gpib_addr) + "\n")
        return self.p_master._set_reset()

    def trigger(self):
        self.p_master._send("++addr " + str(self.gpib_addr) + "\n")
        return self.p_master._set_trigger()


    # this is in the Gpib class of pyvisa, has to move there later
    def send_ifc(self):
        return self._set_ifc()

    # utility functions
    def _get_gpib_adr_from_string(self,gpib_str):
        # very,very simple GPIB address extraction.
        p = re.compile('(gpib::|GPIB::)(\d+)')
        m = p.match(gpib_str)
        if m:
            return int(m.group(2))
        else:
            raise self.Error("Only GPIB:: is supported!")
    # 
    # internal commands to access the prologix gpib device
    #
    
    def _send(self,cmd):
        cmd=cmd.rstrip()
        cmd+=self.term_char
        #self._set_read_after_write(False)
        self.sock.send(cmd.encode())
        time.sleep(self.delay)
        
    def _send_recv(self,cmd,**kwargs):
        bufflen=kwargs.get("bufflen",self.chunk_size)
        cmd=cmd.rstrip()
        cmd+=self.term_char
        #print cmd
        
        self._send(cmd)
        self._set_read()

        response=''
        while True:
            resp=self.sock.recv(bufflen).decode()
            if resp == '':
                raise RuntimeError("socket connection broken")
            response+=resp
            if response[-1] == '\n': # kind of delimeter used to check if message is complete, problem when response too short
                break
        return response

    def _recv(self, **kwargs):
        bufflen = kwargs.get("bufflen", self.chunk_size)
        response=''
        while True:
            resp=self.sock.recv(bufflen).decode()
            if resp == '':
                raise RuntimeError("socket connection broken")
            response+=resp
            if response[-1] == '\n': # kind of delimeter used to check if message is complete, problem when response too short
                break
        return response


    def _open_connection(self,**kwargs):
        # these calls should not be used any more
        self.ip = kwargs.get("ip",self.ip)
        #self.gpib_addr = kwargs.get("gpib_addr",self.gpib_addr)
        # Open TCP connect to port 1234 of GPIB-ETHERNET
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #socket.IPPROTO_TCP)
        self.sock.settimeout(3)
        self.sock.connect((self.ip, self.ethernet_port))

    def _close_connection(self):
        self.sock.close()

    def _set_read(self):
        self._send("++read eoi")

    def _set_saveconfig(self,On=False):
        # should not be used very frequently
        if On:
            self._send("++savecfg 1")
        else:
            self._send("++savecfg 0")

    def _set_gpib_address(self,**kwargs):
        # GET GPIB address
        self.gpib_addr = kwargs.get("gpib_addr",self.gpib_addr)
        # SET GPIB address on the device
        self._send("++addr " + str(self.gpib_addr) + "\n")

    def _set_controller_mode(self,C_Mode=True):
        # set gpib_ethernet into controller mode (True) or in device mode (False)
        if C_Mode:
            # controller mode
            self._send("++mode 1")
        else:
            # device mode
            self._send("++mode 0")

    def _set_read_after_write(self, On=True):
        if On:
            # Turn on read-after-write
            self.sock.send("++auto 1\r\n".encode())
        else:
            # Turn off read-after-write to avoid "Query Unterminated" errors
            self.sock.send("++auto 0\r\n".encode())

    def _set_read_timeout(self,**kwargs):
        timeout = kwargs.get("timeout",self.timeout)
        if timeout > 3:
            timeout = 3
        self._send("++read_tmo_ms "+str(timeout*1000))

    def _set_EOI_assert(self,On=True): #
        # Assert EOI signal line with last byte to indicate end of data
        if On:
            self._send("++eoi 1\n")
        else:
            self._send("++eoi 0\n")

    def _set_GPIB_EOS(self,EOS='\n'): # end of signal/string
        EOSs={'\r\n':0,'\r':1,'\n':2,'':3}
        self.sock.send("++eos"+EOSs.get(EOS)+"\n".encode())

    def _set_GPIB_EOT(self,EOT=False):
        # send at EOI an EOT (end of transmission) character ?
        if EOT:
            self.sock.send("++eot_enable 1\n".encode())
        else:
            self.sock.send("++eot_enable 0\n".encode())
    def _set_GPIB_EOT_char(self,EOT_char=42):
        # set the EOT character
        self.sock.send("++eot_char"+EOT_char+"\n".encode())

    def _set_ifc(self):
        self._send("++ifc")

    # get the service request bit
    def _get_srq(self,**kwargs):
        cmd="++srq"
        bufflen=kwargs.get("bufflen",self.chunk_size)
        cmd=cmd.rstrip()
        cmd+=self.term_char

        self._send(cmd)
        #self._set_read()
        return self.sock.recv(bufflen)

    def _get_spoll(self):
        cmd="++spoll"
        cmd=cmd.rstrip()
        cmd+=self.term_char
        self._send(cmd)
        return self.sock.recv(self.chunk_size)

    def _get_status(self):
        cmd="++status 48"
        #cmd=cmd.rstrip()
        cmd+=self.term_char
        self._send(cmd)
        return self.sock.recv(self.chunk_size)

    def _set_reset(self):
        # Reset Device GPIB endpoint
        self._send("++rst")

    def _set_GPIB_dev_reset(self):
        # Reset Device GPIB endpoint
        self._send("*RST")

    def _get_idn(self):
        return self._send_recv("*IDN?")

    def _dump_internal_vars(self):
        print("timeout"+ str(self.timeout))
        print("chunk_size"+ str(self.chunk_size))
        print("values_format"+ str(self.values_format))
        print("term_char"+ str(self.term_char))
        print("send_end"+ str(self.send_end))
        print("delay"+ str(self.delay))
        print("lock"+str(self.lock))
        print("gpib_addr"+ str(self.gpib_addr))
        print("ip"+ str(self.ip))
        print("ethernet_port"+ str(self.ethernet_port))

    def CheckError(self):
        # check for device error
        self.sock.send("SYST:ERR?\n".encode())
        self.sock.send("++read eoi\n".encode())

        s = None
        try:
            s = self.sock.recv(100)
        except socket.timeout:
            print("socket timeout")
            s = ""
        except socket.error as e:
            pass
        print("Prologix CheckError():{}".format(s))
