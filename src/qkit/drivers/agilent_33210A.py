#!/usr/bin/env python

# agilent_33210A class, derived from Picowatt_AVS47 class by Hannes Rotzinger.
# Jochen Zimmer, June 2012 -- ALPHA release version 0.1
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


QTLAB = True

if QTLAB:
    from qkit.core.instrument_base import Instrument
else:
    class Instrument(object):
        FLAG_GETSET = 0 
        FLAG_GET_AFTER_SET = 1
        def __init__(self,name,**kwargs):
            pass
        def add_parameter(self,name,**kwargs):
            pass
        def add_function(self,name):
            pass

from qkit import visa
from time import sleep
import sys

class agilent_33210A(Instrument):

    def __init__(self, name, address):

        Instrument.__init__(self, name, tags=['physical'])

        self._address = address
        self._visainstrument = visa.instrument(self._address)

        self.min_freq = self.get_MIN_frequency()
        self.max_freq = self.get_MAX_frequency()

        self.min_ampl = self.get_MIN_amplitude()
        self.max_ampl = self.get_MAX_amplitude()

        self.min_offs = self.get_MIN_offset()
        self.max_offs = self.get_MAX_offset()

        self.set_default() #reset

        self.add_function('set_default')
        self.add_function('get_frequency')
        self.add_function('set_frequency')
        self.add_function('get_function')
        self.add_function('set_function')
        self.add_function('get_amplitude')
        self.add_function('set_amplitude')
        self.add_function('get_output')
        self.add_function('set_output')
        self.add_function('get_offset')
        self.add_function('set_offset')
        self.add_function('get_voltage_units')
        self.add_function('set_voltage_units')
        self.add_function('get_output_load')
        self.add_function('set_output_load')


    def set_default(self):
        com_str = "*RST"
        self._visainstrument.write(com_str)
        sleep(0.1)
        return 0

    def get_frequency(self):
        com_str = "FREQuency?"
        self._visainstrument.write(com_str)
        res_str = self._visainstrument.read()
        return float(res_str)

    def get_MAX_frequency(self):
        com_str = "FREQuency? MAX"
        self._visainstrument.write(com_str)
        res_str = self._visainstrument.read()
        return float(res_str)

    def get_MIN_frequency(self):
        com_str = "FREQuency? MIN"
        self._visainstrument.write(com_str)
        res_str = self._visainstrument.read()
        return float(res_str)

    def set_frequency(self, freq):
        freq = float(freq)
        if (freq<self.min_freq) or (freq>self.max_freq):
            print("agilent_33210A: frequency out of range!", file=sys.stderr)
            return -1
        com_str = "FREQuency %f" % freq
        self._visainstrument.write(com_str)
        sleep(0.05)
        return self.get_frequency()

    def get_function(self):
        com_str = "FUNCtion?"
        self._visainstrument.write(com_str)
        res_str = self._visainstrument.read()
        return res_str

    def set_function(self,f_str):
        if (f_str != "SIN") and (f_str != "SQU"):
            print("agilent_33210A: selected function not recognized!", file=sys.stderr)
            # FUNCtion {SINusoid|SQUare|RAMP|PULSe|NOISe|DC|USER}, some not implemented
            return -1
        com_str = "FUNCtion %s" % f_str
        self._visainstrument.write(com_str)
        sleep(0.05)
        return self.get_function()

    def get_amplitude(self):
        com_str = "VOLTage?"
        self._visainstrument.write(com_str)
        res_str = self._visainstrument.read()
        return float(res_str)

    def get_MAX_amplitude(self):
        com_str = "VOLTage? MAX"
        self._visainstrument.write(com_str)
        res_str = self._visainstrument.read()
        return float(res_str)

    def get_MIN_amplitude(self):
        com_str = "VOLTage? MIN"
        self._visainstrument.write(com_str)
        res_str = self._visainstrument.read()
        return float(res_str)

    def set_amplitude(self, ampl):
        ampl = float(ampl)
        if (ampl<self.min_ampl) or (ampl>self.max_ampl):
            print("agilent_33210A: amplitude out of range!", file=sys.stderr)
            return -1
        com_str = "VOLTage %f" % ampl
        self._visainstrument.write(com_str)
        sleep(0.05)
        return self.get_amplitude()

    def get_output(self):
        com_str = "OUTPut?"
        self._visainstrument.write(com_str)
        res_str = self._visainstrument.read()
        return res_str

    def set_output(self, onoff = 0):
        onoff = int(bool(onoff))
        com_str = "OUTPut %i" % onoff
        self._visainstrument.write(com_str)
        sleep(0.05)
        return self.get_output()

    def get_offset(self):
        com_str = "VOLTage:OFFset?"
        self._visainstrument.write(com_str)
        res_str = self._visainstrument.read()
        return float(res_str)

    def get_MAX_offset(self):
        com_str = "VOLTage:OFFset? MAX"
        self._visainstrument.write(com_str)
        res_str = self._visainstrument.read()
        return float(res_str)

    def get_MIN_offset(self):
        com_str = "VOLTage:OFFset? MIN"
        self._visainstrument.write(com_str)
        res_str = self._visainstrument.read()
        return float(res_str)

    def set_offset(self, offs = 0):
        offs = float(offs)
        if (offs > self.max_offs) or (offs < self.min_offs):
            print("agilent_33210A: offset out of range!", file=sys.stderr)
            return -1
        com_str = "VOLTage:OFFset %f" % offs
        self._visainstrument.write(com_str)
        sleep(0.05)
        return self.get_offset()

    def get_voltage_units(self):
        com_str = "VOLTage:UNIT?"
        self._visainstrument.write(com_str)
        res_str = self._visainstrument.read()
        return res_str

    def set_voltage_units(self, vunits = "VPP"):
        if (vunits != "VPP") and (vunits != "VRMS") and (vunits != "DBM"):
            print("agilent_33210A: input error in set_voltage_units()", file=sys.stderr)
            return -1
        com_str = "VOLTage:UNIT %s" % vunits
        self._visainstrument.write(com_str)
        sleep(0.05)
        self.min_ampl = self.get_MIN_amplitude() # depends on the units, of course
        self.max_ampl = self.get_MAX_amplitude()
        return self.get_voltage_units()

    def get_output_load(self):
        com_str = "OUTPut:LOAD?"
        self._visainstrument.write(com_str)
        res_str = self._visainstrument.read()
        return float(res_str)

    def set_output_load(self, load):
        if (load == "INF"):
            com_str = "OUTPut:LOAD %s" % load
        elif float(load) > 1.0:
            com_str = "OUTPut:LOAD %f" % float(load)
        else:
            print("agilent_33210A: input error in set_output_load()", file=sys.stderr)
            return -1
        self._visainstrument.write(com_str)
        sleep(0.05)
        self.min_ampl = self.get_MIN_amplitude() # also depends on load
        self.max_ampl = self.get_MAX_amplitude()
        return self.get_output_load()


## testing:

if __name__ == "__main__":

    agilent_AWG = agilent_33210A("agilent_AWG", "TCPIP::192.168.0.2")

    print( agilent_AWG._visainstrument.ask("*IDN?"))
    
    print( agilent_AWG.set_voltage_units("VRMS"))
        
    print( agilent_AWG.set_output_load("INF"))

    print( agilent_AWG.set_frequency(1000.0))

    print( agilent_AWG.set_amplitude(0.1))

    print( agilent_AWG.set_offset(0.1))
    
    print( agilent_AWG.set_output(1))

    sleep(1)

    print( agilent_AWG.set_output(0))

#    start = float(clock())
#    for i in range(100):
#        hp_mm.get_configuration()
#    end = float(clock())    
#    print "Getting conf took:", end-start



