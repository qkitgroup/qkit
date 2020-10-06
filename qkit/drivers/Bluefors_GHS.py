# Bluefors_GHS.py
# S1@KIT 10/2020
#
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

from qkit.core.instrument_base import Instrument
import socket
import logging
import time

class Bluefors_GHS(Instrument):
    """
    This is the python driver to read valve status and pressures from the
    Bluefors control PC

    Usage:
    Initialise with
    <name> = instruments.create('<name>', host='<IP address>', port=<port>)
    """
    
    def __init__(self, name, host, port):
        '''
        Initializes

        Input:
            name (string)    : name of the instrument
            address (string) : IP address
            port (int)       : port
        '''
        
        logging.info(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])
        
        self._host = host
        self._port = port
        self._reconnect()
        self._wait_time = .05
        
        # Implement parameters
        self.add_parameter('pressure', type=float,flags=Instrument.FLAG_GET, channels=(1, 6), channel_prefix='p%d_',units='mbar')
        self.add_parameter('flowmeter', type=float,flags=Instrument.FLAG_GET,units='mmol/s')
        self.add_parameter('state', type=bool, flags=Instrument.FLAG_GET, channel_prefix="%s_",
                           channels=["v%i"%i for i in range(1,22)]+["compressor","ext","hs-mc","hs-still","pulsetube","scroll1","scroll2","turbo1"])
        
        
        self.get_all()
        
    def get_all(self):
        pass
    ###
    # Communication with device
    ###
    
    def do_get_pressure(self,channel):
        r = self._ask("mgstatus %i"%channel)
        return float(r.split(":")[1].strip())
    
    def do_get_flowmeter(self):
        r = self._ask("fmstatus")
        return float(r.split(":")[1].strip())
    
    def do_get_state(self,channel):
            r = self._ask("status %s" % channel)
            return bool(int(r.split("=")[1].strip()))

    def _ask(self,command):
        #print(command)
        if type(command) is not bytes:
            command = bytes(str(command), "utf-8")
        command += b"\r\n"
        try:
            self._soc.send(command)
            time.sleep(self._wait_time)
            data = self._soc.recv(1024)
            return data.decode().strip()
        except ConnectionAbortedError:
            self._reconnect()
            return self._ask(command)
            
    
    def _reconnect(self):
        logging.info(__name__+": Bluefors_GHS: reconnecting to control PC.")
        for i in range(5):
            try:
                if i>1:
                    print(__name__+": waiting 30 seconds before next reconnect attempt.")
                    time.sleep(30)
                self._soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._soc.connect((self._host, self._port))
                self._soc.settimeout(5)
                self._soc.send(b"test\r\n")
                time.sleep(.5)
                self._soc.recv(1024)
                return True
            except Exception as e:
                if i>=5:
                    raise e
                else:
                    print(e)