#!/usr/bin/env python

# SR_830 class, derived from Picowatt_AVS47 class by Hannes Rotzinger.
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
from time import sleep
import sys

class SR_830(Instrument):

    def __init__(self, name, address,ip=""):

        Instrument.__init__(self, name, tags=['physical'])

        self._address = address
        self._visainstrument = visa.instrument(self._address,ip=ip)

        self.set_default() # reset everything to:

#REFERENCE / PHASE
#Phase                  0.000 deg
#Reference Source       Internal
#Harmonic               1
#Sine Amplitude         1.000 Vrms
#Internal Frequency     1.000 kHz
#Ext Reference Trigger  Sine
#
#INPUT / FILTERS
#Source                 A
#Grounding              Float
#Coupling               AC
#Line Notches           Out
#
#GAIN / TC
#Sensitivity            1V
#Reserve                Low Noise
#Time Constant          100 ms
#Filter dB/oct.         12 dB
#Synchronous            Off
#
#DISPLAY
#CH1                    X
#CH2                    Y
#Ratio                  None
#Reference              Frequency
#
#OUTPUT / OFFSET
#CH1 Output             X
#CH2 Output             Y
#All Offsets            0.00%
#All Expands            1
#
#AUX OUTPUTS 
#All Output Voltages    0.000 V
#
#SETUP
#Output To              GPIB
#GPIB Address           8
#RS232 Baud Rate        9600
#Parity                 None
#Key Click              On
#Alarms                 On
#Override Remote        On
#
#DATA STORAGE 
#Sample Rate            1 Hz
#Scan Mode              Loop
#Trigger Starts         No
#
#STATUS ENABLE 
#REGISTERS              Cleared

        self.add_function('set_default')
        self.add_function('set_outx')
        self.add_function('get_reference')
        self.add_function('set_reference')
        self.add_function('get_phase_shift')
        self.add_function('set_phase_shift')
        self.add_function('get_frequency')
        self.add_function('set_frequency')
        self.add_function('get_ref_trigger')
        self.add_function('set_ref_trigger')
        self.add_function('get_harmonic')
        self.add_function('set_harmonic')
        self.add_function('get_sine_ampl')
        self.add_function('set_sine_ampl')
        self.add_function('get_input_source')
        self.add_function('set_input_source')
        self.add_function('get_input_shield_gnd')
        self.add_function('set_input_shield_gnd')
        self.add_function('get_input_coupling')
        self.add_function('set_input_coupling')
        self.add_function('get_notch_filters')
        self.add_function('set_notch_filters')
        self.add_function('get_sensitivity')
        self.add_function('set_sensitivity')
        self.add_function('get_reserve_mode')
        self.add_function('set_reserve_mode')
        self.add_function('get_time_constant')
        self.add_function('set_time_constant')
        self.add_function('get_filter_slope')
        self.add_function('set_filter_slope')
        self.add_function('get_sync_filter')
        self.add_function('set_sync_filter')
        self.add_function('get_display_CH1')
        self.add_function('get_display_CH2')
        self.add_function('get_display_CH')
        self.add_function('set_display_CH')
        self.add_function('get_front_panel_output_source_CH1')
        self.add_function('get_front_panel_output_source_CH2')
        self.add_function('get_front_panel_output_source')
        self.add_function('set_front_panel_output_source')
        self.add_function('get_offsets_and_expands_X')
        self.add_function('get_offsets_and_expands_Y')
        self.add_function('get_offsets_and_expands_R')
        self.add_function('get_offsets_and_expands')
        self.add_function('set_offsets_and_expands')
        self.add_function('set_auto_offset_X')
        self.add_function('set_auto_offset_Y')
        self.add_function('set_auto_offset_R')
        self.add_function('set_auto_offset')
        self.add_function('get_aux_input_AUX1')
        self.add_function('get_aux_input_AUX2')
        self.add_function('get_aux_input_AUX3')
        self.add_function('get_aux_input_AUX4')
        self.add_function('get_aux_input')
        self.add_function('get_aux_output')
        self.add_function('get_aux_output_AUX1')
        self.add_function('get_aux_output_AUX2')
        self.add_function('get_aux_output_AUX3')
        self.add_function('get_aux_output_AUX4')
        self.add_function('set_aux_output')
        self.add_function('set_override_remote')
        self.add_function('save_setup')
        self.add_function('recall_setup')
        self.add_function('get_output')
        self.add_function('get_output_X')
        self.add_function('get_output_Y')
        self.add_function('get_output_Z')
        self.add_function('get_output_theta')
        self.add_function('get_snap')

    # communication with device

    def set_default(self):
        com_str = "*RST"
        self._visainstrument.write(com_str)
        sleep(2)
        return 0

    def set_outx(self,i = 1): # RS232 (i=0) or GPIB (i=1)
        i = int(bool(i)) # bam! (forces everything to be zero or one)
        com_str = "OUTX %i" % i
        self._visainstrument.write(com_str)
        sleep(0.05)
        return i

    def get_reference(self):
        self.set_outx(1)
        com_str = "FMOD?"
        self._visainstrument.write(com_str)
        return int(self._visainstrument.read())

    def set_reference(self, ref = 0): ## reference? 1 = internal, 0 = external
        if (ref != 1) and (ref != 0):
            print >> sys.stderr, "Input error in set_reference()!"
            return -1
        else:
            com_str = ("FMOD %i") % ref
            self._visainstrument.write(com_str)
            sleep(0.05)
            return self.get_reference()

    def get_phase_shift(self):
        self.set_outx(1)
        com_str = "PHAS?"
        self._visainstrument.write(com_str)
        return float(self._visainstrument.read())

    def set_phase_shift(self,phas = 0.0):
        phas = float(phas)
        if (phas < -360.00) or (phas > 729.99):
            print >> sys.stderr, "Input error in set_phase_shift()!"
            return -1
        else:
            com_str = "PHAS %.2f" % phas
            self._visainstrument.write(com_str)
            sleep(0.05)
            return self.get_phase_shift()

    def get_frequency(self):
        self.set_outx(1)
        com_str = "FREQ?"
        self._visainstrument.write(com_str)
        return float(self._visainstrument.read())

    def set_frequency(self, freq = 102000):
        freq = float(freq)
        if (freq < 0.001) or (freq > 102000):
            print >> sys.stderr, "Input error in set_frequency()!"
            return -1
        elif self.get_reference() != 1:
            print >> sys.stderr, "Error in set_frequency(): SR830 needs to be set to internal reference!"
            return -1
        else:
            com_str = "FREQ %.4f" % freq
            self._visainstrument.write(com_str)
            sleep(0.05)
            return self.get_frequency()

    def get_ref_trigger(self): # 0 = sine zero crossing, 1 = TTL rising, 2 = TTL falling
        self.set_outx(1)
        com_str = "RSLP?"
        self._visainstrument.write(com_str)
        return int(self._visainstrument.read())

    def set_ref_trigger(self, ref = 1):
        if (ref != 1) and (ref != 0) and (ref != 2):
            print >> sys.stderr, "Input error in set_ref_trigger()!"
            return -1
        elif self.get_reference() != 0:
            print >> sys.stderr, "Error in ref_trigger(): SR830 needs to be set to external reference!"
            return -1
        else:
            com_str = ("RSLP %i") % ref
            self._visainstrument.write(com_str)
            sleep(0.05)
            return self.get_ref_trigger()

    def get_harmonic(self):
        self.set_outx(1)
        com_str = "HARM?"
        self._visainstrument.write(com_str)
        return int(self._visainstrument.read())

    def set_harmonic(self, harm = 1):
        harm = int(harm)
        if (harm < 1) or (harm > 19999):
            print >> sys.stderr, "Input error in set_harmonic()!"
            return -1
        else: 
            com_str = "HARM %i" % harm
            self._visainstrument.write(com_str)
            sleep(0.05)
            return self.get_harmonic()

    def get_sine_ampl(self):
        self.set_outx(1)
        com_str = "SLVL?"
        self._visainstrument.write(com_str)
        return float(self._visainstrument.read())

    def set_sine_ampl(self, ampl = 0.004):
        ampl = float(ampl)
        if (ampl < 0.004) or (ampl > 5.0):
            print >> sys.stderr, "Input error in set_sine_ampl()!"
            return -1
        else:
            com_str = "SLVL %f" % ampl
            self._visainstrument.write(com_str)
            sleep(0.05)
            return self.get_sine_ampl()

    def get_input_source(self):     # A (i=0) single ended, A-B (i=1) differential, 
        self.set_outx(1)            # I (1 MOhm) (i=2) or I (100 MOhm) (i=3)
        com_str = "ISRC?"
        self._visainstrument.write(com_str)
        return int(self._visainstrument.read())

    def set_input_source(self, isrc = 0):
        isrc = int(isrc)
        if (isrc < 0) or (isrc > 3):
            print >> sys.stderr, "Input error in set_input_source()!"
            return -1
        else:
            com_str = "ISRC %i" % isrc
            self._visainstrument.write(com_str)
            sleep(0.5)
            return self.get_input_source()

    def get_input_shield_gnd(self): # floating (0) or grounded (1)
        self.set_outx(1)
        com_str = "IGND?"
        self._visainstrument.write(com_str)
        return int(self._visainstrument.read())

    def set_input_shield_gnd(self, gnd = 0):
        gnd = int(gnd)
        if (gnd < 0) or (gnd > 1):
            print >> sys.stderr, "Input error in set_input_shield_gnd()!"
            return -1
        else:
            com_str = "IGND %i" % gnd
            self._visainstrument.write(com_str)
            sleep(0.5)
            return self.get_input_shield_gnd()

    def get_input_coupling(self): # AC (0) or DC (1)
        self.set_outx(1)
        com_str = "ICPL?"
        self._visainstrument.write(com_str)
        return int(self._visainstrument.read())

    def set_input_coupling(self, icpl = 0):
        icpl = int(icpl)
        if (icpl < 0) or (icpl > 1):
            print >> sys.stderr, "Input error in set_input_coupling()!"
            return -1
        else:
            com_str = "ICPL %i" % icpl
            self._visainstrument.write(com_str)
            sleep(0.5)
            return self.get_input_coupling()

    def get_notch_filters(self):
        self.set_outx(1)
        com_str = "ILIN?"
        self._visainstrument.write(com_str)
        return int(self._visainstrument.read())

    def set_notch_filters(self, ilin = 3): # no filters (i=0), Line notch in (i=1), 
        ilin = int(ilin)                   # 2xLine notch in (i=2) or Both notch filters in (i=3)    
        if (ilin < 0) or (ilin > 3):
            print >> sys.stderr, "Input error in set_notch_filters()!"
            return -1
        else:
            com_str = "ILIN %i" % ilin
            self._visainstrument.write(com_str)
            sleep(0.5)
            return self.get_notch_filters()

    def get_sensitivity(self):
        self.set_outx(1)
        com_str = "SENS?"
        self._visainstrument.write(com_str)
        return int(self._visainstrument.read())

    # i   sensitivity
    # 0   2 nV/fA
    # 1   5 nV/fA
    # 2   10 nV/fA
    # 3   20 nV/fA
    # 4   50 nV/fA
    # 5   100 nV/fA
    # 6   200 nV/fA
    # 7   500 nV/fA
    # 8   1 muV/pA
    # 9   2 muV/pA
    # 10  5 muV/pA
    # 11  10 muV/pA
    # 12  20 muV/pA
    # 13  50 muV/pA
    # 14  100 muV/pA
    # 15  200 muV/pA
    # 16  500 muV/pA
    # 17  1 mV/nA
    # 18  2 mV/nA
    # 19  5 mV/nA
    # 20  10 mV/nA
    # 21  20 mV/nA
    # 22  50 mV/nA
    # 23  100 mV/nA
    # 24  200 mV/nA
    # 25  500 mV/nA
    # 26  1 V/muA

    def set_sensitivity(self, sens = 10):
        sens = int(sens)
        if (sens < 0) or (sens > 26):
            print >> sys.stderr, "Input error in set_sensitivity()!"
            return -1
        else:
            com_str = "SENS %i" % sens
            self._visainstrument.write(com_str)
            sleep(0.5)
            return self.get_sensitivity()

    def get_reserve_mode(self):  # high reserve (0), normal (1), low noise (2)
        self.set_outx(1)
        com_str = "RMOD?"
        self._visainstrument.write(com_str)
        return int(self._visainstrument.read())

    def set_reserve_mode(self, rmod = 1):
        rmod = int(rmod)
        if (rmod < 0) or (rmod > 2):
            print >> sys.stderr, "Input error in set_reserve_mode()!"
            return -1
        else:
            com_str = "RMOD %i" % rmod
            self._visainstrument.write(com_str)
            sleep(0.5)
            return self.get_reserve_mode()

    def get_time_constant(self):
        self.set_outx(1)
        com_str = "OFLT?"
        self._visainstrument.write(com_str)
        return int(self._visainstrument.read())

    # i time constant
    # 0     10 mus
    # 1     30 mus
    # 2     100 mus
    # 3     300 mus
    # 4     1 ms
    # 5     3 ms
    # 6     10 ms
    # 7     30 ms
    # 8     100 ms
    # 9     300 ms
    # 10    1s
    # 11    3s
    # 12    10 s
    # 13    30 s
    # 14    100 s
    # 15    300 s
    # 16    1 ks
    # 17    3 ks
    # 18    10 ks
    # 19    30 ks

    def set_time_constant(self, timec = 7):
        timec = int(timec)
        if (timec < 0) or (timec > 19):
            print >> sys.stderr, "Input error in set_time_constant()!"
            return -1
        else:
            com_str = "OFLT %i" % timec
            self._visainstrument.write(com_str)
            sleep(1)
            actual_time_constant = self.get_time_constant()
            if (actual_time_constant != timec):
                print >> sys.stderr, "Warning: time constant could not be set (incompatible with filters?)!"
            return actual_time_constant

    def get_filter_slope(self):
        self.set_outx(1)
        com_str = "OFSL?"
        self._visainstrument.write(com_str)
        return int(self._visainstrument.read())

    # 0      6 dB/oct
    # 1     12 dB/oct
    # 2     18 dB/oct
    # 3     24 dB/oct

    def set_filter_slope(self, slp = 1):
        slp = int(slp)
        if (slp < 0) or (slp > 3):
            print >> sys.stderr, "Input error in set_filter_slope()!"
            return -1
        else:
            com_str = "OFSL %i" % slp
            self._visainstrument.write(com_str)
            sleep(0.2)
            return self.get_filter_slope()

    def get_sync_filter(self):  # off (0) or synchronous filter below 200 Hz (1)
        self.set_outx(1)
        com_str = "SYNC?"
        self._visainstrument.write(com_str)
        return int(self._visainstrument.read())

    def set_sync_filter(self, sync = 0):
        sync = int(sync)
        if (sync < 0) or (sync > 1):
            print >> sys.stderr, "Input error in set_sync_filter()!"
            return -1
        else:
            if (sync == 1) and ((self.get_harmonic()*self.get_frequency()) > 200):
                print >> sys.stderr, "No synchronous filtering: detection frequency above 200 Hz!"
                return -1
            else:
                com_str = "SYNC %i" % sync
                self._visainstrument.write(com_str)
                sleep(0.05)
                return self.get_sync_filter()

    def get_display_CH1(self):
        self.set_outx(1)
        com_str = "DDEF? 1"
        self._visainstrument.write(com_str)
        res_str = self._visainstrument.read()
        return int(res_str.split(',')[0]),int(res_str.split(',')[1])

    def get_display_CH2(self):
        self.set_outx(1)
        com_str = "DDEF? 2"
        self._visainstrument.write(com_str)
        res_str = self._visainstrument.read()
        return int(res_str.split(',')[0]),int(res_str.split(',')[1])

    def get_display_CH(self, number = 1):
        number = int(number)
        if number == 1:
            return self.get_display_CH1()
        elif number == 2:
            return self.get_display_CH2()
        else:
            print >> sys.stderr, "get_display_CH(): invalid display number!"
            return -1

    # CH1 (1)         CH2 (2)
    #
    # display
    # 0   X           0   Y
    # 1   R           1   theta
    # 2   X noise     2   Y noise
    # 3   Aux In 1    3   Aux In 3
    # 4   Aux In 2    4   Aux In 4
    #
    # ratio
    # 0   none        0   none
    # 1   Aux In 1    1   Aux In 3
    # 2   Aux In 2    2   Aux In 4

    def set_display_CH(self, chan = 1, display = 0, ratio = 0):
        chan = int(chan)
        display = int(display)
        ratio = int(ratio)
        if (chan < 1) or (chan > 2):
            print >> sys.stderr, "Input error in set_display_CH()!"
            return -1
        elif (display < 0) or (display > 4):
            print >> sys.stderr, "Input error in set_display_CH()!"
            return -1
        elif (ratio < 0) or (ratio > 2):
            print >> sys.stderr, "Input error in set_display_CH()!"
            return -1
        else:
            com_str = "DDEF %i,%i,%i" % (chan, display, ratio)
            self._visainstrument.write(com_str)
            sleep(0.05)
            return self.get_display_CH(chan)

    def get_front_panel_output_source_CH1(self):
        self.set_outx(1)
        com_str = "FPOP? 1"
        self._visainstrument.write(com_str)
        res_str = self._visainstrument.read()
        return int(res_str)

    def get_front_panel_output_source_CH2(self):
        self.set_outx(1)
        com_str = "FPOP? 2"
        self._visainstrument.write(com_str)
        res_str = self._visainstrument.read()
        return int(res_str)

    def get_front_panel_output_source(self, number = 1):
        number = int(number)
        if number == 1:
            return self.get_front_panel_output_source_CH1()
        elif number == 2:
            return self.get_front_panel_output_source_CH2()
        else:
            print >> sys.stderr, "get_front_panel_output_source(): invalid display number!"
            return -1

    #     CH1 (1)       CH2 (2)
    #    output quantity
    # 0   CH1 Display   CH2 Display
    # 1   X             Y

    def set_front_panel_output_source(self, chan = 1, fpop = 0):
        chan = int(chan)
        fpop = int(fpop)
        if (chan < 1) or (chan > 2):
            print >> sys.stderr, "Input error in set_display_CH()!"
            return -1
        elif (fpop < 0) or (fpop > 1):
            print >> sys.stderr, "Input error in set_display_CH()!"
            return -1
        else:
            com_str = "FPOP %i,%i" % (chan, fpop)
            self._visainstrument.write(com_str)
            sleep(0.05)
            return self.get_front_panel_output_source(chan)

    def get_offsets_and_expands_X(self):
        self.set_outx(1)
        com_str = "OEXP? 1"
        self._visainstrument.write(com_str)
        res_str = self._visainstrument.read()
        return float(res_str.split(',')[0]),int(res_str.split(',')[1])

    def get_offsets_and_expands_Y(self):
        self.set_outx(1)
        com_str = "OEXP? 2"
        self._visainstrument.write(com_str)
        res_str = self._visainstrument.read()
        return float(res_str.split(',')[0]),int(res_str.split(',')[1])

    def get_offsets_and_expands_R(self):
        self.set_outx(1)
        com_str = "OEXP? 3"
        self._visainstrument.write(com_str)
        res_str = self._visainstrument.read()
        return float(res_str.split(',')[0]),int(res_str.split(',')[1])

    def get_offsets_and_expands(self, number = 1):
        number = int(number)
        if number == 1:
            return self.get_offsets_and_expands_X()
        elif number == 2:
            return self.get_offsets_and_expands_Y()
        elif number == 3:
            return self.get_offsets_and_expands_R()
        else:
            print >> sys.stderr, "get_front_panel_output_source(): invalid display number!"
            return -1

    # first parameter is X (1), Y (2), R (3)
    # second parameter is offset in percent (-105.00 <= x <= 105.00)
    # third parameter is expand - 0:no expand, 1:expand by 10, 2:expand by 100

    def set_offsets_and_expands(self, chan = 1, offset = 0.0, expand = 0):
        chan = int(chan)
        offset = float(offset)
        expand = int(expand)
        if (chan < 1) or (chan > 3):
            print >> sys.stderr, "Input error in set_offsets_and_expands()!"
            return -1
        if abs(offset) > 105.0:
            print >> sys.stderr, "Input error in set_offsets_and_expands()!"
            return -1
        if (expand < 0) or (expand > 2):
            print >> sys.stderr, "Input error in set_offsets_and_expands()!"
            return -1
        else:
            com_str = "OEXP %i,%f,%i" % (chan, offset, expand)
            self._visainstrument.write(com_str)
            sleep(0.5)
            return self.get_offsets_and_expands(chan)

    def set_auto_offset_X(self):  # turn off auto offset with:
        com_str = "AOFF 1"    # set_offsets_and_expands(i, 0.0, k)
        self._visainstrument.write(com_str)
        return 0

    def set_auto_offset_Y(self):
        com_str = "AOFF 2"
        self._visainstrument.write(com_str)
        return 0

    def set_auto_offset_R(self):
        com_str = "AOFF 3"
        self._visainstrument.write(com_str)
        return 0

    def set_auto_offset(self, chan = 1):
        chan = int(chan)
        if chan == 1:
            return self.set_auto_offset_X()
        elif chan == 2:
            return self.set_auto_offset_Y()   
        elif chan == 3:
            return self.set_auto_offset_R()
        else:     
            print >> sys.stderr, "set_auto_offset(): invalid variable (X=1, Y=2, R=3)!"
            return -1

    def get_aux_input_AUX1(self): # in units of volt
        self.set_outx(1)
        com_str = "OAUX? 1"
        self._visainstrument.write(com_str)
        res_str = self._visainstrument.read()
        return float(res_str)

    def get_aux_input_AUX2(self):
        self.set_outx(1)
        com_str = "OAUX? 2"
        self._visainstrument.write(com_str)
        res_str = self._visainstrument.read()
        return float(res_str)

    def get_aux_input_AUX3(self):
        self.set_outx(1)
        com_str = "OAUX? 3"
        self._visainstrument.write(com_str)
        res_str = self._visainstrument.read()
        return float(res_str)

    def get_aux_input_AUX4(self):
        self.set_outx(1)
        com_str = "OAUX? 4"
        self._visainstrument.write(com_str)
        res_str = self._visainstrument.read()
        return float(res_str)

    def get_aux_input(self, aux = 1):
        aux = int(aux)
        if aux == 1:
            return self.get_aux_input_AUX1()
        elif aux == 2:
            return self.get_aux_input_AUX2()
        elif aux == 3:
            return self.get_aux_input_AUX3()
        elif aux == 4:
            return self.get_aux_input_AUX4()
        else:
            print >> sys.stderr, "get_aux_input(): invalid channel (choose 1-4)!"
            return -1

    def get_aux_output(self, chan = 1):
        chan = int(chan)
        if (chan < 1) or (chan > 4):
            print >> sys.stderr, "get_aux_output(): invalid channel (choose 1-4)!"
            return -1
        else:
            self.set_outx(1)
            com_str = "AUXV? %i" % chan
            self._visainstrument.write(com_str)
            res_str = self._visainstrument.read()
            return float(res_str)

    def get_aux_output_AUX1(self):
        return self.get_aux_output(1)

    def get_aux_output_AUX2(self):
        return self.get_aux_output(2)

    def get_aux_output_AUX3(self):
        return self.get_aux_output(3)

    def get_aux_output_AUX4(self):
        return self.get_aux_output(4)

    def set_aux_output(self, chan = 1, auxv = 0.0):
        chan = int(chan)
        auxv = float(auxv)
        if (chan < 1) or (chan > 4):
            print >> sys.stderr, "set_aux_output(): invalid channel (choose 1-4)!"
            return -1
        elif abs(auxv) > 10.5:
            print >> sys.stderr, "set_aux_output(): voltage too large!"
            return -1
        else:
            com_str = "AUXV %i,%f" % (chan,auxv)
            self._visainstrument.write(com_str)
            sleep(0.05)
            return self.get_aux_output(chan)

    def set_override_remote(self, mode = 0): # 1: override GPIB remote mode; 0: normal operation (GPIB 
        mode = int(bool(mode))               # blocks front panel access)
        com_str = "OVRM %i" % mode
        self._visainstrument.write(com_str)
        sleep(0.05)
        return mode

################  below: storage not propperly tested  ################

    def save_setup(self, n_buffer = 1):  # Save setup in a buffer. Buffers will survive power off.
        n_buffer = int(n_buffer)
        if (n_buffer < 1) or (n_buffer > 9):
            print >> sys.stderr, "save_setup(): invalid buffer (choose 1-9)!"
            return -1
        else:
            com_str = "SSET %i" % n_buffer
            self._visainstrument.write(com_str)
            sleep(0.05)
            return n_buffer

    def recall_setup(self, n_buffer = 1):  # Recall setup from buffer.
        n_buffer = int(n_buffer)
        if (n_buffer < 1) or (n_buffer > 9):
            print >> sys.stderr, "recall_setup(): invalid buffer (choose 1-9)!"
            return -1
        else:
            com_str = "RSET %i" % n_buffer
            self._visainstrument.write(com_str)
            sleep(0.5)
            return n_buffer

################  above: storage not propperly tested  ################

    def to_seconds(self, time_const):  # decodes the time constant setting to seconds
        time_const = int(time_const)
        if (time_const%2 == 1):
            factor = 3.0
        else:
            factor = 1.0
        return factor*0.001*0.01*pow(10,time_const/2) 

# since I don't check the status bit, the auto functions are too unstable
#    def set_auto_gain(self):
#        time_const = self.get_time_constant()
#        if time_const > 7:
#            print >> sys.stderr, "set_auto_gain(): not possible, time constant too high."
#            return -1
#        com_str = "AGAN"
#        self._visainstrument.write(com_str)
#        sleep(max(20*self.to_seconds(time_const),1.0))  # auto gain takes surprisingly long
#        self.get_time_constant() # just to force a crash here if the instrument still 
#        return 0                 # does not react after 5 seconds of sleep
#
#    def set_auto_reserve(self):
#        self.get_time_constant()
#        com_str = "ARSV"
#        self._visainstrument.write(com_str)
#        sleep(10)
#        self.get_time_constant() # just to force a crash here if the instrument still 
#        return 0                 # does not react after 5 seconds of sleep
#
# will not include the auto phase here, since it "takes many time constants" to apply

    # finally, to measuring

    def get_output(self, meas = 1): # 1:X, 2:Y, 3:R, 4:theta
        meas = int(meas)
        if (meas < 1) or (meas > 4):
            print >> sys.stderr, "Input error in get_output(): choose 1-4"
            return -1
        else:
            self.set_outx(1)
            com_str = "OUTP? %i" % meas
            self._visainstrument.write(com_str)
            res_str = self._visainstrument.read()
            return float(res_str)

    def get_output_X(self):
        return self.get_output(1)

    def get_output_Y(self):
        return self.get_output(2)

    def get_output_Z(self):
        return self.get_output(3)

    def get_output_theta(self):
        return self.get_output(4)

    def get_snap(self, nargs=2, query_str="1,2"): # simultanious reading of several parameters
        nargs = int(nargs)
        query_str = query_str.split(',')
        if len(query_str) < nargs or nargs < 2 or nargs > 6:
            print >> sys.stderr, "Input error in get_snap()!"    
            return -1
        com_str = "SNAP? "
        for i in range(nargs):
            temp= int(query_str[i])
            if (temp < 1) or (temp > 11):
                print >> sys.stderr, "Input error in get_snap()!"    
                return -1
            else:
                com_str = "%s%i," % (com_str,temp)
        self.set_outx(1)
        com_str = com_str[0:(len(com_str)-1)]
        self._visainstrument.write(com_str)
        res_str = self._visainstrument.read()        
        res_str = res_str.split(',')
        for i in range(nargs):
            res_str[i] = float(res_str[i])
        return res_str

    # The SNAP? command requires at least two parameters and at most six
    # parameters. The parameters i, j, k, l, m, n select the parameters below.
    # 1     X
    # 2     Y
    # 3     R
    # 4     theta
    # 5     Aux In 1
    # 6     Aux In 2
    # 7     Aux In 3
    # 8     Aux In 4
    # 9     Reference Frequency
    # 10    CH1 display
    # 11    CH2 display


## testing:

if __name__ == "__main__":
    sr830=SR_830("SR830","GPIB::8",ip="192.168.0.100")

    sr830._visainstrument.write("*IDN?")
    print "IDN: ", sr830._visainstrument.read()

#    print sr830.set_time_constant(7)

    print "Freq:", sr830.get_frequency()

    print "Sync:", sr830.get_sync_filter()

    print sr830.set_frequency(150)

    print sr830.set_sync_filter(1)

    print "Freq:", sr830.get_frequency()

    print "Sync:", sr830.get_sync_filter()

    print sr830.get_input_source()

    print sr830.get_snap(4, "1,2,6,7")[2]
