# progress bar handler by JB@KIT 09/2014
# use:
# initialize and create empty progress bar by instantiating, passing the number of iterations: e.g. p = Progress_Bar(100)
# to iterate the progress bar call p.iterate()


import numpy as np
import time,sys

import uuid
from IPython.display import HTML, Javascript, display
from IPython.display import clear_output


class Progress_Bar(object):
		
	def __init__(self, max_it):
	
		#create HTML progress bar
		
		self.divid = str(uuid.uuid4())
		
		self.max_it = max_it
		self.progr = 0
		self.pb = HTML(
		"""
		<div id="%sh" style="border: 1px solid black; width:900px">
		  <div id="%s" style="text-align: center; color:white; background-color:blue; width:0%%">&nbsp;</div>
		</div> 
		<div id="%st">(0/%i) Starting</div>
		""" % (self.divid,self.divid,self.divid,max_it))
		display(self.pb)
		display(Javascript("$('div#%s').width('%i%%')" % (self.divid, 100*self.progr/self.max_it)))
		sys.stdout.flush()
		self.starttime = time.time()
		
	def iterate(self):
		self.progr += 1
		display(Javascript("$('div#%s').width('%i%%');" % (self.divid, 100*self.progr/self.max_it)))
		outp = "(%i/%i) &#10148;  ETA: %s &#10148; Time elapsed: %s"%(self.progr,self.max_it,time.ctime(time.time() + float(time.time()-self.starttime)/self.progr * (self.max_it - self.progr)),time.strftime('%H:%M:%S',time.gmtime(time.time()-self.starttime)))
		display(Javascript("document.getElementById('%st').innerHTML = '%s';"%(self.divid,outp)))
		
		if self.progr == self.max_it:   #end
			#Turn the status bar into green
			display(Javascript("document.getElementById('%s').style.backgroundColor = 'green';"%self.divid))
			#Delete all <div> containers
			#display(Javascript("document.getElementById('%s').remove();"%self.divid)) #blue box
			#display(Javascript("document.getElementById('%sh').remove();"%self.divid)) #frame
			display(Javascript("document.getElementById('%st').remove();"%self.divid)) #text
			
			#Print status text into progress bar (not below)
			display(Javascript("document.getElementById('%s').innerHTML = '%s';"%(self.divid,outp)))
			
