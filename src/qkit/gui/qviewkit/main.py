#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: hannes.rotzinger@kit.edu / 2015,2016,2017
         marco.pfirrmann@kit.edu / 2016, 2017
@license: GPL
"""

import platform
if platform.system() == "Windows":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(False) # Fix Bug on Windows when using multiple screens with different scaling
    except:
        pass
import sys
# support both PyQt4 and 5
in_pyqt5 = False
in_pyqt4 = False
try:
    from PyQt5.QtCore import Qt, QObject
    from PyQt5.QtWidgets import QApplication
    in_pyqt5 = True
except ImportError as e:
    print("import of PyQt5 failed, trying PyQt4 (error: {})".format(e))

if not in_pyqt5:
    try:
        from PyQt4.QtCore import Qt, QObject
        from PyQt4.QtGui import QApplication
        in_pyqt4 = True
    except ImportError:
        print("import of PyQt5 and PyQt4 failed. Install one of those.")
        sys.exit(-1)


import argparse
import qkit
from qkit.gui.qviewkit.PlotWindow import PlotWindow
from threading import Lock

class DATA(QObject):
    """Class for housekeeping the different windows in qviewkit.

    This class handles the relationship; opening and closing of different
    PlotWindow objects.
    """

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

        #print(window, window_id)
        self.open_plots[str(window_id)]=window
        self.open_ds[ds] = window_id

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
                window_id.setCheckState(0,Qt.Unchecked)

                # make sure data is consitent
                if str(window_id) in self.open_plots:
                    self.open_plots[str(window_id)].deleteLater()
                    self.open_plots.pop(str(window_id))


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
def main(argv=sys.argv):
    """Main function to open a h5 file with qviewkit.

    This function is called via command line. It opens the optional parsed
    h5 file and the optional parsed datasets automatically.
    The DatasetsWindow object creates a Qt based window with some UI buttons
    for file handling and a populated tree of the datasets.

    Args:
        '-f','--file',     type=str, help='hdf filename to open'
        '-ds','--datasets', type=str, help='(optional) datasets opened by default'

        '-rt','--refresh_time', type=float, help='(optional) refresh time'
        '-sp','--save_plot',  default=False,action='store_true', help='(optional) save default plots'
        '-live','--live_plot',default=False,action='store_true', help='(optional) if set, plots are reloaded'
        '-qinfo','--qkit_info',default=False,action='store_true', help='(optional) if set, listen to qkit infos'
    """
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
    args=parser.parse_args(args=argv[1:])
    data.args = args

    # create Qt application
    if in_pyqt5:
        app = QApplication(argv)
    if in_pyqt4:
        app = QApplication(argv,True)

    # if activated, start info thread
    if data.args.qkit_info:
        from qkit.gui.qviewkit.info_subsys import info_thread
        it = info_thread(data)
        it.start()


    # create main window
    from qkit.gui.qviewkit.DatasetsWindow import DatasetsWindow
    #
    dsw = DatasetsWindow(data)
    dsw.show()
    dsw.raise_()

    # Connect signal for app quit
    app.lastWindowClosed.connect(quit)
    app.exec_()

if __name__ == "__main__":
    main()