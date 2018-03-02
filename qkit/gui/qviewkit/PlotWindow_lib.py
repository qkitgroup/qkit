# -*- coding: utf-8 -*-
"""
@author: hannes.rotzinger@kit.edu / 2015,2016,2017, 2018
         marco.pfirrmann@kit.edu / 2016, 2017, 2018
@license: GPL
"""
import sys
in_pyqt5 = False
try:
    from PyQt5.QtCore import Qt
    in_pyqt5 = True
except ImportError as e:
    pass

if not in_pyqt5:
    try:
        from PyQt4.QtCore import Qt
    except ImportError:
        print("import of PyQt5 and PyQt4 failed. Install one of those.")
        sys.exit(-1)

import numpy as np
import json
import pyqtgraph as pg
import qkit
from qkit.storage.hdf_constants import ds_types

""" A few handy methods for label and scale """
def _get_ds_url(ds,url):
    """
    If 'url' is already a absolute url in the h5 file it gets returned.
    Otherwise the absolute url in read out of the ds-metadata.
    """
    if _get_ds(ds, url): 
        return url
    else:
        return ds.attrs.get(url,'_none_')
       
def _get_ds(ds,ds_url):
    try:
        return ds.file[ds_url]
    except:
        return None
    
def _get_axis_scale(ds):
    # assumed that a axis is one dimensional:
    try:
        x0 = ds[0]
        dx = ds[1]-ds[0]
        return (x0,dx)
    except:
        return (0,1)

def _get_unit(ds):
    return ds.attrs.get('unit','_none_')

def _get_name(ds):
    return ds.attrs.get('name','_none_')
        
def _get_all_ds_names_units_scales(ds,ds_urls= []):
    """ method to unify the way labels, units, and scales are defined """
    dss = []
    
    for ds_url in ds_urls:
        dss.append(_get_ds(ds, _get_ds_url(ds, ds_url)))
    # the last dataset is always the displayed data.
    dss.append(ds)
    
    names = []
    units = []  
    scales = []
    for ds in dss:
        names.append(_get_name(ds))
        units.append(_get_unit(ds))
        scales.append(_get_axis_scale(ds))

    return dss, names, units, scales

def _display_1D_view(self,graphicsView):
    graphicsView.clear()    

    if not graphicsView.plotItem.legend:
        graphicsView.plotItem.addLegend(size=(160,48),offset=(30,15))
    
    overlay_num = self.ds.attrs.get("overlays",0)

    for i in range(overlay_num+1):
        xyurls = self.ds.attrs.get("xy_"+str(i),"")
        ds_urls = [xyurls.split(":")[0], xyurls.split(":")[1]]
        if xyurls:
            err_url = self.ds.attrs.get("xy_"+str(i)+"_error","")
            if err_url:
                ds_urls.append(err_url)
            dss, names, units, scales = _get_all_ds_names_units_scales(self.ds, ds_urls)

            # retrieve the data type and store it in  x_ds_type, y_ds_type
            x_ds_type = dss[0].attrs.get('ds_type',ds_types['coordinate'])
            y_ds_type = dss[1].attrs.get('ds_type',ds_types['coordinate'])
            
            if x_ds_type == ds_types['coordinate'] or x_ds_type == ds_types['vector']:
                if y_ds_type == ds_types['vector'] or y_ds_type == ds_types['coordinate']:
                    self.VTraceXSelector.setEnabled(False)
                    self.VTraceYSelector.setEnabled(False)
                    
                    x_data = dss[0][()]
                    y_data = dss[1][()]
                    if err_url:
                        err_data = dss[2][()]
    
                elif y_ds_type == ds_types['matrix']:
                    self.VTraceXSelector.setEnabled(True)
                    range_max = dss[1].shape[0]
                    self.VTraceXSelector.setRange(-1*range_max,range_max-1)
                    self.VTraceXValue.setText(self._getXValueFromTraceNum(dss[1],self.VTraceXNum))
                    self.VTraceYSelector.setEnabled(False)
        
                    x_data = dss[0][()]
                    y_data = dss[1][()][self.VTraceXNum]
                    if err_url:
                        err_data = dss[2][()][self.VTaceXNum]
                
                elif y_ds_type == ds_types['box']:
                    self.VTraceXSelector.setEnabled(True)
                    range_maxX = dss[1].shape[0]
                    self.VTraceXSelector.setRange(-1*range_maxX,range_maxX-1)
                    self.VTraceXValue.setText(self._getXValueFromTraceNum(dss[1],self.VTraceXNum))
                    self.VTraceYSelector.setEnabled(True)
                    range_maxY = dss[1].shape[1]
                    self.VTraceYSelector.setRange(-1*range_maxY,range_maxY-1)
                    self.VTraceYValue.setText(self._getYValueFromTraceNum(dss[1],self.VTraceYNum))
                    
                    x_data = dss[0][()]
                    y_data = dss[1][()][self.VTraceXNum,self.VTraceYNum,:]
                    if err_url:
                        err_data = dss[2][()][self.VTraceXNum,self.VTraceYNum,:]
                
            ## This is in our case used so far only for IQ plots. The functionality derives from this application.
            elif x_ds_type == ds_types['matrix']:
                self.VTraceXSelector.setEnabled(True)
                range_max = np.minimum(dss[0].shape[0],dss[1].shape[0])
                self.VTraceXSelector.setRange(-1*range_max,range_max-1)
                self.VTraceXValue.setText(self._getXValueFromTraceNum(dss[1],self.VTraceXNum))
                self.VTraceYSelector.setEnabled(False)
    
                x_data = dss[0][()][self.VTraceXNum]
                y_data = dss[1][()][self.VTraceXNum]
    
            elif x_ds_type == ds_types['box']:
                self.VTraceXSelector.setEnabled(True)
                range_maxX = dss[1].shape[0]
                self.VTraceXSelector.setRange(-1*range_maxX,range_maxX-1)
                self.VTraceXValue.setText(self._getXValueFromTraceNum(dss[1],self.VTraceXNum))
                self.VTraceYSelector.setEnabled(True)
                range_maxY = dss[1].shape[1]
                self.VTraceYSelector.setRange(-1*range_maxY,range_maxY-1)
                self.VTraceYValue.setText(self._getYValueFromTraceNum(dss[1],self.VTraceYNum))
                
                x_data = dss[0][()][self.VTraceXNum,self.VTraceYNum,:]
                y_data = dss[1][()][self.VTraceXNum,self.VTraceYNum,:]
    
            else:
                return
    
            # set the y data  to the decibel scale 
            if self.manipulation & self.manipulations['dB']:
                y_data = 20 *np.log10(y_data)
                units[1]='dB'
              
            # unwrap the phase
            if self.manipulation & self.manipulations['wrap']:
                y_data = np.unwrap(y_data)
            
            # linearly correct the data    
            if self.manipulation & self.manipulations['linear']:
                y_data = y_data - np.linspace(y_data[0],y_data[-1],len(y_data))
    
            graphicsView.setLabel('left', names[1], units=units[1])
            graphicsView.setLabel('bottom', names[0], units=units[0])
                        
            view_params = json.loads(self.ds.attrs.get("view_params",{}))
            
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
                graphicsView.plotItem.legend.removeItem(names[1])
            except:
                pass
            
            if self.plot_style==self.plot_styles['line']:
                graphicsView.plot(y=y_data, x=x_data,pen=(i,3), name = names[1], connect='finite')
            elif self.plot_style==self.plot_styles['linepoint']:
                symbols=['+','o','s','t','d']
                graphicsView.plot(y=y_data, x=x_data,pen=(i,3), name = names[1], connect='finite',symbol=symbols[i%len(symbols)])
            elif self.plot_style==self.plot_styles['point']:
                symbols=['+','o','s','d','t']
                graphicsView.plot(y=y_data, x=x_data, name = names[1], pen=None, symbol=symbols[i%len(symbols)])    
            if err_url:
                err = pg.ErrorBarItem(x=x_data, y=y_data, height=err_data, beam=0.25*scales[0][0])
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
            self.PointX.setText("X: %.6e %s"%(xval,units[0])) 
            self.PointY.setText("Y: %.6e %s"%(yval,units[1])) 
            
            try:
                self.data_coord=  "%e\t%e\t%e\t%e" % (xval, yval,self._last_x_pos-xval,xval/(self._last_x_pos-xval))
            except ZeroDivisionError:
                pass
                
            self._last_x_pos = xval
    
    self.proxy = pg.SignalProxy(plVi.scene().sigMouseMoved, rateLimit=15, slot=mouseMoved)

def _display_1D_data(self,graphicsView):
    """
    This is the most basic way to display data. It plots the values in the dataset against the hightes
    coordinate, ie a VNA trace or the latest IV curve (data vs bias).
    For getting the correct values on the x-axis and the labeling the different types of dataset are
    handled individually.
    """
    if self.ds_type == ds_types['vector'] or self.ds_type == ds_types['coordinate'] or (self.ds_type == -1 and len(self.ds.shape) == 1): #last expresson is for old hdf-files
        dss, names, units, scales = _get_all_ds_names_units_scales(self.ds, ['x_ds_url'])
        
        # timestamps do (not?) have a x_ds_url in the 1d case. This is more a bug to be fixed in the
        # timstamp_ds part of qkit the resulting error is fixed here for now.
        try:
            x_data =dss[0][()][:dss[1].shape[-1]] #x_data gets truncated to y_data shape if neccessary
        except:
            x_data = [i for i in range(dss[1].shape[-1])]
        y_data = dss[1][()]

    elif self.ds_type == ds_types['matrix'] or (self.ds_type == -1 and len(self.ds.shape) == 2): #last expresson is for old hdf-files
        """
        For a matrix type the data to be displayed on the x-axis is the y-axis (highest coordinate) of the ds
        """
        dss, names, units, scales = _get_all_ds_names_units_scales(self.ds, ['y_ds_url'])

        if self.TraceValueChanged:
            """
            If the trace to be displayed has been changed, the correct dataslice and the displayed
            text has to be adjusted.
            """
            #calc trace number from entered value
            (x0, dx) = _get_axis_scale(_get_ds(self.ds, _get_ds_url(self.ds, 'x_ds_url')))
            num = int((self._trace_value-x0)/dx)
            self.TraceNum = num
            self.TraceSelector.setValue(self.TraceNum)
            self.TraceValueChanged = False

        self.TraceValue.setText(self._getXValueFromTraceNum(self.ds,self.TraceNum))

        x_data =dss[0][()][:dss[1].shape[-1]] #x_data gets truncated to y_data shape if neccessary
        y_data = dss[1][()][self.TraceNum]

    elif self.ds_type == ds_types['box']:
        """
        For a box type the data to be displayed on the x-axis is the z-axis (highest coordinate) of the ds
        """
        dss, names, units, scales = _get_all_ds_names_units_scales(self.ds, ['z_ds_url'])

        if self.TraceXValueChanged:
            """
            If the trace to be displayed has been changed, the correct dataslice and the displayed
            text has to be adjusted.
            """
            #calc trace number from entered value
            (x0, dx) = _get_axis_scale(_get_ds(self.ds, _get_ds_url(self.ds, 'x_ds_url')))
            num = int((self._traceX_value-x0)/dx)+1
            self.TraceXNum = num
            self.TraceXSelector.setValue(self.TraceXNum)
            self.TraceXValueChanged = False
        
        if self.TraceYValueChanged:
            """
            If the trace to be displayed has been changed, the correct dataslice and the displayed
            text has to be adjusted.
            """
            #calc trace number from entered value
            (y0, dy) = _get_axis_scale(_get_ds(self.ds, _get_ds_url(self.ds, 'y_ds_url')))
            num = int((self._traceY_value-y0)/dy)
            self.TraceYNum = num
            self.TraceYSelector.setValue(self.TraceYNum)
            self.TraceYValueChanged = False

        self.TraceXValue.setText(self._getXValueFromTraceNum(self.ds,self.TraceXNum))
        self.TraceYValue.setText(self._getYValueFromTraceNum(self.ds,self.TraceYNum))
        
        x_data =dss[0][()][:dss[1].shape[-1]] #x_data gets truncated to y_data shape if neccessary
        y_data = dss[1][()][self.TraceXNum,self.TraceYNum,:]


    # set the y data  to the decibel scale 
    if self.manipulation & self.manipulations['dB']:
        y_data = 20 *np.log10(y_data)
        units[1] = 'dB'
    
    # unwrap the phase
    if self.manipulation & self.manipulations['wrap']:
        y_data = np.unwrap(y_data)
        
    # linearly correct the data    
    if self.manipulation & self.manipulations['linear']:
        y_data = y_data - np.linspace(y_data[0],y_data[-1],len(y_data))
    
    graphicsView.setLabel('left', names[1], units=units[1])
    graphicsView.setLabel('bottom', names[0] , units=units[0])

    #if only one entry in the dataset --> point-style
    if self.ds.shape[-1]==1:
        self.plot_style = self.plot_styles['point']

    if self.plot_style==self.plot_styles['line']:
        graphicsView.plot(y=y_data, x=x_data, clear = True, pen=(200,200,100),connect='finite')
    elif self.plot_style==self.plot_styles['linepoint']:
        graphicsView.plot(y=y_data, x=x_data, clear = True, pen=(200,200,100),connect='finite',symbol='+')
    elif self.plot_style==self.plot_styles['point']:
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

            self.PointX.setText("X: %.6e %s"%(xval, units[0])) 
            self.PointY.setText("Y: %.6e %s"%(yval, units[1])) 
            
            try:
                self.data_coord=  "%e\t%e\t%e\t%e" % (xval, yval,self._last_x_pos-xval,xval/(self._last_x_pos-xval))
            except ZeroDivisionError:
                pass
            
            self._last_x_pos = xval

    self.proxy = pg.SignalProxy(plVi.scene().sigMouseMoved, rateLimit=15, slot=mouseMoved)

def _display_2D_data(self,graphicsView):
    """
    The 2d color plot gets treated similar: data and labels are looked up with respect to the dataset type
    and the PlotType for ds-boxes.
    Here the only relevant information is the data to be plotted (a 2d matrix of values) and the x- and 
    y-axis. From them the specific "slice" of data is selected and the lable infos are read out. The exact data
    in the datasets on the x- and y-axis are not needed. The underlying pyqtgraph fct works with a position 
    (x0, y0) and a scale (dx, dy) for creating the axis tics and tic lables. This means it is not possible
    to display any non-linear scaled axis data.
    """

    if self.ds_type == ds_types['matrix']:
        """
        The matrix ds-type only knows one 2d plotting option. x_ds on x- and y_ds on y-axis
        """
        dss, names, units, scales = _get_all_ds_names_units_scales(self.ds, ['x_ds_url', 'y_ds_url'])
        data = dss[2][()]
        
        fill_x = dss[2].shape[0]
        fill_y = dss[2].shape[1]        
    if self.ds_type == ds_types['box']:
        """
        The box ds-type can be plotted from 3 different "viewing directions" (PlotType). Depending on its 
        setting the x- and y-axis are set.
        The ds-type box also has a z_ds_url.
        """
        if self.PlotTypeSelector.currentIndex() == 0: #y_ds on x-axis; z_ds on y-axis
            if self.TraceXValueChanged:
                #calc trace number from entered value
                num = int((self._traceX_value-self.ds.attrs.get("x0",0))/(self.ds.attrs.get("dx",1)))
                self.TraceXNum = num
                self.TraceXSelector.setValue(self.TraceXNum)
                self.TraceXValueChanged = False
            
            dss, names, units, scales = _get_all_ds_names_units_scales(self.ds, ['y_ds_url', 'z_ds_url'])
            data = dss[2][()][self.TraceXNum,:,:]
            
            fill_x = dss[2].shape[1]
            fill_y = dss[2].shape[2]
            
        if self.PlotTypeSelector.currentIndex() == 1: #x_ds on x-axis; z_ds on y-axis
            if self.TraceYValueChanged:
                #calc trace number from entered value
                num = int((self._traceY_value-self.ds.attrs.get("y0",0))/(self.ds.attrs.get("dy",1)))
                self.TraceYNum = num
                self.TraceYSelector.setValue(self.TraceYNum)
                self.TraceYValueChanged = False

            dss, names, units, scales = _get_all_ds_names_units_scales(self.ds, ['x_ds_url', 'z_ds_url'])       
            data = dss[2][()][:,self.TraceYNum,:]
            
            fill_x = dss[2].shape[0]
            fill_y = dss[2].shape[2]
            
        if self.PlotTypeSelector.currentIndex() == 2: #x_ds on x-axis; y_ds on y-axis
            if self.TraceZValueChanged:
                #calc trace number from entered value
                num = int((self._traceZ_value-self.ds.attrs.get("z0",0))/(self.ds.attrs.get("dz",1)))
                self.TraceZNum = num
                self.TraceZSelector.setValue(self.TraceZNum)
                self.TraceZValueChanged = False

            dss, names, units, scales = _get_all_ds_names_units_scales(self.ds, ['x_ds_url', 'y_ds_url'])       
            data = dss[2][()][:,:,self.TraceZNum]
            
            fill_x = dss[2].shape[0]
            fill_y = dss[2].shape[1]

        self.TraceXValue.setText(self._getXValueFromTraceNum(self.ds,self.TraceXNum))
        self.TraceYValue.setText(self._getYValueFromTraceNum(self.ds,self.TraceYNum))
        self.TraceZValue.setText(self._getZValueFromTraceNum(self.ds,self.TraceZNum))

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
    
    if self.manipulation & self.manipulations['sub_offset_avg_y']:
        #ignore division by zero
        old_warn = np.seterr(divide='print')
        data = data - np.nanmean(data,axis=1,keepdims=True)
        np.seterr(**old_warn)
    
    # subtract offset from the data
    if self.manipulation & self.manipulations['norm_data_avg_x']:
        #ignore division by zero
        old_warn = np.seterr(divide='print')
        data = data / np.nanmean(data,axis=0,keepdims=True)
        np.seterr(**old_warn)

    graphicsView.clear()   
    graphicsView.view.setLabel('left', names[1], units=units[1])
    graphicsView.view.setLabel('bottom', names[0], units=units[0])
    graphicsView.view.setTitle(names[2]+" ("+units[2]+")")
    graphicsView.view.invertY(False)
    
    # pos is the zero-point of the axis  
    # scale is responsible for the "accidential" correct display of the axis
    # for downsweeps scale has negative values and extends the axis from the min values into the correct direction
    graphicsView.setImage(data,pos=(scales[0][0]-scales[0][1]/2.,scales[1][0]-scales[1][1]/2.),scale=(scales[0][1], scales[1][1]))
    graphicsView.show()

    # Fixme roi ...
    """
    The error in the ROI may come from a not always correct setting of xmin/xmax...
    """
    graphicsView.roi.setPos([scales[0][0],scales[1][0]])
    graphicsView.roi.setSize([fill_x * scales[0][1],fill_y * scales[1][1]])
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
                if x_index >= 0 and y_index >= 0:
                    if x_index < fill_x and y_index < fill_y:
                        
                        #Check this for < or <=
                        #Also the x0s and dxs
                        
                        xval = scales[0][0]+x_index * scales[0][1]
                        yval = scales[1][0]+y_index * scales[1][1]
                        zval = data[x_index][y_index]
                        self.PointX.setText("X: %.6e %s"%(xval,units[0])) 
                        self.PointY.setText("Y: %.6e %s"%(yval,units[1])) 
                        self.PointZ.setText("Z: %.6e %s"%(zval,units[2])) 
                        self.data_coord=  "%g\t%g\t%g" % (xval, yval,zval)

        else:
            xval = 0
            yval = 0
            zval = 0
            self.PointX.setText("X: %.6e %s"%(xval,units[0])) 
            self.PointY.setText("Y: %.6e %s"%(yval,units[1])) 
            self.PointZ.setText("Z: %.6e %s"%(zval,units[2])) 
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
        graphicsView.setFormat(str(data))
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