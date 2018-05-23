#!/usr/bin/env python

# HP_34401A class, derived from Picowatt_AVS47 class by Hannes Rotzinger.
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

import visa_prologix as visa
from time import sleep,clock
import sys

class HP_34401A(Instrument):

    def __init__(self, name, address,ip=""):

        Instrument.__init__(self, name, tags=['physical'])

        self._address = address
        self._visainstrument = visa.instrument(self._address,ip=ip)

        self.set_default() #reset

        self.add_function('set_default')
        self.add_function('get_bandwidth')
        self.add_function('set_bandwidth')
        self.add_function('get_auto_zero')
        self.add_function('set_auto_zero')
        self.add_function('get_configuration')
        self.add_function('get_measurement_mode')
        self.add_function('get_range')
        self.add_function('get_resolution')
        self.add_function('set_measurement_mode')
        self.add_function('set_range_resolution')
        self.add_function('get_NPLC')
        self.add_function('set_NPLC')
        self.add_function('get_autorange')
        self.add_function('set_autorange')
        self.add_function('measure')

    def set_default(self):
        com_str = "*RST"
        self._visainstrument.write(com_str)
        sleep(0.5)
        return 0

    def get_bandwidth(self):
        com_str = "DETector:BANDwidth?"
        self._visainstrument.write(com_str)
        res_str = self._visainstrument.read()
        return int(float(res_str))

    #  DETector:BANDwidth {3|20|200|MINimum|MAXimum}
    ## 3 Hz to 300 kHz     7 seconds / reading
    ## 20 Hz to 300 kHz    1 reading / second
    ## 200 Hz to 300 kHz   10 readings / second

    def set_bandwidth(self, bw = 20):
        bw = int(bw)
        if (bw != 3) and (bw != 20) and (bw != 200):
            print >> sys.stderr, "HP_34401A: Input error in set_bandwidth()!"
            return -1
        com_str = "DETector:BANDwidth %i" % bw
        self._visainstrument.write(com_str)
        sleep(0.05)
        return self.get_bandwidth()

    def get_auto_zero(self): # on or off
        com_str = "ZERO:AUTO?"
        self._visainstrument.write(com_str)
        res_str = self._visainstrument.read()
        return res_str

# ZERO:AUTO {OFF|ONCE|ON}
# auto-zeroing after each measurement

    def set_auto_zero(self, autoz = "OFF"):
        if (autoz != "OFF") and (autoz != "ONCE") and (autoz != "ON"):
            print >> sys.stderr, "HP_34401A: Input error in set_auto_zero()!"
            return -1
        com_str = "ZERO:AUTO %s" % autoz
        self._visainstrument.write(com_str)
        sleep(0.1)
        return self.get_auto_zero()

    def get_configuration(self):
        com_str = "CONF?"
        self._visainstrument.write(com_str)
        res_str = self._visainstrument.read()
        res_str = res_str.split(" ")
        m_mode = res_str[0].split("\"")[1]
        res_str = res_str[1].split(",")
        m_range = float(res_str[0])
        m_resolution = float(res_str[1].split("\"")[0])
        return m_mode, m_range, m_resolution

    def get_measurement_mode(self):
        return self.get_configuration()[0]

    def get_range(self):
        return self.get_configuration()[1]

    def get_resolution(self):
        return self.get_configuration()[2]

    def set_measurement_mode(self, mode = "VOLT:DC"):
        vcf = mode.split(":")[0]
        if (vcf != "VOLT") and (vcf != "CURR") and (vcf != "FREQ"):
            print >> sys.stderr, "HP_34401A: Input error in set_measurement_mode()!"
            return -1
        if (vcf == "FREQ"):
            com_str = "CONF:FREQ"
            self._visainstrument.write(com_str)
            sleep(0.1)
            return self.get_measurement_mode()
        if len(mode.split(":")) < 2:
            print >> sys.stderr, "HP_34401A: Input error in set_measurement_mode()!"
            return -1
        ac_dc = mode.split(":")[1]
        if (ac_dc != "AC") and (ac_dc != "DC"):
            print >> sys.stderr, "HP_34401A: Input error in set_measurement_mode()!"
            return -1
        mode = "%s:%s" % (vcf, ac_dc)
        com_str = "CONF:%s" % mode
        self._visainstrument.write(com_str)
        sleep(0.1)
        return self.get_measurement_mode()

    def set_range_resolution(self,new_range,new_res):
        new_range = float(new_range)
        new_res = float(new_res)
        mode = self.get_measurement_mode()
        com_str = "CONF:%s %f,%f" % (mode, new_range, new_res)
        self._visainstrument.write(com_str)
        sleep(0.1)
        return self.get_range(),self.get_resolution()

    def get_NPLC(self):
        mode = self.get_measurement_mode()
        if (mode != "CURR") and (mode != "VOLT"):
            print >> sys.stderr, "HP_34401A: NPLC not defined"
            return -1
        com_str = "%s:NPLCycles?" % mode
        self._visainstrument.write(com_str)
        res_str = self._visainstrument.read()
        return float(res_str)

    def set_NPLC(self, plc = 10):  # number of power line cycles, default is 10
        plc = float(plc)
        if (plc != 100) and (plc != 10) and (plc != 1) and (plc != 0.2) and (plc != 0.02):
            print >> sys.stderr, "HP_34401A: NPLC can only be 1, 10 or 100"
            return -1
        mode = self.get_measurement_mode()
        if (mode != "CURR") and (mode != "VOLT"):
            print >> sys.stderr, "HP_34401A: NPLC not defined"
            return -1
        com_str = "%s:NPLCycles %f" % (mode, plc)
        self._visainstrument.write(com_str)
        sleep(0.05)
        return self.get_NPLC()

    def get_autorange(self):
        mode = self.get_measurement_mode()
        com_str = "%s:RANGe:AUTO?" % mode
        self._visainstrument.write(com_str)
        res_str = self._visainstrument.read()
        return int(res_str)

    def set_autorange(self, autoran = 0):
        autoran = int(bool(autoran))
        mode = self.get_measurement_mode()
        com_str = "%s:RANGe:AUTO %i" % (mode, autoran)
        self._visainstrument.write(com_str)
        sleep(0.1)
        return self.get_autorange()

    def measure(self):
        mode = self.get_measurement_mode()
        com_str = "MEAS:%s?" % mode
        self._visainstrument.write(com_str)
        sleep(0.5)
        res_str = self._visainstrument.read()
        return float(res_str)


## testing:

if __name__ == "__main__":

    hp_mm = HP_34401A("HP_34401A", "GPIB::17", ip="192.168.0.100")

    hp_mm._visainstrument.write("*IDN?")
    print hp_mm._visainstrument.read()

#    start = float(clock())
#    for i in range(100):
#        hp_mm.get_configuration()
#    end = float(clock())    
#    print "Getting conf took:", end-start

    print hp_mm.set_measurement_mode("CURR:DC")

    print hp_mm.set_range_resolution(2,0.00001)

    print hp_mm.set_NPLC(10)

    print hp_mm.measure()

    print hp_mm.get_measurement_mode()

