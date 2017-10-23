#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: hannes.rotzinger@kit.edu / 2015,2016,2017 
         marco.pfirrmann@kit.edu / 2016, 2017
@license: GPL
"""
import sys
# support both PyQt4 and 5
in_pyqt5 = False
in_pyqt4 = False
try:
    from PyQt5 import QtCore
    from PyQt5.QtCore import QObject
    from PyQt5.QtWidgets import QApplication
    in_pyqt5 = True
except ImportError as e:
    print("import of PyQt5 failed, trying PyQt4")

if not in_pyqt5:
    try:
        from PyQt4 import QtCore
        from PyQt4.QtCore import QObject,SIGNAL,SLOT
        from PyQt4.QtGui import QApplication
        in_pyqt4 = True
    except ImportError:
        print("import of PyQt5 and PyQt4 failed. Install one of those.")
        sys.exit(-1)


import argparse
from PlotWindow import PlotWindow
from threading import Lock

class DATA(QObject):
    open_plots = {}
    open_ds    = {}
    dataset_info = {}
    ds_tree_items= {}
    ds_cmd_open = {}
    toBe_deleted = []
    lock = Lock()
    info_thread_continue = True
    "a set of housekeeping functions..."
        
    def append_plot(self,parent,window_id,ds):
        # self, item, dataset
        
        window = PlotWindow(parent,self,ds)
        
        self.open_plots[window_id]=window
        self.open_ds[ds]=window_id
        
        window.show()   # non-modal
        
        return window
    def _toBe_deleted(self,ds):
        if ds in self.open_ds:
            self.toBe_deleted.append(ds)
            
    def _remove_plot_widgets(self, closeAll = False):
        # helper func to close widgets
        def close_ds(ds):
            if ds in self.open_ds:
                window_id = self.open_ds[ds]
                window_id.setCheckState(0,QtCore.Qt.Unchecked)
                
                # make sure data is consitent                
                if window_id in self.open_plots:
                    self.open_plots[window_id].deleteLater()
                    self.open_plots.pop(window_id)
                    
                    
                if ds in self.open_ds:
                    self.open_ds.pop(ds)

        if closeAll:
            for ds in list(self.open_ds.keys()):
                close_ds(ds)
        else:
            for ds in self.toBe_deleted:
                close_ds(ds)
       
        self.toBe_deleted = []
            
    def remove_plot(self,window_id,ds):

        if window_id in self.open_plots:
            win = self.open_plots.pop(window_id)
            win.deleteLater()
            
        if ds in self.open_ds:
            self.open_ds.pop(ds)

        
    def plot_is_open(self,ds):
        return ds in self.open_ds
        
    def has_dataset(self,ds):
        return ds in self.dataset_info
        
    def set_info_thread_continue(self,On):
        with self.lock:
            self.info_thread_continue = On
    def close_all(self):
        QApplication.quit()

        
# Main entry to program.  
def main(argv):
    
    # some configuration boilerplate
    data = DATA()
    
    parser = argparse.ArgumentParser(
        description="Qviewkit / qkit tool to visualize qkit-hdf files // HR@KIT 2015")
    

    parser.add_argument('-f','--file',     type=str, help='hdf filename to open')
    parser.add_argument('-ds','--datasets', type=str, help='(optional) datasets opened by default')
    
    parser.add_argument('-rt','--refresh_time', type=float, help='(optional) refresh time')
    parser.add_argument('-sp','--save_plot',  default=False,action='store_true', help='(optional) save default plots')
    parser.add_argument('-live','--live_plot',default=False,action='store_true', help='(optional) if set, plots are reloaded')
    parser.add_argument('-qinfo','--qkit_info',default=False,action='store_true', help='(optional) if set, listen to qkit infos')    
    args=parser.parse_args()
    data.args = args
    
    # create Qt application
    if in_pyqt5:
        app = QApplication(argv)
    if in_pyqt4:
        app = QApplication(argv,True)
    
    # if activated, start info thread
    if data.args.qkit_info:
        from info_subsys import info_thread
        it = info_thread(data)
        it.start()
        
            
    # create main window
    from DatasetsWindow import DatasetsWindow
    #
    dsw = DatasetsWindow(data)
    dsw.show()
    dsw.raise_()
    
    # Connect signal for app quit
    app.lastWindowClosed.connect(quit)
    app.exec_()
 
if __name__ == "__main__":
    main(sys.argv)
