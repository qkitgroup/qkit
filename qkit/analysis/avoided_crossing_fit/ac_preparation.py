import numpy as np
import peakutils
import matplotlib.pyplot as plt

class acp(object):
    def __init__(self, signal=None, curr=None, freq=None):
        if not (signal is None or curr is None or freq is None):
            self.signal=signal
            self.curr=curr
            self.freq=freq
            self.f_prec=(freq[-1]-freq[0])/(freq.size-1)
        else:
            print "Data missing."
        # Andere Fehler abfangen! Z.B. ungleich lange Arrays...
        # Import peakutils am Anfang von Alex' .py file.
        # Und auch Importfehler abfangen.
        
        
    def _peaksinit(self, f0=None, df=None, i=0):
        if not f0:
            try: f0=self.f0_0
            except NameError: f0=self.freq[int(self.freq.size/2)]
        if not df:
            try: df=self.df
            except NameError: df=self.freq[-1]-self.freq[0]
        # Noch abzufangen: wenn kein thres oder mindist verfügbar, weil peaks noch nicht gestartet
        # Initial values for the span as given by user
        i_min=np.where(abs(self.freq-(f0-df))<self.f_prec)[0][0]
        i_max=np.where(abs(self.freq-(f0+df))<self.f_prec)[0][-1]
        self.di=int((abs(i_max-i_min))/2)
        # Define data array in span:
        sigint=self.signal[i_min:i_max,i]
        # Find first peak:
        self.i_f0=i_min+peakutils.indexes(-sigint,thres=self.thres,min_dist=self.min_dist)[0]
        # Define shift of peak relativ to last found peak
        self.df0=0
        # Define Array for Peakindexes and add first peak
        self.ips=np.array([self.i_f0],dtype=int)
        self.ipcs=np.array([i],dtype=int)
        

    def _peaksearch(self, start=None, stop=None):
        # Funktion funktioniert nur, wenn vorher peaksinit ausgeführt wurde...
        # Care about different looping directions
        if not start: start=1
        if not stop: stop=self.curr.size
        if stop > start:
            step=+1
        else:
            step=-1
            stop=stop-1
        # Walk through signal array and fill peak array
        for i in range(start,stop,step):
            # Define data array for next peak to be searched in
            i_min=self.i_f0+self.df0-self.di
            i_max=self.i_f0+self.df0+self.di
            # If edge of frequency span reached, break
            if (i_min<0 or i_max>self.signal.size):
                break
            # Set new span to signal array
            sigint=self.signal[i_min:i_max,i]
            # Search for peaks
            indexes_found=peakutils.indexes(-sigint,thres=self.thres,min_dist=self.min_dist)
            # If peaks found, add freq index and current index to arrays
            if indexes_found.size>=1:
                i_f0_new=i_min+indexes_found[0]
                self.ips=np.append(self.ips,i_f0_new)
                self.ipcs=np.append(self.ipcs,i)
                # Calculate shift of peak relativ to last found peak
                self.df0=i_f0_new-self.i_f0
                # Set last found peak to new peak
                self.i_f0=i_f0_new
                # If more than one peak found, print it and take the first one
                if indexes_found.size>1:
                    print "Found more than one peak in trace " + str(i)
                    print "First found peak added"
            # If no peak found, print it and continue with next current trace
            else:
                print "No peak found in trace " + str(i)
                # Add distance between to last found peaks to shift
                if self.ips.size>=2:
                    self.df0=self.df0+(self.ips[-1]-self.ips[-2])
                # If not at least 2 peaks found already, set shift to 0
                else:
                    self.df0=0


    def peaks(self, f0_0=None, df=None, f0_e=None, thres=0.3, min_dist=30):
        if f0_0: self.f0_0=f0_0
        else: self.f0_0=self.freq[int(self.freq.size/2)]
        if df: self.df=df
        else: self.df=self.freq[-1]-self.freq[0]
        self.thres=thres
        self.min_dist=min_dist
        # Search for first arm:
        self._peaksinit()
        self._peaksearch()
        self.fitfreqs1=self.freq[self.ips]
        self.fitcurrs1=self.curr[self.ipcs]
        # Search for second arm:
        # If seperate resonator freq given, use that, otherwise use same as for first arm
        if f0_e: self._peaksinit(f0=f0_e,i=-1)
        else: self._peaksinit(i=-1)
        self._peaksearch(start=-2, stop=-self.curr.size)
        self.fitfreqs2=self.freq[self.ips]
        self.fitcurrs2=self.curr[self.ipcs]
        # Make sure data is in the right order for fit
        if np.mean(self.fitfreqs1)>np.mean(self.fitfreqs2):
            self.fitfreqs1,self.fitfreqs2=self.fitfreqs2,self.fitfreqs1
            self.fitcurrs1,self.fitcurrs2=self.fitcurrs2,self.fitcurrs1


    def plot_peaks(self):
        fig, axes = plt.subplots(figsize=(16,8))
        plt.pcolormesh(self.curr, self.freq, self.signal, cmap="coolwarm", vmin=self.signal.min(), vmax=self.signal.max())
        plt.xlim(min(self.curr), max(self.curr))
        plt.ylim(min(self.freq), max(self.freq))
        plt.colorbar()
        plt.plot(self.fitcurrs1,self.fitfreqs1,"xb",label="Fit Freqs 1")
        plt.plot(self.fitcurrs2,self.fitfreqs2,"xr",label="Fit Freqs 2")
        plt.legend()


    def cut1(self,i=0):
        self.fitfreqs1=self.fitfreqs1[0:self.fitfreqs1.size-i]
        self.fitcurrs1=self.fitcurrs1[0:self.fitcurrs1.size-i]
    
    
    def cut2(self,i=0):
        self.fitfreqs2=self.fitfreqs2[0:self.fitfreqs2.size-i]
        self.fitcurrs2=self.fitcurrs2[0:self.fitcurrs2.size-i]