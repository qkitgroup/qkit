# -*- coding: utf-8 -*-
"""
Created on Thu Jun 25 20:41:51 2015

@author: hrotzing
"""

import sys
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
    def __init__(self,DATA):
        self.DATA = DATA
        QMainWindow.__init__(self)
        # set up User Interface (widgets, layout...)
        self.setupUi(self)
        
        self.treeWidget.setHeaderHidden(True)
        self.refreshTime_value = 5000
        self.tree_refresh  = True
        self._setup_signal_slots()
        self.setup_timer()
        self.set_cmd_options()
        
        
    def setup_timer(self):
         self.timer = QTimer()
         self.timer.timeout.connect(self.update_file)
         self.timer.timeout.connect(self.live_update_onoff)


            
    def set_cmd_options(self):
        if self.DATA.args.file:
            self.DATA.DataFilePath = self.DATA.args.file
            self.update_file()
        if self.DATA.args.refresh_time:
            self.refreshTime.setValue(self.DATA.args.refresh_time)
            self._refresh_time_handler(self.DATA.args.refresh_time)
        if self.DATA.args.live_plot:
            self.liveCheckBox.click()
            
        # prepare datasets to display
        if self.DATA.args.datasets:
            dss = self.DATA.args.datasets.split(',')
            fds = []
            for ds in dss:
                fd = ds.split('/')
                if len(fd) == 1:
                    dsp = "/entry/data0/"+fd[0]
                    if self.DATA.has_dataset(dsp):
                        fds.append(dsp)
                    else:
                        print  "cmd-line: Dataset " + dsp + " not found!"
                if len(fd) == 2:
                    dsp = "/entry/"+fd[0]+"/"+fd[1]
                    if self.DATA.has_dataset(dsp):
                        fds.append(dsp)
                    else:
                        print  "cmd-line: Dataset " + dsp + " not found!"
            print "Display:", fds

            
    
    def _setup_signal_slots(self):
        self.treeWidget.itemChanged.connect(self.handleChanged)
        self.treeWidget.itemSelectionChanged.connect((self.handleSelectionChanged))
        QObject.connect(self.refreshTime,SIGNAL("valueChanged(double)"),self._refresh_time_handler)
        QObject.connect(self.updateButton,SIGNAL("released()"),self.update_file)
        #QObject.connect(self.Quit,SIGNAL("released()"),self._quit_tip_gui)
        self.FileButton.clicked.connect(self.open_file)
        self.liveCheckBox.clicked.connect(self.live_update_onoff)
        
    def live_update_onoff(self):
        if self.liveCheckBox.isChecked():
            #print "start timer"
            self.timer.start(self.refreshTime_value)
            if self.heardBeat.isChecked() == False:
                self.heardBeat.setChecked(True)
            else:
                self.heardBeat.setChecked(False)
        else:
            #print "stop timer"
            self.timer.stop()
            
    def _refresh_time_handler(self,refreshTime):
        self.refreshTime_value = refreshTime*1000 # ms -> s
        

    def populate_data_list(self):
        
        #        self.treeWidget.clear()
        self.parent = self.treeWidget.invisibleRootItem()
        parent = self.parent
        column = 0
        parents = []
        #self.DATA.dataset_info = {}
        #first parents
        s=""
        """itterate over the whole entry tree and collect the attributes """
        for i,pentry in enumerate(self.h5file["/entry"].keys()):
            parents.append(self.addParent(parent, column, str(pentry)))
            s= "comment:\t" +str(self.h5file["/entry/"+pentry].attrs.get('comment',"")+"\n")
            self.DATA.dataset_info["/entry/"+pentry] = s
            
            for j,centry in enumerate(self.h5file["/entry/"+pentry].keys()):
                self.addChild(parents[i], column, str(centry),"/entry/"+pentry+"/"+centry)
                s = ""
                for k in self.h5file["/entry/"+pentry+"/"+centry].attrs.keys(): 
                    s+=k +"\t" +str(self.h5file["/entry/"+pentry+"/"+centry].attrs[k])+"\n"
                self.DATA.dataset_info["/entry/"+pentry+"/"+centry] = s
                #print "/entry/"+pentry+"/"+centry
                #print s
        #root = self.treeWidget.invisibleRootItem()
            """
            child_count = parent.childCount()
            for i in range(child_count):
                group = parent.child(i)
                key = "/entry/"+group.text(0)
                for j in range(item.childCount()):
                    print item.child(j).text(0) # text at first (0) column
                    #item.setText(1, 'result from %s' % url) # update result column (1)
                    #item.child(j).setCheckState(0,QtCore.Qt.Checked)
                #self.treeWidget.
                    """
    def addParent(self, parent, column, title,data = ''):
        item = QtGui.QTreeWidgetItem(parent, [title])
        #item.setData(column, QtCore.Qt.UserRole, data)
        item.setChildIndicatorPolicy(QtGui.QTreeWidgetItem.ShowIndicator)
        item.setExpanded (True)
        return item

    def addChild(self, parent, column, title, ds, data=''):
        item = QtGui.QTreeWidgetItem(parent, [title])
        item.setData(column, QtCore.Qt.UserRole, data)
        self.tree_refresh = True
        if self.DATA.plot_is_open(ds):
            item.setCheckState (column, QtCore.Qt.Checked)
        else:
            item.setCheckState (column, QtCore.Qt.Unchecked)
        self.tree_refresh = False
        return item

    def handleChanged(self, item, column):
        ds = str("/entry/"+item.parent().text(column)+"/"+item.text(column))
        if item.checkState(column) == QtCore.Qt.Checked:
            #print "checked", item, item.text(column)
            if not self.tree_refresh:
                self.DATA.append_plot(self,item,ds)
            #self.refresh_signal.emit()
            #self.DATA.open_plots[item].show()
            self.update_file()
            
        if item.checkState(column) == QtCore.Qt.Unchecked:
            #print "unchecked", item, item.text(column)
            #if self.DATA.open_plots
            if not self.tree_refresh:
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
            self.h5file= h5py.File(str(self.DATA.DataFilePath))
            if self.tree_refresh:
                self.populate_data_list()
            self.update_plots()
            self.h5file.close()
            self.statusBar().showMessage(self.DATA.DataFilePath)
        except IOError:
            print "IOError"

    def open_file(self):
        self.DATA.DataFilePath=QFileDialog.getOpenFileName(filter="*.h5")
        if self.DATA.DataFilePath:
            self.h5file= h5py.File(str(self.DATA.DataFilePath))
            self.populate_data_list()
            self.h5file.close()
            print self.DATA.DataFilePath
            self.statusBar().showMessage(self.DATA.DataFilePath)
            
    def update_plots(self):
        self.refresh_signal.emit()

        
            
if __name__ == "__main__":

    app = QtGui.QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())