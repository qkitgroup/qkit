#Virtual_Coil.py
#script mediating IVVI and measurement script
#Started by Jochen Braumueller <jochen.braumueller@kit.edu> 08/11/2013
#last update: 05/02/2015
#use: set and get current always in mA, make sure to have the correct c_range set which is an attribute of the instance vcoil


from instrument import Instrument
import instruments
import types
import logging
import numpy as np
import time
from time import sleep
import os, sys, qt

IVVI = qt.instruments.get('IVVI')
if 'IVVI' not in qt.instruments.get_instrument_names():
	print 'Warning: IVVI not found...aborting'

DAC_ROUT = 5    #number of routed dac port
dac_val = {'20m':1.30103,'10m':1,'1m':0,'100u':-1,'10u':-2,'1u':-3,'100n':-4,'10n':-5,'1n':-6}

class Virtual_Coil(Instrument):

	def __init__(self, name, dac = DAC_ROUT):
	
		Instrument.__init__(self, name, tags=['virtual'])
		
		self.add_parameter('current', type=types.FloatType,
			flags=Instrument.FLAG_GETSET, units='mA')
		
		#print dac
		self.dac_rout = dac
		self.c_range = '1m'

	def set_c_range(self, range):
		if range in dac_val:
			self.c_range = range
		else:
			print 'Invalid current range.'

	def get_c_range(self):
		return self.c_range
		
	def do_set_current(self, current):     #current in mA
		try:  
			val = np.round((current * 1000 * np.power(10.,-dac_val[self.c_range])),10)
			
			if val > 2000 or val < -2000:
				print 'Error: Value exceeds upper threshold!'
				raise ArithmeticError
			else:
				#if (val < 1 and val > -1 and val != 0) or np.round(val,0) != val:
				#	logging.warning('Warning: Possible resolution not enough for the value you are attempting to set. Instead setting '+str(np.round(val,0) * 1e-3 * np.power(10.,dac_val[self.c_range])) + ' mA')
				#IVVI.set_dac(self.dac_rout,np.round(val))
				print val
				IVVI.set_dac(self.dac_rout,val)
			   
		except IndexError as detail:
			print 'Error: Electronics might be disconnected. ',detail
		except ArithmeticError as detail:
			print 'Invalid current setting. No changees made.',detail


	def do_get_current(self):
		
		val = float(IVVI.get_dac(self.dac_rout))/1000   #val = voltage in Volts
		#print val
		try:
			return val#self.round_to_x_valids(4,val*np.power(10.,dac_val[self.c_range]))
		except IndexError as detail:
			print 'Error: Electronics might be disconnected. ',detail
		except Exception as detail:
			print 'Error: ',detail

	def init(self):
		IVVI.initialize()
		time.sleep(0.1)

		if IVVI.reset_dac() == None:
			print 'Error!'
		else:
			self.set_current(0)
			print 'Done.'

