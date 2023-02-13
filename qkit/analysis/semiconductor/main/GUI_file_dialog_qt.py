from PyQt5.QtWidgets import QFileDialog
from PyQt5 import QtCore, QtWidgets

import sys

app = QtCore.QCoreApplication.instance()
if app is None:
    app = QtWidgets.QApplication(sys.argv)

name = []
def gui_fname(dir=None):
    """Select a file via a dialog and return the file name."""
    if dir is None: dir ='./'
    fname = QFileDialog.getOpenFileNames(None, "Select data file...", dir, filter="All files (*);; SM Files (*.sm)")
    name.extend(fname[0])
    return name

gui_fname()
