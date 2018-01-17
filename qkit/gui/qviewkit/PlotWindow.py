# -*- coding: utf-8 -*-
"""
@author: hannes.rotzinger@kit.edu / 2015,2016,2017 
         marco.pfirrmann@kit.edu / 2016, 2017
Qlicense: GPL
"""
# support both PyQt4 and 5
in_pyqt5 = False
import sys
try:
    from PyQt5 import QtCore
    from PyQt5.QtCore import Qt,QObject,pyqtSlot
    from PyQt5.QtWidgets import QWidget,QPlainTextEdit,QMenu,QAction
    #from PyQt5 import Qt
    in_pyqt5 = True
except ImportError as e:
    pass
if not in_pyqt5:
    try:
        from PyQt4 import QtCore
        from PyQt4.QtCore import Qt,QObject,pyqtSlot
        from PyQt4.QtGui import QWidget,QPlainTextEdit,QMenu,QAction
    except ImportError:
        print("import of PyQt5 and PyQt4 failed. Install one of those.")
        sys.exit(-1)

import pyqtgraph as pg

import qkit
from qkit.gui.qviewkit.plot_view import Ui_Form
from qkit.storage.hdf_constants import ds_types, view_types
from qkit.gui.qviewkit.PlotWindow_lib import _display_1D_view, _display_1D_data, _display_2D_data, _display_table, _display_text



class PlotWindow(QWidget,Ui_Form):

    def myquit(self):
        exit()

    def __init__(self,parent,data,dataset_url):
        self.DATA = data
        self.dataset_url = dataset_url
        self.obj_parent = parent


        super(PlotWindow , self).__init__()
        Ui_Form.__init__(self)
        # move forward ...
        self.setWindowState(Qt.WindowActive)
        self.activateWindow()
        self.raise_()



        "This variable controlles if a window is new, see update_plots()."
        self._windowJustCreated = True
        "connect update_plots to the DatasetWindow"
        self.obj_parent.refresh_signal.connect(self.update_plots)

    def closeEvent(self, event):
        "overwrite the closeEvent handler"
        self.DATA._toBe_deleted(self.dataset_url)
        self.DATA._remove_plot_widgets()
        event.accept()

    @pyqtSlot()
    def update_plots(self):
        """ This brings up everything and is therefore the main function.
        Update Plots is either periodically called e.g. by the timer or once on startup. """
        #print "PWL update_plots:", self.obj_parent.h5file

        self.ds = self.obj_parent.h5file[self.dataset_url]
        self.ds_type = self.ds.attrs.get('ds_type', -1)

        if self._windowJustCreated:
            # A few state variables:
            self._onPlotTypeChanged = True
            self._windowJustCreated = False

            self.graphicsView = None
            self.TraceValueChanged  = False
            self.TraceZValueChanged = False
            self.TraceXValueChanged = False
            self.TraceYValueChanged = False
            self.VTraceZValueChanged = False
            self.VTraceXValueChanged = False
            self.VTraceYValueChanged = False

            # the following calls rely on ds_type and setup the layout of the plot window.
            self.setupUi(self,self.ds_type)

            window_title = str(self.dataset_url.split('/')[-1]) +" "+ str(self.DATA.filename)
            self.setWindowTitle(window_title)


            self._setDefaultView()
            self._setup_signal_slots()



        try:
            if self.view_type == view_types['1D-V']:
                if not self.graphicsView or self._onPlotTypeChanged:
                    self._onPlotTypeChanged = False
                    self.graphicsView = pg.PlotWidget(name=self.dataset_url)
                    self.graphicsView.setObjectName(self.dataset_url)
                    self.addQvkMenu(self.graphicsView.plotItem.getMenu())
                    self.gridLayout.addWidget(self.graphicsView,0,0)
                _display_1D_view(self,self.graphicsView)

            elif self.view_type == view_types['1D']:
                if not self.graphicsView or self._onPlotTypeChanged:
                    self._onPlotTypeChanged = False
                    self.graphicsView = pg.PlotWidget(name=self.dataset_url)
                    self.graphicsView.setObjectName(self.dataset_url)
                    self.addQvkMenu(self.graphicsView.plotItem.getMenu())
                    self.gridLayout.addWidget(self.graphicsView,0,0)
                _display_1D_data(self,self.graphicsView)

            elif self.view_type == view_types['2D']:
                if not self.graphicsView or self._onPlotTypeChanged:
                    self._onPlotTypeChanged = False
                    self.graphicsView = pg.ImageView(self.obj_parent,view=pg.PlotItem())
                    self.graphicsView.setObjectName(self.dataset_url)
                    self.addQvkMenu(self.graphicsView.view.getMenu())
                    #self.addQvkMenu(self..graphicsView.getImageItem().getMenu())
                    self.graphicsView.view.setAspectLocked(False)
                    self.gridLayout.addWidget(self.graphicsView,0,0)
                _display_2D_data(self,self.graphicsView)

            elif self.view_type == view_types['table']:
                if not self.graphicsView or self._onPlotTypeChanged:
                    self._onPlotTypeChanged = False
                    self.graphicsView = pg.TableWidget(sortable=False)
                    self.graphicsView.setWindowTitle(self.dataset_url+'_table')
                    self.graphicsView.setObjectName(self.dataset_url)
                    self.gridLayout.addWidget(self.graphicsView,0,0)
                _display_table(self,self.graphicsView)

            elif self.view_type == view_types['txt']:
                if not self.graphicsView or self._onPlotTypeChangeBox:
                    self._onPlotTypeChangeBox = False
                    self.graphicsView = QPlainTextEdit()
                    self.graphicsView.setObjectName(self.dataset_url)
                    self.gridLayout.addWidget(self.graphicsView,0,0)
                    #self.graphicsView.setObjectName(self.dataset_url)
                    self.gridLayout.addWidget(self.graphicsView,0,0)
                self.graphicsView.clear()
                _display_text(self,self.graphicsView)
            else:
                print("This should not be here: View Type:"+str(self.view_type))
        except ValueError as e:
            print("PlotWindow: Value Error; Dataset not yet available", self.dataset_url)
            print(e)


    def _setup_signal_slots(self):
        if self.ds_type == ds_types['vector'] or self.ds_type == ds_types['coordinate']:
            self.PlotTypeSelector.currentIndexChanged.connect(self._onPlotTypeChangeVector)

        elif self.ds_type == ds_types['matrix'] or self.ds_type == -1:
            self.PlotTypeSelector.currentIndexChanged.connect(self._onPlotTypeChangeMatrix)
            self.TraceSelector.valueChanged.connect(self._setTraceNum)
            self.TraceValue.returnPressed.connect(self._setTraceValue)

        elif self.ds_type == ds_types['box']:
            self.PlotTypeSelector.currentIndexChanged.connect(self._onPlotTypeChangeBox)
            self.TraceXSelector.valueChanged.connect(self._setBTraceXNum)
            self.TraceYSelector.valueChanged.connect(self._setBTraceYNum)
            self.TraceZSelector.valueChanged.connect(self._setBTraceZNum)
            self.TraceXValue.returnPressed.connect(self._setBTraceXValue)            
            self.TraceYValue.returnPressed.connect(self._setBTraceYValue)            
            self.TraceZValue.returnPressed.connect(self._setBTraceZValue)

        elif self.ds_type == ds_types['view']:
            self.VTraceXSelector.valueChanged.connect(self._setVTraceXNum)
            self.VTraceYSelector.valueChanged.connect(self._setVTraceYNum)
            self.VTraceXValue.returnPressed.connect(self._setVTraceXValue)           
            self.VTraceYValue.returnPressed.connect(self._setVTraceYValue)

    def keyPressEvent(self, ev):
        #print("Received Key Press Event!! You Pressed: "+ event.text())
        if ev.key() == Qt.Key_S:
            #print '# ',ev.key()
            print(self.data_coord)
            sys.stdout.flush()

    def _setDefaultView(self):
        """
        Setup the view type: settle which type of window is displaying a dataset.
        It is distinguished with what layout a dataset is displayed.
        Co -> 1d
        vec -> 1d
        matrix -> 2d
        box -> 3d
        """

        self.plot_styles = {'line':0,'linepoint':1,'point':2}
        self.manipulations = {'dB':1, 'wrap':2, 'linear':4, 'remove_zeros':8,
                              'sub_offset_avg_y':16, 'norm_data_avg_x':32} #BITMASK for manipulation

        self.plot_style = 0
        self.manipulation = 8
        self.TraceNum = -1
        self.view_type = self.ds.attrs.get("view_type",None)

        if self.ds_type == ds_types["coordinate"]:
            self.view_type = view_types['1D']
            self._defaultCoord()

        elif self.ds_type == ds_types["vector"]:
            self.view_type = view_types['1D']
            self._defaultVector()

        elif self.ds_type == ds_types["matrix"]:
            self.view_type = view_types['2D']
            self._defaultMatrix()

        elif self.ds_type == ds_types["box"]:
            self.view_type = view_types['2D']
            self._defaultBox()

        elif self.ds_type == ds_types["txt"]:
            self.view_type = view_types['txt']

        elif self.ds_type == ds_types["view"]:
            self.view_type = view_types['1D-V']
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
        
        self.TraceZSelector.setEnabled(True)
        self.TraceZSelector.setRange(-1*shape[2],shape[2]-1)
        self.TraceZSelector.setValue(shape[2]/2)
        self.TraceZNum = shape[2]/2
        
        self.TraceXSelector.setEnabled(False)
        self.TraceXSelector.setRange(-1*shape[0],shape[0]-1)
        self.TraceXNum = -1        

        self.TraceYSelector.setEnabled(False)
        self.TraceYSelector.setRange(-1*shape[1],shape[1]-1)
        self.TraceYNum = -1
        
        self.PlotTypeSelector.setCurrentIndex(2)

    def _defaultView(self):
        self.VTraceXSelector.setEnabled(True)
        self.VTraceYSelector.setEnabled(True)
        self.VTraceXNum = -1
        self.VTraceYNum = -1 

    def _defaultOld(self):
        if not self.view_type:
            if len(self.ds.shape) == 1:
                self.PlotTypeSelector.setCurrentIndex(1)
                self.view_type = view_types['1D']
                self.TraceSelector.setEnabled(False)
                self.PlotTypeSelector.setEnabled(False)
                self.plot_style = self.plot_styles['line']
            elif len(self.ds.shape) == 2:
                self.TraceSelector.setEnabled(False)
                shape = self.ds.shape[0]
                self.TraceSelector.setRange(-1*shape,shape-1)
                self.PlotTypeSelector.setCurrentIndex(0)
                self.view_type = view_types['2D']
            elif len(self.ds.shape) == 3:
                self.TraceSelector.setEnabled(False)
                shape = self.ds.shape[0]
                self.view_type = view_types['2D']
                self.PlotTypeSelector.setEnabled(False)
            else:
                self.TraceSelector.setEnabled(True)
                self.view_type = view_types['1D']
        else:
            self.TraceSelector.setEnabled(True)
            self.PlotTypeSelector.setEnabled(False)

    ####### this looks ugly
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
    #######
    def _setVTraceXValue(self):
        xval = str(self.VTraceXValue.displayText())
        try:
            self._VtraceX_value = float(xval.split()[0])
        except ValueError:
            return
        self.VTraceXValueChanged = True
        self.obj_parent.pw_refresh_signal.emit()


    def _setVTraceXNum(self,num):
        self.VTraceXNum = num
        if not self.VTraceXValueChanged:
            self.obj_parent.pw_refresh_signal.emit()

    def _setVTraceYValue(self):
        xval = str(self.VTraceYValue.displayText())
        try:
            self._VtraceY_value = float(xval.split()[0])
        except ValueError:
            return
        self.VTraceYValueChanged = True
        self.obj_parent.pw_refresh_signal.emit()


    def _setVTraceYNum(self,num):
        self.VTraceYNum = num
        if not self.TraceYValueChanged:
            self.obj_parent.pw_refresh_signal.emit()

    def _setBTraceXValue(self):
        xval = str(self.TraceXValue.displayText())
        try:
            self._traceX_value = float(xval.split()[0])
        except ValueError:
            return
        self.TraceXValueChanged = True
        self.obj_parent.pw_refresh_signal.emit()

    def _setBTraceXNum(self,num):
        self.TraceXNum = num
        if not self.TraceXValueChanged:
            self.obj_parent.pw_refresh_signal.emit()

    def _setBTraceYValue(self):
        xval = str(self.TraceYValue.displayText())
        try:
            self._traceY_value = float(xval.split()[0])
        except ValueError:
            return
        self.TraceYValueChanged = True
        self.obj_parent.pw_refresh_signal.emit()

    def _setBTraceYNum(self,num):
        self.TraceYNum = num
        if not self.TraceYValueChanged:
            self.obj_parent.pw_refresh_signal.emit()

    def _setBTraceZValue(self):
        xval = str(self.TraceZValue.displayText())
        try:
            self._traceZ_value = float(xval.split()[0])
        except ValueError:
            return
        self.TraceZValueChanged = True
        self.obj_parent.pw_refresh_signal.emit()

    def _setBTraceZNum(self,num):
        self.TraceZNum = num
        if not self.TraceZValueChanged:
            self.obj_parent.pw_refresh_signal.emit()

    def _onPlotTypeChangeVector(self, index):
        self._onPlotTypeChanged = True
        if index == 0:
            self.view_type = view_types['1D']
        if index == 1:
            self.view_type = view_types['table']

        if not self._windowJustCreated:
            self.obj_parent.pw_refresh_signal.emit()

    def _onPlotTypeChangeMatrix(self, index):
        self._onPlotTypeChanged = True
        if index == 0:
            self.view_type = view_types['2D']
            self.TraceSelector.setEnabled(False)
        if index == 1:
            self.view_type = view_types['1D']
            self.TraceSelector.setEnabled(True)
        if index == 2:
            self.view_type = view_types['table']
            self.TraceSelector.setEnabled(False)

        if not self._windowJustCreated:
            self.obj_parent.pw_refresh_signal.emit()

    def _onPlotTypeChangeBox(self, index):
        self._onPlotTypeChanged = True
        if index == 0:
            self.view_type = view_types['2D']
            self.TraceXSelector.setEnabled(True)
            self.TraceYSelector.setEnabled(False)
            self.TraceZSelector.setEnabled(False)
        if index == 1:
            self.view_type = view_types['2D']
            self.TraceXSelector.setEnabled(False)
            self.TraceYSelector.setEnabled(True)
            self.TraceZSelector.setEnabled(False)
        if index == 2:
            self.view_type = view_types['2D']
            self.TraceXSelector.setEnabled(False)
            self.TraceYSelector.setEnabled(False)
            self.TraceZSelector.setEnabled(True)
        if index == 3:
            self.view_type = view_types['1D']
            self.TraceXSelector.setEnabled(True)
            self.TraceYSelector.setEnabled(True)
            self.TraceZSelector.setEnabled(False)

        if not self._windowJustCreated:
            self.obj_parent.pw_refresh_signal.emit()

    def _addXPlotChange(self):
        pass
    def _addYPlotChange(self):
        pass

    def _init_XY_add(self):
        for i,key in enumerate(self.DATA.ds_tree_items.keys()):
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
        return str(xval)+" "+str(unit)

    def _getYValueFromTraceNum(self,ds,num):
        y0 = ds.attrs.get("y0",0)
        dy = ds.attrs.get("dy",1)
        unit = ds.attrs.get("y_unit","")
        max_len = ds.shape[1]
        if num>-1:
            yval = y0+num*dy
        else:
            yval = y0+(max_len+num)*dy
        return str(yval)+" "+str(unit)

    def _getZValueFromTraceNum(self,ds,num):
        z0 = ds.attrs.get("z0",0)
        dz = ds.attrs.get("dz",1)
        unit = ds.attrs.get("z_unit","")
        max_len = ds.shape[2]
        if num>-1:
            zval = z0+num*dz
        else:
            zval = z0+(max_len+num)*dz
        return str(zval)+" "+str(unit)

    def addQvkMenu(self,menu):
        self.qvkMenu = QMenu("Qviewkit")

        point = QAction('Point', self.qvkMenu)
        self.qvkMenu.addAction(point)
        point.triggered.connect(self.setPointMode)

        line = QAction('Line', self.qvkMenu)
        self.qvkMenu.addAction(line)
        line.triggered.connect(self.setLineMode)

        pointLine = QAction('Point+Line', self.qvkMenu)
        self.qvkMenu.addAction(pointLine)
        pointLine.triggered.connect(self.setPointLineMode)

        dB_scale = QAction('dB / linear', self.qvkMenu)
        self.qvkMenu.addAction(dB_scale)
        dB_scale.triggered.connect(self.setdBScale)
        
        phase_wrap = QAction('(un)wrap phase data', self.qvkMenu)
        self.qvkMenu.addAction(phase_wrap)
        phase_wrap.triggered.connect(self.setPhaseWrap)
        
        linear_correction = QAction('linearly correct data', self.qvkMenu)
        self.qvkMenu.addAction(linear_correction)
        linear_correction.triggered.connect(self.setLinearCorrection)
        
        offset_correction = QAction('data-<data:y>', self.qvkMenu)
        self.qvkMenu.addAction(offset_correction)
        offset_correction.triggered.connect(self.setOffsetCorrection)
        
        norm_correction = QAction('data/<data:x>', self.qvkMenu)
        self.qvkMenu.addAction(norm_correction)
        norm_correction.triggered.connect(self.setNormDataCorrection)

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

    @pyqtSlot()
    def setdBScale(self):
        self.manipulation = self.manipulation ^ self.manipulations['dB']
        #print "{:08b}".format(self.manipulation)
        if not self._windowJustCreated:
            self.obj_parent.pw_refresh_signal.emit()
      
    @pyqtSlot()
    def setPhaseWrap(self):
        self.manipulation = self.manipulation ^ self.manipulations['wrap']
        #print "{:08b}".format(self.manipulation)
        if not self._windowJustCreated:
            self.obj_parent.pw_refresh_signal.emit()

    @pyqtSlot()
    def setLinearCorrection(self):
        self.manipulation = self.manipulation ^ self.manipulations['linear']
        #print "{:08b}".format(self.manipulation)
        if not self._windowJustCreated:
            self.obj_parent.pw_refresh_signal.emit()
            
    @pyqtSlot()
    def setOffsetCorrection(self):
        self.manipulation = self.manipulation ^ self.manipulations['sub_offset_avg_y']
        #print "{:08b}".format(self.manipulation)
        if not self._windowJustCreated:
            self.obj_parent.pw_refresh_signal.emit()

    @pyqtSlot()
    def setNormDataCorrection(self):
        self.manipulation = self.manipulation ^ self.manipulations['norm_data_avg_x']
        #print "{:08b}".format(self.manipulation)
        if not self._windowJustCreated:
            self.obj_parent.pw_refresh_signal.emit()