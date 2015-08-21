# -*- coding: utf-8 -*-
"""
@author: hannes.rotzinger@kit.edu @ 2015
"""

import sys,os
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import h5py
from time import sleep

from main_view import Ui_MainWindow

#from PlotWindow import PlotWindow
class DatasetsWindow(QMainWindow, Ui_MainWindow):
#class DatasetsWindow(QtGui.QWidget):
    refresh_signal = pyqtSignal()
    pw_refresh_signal = pyqtSignal()
    def __init__(self,DATA):
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
            print "Display:", self.DATA.ds_cmd_open
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
        QObject.connect(self.refreshTime,SIGNAL("valueChanged(double)"),self._refresh_time_handler)
        QObject.connect(self.updateButton,SIGNAL("released()"),self.update_file)
        #QObject.connect(self.Quit,SIGNAL("released()"),self._quit_tip_gui)
        #QObject.connect(self,SIGNAL("destroyed()"),self._close_plot_window)
        self.FileButton.clicked.connect(self.open_file)
        self.liveCheckBox.clicked.connect(self.live_update_onoff)
        self.pw_refresh_signal.connect(self.update_file)
        
        
    def closeEvent(self, event):
        widgetList = QApplication.topLevelWidgets()
        #print len(widgetList)
        #print widgetList
        #numWindows = len(widgetList)
        #if numWindows > 1:
        #    event.ignore()
        #else:
        self.DATA._remove_plot_widgets( closeAll = True)
        event.accept()
    
    @pyqtSlot()
    def _close_plot_window(self):
        #print "Plot window closed"
        self.DATA._remove_plot_widgets()
        
        
    def live_update_onoff(self):
        if self.liveCheckBox.isChecked():
            #print "start timer"
            self.timer.start(self.refreshTime_value)
            if self.heardBeat.isChecked() == False:
                self.heardBeat.setChecked(True)
            else:
                self.heardBeat.setChecked(False)
        else:
            self.timer.stop()
            
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
            if not self.DATA.ds_tree_items.has_key(tree_key):
                parent = self.addParent(self.parent, column, str(pentry))
                self.DATA.ds_tree_items[tree_key] = parent
                parents.append(parent)
            else:
                parent = self.DATA.ds_tree_items[tree_key]
                
            s= "comment:\t" +str(self.h5file[tree_key].attrs.get('comment',"")+"\n")
            self.DATA.dataset_info[tree_key] = s
            
            for j,centry in enumerate(self.h5file[tree_key].keys()):
                tree_key = "/entry/"+pentry+"/"+centry
                if not self.DATA.ds_tree_items.has_key(tree_key):
                    item = self.addChild(parent, column, str(centry),tree_key)
                    self.DATA.ds_tree_items[tree_key] = item
                    

                    if self.DATA.ds_cmd_open.has_key(tree_key):
                        item.setCheckState(0,QtCore.Qt.Checked)
                        self.DATA.append_plot(self,item,tree_key)
                        self.update_plots()
                        
                s = ""
                try:
                    s="shape\t"+str(self.h5file[tree_key].shape)+"\n"
                    for k in self.h5file[tree_key].attrs.keys(): 
                        s+=k +"\t" +str(self.h5file[tree_key].attrs[k])+"\n"
                except ValueError,e:
                #except IOError:
                    # dataset is available, but the attrs are not yet readable
                    #print "Dataset:ValueError ", tree_key
                    print e
                #print tree_key
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
            #print "checked", item, item.text(column)
            #if not self.tree_refresh:
            self.DATA.append_plot(self,item,ds)

            # this is a not very sound hack of a concurrency problem!
            # better to use a locking technique            
            if not self.h5file:
                self.update_file()
            else:
                self.update_plots()
                
            # uncheck 
            window = self.DATA.open_plots[item]
            QObject.connect(window,SIGNAL("destroyed()"),self._close_plot_window)
                
        if item.checkState(column) == QtCore.Qt.Unchecked:
            #print "unchecked", item, item.text(column)
            self.DATA.remove_plot(item,ds)
        
    def handleSelectionChanged(self):
        getSelected = self.treeWidget.selectedItems()
        if getSelected[0].parent():
            ds =str("/entry/"+getSelected[0].parent().text(0)+"/"+getSelected[0].text(0)) 
            #print ds
            #print self.DATA.dataset_info[ds]
            self.Dataset_properties.clear()
            self.Dataset_properties.insertPlainText(self.DATA.dataset_info[ds])
        else:
            ds =str("/entry/"+getSelected[0].text(0)) 
            #print ds
            #print self.DATA.dataset_info[ds]
            self.Dataset_properties.clear()
            self.Dataset_properties.insertPlainText(self.DATA.dataset_info[ds])
 
            
    def update_file(self):
        try:
            
            self.h5file= h5py.File(str(self.DATA.DataFilePath),mode='r')
            self.DATA.filename = self.h5file.filename.split(os.path.sep)[-1]
            self.populate_data_list()
            self.update_plots()
            self.h5file.close()
            s = (self.DATA.DataFilePath.split(os.path.sep)[-5:])
            self.statusBar().showMessage((os.path.sep).join(s for s in s))
        #except IOError:
        except ValueError,e:
            print "Error in Dataset: File not yet available.", self.DATA.DataFilePath
            print e
    def open_file(self):
        self.DATA.DataFilePath=str(QFileDialog.getOpenFileName(filter="*.h5"))
        if self.DATA.DataFilePath:
            self.h5file= h5py.File(self.DATA.DataFilePath,mode='r')
            self.DATA.filename = self.h5file.filename.split(os.path.sep)[-1]
            self.populate_data_list()
            self.h5file.close()
            s = (self.DATA.DataFilePath.split(os.path.sep)[-5:])
            self.statusBar().showMessage((os.path.sep).join(s for s in s))
            
    def update_plots(self):
        self.refresh_signal.emit()

        
            
if __name__ == "__main__":

    app = QtGui.QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())