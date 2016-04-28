# progress bar handler by AS/JB@KIT 09/2014, 08/2015
# jupyter adjust HR@KIT/2016
# use:
# import Progress_Bar
# initialize and create empty progress bar by instantiating, passing the number of iterations: e.g. p = Progress_Bar.Progress_Bar(100)
# to iterate the progress bar call p.iterate()



import time,sys

debug = False

try:
    "try using the jupyter progress bar"
    from ipywidgets import IntProgress, HTML
    from IPython.display import display
    class Progress_Bar(object):
        def __init__(self,max_it,name= 'Progress:'):
            if debug:
                print("new style progress bar")
            self.first = True
            self.starttime = time.time()
            
            self.max_it = max_it
            self.name = name
            self.progr = 0

            self.pb = IntProgress(
                value=0,
                min=0,
                max=self.max_it,
                description=self.name,
                )     
            
            self.pi = HTML(
                value = " (0/%i) &#10148;  ETA: - &#10148; Time elapsed: -" % (self.max_it),
                )

            display(self.pi)
            display(self.pb)            
            
            
        def iterate(self,param=""):
            
            if self.first:
                "this is a little academic, but the time between the first and the second iteration has usually a time lag."
                self.first = False
                self.start_eta_time = time.time()
                
            self.progr += 1
            progr_info = "%s (%i/%i) &#10148;  ETA: %s &#10148; Time elapsed: %s" %(param,
                    self.progr,
                    self.max_it,
                    time.ctime(time.time() + float(time.time()-self.start_eta_time)/self.progr * (self.max_it - 1  - self.progr)),
                    time.strftime('%H:%M:%S',time.gmtime(time.time()-self.starttime)))
            self.pi.value = progr_info
            self.pb.value = self.progr
                    
except ImportError,e:
    if debug:
        print e
    "Most likely not yet in the jupyter environment ... Falling back to old style progress bar, untouched."
    import uuid
    from IPython.display import HTML, Javascript, display
    from IPython.display import clear_output


    class Progress_Bar(object):

        def __init__(self, max_it, name = 'Progress:'):
            if debug:
                print("old style progress bar")
            #create HTML progress bar

            self.divid = str(uuid.uuid4())
            self.max_it = max_it
            self.name = name
            self.progr = 0

            #delete existing progress bar with same name
            display(Javascript("if(document.getElementById('%st') !== null) document.getElementById('%st').parentNode.remove()"%(self.name,self.name)))
            #display(Javascript("if(document.getElementById('%s') !== null) document.getElementById('%s').remove()"%(self.name,self.name)))

            self.pb = HTML(
            """
            <div id="%s_title"> %s</div>
            <div id="%s1" style="border: 1px solid black; width:900px">
              <div id="%s0" style="text-align: center; color:white; background-color:blue; width:0%%">&nbsp;</div>
            </div>
            <div id="%s_text">(0/%i) Starting</div>
            """ % (self.divid,self.name,self.divid,self.divid,self.divid,max_it))
            display(self.pb)
            display(Javascript("$('div#%s').width('%i%%')" % (self.divid, 100*self.progr/self.max_it)))
            sys.stdout.flush()
            self.starttime = time.time()

        def iterate(self,param=""):
            self.progr += 1
            display(Javascript("$('div#%s0').width('%i%%');" % (self.divid, 100*self.progr/self.max_it)))
            outp = "%s (%i/%i) &#10148;  ETA: %s &#10148; Time elapsed: %s"%(param,self.progr,self.max_it,time.ctime(time.time() + float(time.time()-self.starttime)/self.progr * (self.max_it - self.progr)),time.strftime('%H:%M:%S',time.gmtime(time.time()-self.starttime)))
            display(Javascript("document.getElementById('%s_text').innerHTML = '%s';"%(self.divid,outp)))

            if self.progr == self.max_it:   #end of progress bar
                #Turn the status bar into green
                #display(Javascript("document.getElementById('%s').style.backgroundColor = 'green';"%self.divid))
                #Delete all <div> containers
                #display(Javascript("document.getElementById('%s0').remove();"%self.divid)) #blue box
                #display(Javascript("document.getElementById('%s1').remove();"%self.divid)) #frame
                #display(Javascript("document.getElementById('%s_text').remove();"%self.divid)) #text
                display(Javascript("document.getElementById('%s_title').parentNode.remove();"%self.divid)) #title
                self.pb = HTML(
                """
                <div id="%st"> %s</div>
                <div id="%s" style="border: 1px solid black; width:900px;text-align: center; color:white; background-color:green;">%s
                </div>
                """ % (self.name, self.name, self.name, outp))
                display(self.pb)