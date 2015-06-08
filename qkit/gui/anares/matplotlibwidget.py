__version__ = "1.0.0"

from PyQt4.QtGui import QSizePolicy
from PyQt4.QtCore import QSize

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as Canvas
''''''
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT
''''''
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from matplotlib import rcParams
rcParams['font.size'] = 9

import numpy as np

class MatplotlibWidget(Canvas):
    
    def __init__(self, parent=None,
                 width=4, height=3, dpi=100):
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        
        Canvas.__init__(self, self.figure)
        self.setParent(parent)
        Canvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        Canvas.updateGeometry(self)
        
        self.toolbar = NavigationToolbar2QT(canvas=self, parent=self)
        self.toolbar.resize(2000,25)
        
    def plot(self,xval,yval,xlabel='x',xunit='-',ylabel='y',yunit='-',save=False,Dir=None):
        self.figure.clear()
        self.figure.subplots_adjust(bottom=0.15,left=0.17)
        self.axes = self.figure.add_subplot(111)
        self.axes.ticklabel_format(style='sci', axis='x', scilimits=(0,0))
        self.axes.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
        self.axes.set_xlabel(xlabel+' ['+xunit+']')
        self.axes.set_ylabel(ylabel+' ['+yunit+']')
        self.axes.plot(xval,yval)
        if save:
            print_fig = self.figure
            print_fig.savefig(Dir)
        else:
            self.draw()

        
    def resData(self,xval,yval,xlabel='Frequency',xunit='Hz',plottype='amp',
                ampformat='log',funct=None,args=None,save=False,Dir=None):
        '''
        plots data along a function R1->C1 (suited for fits).
        -Plot types: Amplitude, Amplitude [dB], Phase, Real/Imag
        Make sure that you follow the corret order of arguments when you define 
        a function in your script: the variable is the first argument followed 
        by its parameters f(xvar,param1,param2,.....)
        
        Example:
                
        def S21(f,fr=10e9,Qr=900.0,Qc=1000.,phi=0.,a=1.,alpha=0.,delay=.0):
            return a*np.exp(np.complex(0,alpha))*np.exp(np.complex(0,-2.*np.pi*f*delay))*(1.-Qr/Qc*np.exp(np.complex(0,phi))/np.complex(1,2*Qr*(f-fr)/fr))
            
        mplwidget.resData(f_data,z_data,plottype='amp',funct=S21,
                          args=(fr,Qr,Qc,phi,alpha,delay))
        '''
        self.figure.clear()
        self.figure.subplots_adjust(bottom=0.15,left=0.17)
        self.axes = self.figure.add_subplot(111)
        
        yval_sim=[]
        
        if funct!=None:
            for xi in xval:
                yval_sim.append(funct(xi,*args))
                
        if plottype=='real/imag':
            self.axes.plot(np.real(yval),np.imag(yval),np.real(yval_sim),np.imag(yval_sim))
            self.axes.set_xlabel("Re(S)")
            self.axes.set_ylabel("Im(S)")
        else:
            self.axes.set_xlabel(xlabel+' ['+xunit+']')
                
        if plottype=='amp':
            if ampformat=="log":
                self.axes.plot(xval,10*np.log(np.absolute(yval)),xval,10*np.log(np.absolute(yval_sim)))
                self.axes.set_ylabel("Amplitude [dB]")
            if ampformat=='lin':
                self.axes.plot(xval,np.absolute(yval),xval,np.absolute(yval_sim))
                self.axes.set_ylabel("Amplitude")      
            
        if plottype=='phase':
            if funct==None:
                self.axes.plot(xval,np.angle(yval))
            else:
                self.axes.plot(xval,np.angle(yval),xval,np.angle(yval_sim))
            self.axes.set_ylabel('Phase [rad]') 
            
        if save:
            print_fig = self.figure
            print_fig.savefig(Dir)
        else:
            self.draw()
            
    def resDataScan(self,xval,yval,zval,xlabel='Frequency',xunit='Hz',ylabel='',
                    yunit='',zlabel='',zunit='',plottype='amp',ampformat='log',save=False,Dir=None):
        '''
        3D-colorplot of data (xval,yval,zval) in which either phase or
        amplitude [dB] are displayed color-coded for complex zval. Use 'std'
        in case zval is real. 
        '''
        if type(xval)==list:
            xval=np.array(xval)
        if type(yval)==list:
            yval=np.array(yval)
        if type(zval)==list:
            zval=np.array(zval)
               
        self.figure.clear()
        self.figure.subplots_adjust(bottom=0.15,left=0.17)
        self.axes = self.figure.add_subplot(111)
        self.axes.axis([xval.min(),xval.max(),yval.min(),yval.max()])                 
        self.axes.ticklabel_format(style='sci', axis='x', scilimits=(0,0))
        self.axes.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
    
        if plottype=='amp':
            if ampformat=='log':
                z2=20*np.log10(np.absolute(zval))
            if ampformat=='lin':
                z2=np.absolute(zval)
        if plottype=='phase':
            z2=np.angle(zval)
        if plottype=='std':
            z2=np.array(zval)
            
        x_color=self.axes.pcolormesh(xval,yval,z2.T)
        self.figure.colorbar(x_color,orientation="vertical",
                             label=zlabel+' ['+zunit+']',format='%.0e')
        self.axes.set_xlabel(xlabel+' ['+xunit+']')
        self.axes.set_ylabel(ylabel+' ['+yunit+']')
        
        if save:
            print_fig = self.figure
            print_fig.savefig(Dir)
        else:
            self.draw()
    
    def resData2(self,xval,yval,yval_sim=None,xlabel='Frequency',xunit='Hz',plottype='amp',
                ampformat='log',save=False,Dir=None):
        
        self.figure.clear()
        self.figure.subplots_adjust(bottom=0.15,left=0.17)
        self.axes = self.figure.add_subplot(111)
                
        if plottype=='real/imag':
            self.axes.plot(np.real(yval),np.imag(yval),np.real(yval_sim),np.imag(yval_sim))
            self.axes.set_xlabel("Re(S)")
            self.axes.set_ylabel("Im(S)")
        else:
            self.axes.set_xlabel(xlabel+' ['+xunit+']')
                
        if plottype=='amp':
            if ampformat=="log":
                self.axes.plot(xval,10*np.log(np.absolute(yval)),xval,10*np.log(np.absolute(yval_sim)))
                self.axes.set_ylabel("Amplitude [dB]")
            if ampformat=='lin':
                self.axes.plot(xval,np.absolute(yval),xval,np.absolute(yval_sim))
                self.axes.set_ylabel("Amplitude")      
            
        if plottype=='phase':
            if yval_sim==None: #this option is needed for lorentz function since we only fit the amplitude
                self.axes.plot(xval,np.angle(yval))
            else:                
                self.axes.plot(xval,np.angle(yval),xval,np.angle(yval_sim))
            self.axes.set_ylabel('Phase [rad]') 
            
        if save:
            print_fig = self.figure
            print_fig.savefig(Dir)
        else:
            self.draw()
            
    