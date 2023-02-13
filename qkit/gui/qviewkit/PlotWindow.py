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
    from PyQt5.QtWidgets import QWidget,QPlainTextEdit,QMenu,QAction, QWidgetAction, QLabel, QActionGroup
    from PyQt5.QtGui import QBrush, QPainter, QPixmap, QFont
    #from PyQt5 import Qt
    in_pyqt5 = True
except ImportError as e:
    pass
if not in_pyqt5:
    try:
        from PyQt4 import QtCore
        from PyQt4.QtCore import Qt,QObject,pyqtSlot
        from PyQt4.QtGui import QWidget,QPlainTextEdit,QMenu,QAction, QWidgetAction, QLabel, QBrush, QPainter, QPixmap, QActionGroup, QFont
    except ImportError:
        print("import of PyQt5 and PyQt4 failed. Install one of those.")
        sys.exit(-1)

import pyqtgraph as pg
import numpy as np

import qkit
from qkit.gui.qviewkit.plot_view import Ui_Form
from qkit.storage.hdf_constants import ds_types, view_types
from qkit.gui.qviewkit.PlotWindow_lib import _display_1D_view, _display_1D_data, _display_2D_data, _display_table, _display_text
from qkit.gui.qviewkit.PlotWindow_lib import _get_ds, _get_ds_url, _get_name, _get_unit
from qkit.core.lib.misc import str3

class PlotWindow(QWidget,Ui_Form):
    """PlotWindow class organizes the correct display of data in a h5 file.

    This class coordinates the display of the data between the UI with it's 
    selector slots in Ui_Form and the plot functions in PlotWindow_lib. Here we
    handle the trigger events; update, open, and close the plot windows.
    Depending on the selector slot settings the associated plot function in the
    lib is called.
    We inherit from PyQt's QWidget class as well as the Ui_Form class.
    
    Heart and soul here is update_plots() which is connected to a timer trigger
    and checks the settings of all user slots and calls the correct lib
    function to display the data. The window starts with some default
    configuration for the dataset types.
    """
    def myquit(self):
        exit()

    def __init__(self,parent,data,dataset_url):
        """Inits PlotWindow with a parent (QMainWindow.treeWidget), data
        (qviewkit.main.DATA object), and a dataset_url to be opened.
        """
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
        """Checks the signal slots and changes the plotting attributes to be 
        evaluated by PlotWindow_lib.
        
        This function coordinates the changing input from the signal slots and
        updates the attributes that are parsed to the plotting lib functions.
        update_plots() is either periodically called e.g. by the timer or once 
        on startup.
        
        Args:
            self: Object of the PlotWindow class.
        Returns:
            No return variable. The function operates on the given object.
        """
        #print "PWL update_plots:", self.obj_parent.h5file
        
        try:
            self.ds = self.obj_parent.h5file[self.dataset_url]
        except ValueError as e:
            print(str(self.dataset_url)+": "+str(e))
            return
        self.ds_type = self.ds.attrs.get('ds_type', -1)
        
        # The axis names are parsed to plot_view's Ui_Form class to label the UI selectors 
        x_ds_name = _get_name(_get_ds(self.ds, self.ds.attrs.get('x_ds_url', '')))
        y_ds_name = _get_name(_get_ds(self.ds, self.ds.attrs.get('y_ds_url', '')))
        z_ds_name = _get_name(_get_ds(self.ds, self.ds.attrs.get('z_ds_url', '')))
        try:
            if self.ds.attrs.get('xy_0', ''):
                x_ds_name_view = _get_name(_get_ds(self.ds,_get_ds(self.ds, str3(self.ds.attrs.get('xy_0', '')).split(':')[1]).attrs.get('x_ds_url','')))
                y_ds_name_view = _get_name(_get_ds(self.ds,_get_ds(self.ds, str3(self.ds.attrs.get('xy_0', '')).split(':')[1]).attrs.get('y_ds_url','')))
            else:
                raise AttributeError
        except AttributeError:
            x_ds_name_view = '_none_'
            y_ds_name_view = '_none_'

        selector_label = [x_ds_name, y_ds_name, z_ds_name, x_ds_name_view, y_ds_name_view]    

        ## At first window creation the attributes are set to state zero.
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
            self.setupUi(self,self.ds_type, selector_label)

            window_title = str(self.dataset_url.split('/')[-1]) +" "+ str(self.DATA.filename)
            self.setWindowTitle(window_title)

            self._setDefaultView()
            self._setup_signal_slots()
        
        ## We check here for the view type given by either default setting or
        ## user input. Creates the canvas and calls the associated plot 
        ## function from the lib. For code constistence the variable names are
        ## the same in all view types.
        try:
            if self.view_type == view_types['1D-V']:
                if not self.graphicsView or self._onPlotTypeChanged:
                    self._onPlotTypeChanged = False
                    self.graphicsView = pg.PlotWidget(name=self.dataset_url)
                    self.graphicsView.setObjectName(self.dataset_url)
                    self.addQvkMenu()
                    self.graphicsView.sceneObj.contextMenu[:0] = [self.qvkMenu]
                    self.gridLayout.addWidget(self.graphicsView,0,0)
                _display_1D_view(self,self.graphicsView)

            elif self.view_type == view_types['1D']:
                if not self.graphicsView or self._onPlotTypeChanged:
                    self._onPlotTypeChanged = False
                    self.graphicsView = pg.PlotWidget(name=self.dataset_url)
                    self.graphicsView.setObjectName(self.dataset_url)
                    self.addQvkMenu()
                    self.graphicsView.sceneObj.contextMenu[:0] = [self.qvkMenu]
                    self.gridLayout.addWidget(self.graphicsView,0,0)
                _display_1D_data(self,self.graphicsView)

            elif self.view_type == view_types['2D']:
                if not self.graphicsView or self._onPlotTypeChanged:
                    self._onPlotTypeChanged = False
                    self.graphicsView = ImageViewMplColorMaps(self.obj_parent, view = pg.PlotItem())
                    self.graphicsView.setObjectName(self.dataset_url)
                    self.addQvkMenu()
                    self.graphicsView.scene.contextMenu[:0] = [self.qvkMenu]
                    self.graphicsView.view.setAspectLocked(False)
                    self.gridLayout.addWidget(self.graphicsView,0,0)
                    self.linestyle_selector.setDisabled(True)
                _display_2D_data(self,self.graphicsView)

            elif self.view_type == view_types['table']:
                if not self.graphicsView or self._onPlotTypeChanged:
                    self._onPlotTypeChanged = False
                    self.graphicsView = pg.TableWidget(sortable=False)
                    self.graphicsView.setWindowTitle(self.dataset_url+'_table')
                    self.graphicsView.setObjectName(self.dataset_url)
                    self.graphicsView.setFormat("%.6g")
                    self.gridLayout.addWidget(self.graphicsView,0,0)
                _display_table(self,self.graphicsView)

            elif self.view_type == view_types['txt']:
                if not self.graphicsView or self._onPlotTypeChangeBox:
                    self._onPlotTypeChangeBox = False
                    self.graphicsView = QPlainTextEdit()
                    self.graphicsView.setObjectName(self.dataset_url)
                    self.gridLayout.addWidget(self.graphicsView,0,0)
                self.graphicsView.clear()
                _display_text(self,self.graphicsView)
            else:
                print("This should not be here: View Type:"+str(self.view_type))
        except ValueError as e:
            print("PlotWindow: Value Error; Dataset not yet available", self.dataset_url)
            print(e)
        except OSError as e:
            print("PlotWindow: OS Error; Probably a read/write conflict occured", self.dataset_url)
            print(e)


    def _setup_signal_slots(self):
        """Depending on the dataset type the possible signal slots are created
        
        Args:
            self: Object of the PlotWindow class.
        Returns:
            No return variable. The function operates on the given object.
        """
        if self.ds_type == ds_types['vector'] or self.ds_type == ds_types['coordinate']:
            self.PlotTypeSelector.currentIndexChanged.connect(self._onPlotTypeChangeVector)

        elif self.ds_type == ds_types['matrix'] or self.ds_type == -1:
            self.PlotTypeSelector.currentIndexChanged.connect(self._onPlotTypeChangeMatrix)
            self.TraceXSelector.valueChanged.connect(self._setBTraceXNum)
            self.TraceYSelector.valueChanged.connect(self._setBTraceYNum)
            self.TraceXValue.returnPressed.connect(self._setBTraceXValue)            
            self.TraceYValue.returnPressed.connect(self._setBTraceYValue) 

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
        """Set the display attributes to a ds_type sensitive default case.
        
        The default attributs for the ds_types are:
        coordinate -> 1d, data vs. x_coord
        vector -> 1d, data vs. x_coord
        matrix -> 2d, color coded data with y_coord and x_coord
        box -> 2d, color coded data with y_coord and x_coord at the mid-point
            of the z-coord.
        The default settings for the user signal slots are set up in their 
        respective functions.
        Args:
            self: Object of the PlotWindow class.
        Returns:
            No return variable. The function operates on the given object.
        """
        
        ## Some look-up dicts for manipulation and plot styles.
        self.plot_styles = {'line':0,'linepoint':1,'point':2}
        self.manipulations = {'dB':1, 'wrap':2, 'linear':4, 'remove_zeros':8,
                              'sub_offset_avg_x':16, 'sub_offset_avg_y':32, 'norm_data_avg_x':64, 'norm_data_avg_y':128, 'histogram':256} #BITMASK for manipulation

        self.plot_style = 0
        self.manipulation = 8
        self.TraceNum = -1
        self.view_type = self.ds.attrs.get("view_type",None)
        self.user_setting_changed = False

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
        shape = self.ds.shape
        self.TraceXSelector.setEnabled(False)
        self.TraceXSelector.setRange(-1*shape[0],shape[0]-1)
        self.TraceXNum = -1        

        self.TraceYSelector.setEnabled(False)
        self.TraceYSelector.setRange(-1*shape[1],shape[1]-1)
        self.TraceYNum = -1
        
        self.PlotTypeSelector.setCurrentIndex(0)

    def _defaultBox(self):
        shape = self.ds.shape
        
        self.TraceZSelector.setEnabled(True)
        self.TraceZSelector.setRange(-1*shape[2],shape[2]-1)
        self.TraceZSelector.setValue(int(shape[2]/2))
        self.TraceZNum = int(shape[2]/2)
        
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
            self.TraceXSelector.setEnabled(False)
            self.TraceYSelector.setEnabled(False)
        if index == 1:
            self.view_type = view_types['1D']
            self.TraceXSelector.setEnabled(True)
            self.TraceYSelector.setEnabled(False)
        if index == 2:
            self.view_type = view_types['1D']
            self.TraceXSelector.setEnabled(False)
            self.TraceYSelector.setEnabled(True)
        if index == 3:
            self.view_type = view_types['table']
            self.TraceXSelector.setEnabled(False)
            self.TraceYSelector.setEnabled(False)

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
            self.TraceXSelector.setEnabled(False)
            self.TraceYSelector.setEnabled(True)
            self.TraceZSelector.setEnabled(True)
        if index == 4:
            self.view_type = view_types['1D']
            self.TraceXSelector.setEnabled(True)
            self.TraceYSelector.setEnabled(False)
            self.TraceZSelector.setEnabled(True)
        if index == 5:
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
        x_ds = _get_ds(ds, ds.attrs.get('x_ds_url'))
        if x_ds is None:
            return "__none__"
        if ds.attrs.get('ds_type') == ds_types['box']:
            x_data = np.array(x_ds)[:ds.attrs.get('fill')[0]]
        else:
            x_data = np.array(x_ds)[:ds.shape[0]]
        xunit = _get_unit(x_ds)
        try:
            xval = x_data[num]
        except (KeyError,IndexError):
            xval = "X"
        return str(xval)+" "+str(xunit)

    def _getYValueFromTraceNum(self,ds,num):
        y_ds = _get_ds(ds, ds.attrs.get('y_ds_url'))
        if ds.attrs.get('ds_type') == ds_types['box']:
            y_data = np.array(y_ds)[:ds.attrs.get('fill')[1]]
        else:
            y_data = np.array(y_ds)[:ds.shape[1]]
        yunit = _get_unit(y_ds)
        try:
            yval = y_data[num]
        except (KeyError,IndexError):
            yval = "X"
        return str(yval)+" "+str(yunit)

    def _getZValueFromTraceNum(self,ds,num):
        z_ds = _get_ds(ds, ds.attrs.get('z_ds_url'))
        z_data = np.array(z_ds)[:ds.shape[2]]
        zunit = _get_unit(z_ds)
        try:
            zval = z_data[num]
        except (KeyError,IndexError):
            zval = "X"
        return str(zval)+" "+str(zunit)
        

    def addQvkMenu(self,menu=None):
        """Add custom entry in the right-click menu.
        
        The data manipulation option are displayed in the menu. Each entry is
        connected with a trigger event and the information about the clicked
        entry is parsed to the plot lib via the plot_style or the manipulation
        attribute.
        Args:
            self: Object of the PlotWindow class.
            menu: Menu of the respective pyqtgraph plot class
        Returns:
            No return variable. The function operates on the given object.
        """
    
        self.qvkMenu = QMenu("Qviewkit")

        self.linestyle_selector = QActionGroup(self.qvkMenu)
        self.linestyle_selector.setExclusive(True)

        self.linestyle_selector.point = QAction('Point', self.qvkMenu, checkable=True)
        self.qvkMenu.addAction(self.linestyle_selector.point)
        self.linestyle_selector.point.triggered.connect(self.setPointMode)
        self.linestyle_selector.addAction(self.linestyle_selector.point)

        self.linestyle_selector.line = QAction('Line', self.qvkMenu, checkable=True)
        self.qvkMenu.addAction(self.linestyle_selector.line)
        self.linestyle_selector.line.triggered.connect(self.setLineMode)
        self.linestyle_selector.addAction(self.linestyle_selector.line)

        self.linestyle_selector.pointLine = QAction('Point+Line', self.qvkMenu, checkable=True)
        self.qvkMenu.addAction(self.linestyle_selector.pointLine)
        self.linestyle_selector.pointLine.triggered.connect(self.setPointLineMode)
        self.linestyle_selector.addAction(self.linestyle_selector.pointLine)
        
        self.qvkMenu.addSeparator()
        
        phase_wrap = QAction('(un)wrap phase data', self.qvkMenu, checkable=True)
        self.qvkMenu.addAction(phase_wrap)
        phase_wrap.triggered.connect(self.setPhaseWrap)
        
        linear_correction = QAction('linearly correct data', self.qvkMenu, checkable=True)
        self.qvkMenu.addAction(linear_correction)
        linear_correction.triggered.connect(self.setLinearCorrection)

        offset_correction_x = QAction('data-<data:x>', self.qvkMenu, checkable=True)
        self.qvkMenu.addAction(offset_correction_x)
        offset_correction_x.triggered.connect(self.setOffsetCorrectionX)
        
        offset_correction_y = QAction('data-<data:y>', self.qvkMenu, checkable=True)
        self.qvkMenu.addAction(offset_correction_y)
        offset_correction_y.triggered.connect(self.setOffsetCorrectionY)

        norm_correction_x = QAction('data/<data:x>', self.qvkMenu, checkable=True)
        self.qvkMenu.addAction(norm_correction_x)
        norm_correction_x.triggered.connect(self.setNormDataCorrectionX)
        
        norm_correction_y = QAction('data/<data:y>', self.qvkMenu, checkable=True)
        self.qvkMenu.addAction(norm_correction_y)
        norm_correction_y.triggered.connect(self.setNormDataCorrectionY)

        dB_scale = QAction('dB / linear', self.qvkMenu, checkable=True)
        self.qvkMenu.addAction(dB_scale)
        dB_scale.triggered.connect(self.setdBScale)

        histogram = QAction('Histogram', self.qvkMenu, checkable=True)
        self.qvkMenu.addAction(histogram)
        histogram.triggered.connect(self.setHistogram)

        self.manipulation_menu = {'dB': dB_scale,
                                  'wrap': phase_wrap,
                                  'linear': linear_correction,
                                  'sub_offset_avg_x': offset_correction_x,
                                  'sub_offset_avg_y': offset_correction_y,
                                  'norm_data_avg_x': norm_correction_x,
                                  'norm_data_avg_y': norm_correction_y,
                                  'histogram': histogram}
        
        self.updateManipulationMenu()
        
        self.qvkMenu.addSeparator()
        
        notefont = QFont("Helvetica",7,12)
        note = QAction("Manipulations are executed in the order shown here.",self.qvkMenu,enabled=False,font=notefont)
        self.qvkMenu.addAction(note)
        
        self.qvkMenu.setTearOffEnabled(True)
        self.qvkMenu.setWindowTitle("Qviewkit "+str(self.dataset_url.split('/')[-1]) +" "+ str(self.DATA.filename))
        
        if menu is not None:
            menu.addMenu(self.qvkMenu)
    
    def updateManipulationMenu(self):
        for m in self.manipulation_menu:
            self.manipulation_menu[m].setChecked(bool(self.manipulation & self.manipulations[m]))

    @pyqtSlot()
    def setPointMode(self):
        self.plot_style = self.plot_styles['point']
        self.user_setting_changed = True
        if not self._windowJustCreated:
            self.obj_parent.pw_refresh_signal.emit()

    @pyqtSlot()
    def setLineMode(self):
        self.plot_style = self.plot_styles['line']
        self.user_setting_changed = True
        if not self._windowJustCreated:
            self.obj_parent.pw_refresh_signal.emit()

    @pyqtSlot()
    def setPointLineMode(self):
        self.plot_style = self.plot_styles['linepoint']
        self.user_setting_changed = True
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
    def setOffsetCorrectionX(self):
        self.manipulation = self.manipulation ^ self.manipulations['sub_offset_avg_x']
        #print "{:08b}".format(self.manipulation)
        if not self._windowJustCreated:
            self.obj_parent.pw_refresh_signal.emit()

    @pyqtSlot()
    def setOffsetCorrectionY(self):
        self.manipulation = self.manipulation ^ self.manipulations['sub_offset_avg_y']
        #print "{:08b}".format(self.manipulation)
        if not self._windowJustCreated:
            self.obj_parent.pw_refresh_signal.emit()

    @pyqtSlot()
    def setNormDataCorrectionX(self):
        self.manipulation = self.manipulation ^ self.manipulations['norm_data_avg_x']
        #print "{:08b}".format(self.manipulation)
        if not self._windowJustCreated:
            self.obj_parent.pw_refresh_signal.emit()

    @pyqtSlot()
    def setNormDataCorrectionY(self):
        self.manipulation = self.manipulation ^ self.manipulations['norm_data_avg_y']
        #print "{:08b}".format(self.manipulation)
        if not self._windowJustCreated:
            self.obj_parent.pw_refresh_signal.emit()

    @pyqtSlot()
    def setHistogram(self):
        self.manipulation = self.manipulation ^ self.manipulations['histogram']
        if not self._windowJustCreated:
            self.obj_parent.pw_refresh_signal.emit()


from collections import OrderedDict

class ImageViewMplColorMaps(pg.ImageView):
    """Class to manually inclued the matplotlib 2.0 colormaps.
    
    The class implements the matplotlib 2.0 colormaps 'viridis', 'inferno', 
    'plasma', and 'magma' to the available colors scales in our 2d plots.
    They are not (yet?) available in the standard pyqtgraph package. However, 
    there is a pull request #446, issued Feb 2017 by github user "WFrsh" to add
    them to the standard available gradient dict.
    The code is a combination by his added rgb color maps and a monkey patch by
    user "honkomonk" posted in the comment section of pull request #561.
    
    The color gradients for the maps are hard coded here and added to the
    available dict of colormaps. The 'viridis' map is set as default.
    """
    def __init__(self, parent=None, name='ImageView', view=None, imageItem=None, *args):
        super(ImageViewMplColorMaps, self).__init__(parent=parent, name=name, view=view, imageItem=imageItem, *args)

        self.gradientEditorItem = self.ui.histogram.item.gradient

        self.activeCm = "viridis"
        self.mplColorMaps = OrderedDict([
                    ('inferno', {'ticks': [(0.0, (0, 0, 3, 255)), (0.25, (87, 15, 109, 255)), (0.5, (187, 55, 84, 255)), (0.75, (249, 142, 8, 255)), (1.0, (252, 254, 164, 255))], 'mode': 'rgb'}),
                    ('plasma', {'ticks': [(0.0, (12, 7, 134, 255)), (0.25, (126, 3, 167, 255)), (0.5, (203, 71, 119, 255)), (0.75, (248, 149, 64, 255)), (1.0, (239, 248, 33, 255))], 'mode': 'rgb'}),
                    ('magma', {'ticks': [(0.0, (0, 0, 3, 255)), (0.25, (80, 18, 123, 255)), (0.5, (182, 54, 121, 255)), (0.75, (251, 136, 97, 255)), (1.0, (251, 252, 191, 255))], 'mode': 'rgb'}),
                    ('viridis', {'ticks': [(0.0, (68, 1, 84, 255)), (0.25, (58, 82, 139, 255)), (0.5, (32, 144, 140, 255)), (0.75, (94, 201, 97, 255)), (1.0, (253, 231, 36, 255))], 'mode': 'rgb'}),
                    ])

        self.registerCmap()

    def registerCmap(self):
        """ Add matplotlib cmaps to the GradientEditors context menu"""
        self.gradientEditorItem.menu.addSeparator()
        savedLength = self.gradientEditorItem.length
        self.gradientEditorItem.length = 100
        
        
        for name in self.mplColorMaps:
            px = QPixmap(100, 15)
            p = QPainter(px)
            self.gradientEditorItem.restoreState(self.mplColorMaps[name])
            grad = self.gradientEditorItem.getGradient()
            brush = QBrush(grad)
            p.fillRect(QtCore.QRect(0, 0, 100, 15), brush)
            p.end()
            label = QLabel()
            label.setPixmap(px)
            label.setContentsMargins(1, 1, 1, 1)
            act =QWidgetAction(self.gradientEditorItem)
            act.setDefaultWidget(label)
            act.triggered.connect(self.cmapClicked)
            act.name = name
            self.gradientEditorItem.menu.addAction(act)
        self.gradientEditorItem.length = savedLength


    def cmapClicked(self):
        """onclick handler for our custom entries in the GradientEditorItem's context menu"""
        act = self.sender()
        self.gradientEditorItem.restoreState(self.mplColorMaps[act.name])
        self.activeCm = act.name