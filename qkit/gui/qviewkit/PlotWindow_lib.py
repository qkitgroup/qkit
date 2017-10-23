# -*- coding: utf-8 -*-
"""
@author: hannes.rotzinger@kit.edu / 2015,2016,2017 
         marco.pfirrmann@kit.edu / 2016, 2017
@license: GPL
"""
import sys
in_pyqt5 = False
try:
    from PyQt5 import QtCore
    from PyQt5.QtCore import Qt,QObject,pyqtSlot
    from PyQt5.QtWidgets import QWidget,QPlainTextEdit,QMenu,QAction
    in_pyqt5 = True
except ImportError, e:
    pass

if not in_pyqt5:
    try:
        from PyQt4 import QtCore
        from PyQt4.QtCore import *
        from PyQt4.QtGui import *
    except ImportError:
        print "import of PyQt5 and PyQt4 failed. Install one of those."
        sys.exit(-1)

import numpy as np
import json
import pyqtgraph as pg
from qkit.storage.hdf_constants import ds_types

def _display_1D_view(self,graphicsView):
    ds = self.ds
    overlay_num = ds.attrs.get("overlays",0)
    overlay_urls = []
    err_urls = []
    for i in range(overlay_num+1):
        ov = ds.attrs.get("xy_"+str(i),"")
        if ov:
            overlay_urls.append(ov.split(":"))
        err_urls.append(ds.attrs.get("xy_"+str(i)+"_error",""))
            
    ds_xs = []
    ds_ys = []
    ds_errs = []
    for xy in overlay_urls:
        ds_xs.append(self.obj_parent.h5file[xy[0]])
        ds_ys.append(self.obj_parent.h5file[xy[1]])
        
    for err_url in err_urls:
        try:
            ds_errs.append(self.obj_parent.h5file[err_url])
        except:
            ds_errs.append(0)

    graphicsView.clear()

    if not graphicsView.plotItem.legend:
        graphicsView.plotItem.addLegend(size=(160,48),offset=(30,15))
        
    for i, x_ds in enumerate(ds_xs):
        y_ds = ds_ys[i]
        err_ds = ds_errs[i]
        
        if x_ds.attrs.get('ds_type',0) == ds_types['coordinate'] or x_ds.attrs.get('ds_type',0) == ds_types['vector']:
            if y_ds.attrs.get('ds_type',0) == ds_types['vector'] or y_ds.attrs.get('ds_type',0) == ds_types['coordinate']:
                self.VTraceXSelector.setEnabled(False)
                self.VTraceYSelector.setEnabled(False)
                x_data = np.array(x_ds)
                y_data = np.array(y_ds)
                if err_ds:
                    err_data = np.array(err_ds)

            elif y_ds.attrs.get('ds_type',0) == ds_types['matrix']:
                self.VTraceXSelector.setEnabled(True)
                range_max = y_ds.shape[0]
                self.VTraceXSelector.setRange(-1*range_max,range_max-1)
                self.VTraceXValue.setText(self._getXValueFromTraceNum(y_ds,self.VTraceXNum))
                self.VTraceYSelector.setEnabled(False)
    
                x_data = np.array(x_ds)
                y_data = np.array(y_ds[self.VTraceXNum])
                if err_ds:
                    err_data = np.array(err_ds[self.VTaceXNum])

            elif y_ds.attrs.get('ds_type',0) == ds_types['box']:
                self.VTraceXSelector.setEnabled(True)
                range_maxX = y_ds.shape[0]
                self.VTraceXSelector.setRange(-1*range_maxX,range_maxX-1)
                self.VTraceXValue.setText(self._getXValueFromTraceNum(y_ds,self.VTraceXNum))
                self.VTraceYSelector.setEnabled(True)
                range_maxY = y_ds.shape[1]
                self.VTraceYSelector.setRange(-1*range_maxY,range_maxY-1)
                self.VTraceYValue.setText(self._getYValueFromTraceNum(y_ds,self.VTraceYNum))
                
                x_data = np.array(x_ds)
                y_data = np.array(y_ds[self.VTraceXNum,self.VTraceYNum,:])
                if err_ds:
                    err_data = np.array(err_ds[self.VTraceXNum,self.VTraceYNum,:])

        ## This is in our case used so far only for IQ plots. The functionality derives from this application.
        elif x_ds.attrs.get('ds_type',0) == ds_types['matrix']:
            if x_ds.attrs.get('ds_type',0) == ds_types['matrix']:
                self.VTraceXSelector.setEnabled(True)
                range_max = np.minimum(x_ds.shape[0],y_ds.shape[0])
                self.VTraceXSelector.setRange(-1*range_max,range_max-1)
                self.VTraceXValue.setText(self._getXValueFromTraceNum(y_ds,self.VTraceXNum))
                self.VTraceYSelector.setEnabled(False)
    
                x_data = np.array(x_ds[self.VTraceXNum])
                y_data = np.array(y_ds[self.VTraceXNum])

        elif x_ds.attrs.get('ds_type',0) == ds_types['box']:
            if x_ds.attrs.get('ds_type',0) == ds_types['box']:
                self.VTraceXSelector.setEnabled(True)
                range_maxX = y_ds.shape[0]
                self.VTraceXSelector.setRange(-1*range_maxX,range_maxX-1)
                self.VTraceXValue.setText(self._getXValueFromTraceNum(y_ds,self.VTraceXNum))
                self.VTraceYSelector.setEnabled(True)
                range_maxY = y_ds.shape[1]
                self.VTraceYSelector.setRange(-1*range_maxY,range_maxY-1)
                self.VTraceYValue.setText(self._getYValueFromTraceNum(y_ds,self.VTraceYNum))
                
                x_data = np.array(x_ds[self.VTraceXNum,self.VTraceYNum,:])
                y_data = np.array(y_ds[self.VTraceXNum,self.VTraceYNum,:])
                
        else:
            return

        x_name = x_ds.attrs.get("name","_none_")
        y_name = y_ds.attrs.get("name","_none_")
        
        self.x_unit = x_ds.attrs.get("unit","_none_")
        self.y_unit = y_ds.attrs.get("unit","_none_")

        graphicsView.setLabel('left', y_name, units=self.y_unit)
        graphicsView.setLabel('bottom', x_name , units=self.x_unit)
        
        
        view_params = json.loads(ds.attrs.get("view_params",{}))
        
        # this allows to set a couple of plot related settings
        if view_params:
            aspect = view_params.pop('aspect',False)
            if aspect:
                graphicsView.setAspectLocked(lock=True,ratio=aspect)
            #bgcolor = view_params.pop('bgcolor',False)
            #if bgcolor:
            #    print tuple(bgcolor)
            #    graphicsView.setBackgroundColor(tuple(bgcolor))
                
        try:
            graphicsView.plotItem.legend.removeItem(y_name)
        except:
            pass

        # set the y data  to the decibel scale 
        if self.manipulation & self.manipulations['dB']:
            y_data = 20 *np.log10(y_data)
            graphicsView.setLabel('left', y_name, units="dB")
            self.y_unit='dB'
          
        # unwrap the phase
        if self.manipulation & self.manipulations['wrap']:
            y_data = np.unwrap(y_data)
        
        # linearly correct the data    
        if self.manipulation & self.manipulations['linear']:
            y_data = y_data - np.linspace(y_data[0],y_data[-1],len(y_data))
        
        if self.plot_style==self.plot_styles['line']:
            graphicsView.plot(y=y_data, x=x_data,pen=(i,3), name = y_name, connect='finite')
        if self.plot_style==self.plot_styles['linepoint']:
            symbols=['+','o','s','t','d']
            graphicsView.plot(y=y_data, x=x_data,pen=(i,3), name = y_name, connect='finite',symbol=symbols[i%len(symbols)])
        if self.plot_style==self.plot_styles['point']:
            symbols=['+','o','s','d','t']
            graphicsView.plot(y=y_data, x=x_data, name = y_name,pen=None,symbol=symbols[i%len(symbols)])    
        if err_ds:
            err = pg.ErrorBarItem(x=x_data, y=y_data, height=err_data, beam=0.25*x_ds.attrs.get("dx",0))
            graphicsView.getPlotItem().addItem(err)    
            
    plIt = graphicsView.getPlotItem()
    plVi = plIt.getViewBox()
    
    
    self._last_x_pos = 0   
    def mouseMoved(mpos):
        mpos = mpos[0]
        if plIt.sceneBoundingRect().contains(mpos):
            mousePoint = plVi.mapSceneToView(mpos)
            xval = mousePoint.x()
            yval = mousePoint.y()
            self.PointX.setText("X: %.6e %s"%(xval,self.x_unit)) 
            self.PointY.setText("Y: %.6e %s"%(yval,self.y_unit)) 
            
            try:
                self.data_coord=  "%e\t%e\t%e\t%e" % (xval, yval,self._last_x_pos-xval,xval/(self._last_x_pos-xval))
            except ZeroDivisionError:
                pass
                
            self._last_x_pos = xval
    
    self.proxy = pg.SignalProxy(plVi.scene().sigMouseMoved, rateLimit=15, slot=mouseMoved)

def _display_1D_data(self,graphicsView):
    ds = self.ds
    name = ds.attrs.get("name","_none_")
    self.unit = ds.attrs.get("unit","_none_")
    y_data = np.array(ds)

    if self.ds_type == ds_types['vector'] or self.ds_type == ds_types['coordinate'] or (self.ds_type == -1 and len(self.ds.shape) == 1): #last expresson is for old hdf-files
        x0 = ds.attrs.get("y0",ds.attrs.get("x0",0))
        dx = ds.attrs.get("dy",ds.attrs.get("dx",1))
        x_name = ds.attrs.get("x_name","_none_")
        x_unit = ds.attrs.get("x_unit","_none_")

        x_data = [x0+dx*i for i in xrange(y_data.shape[0])]

        #only one entry in ds, line style does not make any sense
        if self.ds.shape[0]==1:
            self.plot_style = self.plot_styles['point']

    elif self.ds_type == ds_types['matrix'] or (self.ds_type == -1 and len(self.ds.shape) == 2): #last expresson is for old hdf-files
        #x-dim in plot is y-dim in matrix dataset
        x0 = ds.attrs.get("y0",ds.attrs.get("x0",0))
        dx = ds.attrs.get("dy",ds.attrs.get("dx",1))
        x_name = ds.attrs.get("y_name","_none_")
        x_unit = ds.attrs.get("y_unit","_none_")

        if self.TraceValueChanged:
            #calc trace number from entered value
            num = int((self._trace_value-ds.attrs.get("x0",0))/(ds.attrs.get("dx",1)))
            self.TraceNum = num
            self.TraceSelector.setValue(self.TraceNum)
            self.TraceValueChanged = False

        x_data = [x0+dx*i for i in xrange(y_data.shape[1])]
        y_data = y_data[self.TraceNum]

        self.TraceValue.setText(self._getXValueFromTraceNum(ds,self.TraceNum))

        #only one y-entry in ds, line style does not make any sense
        if self.ds.shape[1]==1:
            self.plot_style = self.plot_styles['point']

    elif self.ds_type == ds_types['box']:
        #x-dim in plot is z-dim in box-dataset
        x0 = ds.attrs.get('z0',0)
        dx = ds.attrs.get('dz',1)
        x_name = ds.attrs.get('z_name','_none_')
        x_unit = ds.attrs.get('z_unit','_none_')

        if self.TraceXValueChanged:
            #calc trace number from entered value
            num = int((self._traceX_value-ds.attrs.get("x0",0))/(ds.attrs.get("dx",1)))
            self.TraceXNum = num
            self.TraceXSelector.setValue(self.TraceXNum)
            self.TraceXValueChanged = False
        
        if self.TraceYValueChanged:
            #calc trace number from entered value
            num = int((self._traceY_value-ds.attrs.get("y0",0))/(ds.attrs.get("dy",1)))
            self.TraceYNum = num
            self.TraceYSelector.setValue(self.TraceYNum)
            self.TraceYValueChanged = False


        x_data = [x0+dx*i for i in range(y_data.shape[2])]
        y_data = y_data[self.TraceXNum,self.TraceYNum,:]

        self.TraceXValue.setText(self._getXValueFromTraceNum(ds,self.TraceXNum))
        self.TraceYValue.setText(self._getYValueFromTraceNum(ds,self.TraceYNum))

        #only one z-entry in ds, line style does not make any sense
        if self.ds.shape[2]==1:
            self.plot_style = self.plot_styles['point']

    graphicsView.setLabel('left', name, units=self.unit)
    graphicsView.setLabel('bottom', x_name , units=x_unit)

    # set the y data  to the decibel scale 
    if self.manipulation & self.manipulations['dB']:
        y_data = 20 *np.log10(y_data)
        graphicsView.setLabel('left', name, units="dB")
        self.unit = 'dB'
    
    # unwrap the phase
    if self.manipulation & self.manipulations['wrap']:
        y_data = np.unwrap(y_data)
        
    # linearly correct the data    
    if self.manipulation & self.manipulations['linear']:
        y_data = y_data - np.linspace(y_data[0],y_data[-1],len(y_data))

    if self.plot_style==self.plot_styles['line']:
        graphicsView.plot(y=y_data, x=x_data, clear = True, pen=(200,200,100),connect='finite')
    if self.plot_style==self.plot_styles['linepoint']:
        graphicsView.plot(y=y_data, x=x_data, clear = True, pen=(200,200,100),connect='finite',symbol='+')
    if self.plot_style==self.plot_styles['point']:
        graphicsView.plot(y=y_data, x=x_data, clear = True, pen=None, symbol='+')

    plIt = graphicsView.getPlotItem()
    plVi = plIt.getViewBox()

    self._last_x_pos = 0
    
    def mouseMoved(mpos):
        mpos = mpos[0]
        if plIt.sceneBoundingRect().contains(mpos):
            mousePoint = plVi.mapSceneToView(mpos)
            xval = mousePoint.x()
            yval = mousePoint.y()

            self.PointX.setText("X: %.6e %s"%(xval,x_unit)) 
            self.PointY.setText("Y: %.6e %s"%(yval,self.unit)) 

            try:
                self.data_coord=  "%e\t%e\t%e\t%e" % (xval, yval,self._last_x_pos-xval,xval/(self._last_x_pos-xval))
            except ZeroDivisionError:
                pass

            self._last_x_pos = xval

    self.proxy = pg.SignalProxy(plVi.scene().sigMouseMoved, rateLimit=15, slot=mouseMoved)

def _display_2D_data(self,graphicsView):
    ds = self.ds
    name = ds.attrs.get("name","_none_")
    self.unit = ds.attrs.get("unit","_none_")

    data = ds[()]
    fill_x = ds.shape[0]
    fill_y = ds.shape[1]
    x0 = ds.attrs.get("x0",0)
    dx = ds.attrs.get("dx",1)
    y0 = ds.attrs.get("y0",0)
    dy = ds.attrs.get("dy",1)
    x_name = ds.attrs.get("x_name","_none_")
    x_unit = ds.attrs.get("x_unit","_none_")
    y_name = ds.attrs.get("y_name","_none_")
    y_unit = ds.attrs.get("y_unit","_none_")
    #print graphicsView.getHistogramWidget().region.getRegion()#.vb.state['autoRange'] #aS 2016-12 for further use

    if self.ds_type == ds_types['box']:
        if self.PlotTypeSelector.currentIndex() == 0:
            if self.TraceXValueChanged:
                #calc trace number from entered value
                num = int((self._traceX_value-ds.attrs.get("x0",0))/(ds.attrs.get("dx",1)))
                self.TraceXNum = num
                self.TraceXSelector.setValue(self.TraceXNum)
                self.TraceXValueChanged = False
                
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
            
        if self.PlotTypeSelector.currentIndex() == 1:
            if self.TraceYValueChanged:
                #calc trace number from entered value
                num = int((self._traceY_value-ds.attrs.get("y0",0))/(ds.attrs.get("dy",1)))
                self.TraceYNum = num
                self.TraceYSelector.setValue(self.TraceYNum)
                self.TraceYValueChanged = False

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

        if self.PlotTypeSelector.currentIndex() == 2:
            if self.TraceZValueChanged:
                #calc trace number from entered value
                num = int((self._traceZ_value-ds.attrs.get("z0",0))/(ds.attrs.get("dz",1)))
                self.TraceZNum = num
                self.TraceZSelector.setValue(self.TraceZNum)
                self.TraceZValueChanged = False

            data = data[:,:,self.TraceZNum]


        self.TraceXValue.setText(self._getXValueFromTraceNum(ds,self.TraceXNum))
        self.TraceYValue.setText(self._getYValueFromTraceNum(ds,self.TraceYNum))
        self.TraceZValue.setText(self._getZValueFromTraceNum(ds,self.TraceZNum))

    # set the y data  to the decibel scale 
    if self.manipulation & self.manipulations['dB']:
        data = 20 *np.log10(data)
        self.unit = 'dB'
        
    # unwrap the phase
    if self.manipulation & self.manipulations['wrap']:
        data = np.unwrap(data)
    
    if self.manipulation & self.manipulations['linear']:
        data = data - np.outer(data[:,-1]-data[:,0],np.linspace(0,1,data.shape[1]))
     
    if self.manipulation & self.manipulations['remove_zeros']:
        data[np.where(data==0)] = np.NaN #replace all exact zeros in the hd5 data with NaNs, otherwise the 0s in uncompleted files blow up the colorscale
    
    
    # subtract offset from the data
    if self.manipulation & self.manipulations['offset']:
        #ignore division by zero
        old_warn = np.seterr(divide='print')
        data = data / np.nanmean(data,axis=0,keepdims=True)
        np.seterr(**old_warn)
        

    xmin = x0-dx/2 #center the data around the labels
    xmax = x0+fill_x*dx-dx/2
    ymin = y0-dy/2
    ymax = y0+fill_y*dy-dy/2

    pos = (xmin,ymin)

    graphicsView.clear()
    # scale is responsible for the "accidential" correct display of the axis
    # for downsweeps scale has negative values and extends the axis from the min values into the correct direction
    scale=((xmax-xmin)/float(fill_x),(ymax-ymin)/float(fill_y))
    graphicsView.view.setLabel('left', y_name, units=y_unit)
    graphicsView.view.setLabel('bottom', x_name, units=x_unit)
    graphicsView.view.setTitle(name+" ("+self.unit+")")
    graphicsView.view.invertY(False)
    
    graphicsView.setImage(data,pos=pos,scale=scale)
    graphicsView.show()

    # Fixme roi ...
    graphicsView.roi.setPos([xmin,ymin])
    graphicsView.roi.setSize([xmax-xmin,ymax-ymin])
    graphicsView.roi.setAcceptedMouseButtons(Qt.RightButton)
    graphicsView.roi.sigClicked.connect(lambda: self.clickRoi(graphicsView.roi.pos(), graphicsView.roi.size()))
    
    imIt = graphicsView.getImageItem()
    imVi = graphicsView.getView()
    
    def mouseMoved(mpos):
        mpos = mpos[0]
        if not self.obj_parent.liveCheckBox.isChecked():
            if imIt.sceneBoundingRect().contains(mpos):
                mousePoint = imIt.mapFromScene(mpos)
                x_index = int(mousePoint.x())
                y_index = int(mousePoint.y())
                if x_index > 0 and y_index > 0:
                    if x_index < fill_x and y_index < fill_y:
                        xval = x0+x_index*dx
                        yval = y0+y_index*dy
                        zval = data[x_index][y_index]
                        self.PointX.setText("X: %.6e %s"%(xval,x_unit)) 
                        self.PointY.setText("Y: %.6e %s"%(yval,y_unit)) 
                        self.PointZ.setText("Z: %.6e %s"%(zval,self.unit)) 
                        self.data_coord=  "%g\t%g\t%g" % (xval, yval,zval)

        else:
            xval = 0
            yval = 0
            zval = 0
            self.PointX.setText("X: %.6e %s"%(xval,x_unit)) 
            self.PointY.setText("Y: %.6e %s"%(yval,y_unit)) 
            self.PointZ.setText("Z: %.6e %s"%(zval,self.unit)) 
            self.data_coord=  "%g\t%g\t%g" % (xval, yval,zval)
    

    self.proxy = pg.SignalProxy(imVi.scene().sigMouseMoved, rateLimit=15, slot=mouseMoved)



def _display_table(self,graphicsView):
    #load the dataset:
    data = np.array(self.ds)
    if self.ds_type == ds_types['matrix']:
        data = data.transpose()
    if self.ds_type == ds_types['vector'] or self.ds_type == ds_types['coordinate']:
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
    try:
        json_dict = json.loads(self.ds.value[0])
    except ValueError:
        txt = _display_string(graphicsView, self.ds)
    else:
        sample = json_dict.pop('sample')
        instruments = json_dict.pop('instruments')
        txt = ""
        for key in sorted(json_dict):
            txt += str(key) + ":   " + str(json_dict[key])+"\n"        
        txt += '\n'
        if sample:
            txt += 'sample:\n   '
            for key in sorted(sample): 
                try:
                    txt += str(key) + ":   " + str(sample[key]['content'])+"\n   "
                except: txt += str(key) + ":   " + str(sample[key])+"\n   "
            txt += '\n'
        if instruments:
            txt += 'instruments:\n   '
            for instrument in sorted(instruments): 
                txt += instrument + ':\n      '
                for parameter in sorted(instruments[instrument]):
                    txt += str(parameter) + ":   " + str(instruments[instrument][parameter]['content'])+"\n      "
                txt = txt[:-3]
    graphicsView.insertPlainText(txt.rstrip())

def _display_string(graphicsView, ds):
    data =np.array(ds)
    txt = ""
    for d in data: 
        txt += d+'\n'
    return txt