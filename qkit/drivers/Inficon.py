# Inficon version 0.1 written by HR@KIT 2012,2018
# updates 05/2017 (JB)

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


import qkit
from qkit.core.instrument_base import Instrument

import logging
import numpy
import time,sys
import atexit
import serial


import time,sys
import atexit


class Inficon(Instrument):
    '''
    This is the driver for the Inficon XTM/2 Quartz Cristal Monitor

    Usage:
    Initialize with
    <name> = qkit.instruments.create('<name>', 'Inficon', address='<GBIP address>', reset=<bool>)

    Set time and thickness to zero
    xtal.set_timer_zero()
    xtal.set_thickness_zero()

    Show actual parameters for this measurement setup
    printxtal.query_parameters()

    Choose material
    xtal.set_material('AlO') 
    '''

    def __init__(self, name, address, reset=False):
        '''
        Initializes the Inficon, and communicates with the wrapper.
        
        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address
            reset (bool)     : resets to default values, default=False
        '''
        
        logging.info(__name__ + ': Initializing instrument Inficon')
        Instrument.__init__(self, name, tags=['physical'])
        #self._address = address
        if sys.version_info[0] < 3:
            def enc(string):
                return string
            def dec(string):
                return string
        else:
            def enc(string):
                return string.encode('latin-1')
            def dec(byte):
                return byte.decode('latin-1')
        self._enc = enc
        self._dec = dec
        
        self.setup(address)

    class inficon_cmds(object):
        # uses Film number 2 for update and query commands
        film_number="2"
        ack="\x06"
        #ack=" \x06"
        get_hello="H"+ack
        get_rate="S 1"+ack
        get_thickness="S 2"+ack
        get_time="S 3"+ack
        get_film="S 4"+ack
        get_xtal_live="S 5"+ack
        set_thickness_zero = "R 4"+ack
        set_timer_zero = "R 5"+ack
        update_tooling = "U "+"0 "+film_number+" %.1f"+ack
        update_final_thickness= "U "+"1 "+film_number+" %.4f"+ack
        update_spt_thickness= "U "+"2 "+film_number+" %.4f"+ack
        update_density = "U "+"3 "+film_number+" %.3f"+ack
        update_zratio = "U "+"4 "+film_number+" %.3f"+ack
        update_spt_timer= "U "+"5 "+film_number+" %i:%i"+ack
        update_film = "U "+"6 "+film_number+" %i"+ack
        query_tooling = "Q "+"0 "+film_number+ack
        query_final_thickness= "Q "+"1 "+film_number+ack
        query_spt_thickness= "Q "+"2 "+film_number+ack
        query_density = "Q "+"3 "+film_number+ack
        query_zratio = "Q "+"4 "+film_number+ack
        query_spt_timer= "Q "+"5 "+film_number+ack
        query_film = "Q "+"6 "+film_number+ack
        
    def setup(self, device="/dev/ttyUSB6"):
        # open serial port, 9600, 8,N,1, timeout 1s
        #device="/dev/tty.usbserial"
        baudrate = 9600
        timeout = 0.1
        self.ack = "\x06"

        # Port A on the USB_to_serial converter, Port B ends with K
        #device = "/dev/tty.usbserial-FTB4J8SC"
        #device = "/dev/ttyUSB0" 
        self.ser = self._std_open(device,baudrate,timeout)
        atexit.register(self.ser.close)

        # load inficon comands
        self.cmds = self.inficon_cmds()
        
    def _std_open(self, device, baudrate, timeout):
        return serial.Serial(device, baudrate, timeout=timeout)

    def remote_cmd(self, cmd):
        self.ser.write(self._enc(cmd))
        
        time.sleep(0.1)
        #value = self.ser.readline().strip("\x06")
        rem_char = self.ser.inWaiting()
        
        value = self._dec(self.ser.read(rem_char)).strip(self.ack)
        #print"##"+value+"##"+value.strip()+"###"
        return value #value.strip()
    
    def get_hello(self):
        return self.remote_cmd(self.cmds.get_hello)

    def get_rate(self, nm=False):
        """
        Check the current rate.

        Args:
            nm (bool): Return the rate in nm/s.

        Returns:
            The current rate in A/s (nm=False) or nm/s (nm=True).
        """
        try:
            ret=self.remote_cmd(self.cmds.get_rate)
            rate = float(ret)
        except ValueError as e:
            print(e)
            print(ret)
            return numpy.NaN
        
        if nm:
            # return rate in nm/s
            return rate/10.
        else:
            # return rate in A/s (10^-10m/s)
            return rate

    def get_thickness(self, nm=False):
        """
        Check the current thickness.

        Args:
            nm (bool): Return the thickness in nm.

        Returns:
            The current thickness in kA (nm=False) or nm (nm=True).
        """
        try:
            ret=self.remote_cmd(self.cmds.get_thickness)
            thickness = float(ret)
        except ValueError as e:
            print(e)
            print(ret)
            return numpy.NaN
        if nm:
            # return thickness in nm
            return thickness*100.
        else:
            # return thickness in kA (10^-7m)
            return thickness

    def get_time(self):
        """
        Check the current time.

        Returns:
            The current time in MIN:SEC
        """
        time_get = (self.remote_cmd(self.cmds.get_time))
            # return time in MIN:SEC
        return time_get

    def get_film(self):
        """
        Check the current film.

        Returns:
            filmnumber (integer from 1-9, 0 in test Mode)
        """
        film = float(self.remote_cmd(self.cmds.get_film))
            # returns film
        return film

    def get_xtal_life(self):
        """
        Check the current crystal life.

        Returns:
            Crystal life in %
        """
        xtal_live = float(self.remote_cmd(self.cmds.get_xtal_live))
            # returns film
        return xtal_live

    def set_thickness_zero(self):
        """
        Sets the thickness to zero

        """
        self.remote_cmd(self.cmds.set_thickness_zero)


    def set_timer_zero(self):
        """
        Sets the timer to zero

        """
        self.remote_cmd(self.cmds.set_timer_zero)


    def set_material(self,material):
        """
        # old (until 07/18) geometry parameter:
        # 'Al': (('tooling-factor',82.0),('Z-ratio',1.080),('density',2.700))
        updates the parameters:
            Tooling factor
            Density
            Z-ration
        for a selected material

        Args:
            string for material such as 'Al' or 'AlO' specified in the dictionary 
            materials
        Returns:
            tooling-factor, Z-ratio and density of actual material 
        """
        materials={
            'Al': (('tooling-factor',72.0),('Z-ratio',1.080),('density',2.700)),
            #'AlO': (('tooling-factor',72.0),('Z-ratio',0.463),('density',3.340))
            #'AlO': (('tooling-factor',72.0),('Z-ratio',1.000),('density',1.548)) #used before 01.2020
            'AlO': (('tooling-factor',72.0),('Z-ratio',1.000),('density',2.322))
            }
        tooling = materials[material][0][1]
        zratio = materials[material][1][1]
        density = materials[material][2][1]
        
        self.remote_cmd(self.cmds.update_tooling % tooling) 
        time.sleep(0.1)
        self.remote_cmd(self.cmds.update_density % density)
        time.sleep(0.1)
        self.remote_cmd(self.cmds.update_zratio % zratio)   
        return materials[material]

    def query_parameters(self):
        """
        queries the parameters:
            Tooling factor
            Density
            Z-ration
            final thickness
            spt thickness
            spt timer
        
        Returns:
            dictionary with the parameters described above
        """
        tooling = self.remote_cmd(self.cmds.query_tooling)     
        density = self.remote_cmd(self.cmds.query_density)
        zratio = self.remote_cmd(self.cmds.query_zratio)

        final_thickness = self.remote_cmd(self.cmds.query_final_thickness)  
        spt_thickness = self.remote_cmd(self.cmds.query_spt_thickness)
        spt_timer = self.remote_cmd(self.cmds.query_spt_timer)

        try:
            tooling=float(tooling)
            density=float(density)
            zratio=float(zratio)
            final_thickness=float(final_thickness)
            spt_thickness=float(spt_thickness)
        except ValueError as e:
            print(e)
            print(tooling)
            print(density)
            print(zratio)
            print(final_thickness)
            print(spt_thickness)
            
        parameter={
            'tooling': (tooling),
            'density': (density),
            'Z-ratio': (zratio),
            'final thickness': (final_thickness),
            'spt thickness': (spt_thickness),
            'spt timer': spt_timer
        }   
        return parameter
      

if __name__ == "__main__":
    INFI=Inficon("Inficon", address="COM5")
    print('Rate:', INFI.get_rate())
    print('Thickness:', INFI.get_thickness())
