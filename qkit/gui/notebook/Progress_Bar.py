# progress bar handler by AS/JB@KIT 09/2014, 08/2015
# use:
# import Progress_Bar
# initialize and create empty progress bar by instantiating, passing the number of iterations: e.g. p = Progress_Bar.Progress_Bar(100)
# to iterate the progress bar call p.iterate()


import numpy as np
import time,sys

import uuid
from IPython.display import HTML, Javascript, display
from IPython.display import clear_output


class Progress_Bar(object):
		
	def __init__(self, max_it, name = 'Progress'):
	
		#create HTML progress bar
		
		self.divid = str(uuid.uuid4())
		self.max_it = max_it
		self.name = name
		self.progr = 0
		
		#delete existing progress bar with same name
		display(Javascript("if(document.getElementById('%st') !== null) document.getElementById('%st').remove()"%(self.name,self.name)))
		display(Javascript("if(document.getElementById('%s') !== null) document.getElementById('%s').remove()"%(self.name,self.name)))
		
		self.pb = HTML(
		"""
		<div id="%stitle"> %s</div>
		<div id="%sbar" style="border: 1px solid black; width:900px">
		  <div id="%s" style="text-align: center; color:white; background-color:blue; width:0%%">&nbsp;</div>
		</div> 
		<div id="%stext">(0/%i) Starting</div>
		""" % (self.divid,self.name,self.divid,self.divid,self.divid,max_it))
		display(self.pb)
		display(Javascript("$('div#%s').width('%i%%')" % (self.divid, 100*self.progr/self.max_it)))
		sys.stdout.flush()
		self.starttime = time.time()
		
	def iterate(self):
		self.progr += 1
		display(Javascript("$('div#%s').width('%i%%');" % (self.divid, 100*self.progr/self.max_it)))
		outp = "(%i/%i) &#10148;  ETA: %s &#10148; Time elapsed: %s"%(self.progr,self.max_it,time.ctime(time.time() + float(time.time()-self.starttime)/self.progr * (self.max_it - self.progr)),time.strftime('%H:%M:%S',time.gmtime(time.time()-self.starttime)))
		display(Javascript("document.getElementById('%stext').innerHTML = '%s';"%(self.divid,outp)))
		
		if self.progr == self.max_it:   #end of progress bar
			#Turn the status bar into green
			#display(Javascript("document.getElementById('%s').style.backgroundColor = 'green';"%self.divid))
			#Delete all <div> containers
			display(Javascript("document.getElementById('%s').remove();"%self.divid)) #blue box
			display(Javascript("document.getElementById('%sbar').remove();"%self.divid)) #frame
			display(Javascript("document.getElementById('%stext').remove();"%self.divid)) #text
			display(Javascript("document.getElementById('%stitle').remove();"%self.divid)) #text
			self.pb = HTML(
			"""
			<div id="%st"> %s</div>
			<div id="%s" style="border: 1px solid black; width:900px;text-align: center; color:white; background-color:green;">%s
			</div> 
			""" % (self.name, self.name, self.name, outp))
			display(self.pb)