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

    # custom slot

    def myquit(self):
        exit()

    def __init__(self,parent,data,dataset):
        self.DATA = data
        self.dataset = dataset
        self.obj_parent = parent
        
        QMainWindow.__init__(self)
        # set up User Interface (widgets, layout...)
        self.setupUi(self)
        self.graphicsView = pg.ImageView(self.centralwidget,view=pg.PlotItem())
        self.graphicsView.setObjectName("graphicsView")
        self.graphicsView.view.setAspectLocked(False)

        
        self.verticalLayout.addWidget(self.graphicsView)
        #self.verticalLayout.addWidget(self.graphicsView2)
        
        
        #self.menubar.setNativeMenuBar(False)
        self._setup_signal_slots()
 
        
    def _setup_signal_slots(self):
        
        #self.live_signal = pyqtSignal()
        #QObject.connect(self.newT_SpinBox,SIGNAL("valueChanged(double)"),self._update_newT)
        
        #QObject.connect(self.P_SpinBox,SIGNAL("valueChanged(double)"),self._update_P)
        #QObject.connect(self.I_SpinBox,SIGNAL("valueChanged(double)"),self._update_I)
        #QObject.connect(self.D_SpinBox,SIGNAL("valueChanged(double)"),self._update_D)
        
        #QObject.connect(self.updateButton,SIGNAL("released()"),self.update_plots)
        self.obj_parent.refresh_signal.connect(self.update_plots)
        #QObject.connect(self.Quit,SIGNAL("released()"),self._quit_tip_gui)
        #QObject.connect(self.DATA.refresh_signal,SIGNAL("").self.update_plots)
        #self.FileButton.clicked.connect(self.selectFile)
        #self.liveCheckBox.clicked.connect(self.live_update_onoff)
    
    
    @pyqtSlot()
    def update_file(self):
        try:
            print "path", self.DATA.DataFilePath
            self.h5file= h5py.File(str(self.DATA.DataFilePath))
            
            self.update_plots()
            self.h5file.close()
            
        except IOError:
            print "IOError"
        
    @pyqtSlot(float)
    def _update_Error(self,Error):
        self.Errors=numpy.delete(numpy.append(self.Errors,Error*1e6),0)
        self.Error_view.plt.setData(self.times, self.Errors)
    
    @pyqtSlot()   
    def update_plots(self):
        #self.live_signal.emit()
        
        #self.h5file= h5py.File(str(self.DATA.DataFilePath))
        
        #self.display_2D_data("amplitude",graphicsView = self.graphicsView)
        self._display_2D_data(graphicsView = self.graphicsView)
        #self.display_2D_data("phase",graphicsView = self.graphicsView2)
        
        #self.h5file.close()
        #print "updated"
    """
    def selectFile(self):
        #lineEdit.setText(
        self.DATA.DataFilePath=QFileDialog.getOpenFileName(filter="*.h5")
        print self.DATA.DataFilePath
        self.statusBar().showMessage(self.DATA.DataFilePath)
        """
        
    def _display_2D_data(self,graphicsView):
        #load the dataset:
        ds_path = self.dataset
        ds = self.obj_parent.h5file[ds_path]
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
        z_name = ds.attrs.get("name")

        x_unit = ds.attrs.get("x_unit")
        y_unit = ds.attrs.get("y_unit")
        z_unit = ds.attrs.get("z_unit")
        
        
        pos = (xmin,ymin)
        
        #scale=(xmax/float(data.shape[0]),ymax/float(data.shape[1]))
        scale=((xmax-xmin)/float(data.shape[0]),(ymax-ymin)/float(data.shape[1]))
        graphicsView.view.setLabel('left', y_name, units=y_unit)
        graphicsView.view.setLabel('bottom', x_name, units=x_unit)
        graphicsView.view.setTitle(z_name+" ("+z_unit+")")
        graphicsView.view.invertY(False)
        
        graphicsView.setImage(data,pos=pos,scale=scale)
        """
        # Fixme roi ...
        graphicsView.roi.setPos([xmin,ymin])
        graphicsView.roi.setSize([xmax,ymax])
        """
        #graphicsView.setImage(data)
        graphicsView.show()
        
    def display_amplitude(self):
       
        data =np.array(self.h5file['/entry/data/phase'])
        
        self.graphicsView.setImage(data)#,pos=pos,scale=scale)
        self.graphicsView.show()
        
        
 

