# -*- coding: utf-8 -*-
"""
Created on Sun Jul  5 22:48:47 2015

@author: hrotzing
"""

import sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from time import sleep

from plot_view import Ui_Form
import pyqtgraph as pg

#import argparse
#import ConfigParser
import numpy as np
#import h5py


#class PlotWindow(QMainWindow, Ui_MainWindow):
class PlotWindow(QWidget,Ui_Form):
    def myquit(self):
        exit()

    def __init__(self,parent,data,dataset_path):
        self.DATA = data
        self.dataset_path = dataset_path
        self.obj_parent = parent
        super(PlotWindow , self).__init__() 
        Ui_Form.__init__(self)
        # set up User Interface (widgets, layout...)
        self.setupUi(self)
        self.graphicsView = None
        self.setWindowTitle(dataset_path.split('/')[-1])
        #self.menubar.setNativeMenuBar(False)
        #self._setPlotDefaults()

        self._setup_signal_slots()
        #self.update_plots()
        
    def _setup_signal_slots(self): 
        self.obj_parent.refresh_signal.connect(self.update_plots)
        #QObject.connect(self.PlotTypeSelector,SIGNAL("currentIndexChanged(int)"),self._onPlotTypeChange)

    def _setPlotDefaults(self):
        self.ds = self.obj_parent.h5file[self.dataset_path]
        if len(self.ds.shape) == 1:
            self.PlotTypeSelector.setCurrentIndex(0)
            self.PlotType = 0
        if len(self.ds.shape) == 2:
            self.PlotTypeSelector.setCurrentIndex(1)
            self.PlotType = 1
            #self.PlotTypeSelector.
    def _onPlotTypeChange(self, index):
        if index == 0:
            self.PlotType = 0
        if index == 1:
            self.PlotType = 1
        #print self.PlotTypeSelector.currentText()
        
    @pyqtSlot()   
    def update_plots(self):
        #print "update_plots"
        try:
            self.ds = self.obj_parent.h5file[self.dataset_path]
            if len(self.ds.shape) == 1:
                if not self.graphicsView:
                    self.graphicsView = pg.PlotWidget(name=self.dataset_path)# pg.ImageView(self.centralwidget,view=pg.PlotItem())
                    self.graphicsView.setObjectName(self.dataset_path)
                    #self.graphicsView.setBackground(None)
                    #self.graphicsView.view.setAspectLocked(False)
                    self.gridLayout.addWidget(self.graphicsView)
                    self.plot = self.graphicsView.plot()
                self. _display_1D_data(self.plot, self.graphicsView)
                    
            if len(self.ds.shape) == 2:
                if not self.graphicsView:
                    self.graphicsView = pg.ImageView(self.obj_parent,view=pg.PlotItem())
                    self.graphicsView.setObjectName(self.dataset_path)
                    self.graphicsView.view.setAspectLocked(False)
                    self.gridLayout.addWidget(self.graphicsView)
                self._display_2D_data(self.graphicsView)
        except IOError:
        #except ValueError:
            #pass
            print "PlotWindow: Value Error; Dataset not yet available", self.dataset_path

        
    def _display_1D_data(self,plot,graphicsView):
        ds = self.ds
        
        fill = ds.attrs.get("fill",1)
        ydata = np.array(ds[:])
        
        x0 = ds.attrs.get("x0",0)
        dx = ds.attrs.get("dx",1)
        x_data = [x0+dx*i for i in xrange(len(ydata[:fill]))]
        
        x_name = ds.attrs.get("x_name","_none_")
        name = ds.attrs.get("name","_none_")
        x_unit = ds.attrs.get("x_unit","_none_")
        unit = ds.attrs.get("unit","_none_")
        
        #plot.clear()
        plot.setPen((200,200,100))
        graphicsView.setLabel('left', name, units=unit)
        graphicsView.setLabel('bottom', x_name , units=x_unit)
        plot.setData(y=ydata[:fill], x=x_data)
        
    def _display_2D_data(self,graphicsView):
        #load the dataset:
        ds = self.ds
        fill = ds.attrs.get("fill",1)
        data = np.array(ds[:fill])
        
        x0 = ds.attrs.get("x0",0)
        dx = ds.attrs.get("dx",1)
        y0 = ds.attrs.get("y0",0)
        dy = ds.attrs.get("dy",1)
        
        xmin = x0
        xmax = x0+fill*dx
        ymin = y0
        ymax = y0+fill*dy

        x_name = ds.attrs.get("x_name","_none_")        
        y_name = ds.attrs.get("y_name","_none_")
        name = ds.attrs.get("name","_none_")

        x_unit = ds.attrs.get("x_unit","_none_")
        y_unit = ds.attrs.get("y_unit","_none_")
        unit = ds.attrs.get("unit","_none_")
        
        
        pos = (xmin,ymin)
        
        #scale=(xmax/float(data.shape[0]),ymax/float(data.shape[1]))
        scale=((xmax-xmin)/float(data.shape[0]),(ymax-ymin)/float(data.shape[1]))
        graphicsView.view.setLabel('left', y_name, units=y_unit)
        graphicsView.view.setLabel('bottom', x_name, units=x_unit)
        graphicsView.view.setTitle(name+" ("+unit+")")
        graphicsView.view.invertY(False)
        
        graphicsView.setImage(data,pos=pos,scale=scale)
        graphicsView.show()
        
        # Fixme roi ...
        graphicsView.roi.setPos([xmin,ymin])
        graphicsView.roi.setSize([xmax-xmin,ymax-ymin])
        
        #graphicsView.setImage(data)
        #graphicsView.show()
        
        
 

