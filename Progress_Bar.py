# progress bar handler by JB@KIT 09/2014
# general class handling a progress bar for all qtLab measurements

import numpy as np
import time,sys

import uuid
from IPython.display import HTML, Javascript, display
from IPython.display import clear_output


class Progress_Bar(object):
		
	def __init__(self, max_it):
	
		#create HTML progress bar
		
		self.divid = str(uuid.uuid4())
		self.pb = HTML(
		"""
		<div style="border: 1px solid black; width:900px">
		  <div id="%s" style="background-color:blue; width:0%%">&nbsp;</div>
		</div> 
		""" % self.divid)
		
		self.max_it = max_it
		self.progr = 0
		clear_output()
		display(self.pb)
		display(Javascript("$('div#%s').width('%i%%')" % (self.divid, 100*self.progr/self.max_it)))
		print 'starting measurement...'
		sys.stdout.flush()
		self.starttime = time.time()
		
	def iterate(self):
		self.progr += 1
		clear_output()
		display(self.pb)
		display(Javascript("$('div#%s').width('%i%%')" % (self.divid, 100*self.progr/self.max_it)))
		print "(%i/%i) ETA: %s"%(self.progr,self.max_it,time.ctime(time.time() + float(time.time()-self.starttime)/self.progr * (self.max_it - self.progr)))
		sys.stdout.flush()
