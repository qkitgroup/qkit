# AS @ KIT 04/2015
# Sample Class to define all values necessary to measure a sample
import time
import pickle
import qt
import logging

class Sample(object):
	'''
	Sample Class to define all values necessary to measure a sample
	'''
	
	def __init__(self):
		self.name = 'Arbitray Sample'
		self.comment = ''
		self.fr = None
		self.f01 = None
		self.mw_power = -50
		self.tpi = 0
		self.tpi2 = 0
		self.clock = 1e9
		self.awg = None
		self.qubit_mw_src = None
		self.iq_frequency = 0
		
	def update_instruments(self):
		'''
		Updates the following values:
		- awg clock
		- qubit_mw_src power
		- qubit_mw_src f01-iq_frequency
		'''
		if (awg == None or qubit_mw_src == None):
			logging.error(__name__ + ' : awg or qubit_mw_src not defined')
		else:
			self.awg.set_clock(self.clock)
			self.qubit_mw_src.set_frequency(self.f01-self.iq_frequency)
			self.qubit_mw_src.set_power(self.mw_power)
			
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
	
	def get_all(self):
		msg = ""
		for key in sorted(self.__dict__):   				# There is a block readable by humans
			msg+= str(key) + ":	" + str(self.__dict__[key])+"\n"
			
		print msg
	
	def save(self,filename=None):
		if filename==None:
			filename=time.strftime("%Y%m%d%H%M%S.sample")
		msg = ""
		for key in sorted(self.__dict__):   				# There is a block readable by humans
			msg+= str(key) + ":	" + str(self.__dict__[key])+"\n"
			
		msg+="\n\n\n<PICKLE PACKET BEGINS HERE>\n" # A Separator
		msg+=pickle.dumps(self.__dict__,protocol=1) # And a block which can be easily converted back to a dict
		filehandle=open(filename,'w+')
		filehandle.write(msg)
		filehandle.close()
	
	
		
		
	def load(self, filename):
		filehandle=open(filename,'r')
		self.__dict__ = pickle.loads(filehandle.read().split("<PICKLE PACKET BEGINS HERE>\n")[1])
		#print pickle.loads(filehandle.read().split("<PICKLE PACKET BEGINS HERE>\n")[1]).__dict__
		filehandle.close()