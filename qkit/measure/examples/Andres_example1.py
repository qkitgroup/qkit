#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 20 13:15:35 2021

@author: lr1740
"""
import qkit
from qkit.gui.notebook.Progress_Bar import Progress_Bar
import qkit.measure.measurement_base as mb
import inspect
import numpy as np


class Cloud(mb.MeasureBase):
    def create_values(a):
        array = np.arange(-10, 10, 1000)
        return np.cos(array), np.sin(array)
    
    def measure_2D(self,iterations=100000,ampmax=None):
        self._measurement_object.measurement_func = 'measure_2D_cloud'
        self._measurement_object.sequence_code = inspect.getsource(self._x_parameter.set_function)
         
        self.nbins=500
        
        self.record = self.create_values
         
        def create_file(ampmax):
            idx = self.Coordinate('iteration', unit='#', values=np.arange(iterations))
            hpx = self.Coordinate("hist_phase_x",unit="rad",values=np.linspace(-np.pi,np.pi,self.nbins+1))
            hax = self.Coordinate("hist_amp_x",unit="arb.u.",values=np.linspace(0,ampmax,self.nbins+1))
            hi = self.Coordinate("hist_I",unit="arb.u.",values=np.linspace(-ampmax,ampmax,self.nbins//1+1))
            hq = self.Coordinate("hist_Q",unit="arb.u.",values=np.linspace(-ampmax,ampmax,self.nbins//1+1))

            self._prepare_measurement_file(
                [self.Data("I", [self._x_parameter,idx], ""),
                 self.Data("Q", [self._x_parameter,idx], ""),
                 self.Data("hist_phase",[self._x_parameter,hpx],"",folder="analysis"),
                 self.Data("hist_amp",[self._x_parameter,hax],"",folder="analysis"),
                 self.Data("hist_IQ",[self._x_parameter,hi,hq],"",folder="analysis"),
                ])
            self._open_qviewkit()
         
         
         
        p = Progress_Bar(len(self._x_parameter.values))
        try:
             print("Do I ever go in here?")
             for ix, x in enumerate(self._x_parameter.values):
                self._x_parameter.set_function()
                qkit.flow.sleep(self._x_parameter.wait_time)

     
                i,q = self.record()
                #print(ix)
                if ix == 0:
                    if ampmax is None:
                        ampmax = np.max(np.abs(np.append(i,q)))
                    print("Peekaboo")
                    create_file(ampmax)
                self._acquire_log_functions()
                self._datasets['I'].append(i)
                self._datasets['Q'].append(q)
                p.iterate()
                
                hist0 = np.histogram(np.angle(np.array(i)+1j*np.array(q)),bins=500,range=(-np.pi,np.pi))
                self._datasets['hist_phase'].append(hist0[0]/ len(i))
                 
                hist0 = np.histogram(np.abs(np.array(i)+1j*np.array(q)),bins=500,range=(0,ampmax))
                self._datasets['hist_amp'].append(hist0[0]/ len(i))
                 
                hist0 = np.histogram2d(np.array(i),np.array(q),bins=self.nbins,range=((-ampmax,ampmax),(-ampmax,ampmax)))
                hist0 = hist0[0]/len(i)
                for d in hist0:
                    self._datasets['hist_IQ'].append(d)
                self._datasets['hist_IQ'].next_matrix()
             
        finally:
# =============================================================================
#             self._views = [self._data_file.add_view("IQ", x=self._datasets['I'], y=self._datasets['Q'],
#                                                     view_params=dict(plot_style=2,aspect=True))]
# =============================================================================

            self._end_measurement()