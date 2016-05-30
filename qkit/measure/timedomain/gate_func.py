# gate_func.py
# adapted from earlier versions by Jochen Braumueller <jochen.beraumueller@kit.edu>, 05/2016

# The gate function resets an AWG to the first waveform of a sequence for state==False and sends a trigger
# by raising a gate for state==True.
# Separate functions are supplied for Tektronix AWG and Tabor AWG

"""
usage and inputs:

 from qkit.measure.timedomain import gate_func
 gfunc = gate_func.Gate_Func(awg = fastawg, ni_daq = ftdidac)
 #pass the name of the AWG as imported to qtLAB (e.g. fastawg or tawg)
 #with the spectrum card wrapper virtual_measure_spec.py:
 mspec.set_gate_func(gfunc.gate_fcn)
"""

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

import logging
import time
import qt

class Gate_Func(object):

	def __init__(self, awg, pulser = None, ni_daq = None, ni_daq_ch = 'PFI0:0'):
		"""
		initialize gate function
		inputs:
		 - awg: awg instrument object
		 - pulser: instrument object (to send out pulse directly from pulser instead of triggering the pulser
		 - ni_daq: ni_daq instrument object (in tunnel electronics rack)
		 - ni_daq_ch: used channel of ni_daq
		outputs:
		 -
		"""
		self.awg = qt.instruments.get(awg)
		if pulser:
			self.pulser = qt.instruments.get(pulser)
		else:
			self.pulser = None
		if ni_daq:
			self.ni_daq = qt.instruments.get(ni_daq)
		else:
			self.ni_daq = None
		if self.pulser == None and self.ni_daq == None:
			raise Exception('either pulser or ni_daq must be given')
		self.ni_daq_ch = ni_daq_ch
		
	def gate_fcn(self, state):
		"""
		gate function
		inputs:
		 - state: boolean, chooses one of the actions reset or trigger
		outputs:
		 -
		"""
		if state:   #switch gate to high
			time.sleep(0.1)
			if(self.pulser != None):
				self.pulser._ins._visainstrument.write(':INIT:CONT 1')
			if(self.ni_daq != None):
				self.ni_daq.digital_out(self.ni_daq_ch, 1)
				
		else:   #reset AWG and wait for it
			if(self.pulser != None):
				self.pulser._ins._visainstrument.write(':INIT:CONT 0')
			if(self.ni_daq != None):
				self.ni_daq.digital_out(self.ni_daq_ch, 0)
				
			time.sleep(0.025)
			
			if self.awg == 'fastawg':
				self._reset_tek()
			elif self.awg == 'tawg':
				self._reset_tabor()
			else:
				logging.error('AWG unknown')
				raise ImportError
			
	def _reset_tek(self):
		"""
		reset Tektronix AWG to first sequence
		"""
		tries = 0
		while self.awg.get_seq_position() != 1:
			if tries > 30:
				logging.error('Tektronix AWG does not respond. Aborting.')
				raise ValueError('AWG did not reset to first waveform after %i iterations. There is something seriously going wrong. Check if AWG can enter run mode!'%tries)
			tries += 1
			self.awg.stop()
			self.awg.wait()
			self.awg.run()
			#self.awg.wait()
			time.sleep(0.05*seq_it)

		if tries > 4:
			print 'Tektronix AWG reached first waveform after %d iterations.'%tries
				
	def _reset_tabor(self):
		"""
		reset Tabor AWG to first sequence
		"""
		# TODO adapt tabor commands
		tries = 0
		while self.awg.get_seq_position() != 1:
			if tries > 30:
				logging.error('Tektronix AWG does not respond. Aborting.')
				raise ValueError('AWG did not reset to first waveform after %i iterations. There is something seriously going wrong. Check if AWG can enter run mode!'%tries)
			tries += 1
			self.awg.stop()
			self.awg.wait()
			self.awg.run()
			#self.awg.wait()
			time.sleep(0.05*seq_it)

		if tries > 4:
			print 'Tabor AWG reached first waveform after %d iterations.'%tries