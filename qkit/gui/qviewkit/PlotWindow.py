# -*- coding: utf-8 -*-
"""
@author: hannes.rotzinger@kit.edu @ 2015
"""


from PyQt4.QtCore import *
from PyQt4.QtGui import *


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

    def __init__(self,parent,data,dataset_url):
        self.DATA = data
        self.dataset_url = dataset_url
        self.obj_parent = parent
        super(PlotWindow , self).__init__() 
        Ui_Form.__init__(self)
        # set up User Interface (widgets, layout...)
        self.setupUi(self)
        window_title = str(dataset_url.split('/')[-1]) +" "+ str(self.DATA.filename)
        self.setWindowTitle(window_title)
        
        self.graphicsView = None
        #self.ds = self.obj_parent.h5file[self.dataset_url]
        #self._setDefaultView()
        self._windowJustCreated = True
        #self._setPlotDefaults()
        #self._init_XY_add()
        #self.menubar.setNativeMenuBar(False)
        

        self._setup_signal_slots()
        #self.update_plots()
        
    def _setup_signal_slots(self): 
        self.obj_parent.refresh_signal.connect(self.update_plots)
        QObject.connect(self.PlotTypeSelector,SIGNAL("currentIndexChanged(int)"),self._onPlotTypeChange)
        #QObject.connect(self,SIGNAL("aboutToQuit()"),self._close_plot_window)
        QObject.connect(self.TraceSelector,SIGNAL("valueChanged(int)"),self._setTraceNum)
        #QObject.connect(self.addXPlotSelector,SIGNAL("currentIndexChanged(int)"),self._addXPlotChange)
        #QObject.connect(self.addYPlotSelector,SIGNAL("currentIndexChanged(int)"),self._addYPlotChange)
        
        
    def _setDefaultView(self):
        self.view_types = {'1D':0,'1D-V':1, '2D':2, '3D':3}
        self.TraceNum = -1
        #self.TraceSelector.setEnabled(True)
        #print self.dataset_url, " opened ..."

        #
        #default view type is 1D
        self.view_type = self.ds.attrs.get("view_type",None)
        if not self.view_type:
            if len(self.ds.shape) == 1:
                self.PlotTypeSelector.setCurrentIndex(1)
                self.view_type = self.view_types['1D']
                self.TraceSelector.setEnabled(False)
            elif len(self.ds.shape) == 2:
                self.TraceSelector.setEnabled(True)
                shape = self.ds.shape[0]
                self.TraceSelector.setRange(-1*shape,shape-1)
                self.PlotTypeSelector.setCurrentIndex(0)
                self.view_type = self.view_types['2D']
            else:
                self.TraceSelector.setEnabled(True)
                self.view_type = self.view_types['1D']
        else:
            self.TraceSelector.setEnabled(True)

        
    
    def _setTraceNum(self,num):
        self.TraceNum = num
        #print self.TraceNum
        self.obj_parent.pw_refresh_signal.emit()
        
    def _addXPlotChange(self):
        pass
    def _addYPlotChange(self):
        pass

    def _init_XY_add(self):
        for i,key in enumerate(self.DATA.ds_tree_items.iterkeys()):
            keys = key.split("/")[-2:]
            key = "/".join(key for key in keys)
            self.addXPlotSelector.addItem("")
            self.addYPlotSelector.addItem("")
            self.addXPlotSelector.setItemText(i, str(key))
            self.addYPlotSelector.setItemText(i, str(key))
            #print i,key
           
        
    def _onPlotTypeChange(self, index):
        self._onPlotTypeChanged = True
        if index == 0:
            self.view_type = self.view_types['2D']
        if index == 1:
            self.view_type = self.view_types['1D']
        #print index
        if not self._windowJustCreated:
            self.obj_parent.pw_refresh_signal.emit()
            
        #print self.PlotTypeSelector.currentText()
    
    def closeEvent(self, event):
        "overwrite the closeEvent handler"
        self.deleteLater()
        self.DATA._toBe_deleted(self.dataset_url)
        event.accept()
        

    @pyqtSlot()   
    def update_plots(self):
        self.ds = self.obj_parent.h5file[self.dataset_url]
        if self._windowJustCreated:
            #print "JC"
            self._setDefaultView()
            self._onPlotTypeChanged = True
            self._windowJustCreated = False
        #print "update_plots"
        
        try:
            #self.ds = self.obj_parent.h5file[self.dataset_url]
            if self.view_type == self.view_types['1D-V']: 
                if not self.graphicsView or self._onPlotTypeChanged:
                    self._onPlotTypeChanged = False
                    self.graphicsView = pg.PlotWidget(name=self.dataset_url)
                    self.graphicsView.setObjectName(self.dataset_url)
                    self.gridLayout.addWidget(self.graphicsView,0,0)
                self._display_1D_view(self.graphicsView)
                
            elif self.view_type == self.view_types['1D']: 
                if not self.graphicsView or self._onPlotTypeChanged:
                    #print "new graphics view"
                    self._onPlotTypeChanged = False
                    self.graphicsView = pg.PlotWidget(name=self.dataset_url)
                    self.graphicsView.setObjectName(self.dataset_url)
                    self.gridLayout.addWidget(self.graphicsView,0,0)
                self._display_1D_data(self.graphicsView)
    
            elif self.view_type == self.view_types['2D']:
                if not self.graphicsView or self._onPlotTypeChanged:
                    self._onPlotTypeChanged = False
                    self.graphicsView = pg.ImageView(self.obj_parent,view=pg.PlotItem())
                    self.graphicsView.setObjectName(self.dataset_url)
                    self.graphicsView.view.setAspectLocked(False)
                    self.gridLayout.addWidget(self.graphicsView,0,0)
                self._display_2D_data(self.graphicsView)
            else:
                pass
        #except NameError:#IOError:
        except ValueError,e:
            print "PlotWindow: Value Error; Dataset not yet available", self.dataset_url
            print e


    def _display_1D_view(self,graphicsView):
        ds = self.ds
        overlay_num = ds.attrs.get("overlays",0)
        overlay_urls = []
        x_axis = []
        y_axis = []
        for i in range(overlay_num+1):
            ov = ds.attrs.get("xy_"+str(i),"")
            ax = ds.attrs.get("xy_"+str(i)+"_axis","0:0")
            if ov:
                overlay_urls.append(ov.split(":"))
                x_a, y_a = ax.split(":")
                #print x_a, y_a
                x_axis.append(int(x_a))
                y_axis.append(int(y_a))
        ds_xs = []
        ds_ys = []
        for xy in overlay_urls:
            ds_xs.append(self.obj_parent.h5file[xy[0]])
            ds_ys.append(self.obj_parent.h5file[xy[1]])
        
        
        ### for compatibility ... to be removed
        ds_x_url = ds.attrs.get("x","")
        ds_y_url = ds.attrs.get("y","")
        if ds_x_url and ds_y_url:
            ds_xs.append(self.obj_parent.h5file[ds_x_url])
            ds_ys.append(self.obj_parent.h5file[ds_y_url])
        ###
        graphicsView.clear()
        
        
        for i, x_ds in enumerate(ds_xs):
            y_ds = ds_ys[i]
            # this is a litte clumsy, but for the cases tested it works well 
            if len(x_ds.shape) == 1 and len(y_ds.shape) == 1:
                self.TraceSelector.setEnabled(False)
                x_data = np.array(x_ds)
                y_data = np.array(y_ds)
                
            if len(x_ds.shape) == 2 and len(y_ds.shape) == 2:
                self.TraceSelector.setEnabled(True)
                range_max = np.minimum( x_ds.shape[0],y_ds.shape[0])
                self.TraceSelector.setRange(-1*range_max,range_max-1)
                
                x_data = np.array(x_ds[self.TraceNum],axis=x_axis[i])
                y_data = np.array(y_ds[self.TraceNum],axis=y_axis[i])

            if len(x_ds.shape) == 1 and len(y_ds.shape) == 2:
                self.TraceSelector.setEnabled(True)
                range_max = y_ds.shape[0]
                self.TraceSelector.setRange(-1*range_max,range_max-1)
                
                x_data = np.array(x_ds)#,axis=x_axis[i])
                y_data = np.array(y_ds[self.TraceNum])#y_axis[i])#,axis=y_axis[i])

            else:
                return
            x_name = x_ds.attrs.get("name","_none_")                
            y_name = y_ds.attrs.get("name","_none_")
            
            x_unit = x_ds.attrs.get("unit","_none_")
            y_unit = y_ds.attrs.get("unit","_none_")
            #print x_name, y_name, x_unit, y_unit
            #plot.setPen((200,200,100))
            graphicsView.setLabel('left', y_name, units=y_unit)
            graphicsView.setLabel('bottom', x_name , units=x_unit)
            #plot.setData(y=y_data, x=x_data)
            graphicsView.plot(y=y_data, x=x_data,pen=(i,3))
                
    def _display_1D_data(self,graphicsView):
        ds = self.ds
        
        ydata = np.array(ds)
        if len(ydata.shape) == 2:
            ydata = ydata[self.TraceNum]
        x0 = ds.attrs.get("x0",0)
        dx = ds.attrs.get("dx",1)
        x_data = [x0+dx*i for i in xrange(len(ydata))]
        
        x_name = ds.attrs.get("x_name","_none_")
        name = ds.attrs.get("name","_none_")
        x_unit = ds.attrs.get("x_unit","_none_")
        unit = ds.attrs.get("unit","_none_")
        
        #plot.setPen((200,200,100))
        graphicsView.setLabel('left', name, units=unit)
        graphicsView.setLabel('bottom', x_name , units=x_unit)
        graphicsView.plot(y=ydata, x=x_data, clear = True, pen=(200,200,100))
        #plot.setData(y=ydata, x=x_data)
        
    def _display_2D_data(self,graphicsView):
        #load the dataset:
        ds = self.ds
        #fill = ds.attrs.get("fill",1)
        fill_x = ds.shape[0]
        fill_y = ds.shape[1]
        #data = np.array(ds[:fill])
        data = np.array(ds)
        
        x0 = ds.attrs.get("x0",0)
        dx = ds.attrs.get("dx",1)
        y0 = ds.attrs.get("y0",0)
        dy = ds.attrs.get("dy",1)
        
        xmin = x0
        xmax = x0+fill_x*dx
        ymin = y0
        ymax = y0+fill_y*dy

        x_name = ds.attrs.get("x_name","_none_")        
        y_name = ds.attrs.get("y_name","_none_")
        name = ds.attrs.get("name","_none_")

        x_unit = ds.attrs.get("x_unit","_none_")
        y_unit = ds.attrs.get("y_unit","_none_")
        unit = ds.attrs.get("unit","_none_")
        
        
        pos = (xmin,ymin)
        
        #scale=(xmax/float(data.shape[0]),ymax/float(data.shape[1]))
        scale=((abs(xmax-xmin))/float(data.shape[0]),(ymax-ymin)/float(data.shape[1]))
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
        
        
 

