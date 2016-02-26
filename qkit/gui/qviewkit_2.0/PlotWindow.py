# -*- coding: utf-8 -*-
"""
@author: hannes.rotzinger@kit.edu @ 2015
"""


from PyQt4.QtCore import *
from PyQt4.QtGui import *

from plot_view import Ui_Form
import pyqtgraph as pg
from qkit.storage.hdf_constants import ds_types
#import argparse
#import ConfigParser
import numpy as np
#import h5py


#class PlotWindow(QMainWindow, Ui_MainWindow):
class PlotWindow(QWidget,Ui_Form):

    def myquit(self):
        exit()

    def __init__(self,parent,data,dataset_url,ds_type):
        self.DATA = data
        self.dataset_url = dataset_url
        self.obj_parent = parent
        try: self.ds_type = int(ds_type)
        except: self.ds_type = -1
        super(PlotWindow , self).__init__()
        Ui_Form.__init__(self)

        self.setupUi(self,self.ds_type)
        window_title = str(dataset_url.split('/')[-1]) +" "+ str(self.DATA.filename)
        self.setWindowTitle(window_title)

        self.graphicsView = None
        self._windowJustCreated = True
        self.TraceValueChanged = False
        self.SliceValueChanged = False
        self.TraceXValueChanged = False
        self.TraceYValueChanged = False

        self._setup_signal_slots()

    def _setup_signal_slots(self):
        self.obj_parent.refresh_signal.connect(self.update_plots)
        if self.ds_type == ds_types['matrix'] or self.ds_type == -1:
            QObject.connect(self.PlotTypeSelector,SIGNAL("currentIndexChanged(int)"),self._onPlotTypeChangeMatrix)
            QObject.connect(self.TraceSelector,SIGNAL("valueChanged(int)"),self._setTraceNum)
            QObject.connect(self.TraceValue,SIGNAL("returnPressed()"),self._setTraceValue)

        elif self.ds_type == ds_types['box']:
            QObject.connect(self.PlotTypeSelector,SIGNAL("currentIndexChanged(int)"),self._onPlotTypeChangeBox)
            QObject.connect(self.SliceSelector,SIGNAL("valueChanged(int)"),self._setSliceNum)
            QObject.connect(self.SliceValue,SIGNAL("returnPressed()"),self._setSliceValue)
            QObject.connect(self.TraceXSelector,SIGNAL("valueChanged(int)"),self._setTraceXNum)
            QObject.connect(self.TraceXValue,SIGNAL("returnPressed()"),self._setTraceXValue)
            QObject.connect(self.TraceYValue,SIGNAL("returnPressed()"),self._setTraceYValue)
            QObject.connect(self.TraceYSelector,SIGNAL("valueChanged(int)"),self._setTraceYNum)

        elif self.ds_type == ds_types['vector'] or self.ds_type == ds_types['coordinate']:
            QObject.connect(self.PlotTypeSelector,SIGNAL("currentIndexChanged(int)"),self._onPlotTypeChangeVector)

        elif self.ds_type == ds_types['view']:
            QObject.connect(self.TraceSelector,SIGNAL("valueChanged(int)"),self._setTraceNum)
            QObject.connect(self.TraceValue,SIGNAL("returnPressed()"),self._setTraceValue)

    def _setDefaultView(self):
        self.view_types = {'1D':0,'1D-V':1, '2D':2, '3D':3, 'table':4, 'txt':5}
        self.TraceNum = -1
        self.plot_styles = {'line':0,'linepoint':1,'point':2}
        self.plot_style = 0

        self.view_type = self.ds.attrs.get("view_type",None)
        if self.ds_type == ds_types["coordinate"]:
            self._defaultCoord()
        elif self.ds_type == ds_types["vector"]:
            self._defaultVector()
        elif self.ds_type == ds_types["matrix"]:
            self._defaultMatrix()
        elif self.ds_type== ds_types["box"]:
            self._defaultBox()
        elif self.ds_type == ds_types["txt"]:
            self._defaultTxt()
        elif self.ds_type == ds_types["view"]:
            self._defaultView()
        else:
            self._defaultOld()

    def _defaultCoord(self):
        self.PlotTypeSelector.setCurrentIndex(0)
        self.view_type = self.view_types['1D']

    def _defaultVector(self):
        self.PlotTypeSelector.setCurrentIndex(0)
        self.view_type = self.view_types['1D']

    def _defaultMatrix(self):
        self.TraceSelector.setEnabled(False)
        shape = self.ds.shape[0]
        self.TraceSelector.setRange(-1*shape,shape-1)
        self.PlotTypeSelector.setCurrentIndex(0)
        self.view_type = self.view_types['2D']

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
        self.view_type = self.view_types['2D']

    def _defaultTxt(self):
        self.view_type = self.view_types['txt']

    def _defaultView(self):
        self.TraceSelector.setEnabled(True)
        self.view_type = self.view_types['1D-V']

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

    def closeEvent(self, event):
        "overwrite the closeEvent handler"
        self.deleteLater()
        self.DATA._toBe_deleted(self.dataset_url)
        event.accept()

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

    @pyqtSlot()
    def update_plots(self):
        self.ds = self.obj_parent.h5file[self.dataset_url]
        if self._windowJustCreated:
            self._setDefaultView()
            self._onPlotTypeChanged = True
            self._windowJustCreated = False

        try:
            if self.view_type == self.view_types['1D-V']:
                if not self.graphicsView or self._onPlotTypeChanged:
                    self._onPlotTypeChanged = False
                    self.graphicsView = pg.PlotWidget(name=self.dataset_url)
                    self.graphicsView.setObjectName(self.dataset_url)
                    self.addQvkMenu(self.graphicsView.plotItem.getMenu())
                    self.gridLayout.addWidget(self.graphicsView,0,0)
                self._display_1D_view(self.graphicsView)

            elif self.view_type == self.view_types['1D']:
                if not self.graphicsView or self._onPlotTypeChanged:
                    self._onPlotTypeChanged = False
                    self.graphicsView = pg.PlotWidget(name=self.dataset_url)
                    self.graphicsView.setObjectName(self.dataset_url)
                    self.addQvkMenu(self.graphicsView.plotItem.getMenu())
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

            elif self.view_type == self.view_types['table']:
                if not self.graphicsView or self._onPlotTypeChanged:
                    self._onPlotTypeChanged = False
                    self.graphicsView = pg.TableWidget()
                    self.graphicsView.setWindowTitle(self.dataset_url+'_table')
                    self.graphicsView.setObjectName(self.dataset_url)
                    self.gridLayout.addWidget(self.graphicsView,0,0)
                self._display_table(self.graphicsView)
            elif self.view_type == self.view_types['txt']:
                if not self.graphicsView or self._onPlotTypeChangeBox:
                    self._onPlotTypeChangeBox = False
                    self.graphicsView = QPlainTextEdit()
                    self.graphicsView.setObjectName(self.dataset_url)
                    self.gridLayout.addWidget(self.graphicsView,0,0)
                    #self.graphicsView.setObjectName(self.dataset_url)
                    self.gridLayout.addWidget(self.graphicsView,0,0)
                self._display_text(self.graphicsView)
            else:
                print "This should not be here: View Type:"+str(self.view_type)
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
        if not graphicsView.plotItem.legend:
            graphicsView.plotItem.addLegend(size=(160,48),offset=(30,15))
        for i, x_ds in enumerate(ds_xs):
            y_ds = ds_ys[i]
            # this is a litte clumsy, but for the cases tested it works well
            if len(x_ds.shape) == 1 and len(y_ds.shape) == 1:
                self.TraceSelector.setEnabled(False)
                x_data = np.array(x_ds)
                y_data = np.array(y_ds)

            elif len(x_ds.shape) == 2 and len(y_ds.shape) == 2:
                self.TraceSelector.setEnabled(True)
                range_max = np.minimum( x_ds.shape[0],y_ds.shape[0])
                self.TraceSelector.setRange(-1*range_max,range_max-1)

                x_data = np.array(x_ds[self.TraceNum])
                y_data = np.array(y_ds[self.TraceNum])

            elif len(x_ds.shape) == 1 and len(y_ds.shape) == 2:
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

            graphicsView.setLabel('left', y_name, units=y_unit)
            graphicsView.setLabel('bottom', x_name , units=x_unit)

            try:
                graphicsView.plotItem.legend.removeItem(y_name)
            except:
                pass
            if self.plot_style==self.plot_styles['line']:
                graphicsView.plot(y=y_data, x=x_data,pen=(i,3), name = y_name, connect='finite')
            if self.plot_style==self.plot_styles['linepoint']:
                symbols=['+','o','s','t','d']
                graphicsView.plot(y=y_data, x=x_data,pen=(i,3), name = y_name, connect='finite',symbol=symbols[i%len(symbols)])
            if self.plot_style==self.plot_styles['point']:
                symbols=['+','o','s','d','t']
                graphicsView.plot(y=y_data, x=x_data, name = y_name,pen=None,symbol=symbols[i%len(symbols)])

    def _display_1D_data(self,graphicsView):
        #only one entry in ds, line style does not make any sense
        if self.ds.shape[0]==1:
            self.plot_style = self.plot_styles['point']
        ds = self.ds
        y_data = np.array(ds)
        if self.ds_type == ds_types['matrix'] or (self.ds_type == -1 and len(self.ds.shape) == 2):
            if self.TraceValueChanged:
                dx = ds.attrs.get("dx",1)
                x0 = ds.attrs.get("x0",0)
                num = int(self._trace_value/dx-x0)
                self.TraceNum = num
                self.TraceSelector.setValue(self.TraceNum)
                self.TraceValueChanged = False
            y_data = y_data[self.TraceNum]
            self.TraceValue.setText(self._getXValueFromTraceNum(ds,self.TraceNum))
        x0 = ds.attrs.get("y0",ds.attrs.get("x0",0))
        dx = ds.attrs.get("dy",ds.attrs.get("dx",1))
        x_data = [x0+dx*i for i in xrange(len(y_data))]

        name = ds.attrs.get("name","_none_")
        unit = ds.attrs.get("unit","_none_")
        x_name = ds.attrs.get("y_name",ds.attrs.get("x_name","_none_"))
        x_unit = ds.attrs.get("y_unit",ds.attrs.get("x_unit","_none_"))
        
        if self.ds_type == ds_types['box']:
            x0 = ds.attrs.get('z0',0)
            dx = ds.attrs.get('dz',1)
            x_name = ds.attrs.get('z_name','_none_')
            x_unit = ds.attrs.get('z_unit','_none_')
            x_data = [x0+dx*i for i in y_data.shape[2]]
            y_data = y_data[self.TraceXNum,self.TraceYNum,:]
            
        #plot.setPen((200,200,100))
        graphicsView.setLabel('left', name, units=unit)
        graphicsView.setLabel('bottom', x_name , units=x_unit)

        if self.plot_style==self.plot_styles['line']:
            graphicsView.plot(y=y_data, x=x_data, clear = True, pen=(200,200,100),connect='finite')
        if self.plot_style==self.plot_styles['linepoint']:
            graphicsView.plot(y=y_data, x=x_data, clear = True, pen=(200,200,100),connect='finite',symbol='+')
        if self.plot_style==self.plot_styles['point']:
            graphicsView.plot(y=y_data, x=x_data, clear = True, pen=None, symbol='+')
        #plot.setData(y=ydata, x=x_data)

    def _display_2D_data(self,graphicsView):
        #load the dataset:
        ds = self.ds
        #fill = ds.attrs.get("fill",1)
        fill_x = ds.shape[0]
        fill_y = ds.shape[1]
        #data = np.array(ds[:fill])
        x0 = ds.attrs.get("x0",0)
        dx = ds.attrs.get("dx",1)
        y0 = ds.attrs.get("y0",0)
        dy = ds.attrs.get("dy",1)
        data = np.array(ds)

        name = ds.attrs.get("name","_none_")
        unit = ds.attrs.get("unit","_none_")
        x_name = ds.attrs.get("x_name","_none_")
        x_unit = ds.attrs.get("x_unit","_none_")
        y_name = ds.attrs.get("y_name","_none_")
        y_unit = ds.attrs.get("y_unit","_none_")

        if self.ds_type == ds_types['box']:
            if self.PlotTypeSelector.currentIndex() == 0:
                data = data[:,:,self.SliceNum]
            if self.PlotTypeSelector.currentIndex() == 1:
                data = data[self.TraceXNum,:,:]
                fill_x = ds.shape[0]
                fill_y = ds.shape[2]
                x0 = ds.attrs.get("y0",0)
                dx = ds.attrs.get("dy",1)
                y0 = ds.attrs.get("z0",0)
                dy = ds.attrs.get("dz",1)
                x_name = ds.attrs.get("y_name","_none_")
                x_unit = ds.attrs.get("y_unit","_none_")
                y_name = ds.attrs.get("z_name","_none_")
                y_unit = ds.attrs.get("z_unit","_none_")

            if self.PlotTypeSelector.currentIndex() == 2:
                data = data[:,self.TraceYNum,:]
                fill_x = ds.shape[1]
                fill_y = ds.shape[2]
                x0 = ds.attrs.get("x0",0)
                dx = ds.attrs.get("dx",1)
                y0 = ds.attrs.get("z0",0)
                dy = ds.attrs.get("dz",1)
                x_name = ds.attrs.get("x_name","_none_")
                x_unit = ds.attrs.get("x_unit","_none_")
                y_name = ds.attrs.get("z_name","_none_")
                y_unit = ds.attrs.get("z_unit","_none_")

        xmin = x0
        xmax = x0+fill_x*dx
        ymin = y0
        ymax = y0+fill_y*dy

        pos = (xmin,ymin)

        #scale=(xmax/float(data.shape[0]),ymax/float(data.shape[1]))
        scale=((xmax-xmin)/float(fill_x),(ymax-ymin)/float(fill_y))
        graphicsView.view.setLabel('left', y_name, units=y_unit)
        graphicsView.view.setLabel('bottom', x_name, units=x_unit)
        graphicsView.view.setTitle(name+" ("+unit+")")
        graphicsView.view.invertY(False)

        graphicsView.setImage(data,pos=pos,scale=scale)
        graphicsView.show()

        # Fixme roi ...
        graphicsView.roi.setPos([xmin,ymin])
        graphicsView.roi.setSize([xmax-xmin,ymax-ymin])
        graphicsView.roi.setAcceptedMouseButtons(Qt.RightButton)
        graphicsView.roi.sigClicked.connect(lambda: self.clickRoi(graphicsView.roi.pos(), graphicsView.roi.size()))

    def clickRoi(self, pos, size):
        """
        pos1 =[pos[0],pos[1]]
        pos2 = [pos1[0]+size[0],pos1[1]+size[1]]
        rangeX = [pos1[0], pos2[0]]
        rangeY = [pos1[1], pos2[1]]
        txt = 'x: '+str(rangeX[0])+', '+str(rangeX[1])+"\ny: "+str(rangeY[0])+', '+str(rangeY[1])
        print txt
        txtItem = pg.TextItem(text=txt)
        vb=self.graphicsView.getView()
        vb.addItem(txtItem)
        """

    def _display_table(self,graphicsView):
        #load the dataset:
        data = np.array(self.ds)
        if self.ds_type == ds_types['matrix']:
            data = data.transpose()
        if self.ds_type == ds_types['vector']:
            data_tmp = np.empty((1,data.shape[0]),dtype=np.float64)
            data_tmp[0] = data
            data = data_tmp.transpose()
        if self.ds_type == ds_types["txt"]:
            data_tmp = []
            for d in data:
                data_tmp.append([d])
            data = np.array(data_tmp)
            graphicsView.setFormat(unicode(data))
        graphicsView.setData(data)
        
    def _display_text(self,graphicsView):
        data = np.array(self.ds)
        txt = ""
        for d in data:
            txt += d+'\n'
        graphicsView.insertPlainText(txt)
