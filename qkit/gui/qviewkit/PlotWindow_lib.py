# -*- coding: utf-8 -*-
"""
@author: hannes.rotzinger@kit.edu / 2015,2016,2017, 2018
         marco.pfirrmann@kit.edu / 2016, 2017, 2018
@license: GPL

This file handles the actual display of the data within the respective canvas.
The functions here are called (case sensitive) by PlotWindow and the
information is mainly stored in self variables of the PlotWindow class object.
Possible display options are 1d (for data and views), 2d, table, as well as
JSON encoded and plain text.
The _display functions are supported by simple getter functions for metadata
readout.
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
import pprint


def _display_1D_view(self, graphicsView):
    """displays the 1d plot(s) views from the respective datasets.

    The entries in the overlay dict get evaluated and handled according to 
    their ds-type. Depending on the ds-type the QComboBox handles the index of 
    the shown data.

    Args:
        self: Object of the PlotWindow class.
        graphicsView: Object of pyqtgraph's PlotWidget class.

    Returns:
        No return variable. The function operates on an object of the 
        PlotWindow class.
    """
    
    graphicsView.clear()
    
    if not graphicsView.plotItem.legend:
        graphicsView.plotItem.addLegend(size=(160, 48), offset=(30, 15))
    
    overlay_num = self.ds.attrs.get("overlays", 0)
    
    ## evaluate the overlay-entries to get the ds_urls of the datasets to be 
    ## displayed.
    view_params = json.loads(self.ds.attrs.get("view_params", {}))
    for i in range(overlay_num + 1):
        xyurls = self.ds.attrs.get("xy_" + str(i), "")
        ds_urls = [xyurls.split(":")[0], xyurls.split(":")[1]]
        if xyurls:
            err_url = self.ds.attrs.get("xy_" + str(i) + "_error", "")
            if err_url:
                ds_urls.append(err_url)
            dss, names, units, scales = _get_all_ds_names_units_scales(self.ds, ds_urls)
            
            ## retrieve the data type and store it in  x_ds_type, y_ds_type
            x_ds_type = dss[0].attrs.get('ds_type', ds_types['coordinate'])
            y_ds_type = dss[1].attrs.get('ds_type', ds_types['coordinate'])
            
            ## If there are more than one dataset we need to check the dimensions
            ## first, the "lower" dimensional ds is the limiting factor.
            if x_ds_type == ds_types['coordinate'] or x_ds_type == ds_types['vector']:
                if y_ds_type == ds_types['vector'] or y_ds_type == ds_types['coordinate']:
                    self.VTraceXSelector.setEnabled(False)
                    self.VTraceYSelector.setEnabled(False)
                    
                    x_data = dss[0][()]
                    y_data = dss[1][()]
                    if err_url:
                        err_data = dss[2][()]
                    
                    # prevent a crash when the two datasets have a different length
                    # solution: truncate the longer dataset to the length of the shorter
                    # Note: This can happen if the hdf.flush() is not in sync with the viewer
                    
                    x_data_len = len(x_data)
                    y_data_len = len(y_data)
                    if x_data_len != y_data_len:
                        if x_data_len > y_data_len:
                            x_data = x_data[:y_data_len]
                        else:
                            y_data = y_data[:x_data_len]
                
                elif y_ds_type == ds_types['matrix']:
                    self.VTraceXSelector.setEnabled(True)
                    range_max = dss[1].shape[0]
                    self.VTraceXSelector.setRange(-1 * range_max, range_max - 1)
                    self.VTraceXValue.setText(self._getXValueFromTraceNum(dss[1], self.VTraceXNum))
                    self.VTraceYSelector.setEnabled(False)
                    
                    x_data = dss[0][()]
                    y_data = dss[1][()][self.VTraceXNum]
                    if err_url:
                        err_data = dss[2][()][self.VTaceXNum]
                
                elif y_ds_type == ds_types['box']:
                    self.VTraceXSelector.setEnabled(True)
                    range_maxX = dss[1].shape[0]
                    self.VTraceXSelector.setRange(-1 * range_maxX, range_maxX - 1)
                    self.VTraceXValue.setText(self._getXValueFromTraceNum(dss[1], self.VTraceXNum))
                    self.VTraceYSelector.setEnabled(True)
                    range_maxY = dss[1].shape[1]
                    self.VTraceYSelector.setRange(-1 * range_maxY, range_maxY - 1)
                    self.VTraceYValue.setText(self._getYValueFromTraceNum(dss[1], self.VTraceYNum))
                    
                    x_data = dss[0][()]
                    y_data = dss[1][()][self.VTraceXNum, self.VTraceYNum, :]
                    if err_url:
                        err_data = dss[2][()][self.VTraceXNum, self.VTraceYNum, :]
            
            ## This is in our case used so far only for IQ plots. The 
            ## functionality derives from this application.
            elif x_ds_type == ds_types['matrix']:
                self.VTraceXSelector.setEnabled(True)
                range_max = np.minimum(dss[0].shape[0], dss[1].shape[0])
                self.VTraceXSelector.setRange(-1 * range_max, range_max - 1)
                self.VTraceXValue.setText(self._getXValueFromTraceNum(dss[1], self.VTraceXNum))
                self.VTraceYSelector.setEnabled(False)
                
                x_data = dss[0][()][self.VTraceXNum]
                y_data = dss[1][()][self.VTraceXNum]
            
            elif x_ds_type == ds_types['box']:
                self.VTraceXSelector.setEnabled(True)
                range_maxX = dss[1].shape[0]
                self.VTraceXSelector.setRange(-1 * range_maxX, range_maxX - 1)
                self.VTraceXValue.setText(self._getXValueFromTraceNum(dss[1], self.VTraceXNum))
                self.VTraceYSelector.setEnabled(True)
                range_maxY = dss[1].shape[1]
                self.VTraceYSelector.setRange(-1 * range_maxY, range_maxY - 1)
                self.VTraceYValue.setText(self._getYValueFromTraceNum(dss[1], self.VTraceYNum))
                
                x_data = dss[0][()][self.VTraceXNum, self.VTraceYNum, :]
                y_data = dss[1][()][self.VTraceXNum, self.VTraceYNum, :]
            
            else:
                return
            
            ## Any data manipulation (dB <-> lin scale, etc) is done here
            y_data, units[1] = _do_data_manipulation(y_data, units[1], ds_types['vector'], self.manipulation, self.manipulations)
            
            graphicsView.setLabel('left', names[1], units=units[1])
            graphicsView.setLabel('bottom', names[0], units=units[0])
            
            # this allows to set a couple of plot related settings
            if view_params:
                aspect = view_params.pop('aspect', False)
                if aspect:
                    graphicsView.setAspectLocked(lock=True, ratio=aspect)
                    # bgcolor = view_params.pop('bgcolor',False)
                    # if bgcolor:
                    #    print tuple(bgcolor)
                    #    graphicsView.setBackgroundColor(tuple(bgcolor))
            
            try:
                graphicsView.plotItem.legend.removeItem(names[1])
            except:
                pass

            if not self.user_setting_changed:
                self.plot_style = view_params.get('plot_style', 0)
            self.markersize = view_params.get('markersize', 5)
            if self.plot_style == self.plot_styles['line']:
                graphicsView.plot(y=y_data, x=x_data, pen=(i, 4), name=names[1], connect='finite')
            elif self.plot_style == self.plot_styles['linepoint']:
                symbols = ['+', 'o', 's', 't', 'd']
                graphicsView.plot(y=y_data, x=x_data, pen=(i, 4), name=names[1], connect='finite', symbol=symbols[i % len(symbols)], symbolSize=self.markersize)
            elif self.plot_style == self.plot_styles['point']:
                symbols = ['+', 'o', 's', 'd', 't']
                graphicsView.plot(y=y_data, x=x_data, name=names[1], pen=None, symbol=symbols[i % len(symbols)], symbolSize=self.markersize)
            if err_url:
                err = pg.ErrorBarItem(x=x_data, y=y_data, height=err_data, beam=0.25 * scales[0][0])
                graphicsView.getPlotItem().addItem(err)

    # optionally take provided x_name, y_name as labels
    if view_params.get("labels", False):
        graphicsView.setLabel('bottom', view_params['labels'][0], units=units[0])
        graphicsView.setLabel('left', view_params['labels'][1], units=units[1])
    
    plIt = graphicsView.getPlotItem()
    plVi = plIt.getViewBox()
    
    self._last_x_pos = 0
    
    def mouseMoved(mpos):
        mpos = mpos[0]
        if plIt.sceneBoundingRect().contains(mpos):
            mousePoint = plVi.mapSceneToView(mpos)
            xval = mousePoint.x()
            yval = mousePoint.y()
            self.PointX.setText("X: %.6e %s" % (xval, units[0]))
            self.PointY.setText("Y: %.6e %s" % (yval, units[1]))
            
            try:
                self.data_coord = "%e\t%e\t%e\t%e" % (xval, yval, self._last_x_pos - xval, xval / (self._last_x_pos - xval))
            except ZeroDivisionError:
                pass
            
            self._last_x_pos = xval
    
    self.proxy = pg.SignalProxy(plVi.scene().sigMouseMoved, rateLimit=15, slot=mouseMoved)


def _display_1D_data(self, graphicsView):
    """displays 1d data from the respective dataset.

    This is the most basic way to display data. It plots the values in the 
    dataset against the highest coordinate, ie a VNA trace or the latest IV 
    curve (data vs bias).
    Depending on the ds-type, the QComboBox handles the index of the shown 
    data.
    
    Args:
        self: Object of the PlotWindow class.
        graphicsView: Object of pyqtgraph's PlotWidget class.

    Returns:
        No return variable. The function operates on an object of the 
        PlotWindow class.
    """
    if self.ds_type == ds_types['vector'] or (self.ds_type == -1 and len(self.ds.shape) == 1):  # last expresson is for old hdf-files
        dss, names, units, scales = _get_all_ds_names_units_scales(self.ds, ['x_ds_url'])
        
        # timestamps do (not?) have a x_ds_url in the 1d case. This is more a bug to be fixed in the
        # timstamp_ds part of qkit the resulting error is fixed here for now.
        try:
            x_data = dss[0][()][:dss[1].shape[-1]]  # x_data gets truncated to y_data shape if neccessary
        except:
            x_data = [i for i in range(dss[1].shape[-1])]
        y_data = dss[1][()]
    
    elif self.ds_type == ds_types['coordinate']:
        ## a coordinate does not have any coordinate. it gets plotted against the entry index.
        ## this does not quite work with the unified readout.
        names, units, scales = ['index'], ['#'], [(0, 1)]
        dss, n, u, s = _get_all_ds_names_units_scales(self.ds)
        names.append(n[0])
        units.append(u[0])
        scales.append(s[0])
        # timestamps do (not?) have a x_ds_url in the 1d case. This is more a bug to be fixed in the
        # timstamp_ds part of qkit the resulting error is fixed here for now.
        x_data = [i for i in range(dss[0].shape[-1])]
        y_data = dss[0][()]
    
    elif self.ds_type == ds_types['matrix'] or (self.ds_type == -1 and len(self.ds.shape) == 2):  # last expresson is for old hdf-files
        """
        For a matrix type the data to be displayed on the x-axis depends on the selected plot_type
        """
        
        if self.PlotTypeSelector.currentIndex() == 1:  # y_ds on x-axis
            dss, names, units, scales = _get_all_ds_names_units_scales(self.ds, ['y_ds_url'])
            if self.TraceXValueChanged:
                """
                If the trace to be displayed has been changed, the correct dataslice and the displayed
                text has to be adjusted.
                """
                # calc trace number from entered value
                (x0, dx) = _get_axis_scale(_get_ds(self.ds, _get_ds_url(self.ds, 'x_ds_url')))
                num = int((self._traceX_value - x0) / dx)
                self.TraceXNum = num
                self.TraceXSelector.setValue(self.TraceXNum)
                self.TraceXValueChanged = False
            
            y_data = dss[1][()][self.TraceXNum]
            x_data = dss[0][()][:dss[1].shape[-1]]  # x_data gets truncated to y_data shape if neccessary
        
        if self.PlotTypeSelector.currentIndex() == 2:  # x_ds on x-axis
            dss, names, units, scales = _get_all_ds_names_units_scales(self.ds, ['x_ds_url'])
            if self.TraceYValueChanged:
                """
                If the trace to be displayed has been changed, the correct dataslice and the displayed
                text has to be adjusted.
                """
                
                # calc trace number from entered value
                (x0, dx) = _get_axis_scale(_get_ds(self.ds, _get_ds_url(self.ds, 'y_ds_url')))
                num = int((self._traceY_value - x0) / dx)
                self.TraceYNum = num
                self.TraceYSelector.setValue(self.TraceYNum)
                self.TraceYValueChanged = False
            
            y_data = dss[1][()][:, self.TraceYNum]
            x_data = dss[0][()][:dss[1].shape[0]]  # x_data gets truncated to y_data shape if neccessary
        
        self.TraceXValue.setText(self._getXValueFromTraceNum(self.ds, self.TraceXNum))
        self.TraceYValue.setText(self._getYValueFromTraceNum(self.ds, self.TraceYNum))
    
    
    
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
            # calc trace number from entered value
            (x0, dx) = _get_axis_scale(_get_ds(self.ds, _get_ds_url(self.ds, 'x_ds_url')))
            num = int((self._traceX_value - x0) / dx) + 1
            self.TraceXNum = num
            self.TraceXSelector.setValue(self.TraceXNum)
            self.TraceXValueChanged = False
        
        if self.TraceYValueChanged:
            """
            If the trace to be displayed has been changed, the correct dataslice and the displayed
            text has to be adjusted.
            """
            # calc trace number from entered value
            (y0, dy) = _get_axis_scale(_get_ds(self.ds, _get_ds_url(self.ds, 'y_ds_url')))
            num = int((self._traceY_value - y0) / dy)
            self.TraceYNum = num
            self.TraceYSelector.setValue(self.TraceYNum)
            self.TraceYValueChanged = False
        
        self.TraceXValue.setText(self._getXValueFromTraceNum(self.ds, self.TraceXNum))
        self.TraceYValue.setText(self._getYValueFromTraceNum(self.ds, self.TraceYNum))
        
        x_data = dss[0][()][:dss[1].shape[-1]]  # x_data gets truncated to y_data shape if neccessary
        y_data = dss[1][()][self.TraceXNum, self.TraceYNum, :]
    
    ## Any data manipulation (dB <-> lin scale, etc) is done here
    y_data, units[1] = _do_data_manipulation(y_data, units[1], self.ds_type, self.manipulation, self.manipulations)
    
    graphicsView.setLabel('left', names[1], units=units[1])
    graphicsView.setLabel('bottom', names[0], units=units[0])
    
    # if only one entry in the dataset --> point-style
    if y_data.shape[-1] == 1:
        self.plot_style = self.plot_styles['point']
    
    if self.plot_style == self.plot_styles['line']:
        graphicsView.plot(y=y_data, x=x_data, clear=True, pen=(200, 200, 100), connect='finite')
    elif self.plot_style == self.plot_styles['linepoint']:
        graphicsView.plot(y=y_data, x=x_data, clear=True, pen=(200, 200, 100), connect='finite', symbol='+')
    elif self.plot_style == self.plot_styles['point']:
        graphicsView.plot(y=y_data, x=x_data, clear=True, pen=None, symbol='+')
    
    plIt = graphicsView.getPlotItem()
    plVi = plIt.getViewBox()
    
    self._last_x_pos = 0
    
    def mouseMoved(mpos):
        mpos = mpos[0]
        if plIt.sceneBoundingRect().contains(mpos):
            mousePoint = plVi.mapSceneToView(mpos)
            xval = mousePoint.x()
            yval = mousePoint.y()
            
            self.PointX.setText("X: %.6e %s" % (xval, units[0]))
            self.PointY.setText("Y: %.6e %s" % (yval, units[1]))
            
            try:
                self.data_coord = "%e\t%e\t%e\t%e" % (xval, yval, self._last_x_pos - xval, xval / (self._last_x_pos - xval))
            except ZeroDivisionError:
                pass
            
            self._last_x_pos = xval
    
    self.proxy = pg.SignalProxy(plVi.scene().sigMouseMoved, rateLimit=15, slot=mouseMoved)


def _display_2D_data(self, graphicsView):
    """displays a 2d matrix of data color coded.

    The 2d color plot gets treated similar: data and labels are looked up with 
    respect to the dataset type and the PlotType for ds-boxes.
    Here the only relevant information is the data to be plotted (a 2d matrix 
    of values) and the x- and y-axis. From them the specific "slice" of data is
    selected and the lable infos are read out. The exact data in the datasets 
    on the x- and y-axis are not needed. The underlying pyqtgraph fct works 
    with a position (x0, y0) and a scale (dx, dy) for creating the axis tics 
    and tic lables. This means it is not possible to display any non-linear 
    scaled axis data.
    Depending on the ds-type, the QComboBox handles the index of the shown 
    data.
    
    Args:
        self: Object of the PlotWindow class.
        graphicsView: Modified object of pyqtgraph's ImageView class.

    Returns:
        No return variable. The function operates on an object of the 
        PlotWindow class.
    """
    
    if self.ds_type == ds_types['matrix']:
        """
        The matrix ds-type only knows one 2d plotting option. x_ds on x- and y_ds on y-axis
        """
        dss, names, units, scales = _get_all_ds_names_units_scales(self.ds, ['x_ds_url', 'y_ds_url'])
        try:
          data = dss[2][()]
        except IOError as e:
              print("Could not open data file")
              print(e)
              return
        
        fill_x = dss[2].shape[0]
        fill_y = dss[2].shape[1]
        
        self.TraceXValue.setText(self._getXValueFromTraceNum(self.ds, self.TraceXNum))
        self.TraceYValue.setText(self._getYValueFromTraceNum(self.ds, self.TraceYNum))
    if self.ds_type == ds_types['box']:
        """
        The box ds-type can be plotted from 3 different "viewing directions" (PlotType). Depending on its 
        setting the x- and y-axis are set.
        The ds-type box also has a z_ds_url.
        """
        if self.PlotTypeSelector.currentIndex() == 0:  # y_ds on x-axis; z_ds on y-axis
            if self.TraceXValueChanged:
                # calc trace number from entered value
                num = int((self._traceX_value - self.ds.attrs.get("x0", 0)) / (self.ds.attrs.get("dx", 1)))
                self.TraceXNum = num
                self.TraceXSelector.setValue(self.TraceXNum)
                self.TraceXValueChanged = False
            
            dss, names, units, scales = _get_all_ds_names_units_scales(self.ds, ['y_ds_url', 'z_ds_url'])
            try:
              data = dss[2][()][self.TraceXNum, :, :]
            except IOError as e:
              print("Could not open data file")
              print(e)
              return
            
            fill_x = dss[2].shape[1]
            fill_y = dss[2].shape[2]
        
        if self.PlotTypeSelector.currentIndex() == 1:  # x_ds on x-axis; z_ds on y-axis
            if self.TraceYValueChanged:
                # calc trace number from entered value
                num = int((self._traceY_value - self.ds.attrs.get("y0", 0)) / (self.ds.attrs.get("dy", 1)))
                self.TraceYNum = num
                self.TraceYSelector.setValue(self.TraceYNum)
                self.TraceYValueChanged = False
            
            dss, names, units, scales = _get_all_ds_names_units_scales(self.ds, ['x_ds_url', 'z_ds_url'])
            try:
              data = dss[2][()][:, self.TraceYNum, :]
            except IOError as e:
              print("Could not open data file")
              print(e)
              return
            
            fill_x = dss[2].shape[0]
            fill_y = dss[2].shape[2]
        
        if self.PlotTypeSelector.currentIndex() == 2:  # x_ds on x-axis; y_ds on y-axis
            if self.TraceZValueChanged:
                # calc trace number from entered value
                num = int((self._traceZ_value - self.ds.attrs.get("z0", 0)) / (self.ds.attrs.get("dz", 1)))
                self.TraceZNum = num
                self.TraceZSelector.setValue(self.TraceZNum)
                self.TraceZValueChanged = False
            
            dss, names, units, scales = _get_all_ds_names_units_scales(self.ds, ['x_ds_url', 'y_ds_url'])
            try:
              data = dss[2][()][:, :, self.TraceZNum]
            except IOError as e:
              print("Could not open data file")
              print(e)
              return
            
            fill_x = dss[2].shape[0]
            fill_y = dss[2].shape[1]
        
        self.TraceXValue.setText(self._getXValueFromTraceNum(self.ds, self.TraceXNum))
        self.TraceYValue.setText(self._getYValueFromTraceNum(self.ds, self.TraceYNum))
        self.TraceZValue.setText(self._getZValueFromTraceNum(self.ds, self.TraceZNum))
    
    data, units[2] = _do_data_manipulation(data, units[2], self.ds_type, self.manipulation, self.manipulations, colorplot=True)
    
    graphicsView.clear()
    graphicsView.view.setLabel('left', names[1], units=units[1])
    graphicsView.view.setLabel('bottom', names[0], units=units[0])
    graphicsView.view.setTitle(names[2] + " (" + units[2] + ")")
    graphicsView.view.invertY(False)
    
    # pos is the zero-point of the axis  
    # scale is responsible for the "accidential" correct display of the axis
    # for downsweeps scale has negative values and extends the axis from the min values into the correct direction
    graphicsView.setImage(data, pos=(scales[0][0] - scales[0][1] / 2., scales[1][0] - scales[1][1] / 2.), scale=(scales[0][1], scales[1][1]))
    graphicsView.show()
    
    # Fixme roi ...
    """
    The error in the ROI may come from a not always correct setting of xmin/xmax...
    """
    graphicsView.roi.setSize([abs(fill_x * scales[0][1]), abs(fill_y * scales[1][1])])
    graphicsView.roi.setPos([scales[0][0], scales[1][0]])
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
                        # Check this for < or <=
                        # Also the x0s and dxs
                        
                        xval = scales[0][0] + x_index * scales[0][1]
                        yval = scales[1][0] + y_index * scales[1][1]
                        zval = data[x_index][y_index]
                        self.PointX.setText("X: %.6e %s" % (xval, units[0]))
                        self.PointY.setText("Y: %.6e %s" % (yval, units[1]))
                        self.PointZ.setText("Z: %.6e %s" % (zval, units[2]))
                        self.data_coord = "%g\t%g\t%g" % (xval, yval, zval)
        
        else:
            xval = 0
            yval = 0
            zval = 0
            self.PointX.setText("X: %.6e %s" % (xval, units[0]))
            self.PointY.setText("Y: %.6e %s" % (yval, units[1]))
            self.PointZ.setText("Z: %.6e %s" % (zval, units[2]))
            self.data_coord = "%g\t%g\t%g" % (xval, yval, zval)
    
    self.proxy = pg.SignalProxy(imVi.scene().sigMouseMoved, rateLimit=15, slot=mouseMoved)


def _display_table(self, graphicsView):
    """displays the data values in a table.

    This function shows a table with the numerical values of the dataset with
    the shape depending on the ds-type.
    
    Args:
        self: Object of the PlotWindow class.
        graphicsView: Object of pyqtgraph's TableWidget class.

    Returns:
        No return variable. The function operates on an object of the 
        PlotWindow class.
    """
    ## ds-type "box" is not (yet?) implemented here. This may be done in the 
    ## future.
    data = np.array(self.ds)
    if self.ds_type == ds_types['matrix']:
        data = data.transpose()
    if self.ds_type == ds_types['vector'] or self.ds_type == ds_types['coordinate']:
        data_tmp = np.empty((1, data.shape[0]), dtype=np.float64)
        data_tmp[0] = data
        data = data_tmp.transpose()
    if self.ds_type == ds_types["txt"]:
        data_tmp = []
        for d in data:
            data_tmp.append([d])
        data = np.array(data_tmp)
        graphicsView.setFormat(str(data))
    graphicsView.setData(data)


def _display_text(self, graphicsView):
    """displays the data (=String) in the dataset.

    This function mainly handles our JSON encoded entries in the settings 
    datasets. The JSON dict is read out and displayed with indentations to be
    nicely readable. If the input string is not JSON encodable it is displayed
    by the _display_string() fcn as it is.
    
    Args:
        self: Object of the PlotWindow class.
        graphicsView: Object of PyQt's QPlainTextEdit class.

    Returns:
        No return variable. The function operates on an object of the 
        PlotWindow class.
    """
    try:
        json_dict = json.loads(self.ds.value[0])
    except ValueError:
        txt = _display_string(self.ds)
    else:
        txt = pprint.pformat(json_dict, indent=4)
    graphicsView.insertPlainText(txt.rstrip())


def _display_string(ds):
    """Reads the sting in dataset ds and returns a formatted string.

    Args:
        ds: hdf_dataset.

    Returns:
        Formatted string.
    """
    data = np.array(ds)
    txt = ""
    for d in data:
        txt += d + '\n'
    return txt


""" A few handy methods for label and scale """


def _get_ds_url(ds, url):
    """Gets the absolute ds_url.

    If 'url' is already a absolute url in the h5 file it gets returned 
    unchanged.
    Otherwise the absolute url in read out of the ds-metadata.
    
    Args:
        ds: hdf_dataset.
        url: string of absolute or relative ds_url

    Returns:
        String of the absolute ds_url.
    """
    
    if _get_ds(ds, url):
        return url
    else:
        return ds.attrs.get(url, '_none_')


def _get_ds(ds, ds_url):
    """Returns the dataset associated with the given ds_url in the same file as
    the given dataset ds.
    
    Args:
        ds: hdf_dataset.
        ds_url: absolute ds_url

    Returns:
        Object of hdf_dataset class.
    """
    try:
        return ds.file[ds_url]
    except:
        return None


def _get_axis_scale(ds):
    """Returns the scale of a coordinate, x0 and dx at an assumed linear 
    scaling.
    
    Args:
        ds: hdf_dataset.

    Returns:
        Tuple with of axis origin and delta distance.
    """
    try:
        x0 = ds[0]
        dx = ds[1] - ds[0]
        return (x0, dx)
    except:
        return (0, 1)


def _get_unit(ds):
    """Returns the unit of a dataset.
    
    Args:
        ds: hdf_dataset.

    Returns:
        String with unit.
    """
    try:
        return ds.attrs.get('unit', '_none_').decode("utf-8")
    except AttributeError as e:
        #print(ds)
        print("Qviewkit _get_unit:",e)
        return '_none_'

def _get_name(ds):
    """Returns the name of a dataset.

    Args:
        ds: hdf_dataset.

    Returns:
        String with name.
    """
    try:
        return ds.attrs.get('name','_none_').decode("utf-8")
    except AttributeError as e:
        #print(ds)
        print("Qviewkit _get_name:",e)
        return '_none_'


def _get_all_ds_names_units_scales(ds, ds_urls=[]):
    """Reads and returns all the relevant information of the given datasets.

    This function gathers all the needed metadata to correctly display the
    dataset given in ds. The metadata of the datasets associated with the given
    urls are read out (data, name, unit, and scale). This information is used
    by the _display_...() fcts to correcly label and scale the plots. The order
    in the input- and output-list is maintained.
    
    Args:
        ds: hdf_dataset.
        ds_url: List of urls to be read. 

    Returns:
        Multiple lists containing the data/metadata 'dataset', 'name', 'unit',
        and 'scale' of the input urls.
    """
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


""" Unify the data manipulation to share code """


def _do_data_manipulation(data, unit, ds_type, manipulation, manipulations, colorplot=False):
    """Data manipulation for display gets done here.
    
    This function gathers all the needed metadata to correctly display the
    dataset given in ds. The metadata of the datasets associated with the given 
    urls are read out (data, name, unit, and scale). This information is used
    by the _display_...() fcts to correcly label and scale the plots. The order
    in the input- and output-list is maintained.
    
    Args:
        data: Numpy array of the to be displayed / to be manipulated data.
        ds_type: Dataset type for information about the dimension.
        manipulation: Integer, power of 2 number indicating the manipulation to
            be performed.
        manipulations: Lookup dict, mapping a manipulation to a power of 2.

    Returns:
        Tuple of a numpy array containing the manipulated data with the same
        dimension as the input array and a string of the data unit after the 
        manipulation.
    """
    # set the y data  to the decibel scale 
    if manipulation & manipulations['dB']:
        data = 20 * np.log10(data)
        unit = 'dB'
    
    # unwrap the phase
    if manipulation & manipulations['wrap']:
        data = np.unwrap(data)
    
    if manipulation & manipulations['linear']:
        if len(data.shape) == 1:
            data = data - np.nan_to_num(np.linspace(data[0], data[-1], len(data)))
        elif len(data.shape) == 2:
            data = data - np.outer(data[:, -1] - data[:, 0], np.linspace(0, 1, data.shape[1]))
        else:
            print("linear correction not implemented for %iD" % len(data.shape))
        
        if colorplot:
            ## This manipulation removes all zeros which would blow up the color scale.
            ## Only relevant for matrices and boxes in 2d
            if manipulation & manipulations['remove_zeros']:
                data[np.where(data == 0)] = np.NaN  # replace all exact zeros in the hd5 data with NaNs, otherwise the 0s in uncompleted files blow up the colorscale
    
    if manipulation & manipulations['sub_offset_avg_y']:
        # ignore division by zero
        old_warn = np.seterr(divide='print')
        np.seterr(**old_warn)
        data = data - np.nanmean(data, axis=1, keepdims=True)
    
    # subtract offset from the data
    if manipulation & manipulations['norm_data_avg_x']:
        # ignore division by zero
        old_warn = np.seterr(divide='print')
        np.seterr(**old_warn)
        data = data / np.nanmean(data, axis=0, keepdims=True)
    
    return data, unit
