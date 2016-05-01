# AS @ KIT 04/2015
# modified JB 04/2016
# Sample Class to define all values necessary to measure a sample

import time
import pickle
import qt
import logging
import os, copy, types

class Sample(object):
	'''
	Sample Class to define all values necessary to measure a sample
	'''
	def __init__(self):
		self.name = 'Arbitray Sample'
		self.comment = ''
		
	def update_instruments(self):
		'''
		Updates the following values:
		- awg clock
		- qubit_mw_src power
		- qubit_mw_src f01-iq_frequency
		'''
		try:
			self.awg
			self.clock
			self.qubit_mw_src
			self.f01
			self.iq_frequency
			self.mw_power
		except AttributeError or NameError:
			logging.error('Relevant instruments and attributes not properly specified.')
		else:
			if self.awg == None:
				logging.error(__name__ + ' : awg not defined')
			else:
				self.awg.set_clock(self.clock)
				
			if self.qubit_mw_src == None:
				logging.error(__name__ + ' : qubit_mw_src not defined')
			else:
				self.qubit_mw_src.set_frequency(self.f01-self.iq_frequency)
				self.qubit_mw_src.set_power(self.mw_power)
			
	def set_exc_T(self,exc_T):
		self.exc_T = exc_T
	
	def get_exc_T(self):
		return self.exc_T
		
	def set_iq_frequency(self,iq_frequency):
		self.iq_frequency = iq_frequency
	
	def get_iq_frequency(self):
		return self.iq_frequency
	
	def set_qubit_mw_src(self,qubit_mw_src):
		self.qubit_mw_src = qubit_mw_src
	
	def get_qubit_mw_src(self):
		return self.qubit_mw_src
	
	def set_awg(self,awg):
		self.awg = awg
	
	def get_awg(self):
		return self.awg
		
	def set_clock(self,clock):
		self.clock = clock
	
	def get_clock(self):
		return self.clock

	def set_name(self,name):
		self.name = name
	
	def get_name(self):
		return self.name
	
	def set_comment(self,comment):
		self.comment = comment
	
	def get_comment(self):
		return self.comment
	
	def set_fr(self,fr):
		self.fr = fr
	
	def get_fr(self):
		return self.fr
		
	def set_f01(self,f01):
		self.f01 = f01
	
	def get_f01(self):
		return self.f01
		
	def set_mw_power(self,mw_power):
		self.mw_power = mw_power
	
	def get_mw_power(self):
		return self.mw_power
	
	def set_tpi(self,tpi):
		self.tpi = tpi
	
	def get_tpi(self):
		return self.tpi
	
	def set_tpi2(self,tpi2):
		self.tpi2 = tpi2
	
	def get_tpi2(self):
		return self.tpi2
	
	def set_times(self,tpi):
		'''
		pass tpi to this function and it will update tpi as well as tpi2 = tpi/2
		'''
		self.tpi  = tpi
		self.tpi2 = tpi/2.
	
	def _prepare_entries(self):
		copydict = copy.copy(self.__dict__)
		for key in sorted(copydict):
			if type(copydict[key]) == types.InstanceType:   #instrument
				copydict[key] = str(copydict[key].get_name()) + ' ins'
		return copydict
	
	def get_all(self):
		'''
		return all keys and entries of sample instance
		'''
		msg = ""
		copydict = self._prepare_entries()
		for key in sorted(copydict):
			msg+= str(key) + ":   " + str(copydict[key])+"\n"
		return msg
	
	def save(self,filename=None):
		'''
		save sample object in the data directory
		'''
		if not os.path.exists(os.path.join(qt.config.get('datadir'),time.strftime("%Y%m%d"))):
			os.makedirs(os.path.join(qt.config.get('datadir'),time.strftime("%Y%m%d")))
			
		if filename==None:
			filename=time.strftime("%H%M%S.sample")
			
		msg = self.get_all()
		msg+="\n\n\n<PICKLE PACKET BEGINS HERE>\n" # A Separator
		
		copydict = self._prepare_entries()
		msg+=pickle.dumps(copydict) # And a block which can be easily converted back to a dict
		filehandle=open(os.path.join(qt.config.get('datadir'),time.strftime("%Y%m%d"),filename),'w+')
		print "Saved to " + str(os.path.join(qt.config.get('datadir'),time.strftime("%Y%m%d"),filename)).replace('\\','/')
		filehandle.write(msg)
		filehandle.close()
		
	def load(self, filename):
		'''
		load sample keys and entries to current sample instance
		'''
		if not os.path.isabs(filename):
			filename = os.path.join(qt.config.get('datadir'),filename)
		filehandle=open(filename,'r')
		self.__dict__ = pickle.loads(filehandle.read().split("<PICKLE PACKET BEGINS HERE>\n")[1])
		#print pickle.loads(filehandle.read().split("<PICKLE PACKET BEGINS HERE>\n")[1]).__dict__
		filehandle.close()
		
		copydict = copy.copy(self.__dict__)
		for key in sorted(copydict):
			if ('xxxx'+str(copydict[key]))[-4:] == ' ins':   #instrument
				copydict[key] = qt.instruments.get(copydict[key][:-4])
			