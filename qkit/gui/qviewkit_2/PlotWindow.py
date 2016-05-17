# -*- coding: utf-8 -*-
"""
@author: hannes.rotzinger@kit.edu @ 2015,2016
"""


from PyQt4.QtCore import *
from PyQt4.QtGui import *

from plot_view import Ui_Form
import pyqtgraph as pg
from qkit.storage.hdf_constants import ds_types
from PlotWindow_lib import _display_1D_view, _display_1D_data, _display_2D_data, _display_table, _display_text
import sys


#class PlotWindow(QMainWindow, Ui_MainWindow):
class PlotWindow(QWidget,Ui_Form):

    def myquit(self):
        exit()

    def __init__(self,parent,data,dataset_url):#,ds_type):
        self.DATA = data
        self.dataset_url = dataset_url
        self.obj_parent = parent
        
        #try: self.ds_type = int(ds_type)
        #except: 
        #self.ds_type = -1
        
        super(PlotWindow , self).__init__()
        Ui_Form.__init__(self)


        "This variable controlles if a window is new, see update_plots()."
        self._windowJustCreated = True
        "connect update_plots to the DatasetWindow"
        self.obj_parent.refresh_signal.connect(self.update_plots)

    def closeEvent(self, event):
        "overwrite the closeEvent handler"
        #print "closeEvent called"
        #self.deleteLater()
        self.DATA._toBe_deleted(self.dataset_url)
        self.DATA._remove_plot_widgets()
        event.accept()
        
    @pyqtSlot()
    def update_plots(self):
        """ This brings up everything and is therefore the main function. 
        Update Plots is either periodically called e.g. by the timer or once on startup. """
        
        self.ds = self.obj_parent.h5file[self.dataset_url]
        self.ds_type = self.ds.attrs.get('ds_type', -1)
        
        if self._windowJustCreated:
            # A few state variables:
            self._onPlotTypeChanged = True
            self._windowJustCreated = False
            
            self.graphicsView = None
            self.TraceValueChanged  = False
            self.SliceValueChanged  = False
            self.TraceXValueChanged = False
            self.TraceYValueChanged = False
            
            # the following calls rely on ds_type and setup the layout of the plot window.
            self.setupUi(self,self.ds_type)
        
            window_title = str(self.dataset_url.split('/')[-1]) +" "+ str(self.DATA.filename)
            self.setWindowTitle(window_title)
            
            self._setup_signal_slots()
            self._setDefaultView()
            
            

        try:
            if self.view_type == self.view_types['1D-V']:
                if not self.graphicsView or self._onPlotTypeChanged:
                    self._onPlotTypeChanged = False
                    self.graphicsView = pg.PlotWidget(name=self.dataset_url)
                    self.graphicsView.setObjectName(self.dataset_url)
                    self.addQvkMenu(self.graphicsView.plotItem.getMenu())
                    self.gridLayout.addWidget(self.graphicsView,0,0)
                _display_1D_view(self,self.graphicsView)

            elif self.view_type == self.view_types['1D']:
                if not self.graphicsView or self._onPlotTypeChanged:
                    self._onPlotTypeChanged = False
                    self.graphicsView = pg.PlotWidget(name=self.dataset_url)
                    self.graphicsView.setObjectName(self.dataset_url)
                    self.addQvkMenu(self.graphicsView.plotItem.getMenu())
                    self.gridLayout.addWidget(self.graphicsView,0,0)
                _display_1D_data(self,self.graphicsView)

            elif self.view_type == self.view_types['2D']:
                if not self.graphicsView or self._onPlotTypeChanged:
                    self._onPlotTypeChanged = False
                    self.graphicsView = pg.ImageView(self.obj_parent,view=pg.PlotItem())
                    self.graphicsView.setObjectName(self.dataset_url)
                    self.graphicsView.view.setAspectLocked(False)
                    self.gridLayout.addWidget(self.graphicsView,0,0)
                _display_2D_data(self,self.graphicsView)

            elif self.view_type == self.view_types['table']:
                if not self.graphicsView or self._onPlotTypeChanged:
                    self._onPlotTypeChanged = False
                    self.graphicsView = pg.TableWidget()
                    self.graphicsView.setWindowTitle(self.dataset_url+'_table')
                    self.graphicsView.setObjectName(self.dataset_url)
                    self.gridLayout.addWidget(self.graphicsView,0,0)
                _display_table(self,self.graphicsView)
                
            elif self.view_type == self.view_types['txt']:
                if not self.graphicsView or self._onPlotTypeChangeBox:
                    self._onPlotTypeChangeBox = False
                    self.graphicsView = QPlainTextEdit()
                    self.graphicsView.setObjectName(self.dataset_url)
                    self.gridLayout.addWidget(self.graphicsView,0,0)
                    #self.graphicsView.setObjectName(self.dataset_url)
                    self.gridLayout.addWidget(self.graphicsView,0,0)
                _display_text(self,self.graphicsView)
            else:
                print "This should not be here: View Type:"+str(self.view_type)
        except NameError:#IOError:
          pass
        #except ValueError,e:
            #print "PlotWindow: Value Error; Dataset not yet available", self.dataset_url
            #print e


    def _setup_signal_slots(self):
        
        if self.ds_type == ds_types['vector'] or self.ds_type == ds_types['coordinate']:
            QObject.connect(self.PlotTypeSelector,SIGNAL("currentIndexChanged(int)"),self._onPlotTypeChangeVector)
            
        elif self.ds_type == ds_types['matrix'] or self.ds_type == -1:
            QObject.connect(self.PlotTypeSelector,SIGNAL("currentIndexChanged(int)"),self._onPlotTypeChangeMatrix)
            QObject.connect(self.TraceSelector,   SIGNAL("valueChanged(int)"),       self._setTraceNum)
            QObject.connect(self.TraceValue,      SIGNAL("returnPressed()"),         self._setTraceValue)

        elif self.ds_type == ds_types['box']:
            QObject.connect(self.PlotTypeSelector,SIGNAL("currentIndexChanged(int)"),self._onPlotTypeChangeBox)
            QObject.connect(self.SliceSelector,   SIGNAL("valueChanged(int)"),       self._setSliceNum)
            QObject.connect(self.SliceValue,      SIGNAL("returnPressed()"),         self._setSliceValue)
            QObject.connect(self.TraceXSelector,  SIGNAL("valueChanged(int)"),       self._setTraceXNum)
            QObject.connect(self.TraceXValue,     SIGNAL("returnPressed()"),         self._setTraceXValue)
            QObject.connect(self.TraceYValue,     SIGNAL("returnPressed()"),         self._setTraceYValue)
            QObject.connect(self.TraceYSelector,  SIGNAL("valueChanged(int)"),       self._setTraceYNum)

        elif self.ds_type == ds_types['view']:
            QObject.connect(self.TraceSelector,   SIGNAL("valueChanged(int)"),       self._setTraceNum)
            QObject.connect(self.TraceValue,      SIGNAL("returnPressed()"),         self._setTraceValue)

    def keyPressEvent(self, ev):
        #print "Received Key Press Event!! You Pressed: "+ event.text()
        if ev.key() == Qt.Key_S:
            #print '# ',ev.key()
            print self.data_coord
            sys.stdout.flush()
        
    def _setDefaultView(self):
        """Setup the view type: settle which type of window is displaying a dataset.
            It is distinguished with what layout a dataset is displayed.
            Co -> 1d
            vec - 1d
            matrix -> 2d
            (...)
        """
        
        self.view_types = {'1D':0,'1D-V':1, '2D':2, '3D':3, 'table':4, 'txt':5}
        self.plot_styles = {'line':0,'linepoint':1,'point':2}

        self.plot_style = 0
        self.TraceNum = -1
        self.view_type = self.ds.attrs.get("view_type",None)
        
        if self.ds_type == ds_types["coordinate"]:
            self.view_type = self.view_types['1D']
            self._defaultCoord()

        elif self.ds_type == ds_types["vector"]:            
            self.view_type = self.view_types['1D']
            self._defaultVector()
            
        elif self.ds_type == ds_types["matrix"]:            
            self.view_type = self.view_types['2D']
            self._defaultMatrix()
            
        elif self.ds_type == ds_types["box"]:            
            self.view_type = self.view_types['2D']
            self._defaultBox()
            
        elif self.ds_type == ds_types["txt"]:
            self.view_type = self.view_types['txt']
 
        elif self.ds_type == ds_types["view"]:
            self.view_type = self.view_types['1D-V']
            self._defaultView()
            
        else:
            self._defaultOld()

    def _defaultCoord(self):
        self.PlotTypeSelector.setCurrentIndex(0)
        
    def _defaultVector(self):
        self.PlotTypeSelector.setCurrentIndex(0)
        
    def _defaultMatrix(self):
        self.TraceSelector.setEnabled(False)
        shape = self.ds.shape[0]
        self.TraceSelector.setRange(-1*shape,shape-1)
        self.PlotTypeSelector.setCurrentIndex(0)
        
    def _defaultBox(self):
        shape = self.ds.shape
        self.SliceSelector.setEnabled(True)
        self.SliceSelector.setRange(-1*shape[2],shape[2]-1)
        self.SliceSelector.setValue(shape[2]/2)

        self.TraceXSelector.setEnabled(False)
        self.TraceXSelector.setRange(-1*shape[0],shape[0]-1)

        self.TraceYSelector.setEnabled(False)
        self.TraceYSelector.setRange(-1*shape[1],shape[1]-1)

        self.PlotTypeSelector.setCurrentIndex(0)
        
    def _defaultView(self):
        self.TraceSelector.setEnabled(True)
        
        
    def _defaultOld(self):
        if not self.view_type:
            if len(self.ds.shape) == 1:
                self.PlotTypeSelector.setCurrentIndex(1)
                self.view_type = self.view_types['1D']
                self.TraceSelector.setEnabled(False)
                self.PlotTypeSelector.setEnabled(False)
                self.plot_style = self.plot_styles['line']
            elif len(self.ds.shape) == 2:
                self.TraceSelector.setEnabled(False)
                shape = self.ds.shape[0]
                self.TraceSelector.setRange(-1*shape,shape-1)
                self.PlotTypeSelector.setCurrentIndex(0)
                self.view_type = self.view_types['2D']
            elif len(self.ds.shape) == 3:
                self.TraceSelector.setEnabled(False)
                shape = self.ds.shape[0]
                self.view_type = self.view_types['3D']
                self.PlotTypeSelector.setEnabled(False)
            else:
                self.TraceSelector.setEnabled(True)
                self.view_type = self.view_types['1D']
        else:
            self.TraceSelector.setEnabled(True)
            self.PlotTypeSelector.setEnabled(False)

    def _setTraceValue(self):
        xval = str(self.TraceValue.displayText())
        try:
            self._trace_value = float(xval.split()[0])
        except ValueError:
            return
        self.TraceValueChanged = True
        self.obj_parent.pw_refresh_signal.emit()

    def _setTraceNum(self,num):
        self.TraceNum = num
        if not self.TraceValueChanged:
            self.obj_parent.pw_refresh_signal.emit()
            
    def _setSliceValue(self):
        xval = str(self.SliceValue.displayText())
        try:
            self._slice_value = float(xval.split()[0])
        except ValueError:
            return
        self.SliceValueChanged = True
        self.obj_parent.pw_refresh_signal.emit()
    
    def _setSliceNum(self,num):
        self.SliceNum = num
        if not self.SliceValueChanged:
            self.obj_parent.pw_refresh_signal.emit()

    def _setTraceXValue(self):
        xval = str(self.TraceXValue.displayText())
        try:
            self._traceX_value = float(xval.split()[0])
        except ValueError:
            return
        self.TraceXValueChanged = True
        self.obj_parent.pw_refresh_signal.emit()
    
    def _setTraceXNum(self,num):
        self.TraceXNum = num
        if not self.TraceXValueChanged:
            self.obj_parent.pw_refresh_signal.emit()
    
    def _setTraceYValue(self):
        xval = str(self.TraceYValue.displayText())
        try:
            self._traceY_value = float(xval.split()[0])
        except ValueError:
            return
        self.TraceYValueChanged = True
        self.obj_parent.pw_refresh_signal.emit()
    
    def _setTraceYNum(self,num):
        self.TraceYNum = num
        if not self.TraceYValueChanged:
            self.obj_parent.pw_refresh_signal.emit()

    def _onPlotTypeChangeVector(self, index):
        self._onPlotTypeChanged = True
        if index == 0:
            self.view_type = self.view_types['1D']
        if index == 1:
            self.view_type = self.view_types['table']

        if not self._windowJustCreated:
            self.obj_parent.pw_refresh_signal.emit()

    def _onPlotTypeChangeMatrix(self, index):
        self._onPlotTypeChanged = True
        if index == 0:
            self.view_type = self.view_types['2D']
            self.TraceSelector.setEnabled(False)
        if index == 1:
            self.view_type = self.view_types['1D']
            self.TraceSelector.setEnabled(True)
        if index == 2:
            self.view_type = self.view_types['table']
            self.TraceSelector.setEnabled(False)

        if not self._windowJustCreated:
            self.obj_parent.pw_refresh_signal.emit()

    def _onPlotTypeChangeBox(self, index):
        self._onPlotTypeChanged = True
        if index == 0:
            self.view_type = self.view_types['2D']
            self.SliceSelector.setEnabled(True)
        if index == 1:
            self.view_type = self.view_types['2D']
            self.SliceSelector.setEnabled(False)
            self.TraceXSelector.setEnabled(True)
            self.TraceYSelector.setEnabled(False)
        if index == 2:
            self.view_type = self.view_types['2D']
            self.SliceSelector.setEnabled(False)
            self.TraceYSelector.setEnabled(True)
            self.TraceXSelector.setEnabled(False)
        if index == 3:
            self.view_type = self.view_types['1D']
            self.SliceSelector.setEnabled(False)
            self.TraceXSelector.setEnabled(True)
            self.TraceYSelector.setEnabled(True)

        if not self._windowJustCreated:
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



    def _getXValueFromTraceNum(self,ds,num):
        x0 = ds.attrs.get("x0",0)
        dx = ds.attrs.get("dx",1)
        unit = ds.attrs.get("x_unit","")
        max_len = ds.shape[0]
        if num>-1:
            xval = x0+num*dx
        else:
            xval = x0+(max_len+num)*dx
        return str(xval)+" "+unit

    def addQvkMenu(self,menu):
        self.qvkMenu = QMenu("Qviewkit")

        point = QAction(u'Point', self.qvkMenu)
        self.qvkMenu.addAction(point)
        point.triggered.connect(self.setPointMode)

        line = QAction(u'Line', self.qvkMenu)
        self.qvkMenu.addAction(line)
        line.triggered.connect(self.setLineMode)

        pointLine = QAction(u'Point+Line', self.qvkMenu)
        self.qvkMenu.addAction(pointLine)
        pointLine.triggered.connect(self.setPointLineMode)

        menu.addMenu(self.qvkMenu)

    @pyqtSlot()
    def setPointMode(self):
        self.plot_style = self.plot_styles['point']
        if not self._windowJustCreated:
            self.obj_parent.pw_refresh_signal.emit()

    @pyqtSlot()
    def setLineMode(self):
        self.plot_style = self.plot_styles['line']
        if not self._windowJustCreated:
            self.obj_parent.pw_refresh_signal.emit()

    @pyqtSlot()
    def setPointLineMode(self):
        self.plot_style = self.plot_styles['linepoint']
        if not self._windowJustCreated:
            self.obj_parent.pw_refresh_signal.emit()
    