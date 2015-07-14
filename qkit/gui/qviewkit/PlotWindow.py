# -*- coding: utf-8 -*-
"""
Created on Sun Jul  5 22:48:47 2015

@author: hrotzing
"""

import sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from time import sleep

from plot_view import Ui_MainWindow
import pyqtgraph as pg

#import argparse
#import ConfigParser
import numpy as np
import h5py


class PlotWindow(QMainWindow, Ui_MainWindow):

    def myquit(self):
        exit()

    def __init__(self,parent,data,dataset_path):
        self.DATA = data
        self.dataset_path = dataset_path
        self.obj_parent = parent
                
        QMainWindow.__init__(self)
        # set up User Interface (widgets, layout...)
        self.setupUi(self)
        self.graphicsView = None
        
        #self.menubar.setNativeMenuBar(False)
        self._setup_signal_slots()
 
        
    def _setup_signal_slots(self): 
        self.obj_parent.refresh_signal.connect(self.update_plots)
        
    @pyqtSlot(float)
    def _update_Error(self,Error):
        self.Errors=numpy.delete(numpy.append(self.Errors,Error*1e6),0)
        self.Error_view.plt.setData(self.times, self.Errors)
    
    @pyqtSlot()   
    def update_plots(self):
        self.ds = self.obj_parent.h5file[self.dataset_path]
        if len(self.ds.shape) == 1:        
            if not self.graphicsView:
                self.graphicsView = pg.PlotWidget(name=self.dataset_path)# pg.ImageView(self.centralwidget,view=pg.PlotItem())
                self.graphicsView.setObjectName(self.dataset_path)
                #self.graphicsView.view.setAspectLocked(False)
                self.verticalLayout.addWidget(self.graphicsView)
                self.plot = self.graphicsView.plot()
            self. _display_1D_data(self.plot, self.graphicsView)
                
        if len(self.ds.shape) == 2:
            if not self.graphicsView:
                self.graphicsView = pg.ImageView(self.centralwidget,view=pg.PlotItem())
                self.graphicsView.setObjectName(self.dataset_path)
                self.graphicsView.view.setAspectLocked(False)
                self.verticalLayout.addWidget(self.graphicsView)
            self._display_2D_data(self.graphicsView)

    def _display_1D_data(self,plot,graphicsView):
        ds = self.ds
        fill = ds.attrs.get("fill")
        ydata = np.array(ds[:])
        
        x0 = ds.attrs.get("x0")
        dx = ds.attrs.get("dx")
        x_data = [x0+dx*i for i in xrange(len(ydata[:fill]))]
        
        x_name = ds.attrs.get("x_name")
        name = ds.attrs.get("name")
        x_unit = ds.attrs.get("x_unit")
        unit = ds.attrs.get("unit")
        
        #plot.clear()
        plot.setPen((200,200,100))
        graphicsView.setLabel('left', name, units=unit)
        graphicsView.setLabel('bottom', x_name , units=x_unit)
        plot.setData(y=ydata[:fill], x=x_data)
        
    def _display_2D_data(self,graphicsView):
        #load the dataset:
        ds = self.ds
        fill = ds.attrs.get("fill")
        data = np.array(ds[:fill])
        
        x0 = ds.attrs.get("x0")
        dx = ds.attrs.get("dx")
        y0 = ds.attrs.get("y0")
        dy = ds.attrs.get("dy")
        
        xmin = x0
        xmax = x0+fill*dx
        ymin = y0
        ymax = y0+fill*dy

        x_name = ds.attrs.get("x_name")        
        y_name = ds.attrs.get("y_name")
        name = ds.attrs.get("name")

        x_unit = ds.attrs.get("x_unit")
        y_unit = ds.attrs.get("y_unit")
        unit = ds.attrs.get("unit")
        
        
        pos = (xmin,ymin)
        
        #scale=(xmax/float(data.shape[0]),ymax/float(data.shape[1]))
        scale=((xmax-xmin)/float(data.shape[0]),(ymax-ymin)/float(data.shape[1]))
        graphicsView.view.setLabel('left', y_name, units=y_unit)
        graphicsView.view.setLabel('bottom', x_name, units=x_unit)
        graphicsView.view.setTitle(name+" ("+unit+")")
        graphicsView.view.invertY(False)
        
        graphicsView.setImage(data,pos=pos,scale=scale)
        """
        # Fixme roi ...
        graphicsView.roi.setPos([xmin,ymin])
        graphicsView.roi.setSize([xmax,ymax])
        """
        #graphicsView.setImage(data)
        graphicsView.show()
        
        
 

