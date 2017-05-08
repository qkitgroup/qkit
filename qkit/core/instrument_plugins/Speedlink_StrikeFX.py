# Speedlink_StrikeFX.py class, to enable joystick movement
# Martijn Schaafsma <qtlab@mcschaafsma.nl>, 2011
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

import pygame as p
import os
from instrument import Instrument
import types
import logging
import numpy
import visa
import time as time
import qt

class Speedlink_StrikeFX(Instrument):
    def __init__(self,name,num, instrlist,varlist,numjoy=0):
        
        # Axes related parameters
        self.numdevices = num
        self.instrlist = instrlist
        self.varlist = varlist

        # Shake hands with qtlab
        Instrument.__init__(self, name, tags=['physical'])

        # Init pygame
        p.init()
        p.joystick.init()
        
        # Init joystick
        self.j = p.joystick.Joystick(numjoy)
        self.j.init()

        # Get properties of joystick
        self.numbuttons = self.j.get_numbuttons()
        self.numaxes = self.j.get_numaxes()
        self.numhats = self.j.get_numhats()

        # Return an error if hats buttons or axes don't exist
        if self.numbuttons<12 or self.numaxes<4 or self.numhats<1:
          print "Not enough controls on joystick!!"
          raise
        
        # steps
        self.step = [1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0]
        self.position = [1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0]

        # Initialize values
        self.buttons = range(self.numbuttons)
        self.axes = range(self.numaxes)
        self.hats = range(self.numhats)

        # Initialize differential values
        self.buttons_changed = range(self.numbuttons)
        self.axes_changed = range(self.numaxes)
        self.hats_changed = range(self.numhats)

        # First reading from device
        self.pump()
        for i in range(self.numaxes):
            self.axes[i] = self.j.get_axis(i)
            self.axes_changed[i] = False
        for i in range(self.numbuttons):
            self.buttons[i] = self.j.get_button(i)
            self.buttons_changed[i] = False
        for i in range(self.numhats):
            self.hats[i] = self.j.get_hat(i)
            self.hats_changed[i] = False

        # Add parameters and functions
        self.add_parameter('stepsize',channels=(1,num),channel_prefix='Axis%d_',
          flags=Instrument.FLAG_GETSET, minval=0.00001, maxval=100, type=types.FloatType)
        self.add_function('run')
        self.add_function('Fire')
        
        # Update qtlab
        for i in range(1,num+1):
          getattr(self,'get_Axis%d_stepsize'%i)()

    def pump(self):
        # Capture state of device
        p.event.pump()

    def do_get_stepsize(self, channel=1):
      return self.step[channel-1]

    def do_set_stepsize(self, stepsize, channel=1):
      self.step[channel-1] = stepsize

    def Fire(self):
        # Read data from controller
        self.pump()
        for i in range(self.numaxes):
            a = int(numpy.round(self.j.get_axis(i)))
            self.axes_changed[i] = (a != self.axes[i])
            self.axes[i] = a
        for i in range(self.numbuttons):
            b = self.j.get_button(i)
            self.buttons_changed[i] = (b != self.buttons[i])
            self.buttons[i] = b
        for i in range(self.numhats):
            c = self.j.get_hat(i)
            self.hats_changed[i] = (c != self.hats[i])
            self.hats[i] = c

        ## Now put the action here
        # Change factor for left
        fact = 1.0
        if self.buttons[4]:
          fact = fact*2.0
        if self.buttons[6]:
          fact = fact*5.0

        # As 1 : hat 0
        if self.hats_changed[0] and self.hats[0][0] and self.numdevices>0:
          if (not self.buttons[4]) and (not self.buttons[6]):
            self.position[0] = getattr(self.instrlist[0],'get_%s'%self.varlist[0])()
            getattr(self.instrlist[0],'set_%s'%self.varlist[0])(self.position[0] + self.hats[0][0]*self.step[0])
            print "Move axis 1 to %f" %(float(self.position[0]) + self.hats[0][0]*self.step[0])
          else:
            if self.hats[0][0] == -1:
              self.set_Axis1_stepsize(self.step[0]/fact)
              self.get_Axis1_stepsize()
            if self.hats[0][0] == 1:
              self.set_Axis1_stepsize(self.step[0]*fact)
              self.get_Axis1_stepsize()
            print "Step 1 changed to %f" %self.step[0]

        # As 2 : hat 0
        if self.hats_changed[0] and self.hats[0][1] and self.numdevices>1:
          if (not self.buttons[4]) and (not self.buttons[6]):
            self.position[1] = getattr(self.instrlist[1],'get_%s'%self.varlist[1])()
            getattr(self.instrlist[1],'set_%s'%self.varlist[1])(self.position[1] + self.hats[0][1]*self.step[1])
            print "Move axis 2 to %f" %(float(self.position[1])+ self.hats[0][1]*self.step[1])
          else:
            if self.hats[0][1] == -1:
              self.set_Axis2_stepsize(self.step[1]/fact)
              self.get_Axis2_stepsize()
            if self.hats[0][1] == 1:
              self.set_Axis2_stepsize(self.step[1]*fact)
              self.get_Axis2_stepsize()
            print "Step 2 changed to %f" %self.step[1]

        # As 3 : axis 0
        if self.axes_changed[0] and self.axes[0] and self.numdevices>2:
          if (not self.buttons[4]) and (not self.buttons[6]):
           self.position[2] = getattr(self.instrlist[2],'get_%s'%self.varlist[2])()
           getattr(self.instrlist[2],'set_%s'%self.varlist[2])(self.position[2] + self.axes[0]*self.step[2])
           print "Move axis 3 to %f" %(float(self.position[2]) + self.axes[0]*self.step[2])
          else:
            if self.axes[0] == -1:
              self.set_Axis3_stepsize(self.step[2]/fact)
              self.get_Axis3_stepsize()
            if self.axes[0] == 1:
              self.set_Axis3_stepsize(self.step[2]*fact)
              self.get_Axis3_stepsize()
            print "Step 3 changed to %f" %self.step[2]

        # As 4 : axis 1
        if self.axes_changed[1] and self.axes[1] and self.numdevices>3:
          if (not self.buttons[4]) and (not self.buttons[6]):
            self.position[3] = getattr(self.instrlist[3],'get_%s'%self.varlist[3])()
            getattr(self.instrlist[3],'set_%s'%self.varlist[3])(self.position[3] + self.axes[1]*self.step[3])
            print "Move axis 4 to %f" %(float(self.position[3]) + self.axes[1]*self.step[3])
          else:
            if self.axes[1] == -1:
              self.set_Axis4_stepsize(self.step[3]/fact)
              self.get_Axis4_stepsize()
            if self.axes[1] == 1:
              self.set_Axis4_stepsize(self.step[3]*fact)
              self.get_Axis4_stepsize()
            print "Step 4 changed to %f" %self.step[3]

        # Change factor for right
        fact = 1.0
        if self.buttons[5]:
          fact = fact*2.0
        if self.buttons[7]:
          fact = fact*5.0

        # As 5 : axis 2
        if self.axes_changed[2] and self.axes[2] and self.numdevices>4:
          if (not self.buttons[5]) and (not self.buttons[7]):
            self.position[4] = getattr(self.instrlist[4],'get_%s'%self.varlist[4])()
            getattr(self.instrlist[4],'set_%s'%self.varlist[4])(self.position[4] + self.axes[2]*self.step[4])
            print "Move axis 5 to %f" %(float(self.position[4]) + self.axes[2]*self.step[4])
          else:
            if self.axes[2] == -1:
              self.set_Axis5_stepsize(self.step[4]/fact)
              self.get_Axis5_stepsize()
            if self.axes[2] == 1:
              self.set_Axis5_stepsize(self.step[4]*fact)
              self.get_Axis5_stepsize()
            print "Step 5 changed to %f" %self.step[4]

        # As 6 : axis 3
        if self.axes_changed[3] and self.axes[3] and self.numdevices>5:
          if (not self.buttons[5]) and (not self.buttons[7]):
#            self.position[5] = self.position[5] + self.axes[3]*self.step[5]
            self.position[5] = getattr(self.instrlist[5],'get_%s'%self.varlist[5])
            setattr(self.instrlist[5],'set_%s'%self.varlist[5],self.position[5] + self.axes[3]*self.step[5])
            print "Move axis 6 to %f" %self.position[5]+ self.axes[3]*self.step[5]
          else:
            if self.axes[3] == -1:
              self.set_Axis6_stepsize(self.step[5]/fact)
              self.get_Axis6_stepsize()
            if self.axes[3] == 1:
              self.set_Axis6_stepsize(self.step[5]*fact)
              self.get_Axis6_stepsize()
            print "Step 6 changed to %f" %self.step[5]

        # As 7 : buttons 3 1
        if self.buttons_changed[3] and self.buttons[3] and self.numdevices>6:
          if (not self.buttons[5]) and (not self.buttons[7]):
            self.position[6] = getattr(self.instrlist[6],'get_%s'%self.varlist[6])()
            getattr(self.instrlist[6],'set_%s'%self.varlist[6])(self.position[6] -self.step[6])
            print "Move axis 7 to %f" %(float(self.position[6])-self.step[6])
          else:
              self.set_Axis7_stepsize(self.step[6]/fact)
              self.get_Axis7_stepsize()
              print "Step 7 changed to %f" %self.step[6]

        if self.buttons_changed[1] and self.buttons[1]:
          if (not self.buttons[5]) and (not self.buttons[7]):
            self.position[6] = getattr(self.instrlist[6],'get_%s'%self.varlist[6])()
            getattr(self.instrlist[6],'set_%s'%self.varlist[6])(self.position[6] + self.step[6])
            print "Move axis 7 to %f" %(float(self.position[6])+ self.step[6])
          else:
              self.set_Axis7_stepsize(self.step[6]*fact)
              self.get_Axis7_stepsize()
              print "Step 7 changed to %f" %self.step[6]

        # As 8 : buttons 2 0
        if self.buttons_changed[2] and self.buttons[2] and self.numdevices>7:
          if (not self.buttons[5]) and (not self.buttons[7]):
            self.position[7] = getattr(self.instrlist[7],'get_%s'%self.varlist[7])()
            getattr(self.instrlist[7],'set_%s'%self.varlist[7])(self.position[7] -self.step[7])
            print "Move axis 8 to %f" %(float(self.position[7])-self.step[7])
          else:
              self.set_Axis8_stepsize(self.step[7]/fact)
              self.get_Axis8_stepsize()
              print "Step 8 changed to %f" %self.step[7]
        if self.buttons_changed[0] and self.buttons[0]:
          if (not self.buttons[5]) and (not self.buttons[7]):
            self.position[7] = getattr(self.instrlist[7],'get_%s'%self.varlist[7])()
            getattr(self.instrlist[7],'set_%s'%self.varlist[7])(self.position[7] + self.step[7])
            print "Move axis 8 to %f" %(float(self.position[7])+ self.step[7])
          else:
              self.set_Axis8_stepsize(self.step[7]*fact)
              self.get_Axis8_stepsize()
              print "Step 8 changed to %f" %self.step[7]

    def run(self):
        qt.mstart()
        self.Fire()
        qt.msleep(0.1)
        while not self.buttons[8]:
            print "=============================="
            self.Fire()
            qt.msleep(0.1)
        qt.mend()
        print "So long, and thanks for all the fish!"
