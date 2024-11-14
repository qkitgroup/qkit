# -*- coding: utf-8 -*-
"""
@author: hannes.rotzinger@kit.edu / 2015,2016,2017 
         marco.pfirrmann@kit.edu / 2016, 2017
@license: GPL
"""

import sys,os
import qkit
# support both PyQt4 and 5
in_pyqt5 = False
in_pyqt4 = False
try:
    from PyQt5 import QtCore
    import PyQt5.QtWidgets as QtGui
    from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject,QTimer
    from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog
    in_pyqt5 = True
except ImportError as e:
    pass
if not in_pyqt5:    
    try:
        from PyQt4 import QtCore, QtGui
        from PyQt4.QtCore import *
        from PyQt4.QtGui import *
        in_pyqt4 = True
    except ImportError:
        print("import of PyQt5 and PyQt4 failed. Install one of those.")
        sys.exit(-1)

import h5py
from qkit.gui.qviewkit.main_view import Ui_MainWindow
from qkit.core.lib.misc import  str3

class DatasetsWindow(QMainWindow, Ui_MainWindow):
    """DatasetsWindow fills the frame of the Ui_MainWindow.

    This class reads the file content and displays i.e. the dataset tree and
    the dataset attributes and handles the signal slots from the UI buttons
    i.e. the checking/unchecking of the live option.
    """
    refresh_signal = pyqtSignal()
    pw_refresh_signal = pyqtSignal()
    def __init__(self,DATA):
        """Inits DatasetsWindows with a DATA object coming from the main call
        in main.py.

        The Ui_MainWindow gets set up, the signal slots to the UI buttons get
        connected and set_cmd_options() evaluates the parsed arguments of the 
        main call.
        Once a file is opened the handle functions emmit signals as soon as 
        some user interaction happens (i.e. a dataset is clicked to be opened)
        and update_plots() emmits the update signal.
        """
        self.DATA = DATA
        #QMainWindow.__init__(self,None,Qt.WindowStaysOnTopHint)
        QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        
        # set up User Interface (widgets, layout...)
        self.setupUi(self)
        self.setWindowTitle("Qviewkit")
        self.treeWidget.setHeaderHidden(True)
        
        self.refreshTime_value = 2000
        self.tree_refresh  = True
        self._force_live_plot = False
        self._setup_signal_slots()        
        self.setup_timer()
        self.set_cmd_options()
        
        
    def setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_file)
        self.timer.timeout.connect(self.live_update_onoff)
            
    def set_cmd_options(self):
        # prepare datasets to display
        if self.DATA.args.datasets:
            dss = self.DATA.args.datasets.split(',')
            
            for ds in dss:
                fd = ds.split('/')
                if len(fd) == 1:
                    dsp = "/entry/data0/"+fd[0]
                    self.DATA.ds_cmd_open[dsp] = True
                if len(fd) == 2:
                    dsp = "/entry/"+fd[0]+"/"+fd[1]
                    self.DATA.ds_cmd_open[dsp] = True
            print("Display:", self.DATA.ds_cmd_open)
        if self.DATA.args.file:
            self.DATA.DataFilePath = self.DATA.args.file
            self.update_file()
        if self.DATA.args.refresh_time:
            self.refreshTime.setValue(self.DATA.args.refresh_time)
            self._refresh_time_handler(self.DATA.args.refresh_time)
        if self.DATA.args.live_plot:
            self.liveCheckBox.click()
            #self.live_update_onoff()
            
    def _setup_signal_slots(self):
        self.treeWidget.itemChanged.connect(self.handleChanged)
        self.treeWidget.itemSelectionChanged.connect((self.handleSelectionChanged))
                
        self.refreshTime.valueChanged.connect(self._refresh_time_handler)
        self.updateButton.released.connect(self.update_file)
        
        self.FileButton.clicked.connect(self.open_file)
        self.liveCheckBox.clicked.connect(self.live_update_onoff)
        self.pw_refresh_signal.connect(self.update_file)

    def closeEvent(self, event):
        widgetList = QApplication.topLevelWidgets()

        self.DATA._remove_plot_widgets( closeAll = True)
        self.DATA.set_info_thread_continue(False)
        event.accept()
    
    @pyqtSlot()
    def _close_plot_window(self):
        self.DATA._remove_plot_widgets()
                
    def live_update_onoff(self):
        if self.liveCheckBox.isChecked():
            self.timer.start(int(self.refreshTime_value))
            self.heardBeat.click()
        else:
            self.timer.stop()
    
    def _disable_live_update(self):
        try:
            if not self._force_live_plot and not self.h5file['entry'].attrs.get('updating',True):
                self.liveCheckBox.setChecked(False)
                self._force_live_plot = True # don't disable the live plot if it is manually enabled again
        except ValueError as e:
            qkit.logging.error("Qviewkit/DatasetsWindow.py: Error on checking for live plot: "+str(e))

    def _refresh_time_handler(self,refreshTime):
        self.refreshTime_value = refreshTime*1000 # ms -> s
        
    def populate_data_list(self):
        """
        populate_data_list is called regularly withing the refresh cycle to
        update the data tree.
        """
        self.parent = self.treeWidget.invisibleRootItem()
        column = 0
        parents = []
        s=""
        """itterate over the whole entry tree and collect the attributes """
        for i,pentry in enumerate(self.h5file["/entry"].keys()):
            tree_key = "/entry/"+pentry
            if tree_key not in self.DATA.ds_tree_items:
                parent = self.addParent(self.parent, column, str(pentry))
                self.DATA.ds_tree_items[tree_key] = parent
                parents.append(parent)
            else:
                parent = self.DATA.ds_tree_items[tree_key]
                
            s= "comment:\t"+str3(self.h5file[tree_key].attrs.get('comment',""))+"\n"
            self.DATA.dataset_info[tree_key] = s
            
            for j,centry in enumerate(self.h5file[tree_key].keys()):
                tree_key = "/entry/"+pentry+"/"+centry
                if tree_key not in self.DATA.ds_tree_items:
                    item = self.addChild(parent, column, str(centry),tree_key)
                    self.DATA.ds_tree_items[tree_key] = item
                    
                    if tree_key in self.DATA.ds_cmd_open:
                        # the order of the following two lines are important! otherwise two plots are opened
                        self.DATA.append_plot(self,item,tree_key)
                        item.setCheckState(0,QtCore.Qt.Checked)
                        self.update_plots()
                       
                s = ""
                try:
                    s="shape\t"+str(self.h5file[tree_key].shape)+"\n"
                    for k in list(self.h5file[tree_key].attrs.keys()):
                        s += k + "\t" + str3(self.h5file[tree_key].attrs[k]) + "\n"
                except TypeError:
                    s="shape\t"+str(self.h5file[tree_key].shape)+"\n"
                    for k in list(self.h5file[tree_key].attrs.keys()): 
                        s += k + "\t" + str(self.h5file[tree_key].attrs[k]) + "\n"
                except ValueError as e:
                    print("catch: populate data list:",e)
                
                self.DATA.dataset_info[tree_key] = s
               
    def addParent(self, parent, column, title,data = ''):
        item = QtGui.QTreeWidgetItem(parent, [title])
        #item.setData(column, QtCore.Qt.UserRole, data)
        item.setChildIndicatorPolicy(QtGui.QTreeWidgetItem.ShowIndicator)
        item.setExpanded (True)
        return item

    def addChild(self, parent, column, title, ds, data=''):
        item = QtGui.QTreeWidgetItem(parent, [title])
        item.setData(column, QtCore.Qt.UserRole, data)
        item.setCheckState (column, QtCore.Qt.Unchecked)
        return item

    def handleChanged(self, item, column):
        ds = str("/entry/"+item.parent().text(column)+"/"+item.text(column))
        if item.checkState(column) == QtCore.Qt.Checked:
            
            if not self.DATA.plot_is_open(ds):
                "this condition occures when the ds is opened from the cmd-l"
                self.DATA.append_plot(self,item,ds)

            # this is a not very sound hack of a concurrency problem!
            # better to use a locking technique            
            if not self.h5file:
                self.update_file()
            else:
                self.update_plots()
                
            # uncheck 
            window = self.DATA.open_plots[str(item)]
            window.destroyed.connect(self._close_plot_window)
                
        if item.checkState(column) == QtCore.Qt.Unchecked:
            
            if self.DATA.plot_is_open(ds):
                self.DATA.remove_plot(str(item),ds)
        
    def handleSelectionChanged(self):
        getSelected = self.treeWidget.selectedItems()
        if getSelected[0].parent():
            ds =str("/entry/"+getSelected[0].parent().text(0)+"/"+getSelected[0].text(0)) 
            self.Dataset_properties.clear()
            self.Dataset_properties.insertPlainText(self.DATA.dataset_info[ds])
        else:
            ds =str("/entry/"+getSelected[0].text(0)) 
            self.Dataset_properties.clear()
            self.Dataset_properties.insertPlainText(self.DATA.dataset_info[ds])
 
            
    def update_file(self):
        "update_file is regularly called when _something_ has to be updated. open-> do something->close"
        try:
            self.h5file= h5py.File(str(self.DATA.DataFilePath),mode='r')
            self.DATA.filename = self.h5file.filename.split(os.path.sep)[-1]
            self.populate_data_list()
            self.update_plots()
            self._disable_live_update()
            self.h5file.close()
            
            s = (self.DATA.DataFilePath.split(os.path.sep)[-5:])
            self.statusBar().showMessage((os.path.sep).join(s for s in s))
            
            title = "Qviewkit: %s"%(self.DATA.DataFilePath.split(os.path.sep)[-1:][0][:6])
            self.setWindowTitle(title)
        except IOError as e:
            print(e)

    def open_file(self):
        if in_pyqt5:
            _DataFilePath=str(QFileDialog.getOpenFileName(filter="*.h5")[0])
        if in_pyqt4:
            _DataFilePath=str(QFileDialog.getOpenFileName(filter="*.h5"))
            
        if _DataFilePath:
            self.DATA.DataFilePath = _DataFilePath
            self.h5file= h5py.File(self.DATA.DataFilePath,mode='r')
            self.DATA.filename = self.h5file.filename.split(os.path.sep)[-1]
            self.populate_data_list()
            self.h5file.close()
            
            s = (self.DATA.DataFilePath.split(os.path.sep)[-5:])
            self.statusBar().showMessage((os.path.sep).join(s for s in s))
            title = "Qviewkit: %s"%(self.DATA.DataFilePath.split(os.path.sep)[-1:][0][:6])
            self.setWindowTitle(title)
            
    def update_plots(self):
        self.refresh_signal.emit()