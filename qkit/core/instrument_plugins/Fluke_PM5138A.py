# Fluke_PM5138A.py class, to perform the communication between the Wrapper and the device
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
import visa

class Fluke_PM5138A(Instrument):
  '''
  This is the driver for the Fluke

  Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Fluke_PM5138A', address='<GBIP address>, reset=<bool>')
    '''
  def __init__(self, name, address, reset=False):
    logging.info(__name__ + ' : Initializing instrument Fluke PM5138A')
    Instrument.__init__(self, name, tags=['physical'])

    self._address = address
    self._visainstrument = visa.instrument(self._address)

    # Add functions
    self.add_function('init_default')
    self.add_function ('get_all')

    # Add parameters
    self.add_parameter('frequency',
      flags=Instrument.FLAG_GETSET, units='Hz', minval=0, maxval=16000, type=types.FloatType)    
    self.add_parameter('ac_amplitude',
      flags=Instrument.FLAG_GETSET, units='V', minval=-15, maxval=25, type=types.FloatType)
    self.add_parameter('dc_amplitude',
      flags=Instrument.FLAG_GETSET, units='V', minval=-15, maxval=25, type=types.FloatType)
    self.add_parameter('dutycycle',
      flags=Instrument.FLAG_GETSET, units='pct', minval=0, maxval=100, type=types.FloatType)
    
    if reset:
      self.init_default()
    self.get_all()
    

  def _write(self, letter):
    self._visainstrument.write(letter)
	  
  def _ask(self, question):
    return self._visainstrument.ask(question)

  def init_default(self):
    self._write("POSPUL")
    self._write("FREQ 10.00E3")
    self._write("AMPLT 20.0")
    self._write("DCOFF")
    self._write("DUTYC 50")
    self._write("SYM ON")
	  
  def get_all(self):
    logging.info(__name__ + ' : get all')
    self.get_dc_amplitude()
    self.get_ac_amplitude()
    self.get_frequency()
    self.get_dutycycle()
      
  def do_set_frequency(self, frequency):
    self._write("FREQ %f"%frequency )
   
  def do_set_ac_amplitude(self, ac):
    self._write("AMPLT %f"%ac)
   
  def do_set_dc_amplitude(self, dc):
    self._write("DCOFFS %f"%dc)
   
  def do_set_dutycycle(self, dutycycle):
    self._write("DUTYC %f"%dutycycle)
   
  def do_get_frequency(self):
    stringval = self._ask("FREQ?")
    v = stringval.split()[1]
    return float(v)
   
  def do_get_ac_amplitude(self):
    stringval =  self._ask("AMPLT?")
    v = stringval.split()[1]
    return float(v)
   
  def do_get_dc_amplitude(self):
    stringval =  self._ask("DCOFFS?")
    v = stringval.split()[1]
    return float(v)
   
  def do_get_dutycycle(self):
    stringval = self._ask("DUTYC?")
    v = stringval.split()[1]
    return int(v)
   
