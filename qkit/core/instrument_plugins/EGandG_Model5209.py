# EGandG_Model5209.py class, to perform the communication between the Wrapper and the device
# Martijn Schaafsma <qtlab@mcschaafsma.nl>, 2010
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


from instrument import Instrument
import types
import logging
import numpy as np
from time import sleep
import visa

class EGandG_Model5209(Instrument):
   '''
   This is the driver for the Lockin

  Usage:
    Initialize with
    <name> = instruments.create('<name>', 'EGandG_Model5209', address='<GBIP address>, reset=<bool>')
   '''
   def __init__(self, name, address, reset=False):
      logging.info(__name__ + ' : Initializing instrument EG&G Model 5209')
      Instrument.__init__(self, name, tags=['physical'])

      self._address = address
      self._visainstrument = visa.instrument(self._address)
      #self.init_default()

      # Sensitivity
      self._sen = 1.0

      # Add functions
      self.add_function('init_default')
      self.add_function ('get_all')
      self.add_function ('auto_measure')
      self.add_function ('auto_phase')

      # Add parameters
      self.add_parameter('value',
        flags=Instrument.FLAG_GET, units='V', type=types.FloatType,tags=['measure'])
      self.add_parameter('frequency',
        flags=Instrument.FLAG_GET, units='mHz', type=types.FloatType)
      self.add_parameter('sensitivity',
        flags=Instrument.FLAG_GETSET, units='', minval=1, maxval=15, type=types.IntType)
      self.add_parameter('timeconstant',
        flags=Instrument.FLAG_GETSET, units='', minval=1, maxval=15, type=types.IntType)
      self.add_parameter('sensitivity_v',
        flags=Instrument.FLAG_GETSET, units='V', minval=0.0, maxval=15.0, type=types.FloatType)
      self.add_parameter('timeconstant_t',
        flags=Instrument.FLAG_GETSET, units='s', minval=0.0, maxval=15.0, type=types.FloatType)

      self.add_parameter('filter',
        flags=Instrument.FLAG_GETSET, units='', minval=0, maxval=3, type=types.IntType)


      if reset:
       self.init_default()
      #self.get_all()

      self.get_sensitivity_v()

   def _write(self, letter):
      self._visainstrument.write(letter)
      sleep(0.1)

   def _ask(self, question):
      return self._visainstrument.ask(question)

   def get_all(self):
     self.get_value()
     self.get_frequency()
     self.get_sensitivity()
     self.get_timeconstant()
     self.get_sensitivity_v()
     self.get_timeconstant_t()

   def init_default(self):
#      self._write("ASM")
      self._write("SEN 7")
      self._write("XTC 3")
      self._write("FLT 3")

   def auto_measure(self):
      self._write("ASM")

   def auto_phase(self):
      self._write("AQN")

   def do_get_frequency(self):
      stringval = self._ask("FRQ?")
      return float(stringval)

   def do_get_value(self):
      stringval =  self._ask("OUT?")
      sd = stringval.split()

      if len(sd)==2:
        s=sd[0]
        v = float(sd[1])
        if (s=='-'):
          v = -v
      else:
        v = float(sd[0])

      return v*self._sen/10000.0

   def do_get_sensitivity(self):
      stringval = self._ask("SEN?")
      self.get_sensitivity_v()
      return int(stringval)

   def do_set_sensitivity(self,val):
      self._write("SEN %d"%val)
      self.get_sensitivity()

   def do_get_filter(self):
      stringval = self._ask("FLT?")
      print stringval
      return int(stringval)

   def do_set_filter(self,val):
      self._write("FLT %d"%val)

   def do_get_timeconstant(self):
      stringval = self._ask("XTC?")
      return int(stringval)

   def do_set_timeconstant(self,val):
      self._write("XTC %d"%val)

   def do_get_sensitivity_v(self):
      stringval = self._ask("SEN?")
      n = int(stringval)
      self._sen = pow(10,(int(n/2)-7+np.log10(3)*np.mod(n,2)))
      return self._sen

   def do_set_sensitivity_v(self,val):
      n = np.log10(val)*2.0+13.99
      if (np.mod(n,2) > 0.9525) & (np.mod(n,2) < 1.1):
          n = n+0.1
      self._write("SEN %d"%n)
      self.get_sensitivity_v()

   def do_get_timeconstant_t(self):
      stringval = self._ask("XTC?")
      n = int(stringval)
      sen = pow(10,(int(n/2)-3+np.log10(3)*mod(n,2)/))
      return sen

   def do_set_timeconstant_t(self,val):
      n = np.log10(val)*2.0+5.99
      if (mod(n,2) > 0.9525) & (mod(n,2) < 1.1):
          n = n+0.1
      self._write("XTC %d"%n)
