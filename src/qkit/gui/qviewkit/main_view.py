# -*- coding: utf-8 -*-

"""
@author: hannes.rotzinger@kit.edu / 2015, 2016, 2017
         marco.pfirrmann@kit.edu / 2016, 2017
@license: GPL
"""


import sys
import qkit

# support both PyQt4 and 5
in_pyqt5 = False
in_pyqt4 = False
try:
    from PyQt5 import QtCore
    import PyQt5.QtWidgets as QtGui
    in_pyqt5 = True
except ImportError as e:
    pass

if not in_pyqt5:
    try:
        from PyQt4 import QtCore, QtGui
        in_pyqt4 = True
    except ImportError:
        print("import of PyQt5 and PyQt4 failed. Install one of those.")
        sys.exit(-1)


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_MainWindow(object):
    """Ui_MainWindow class creates the frame of the  h5 file.

    The main window features some general interface buttons for file selection
    and live update as well as a interactive display to show and interact
    with the datasets in the populated dataset tree.
    """
    def setupUi(self, MainWindow):
        """setupUi creates the main window based on QMainWindow.

        Args:
            self: Object of the PlotWindow class.
            MainWindow: QMainWindow object.
        Returns:
            No return variable. The function operates on the given object.
        """
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(271, 554)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.gridLayout_2 = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 1, 1, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem1, 0, 1, 1, 1)
        self.FileButton = QtGui.QPushButton(self.centralwidget)
        self.FileButton.setObjectName(_fromUtf8("FileButton"))
        self.gridLayout.addWidget(self.FileButton, 0, 0, 1, 1)
        self.liveCheckBox = QtGui.QCheckBox(self.centralwidget)
        self.liveCheckBox.setObjectName(_fromUtf8("liveCheckBox"))
        self.gridLayout.addWidget(self.liveCheckBox, 1, 2, 1, 1)
        self.updateButton = QtGui.QPushButton(self.centralwidget)
        self.updateButton.setObjectName(_fromUtf8("updateButton"))
        self.gridLayout.addWidget(self.updateButton, 1, 0, 1, 1)
        self.refreshTime = QtGui.QDoubleSpinBox(self.centralwidget)
        self.refreshTime.setMinimum(1.0)
        self.refreshTime.setMaximum(999.99)
        self.refreshTime.setProperty("value", 2.0)
        self.refreshTime.setObjectName(_fromUtf8("refreshTime"))
        self.gridLayout.addWidget(self.refreshTime, 1, 3, 1, 1)
        self.heardBeat = QtGui.QRadioButton(self.centralwidget)
        self.heardBeat.setText(_fromUtf8(""))
        self.heardBeat.setObjectName(_fromUtf8("heardBeat"))
        self.gridLayout.addWidget(self.heardBeat, 1, 4, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.treeWidget = QtGui.QTreeWidget(self.centralwidget)
        self.treeWidget.setObjectName(_fromUtf8("treeWidget"))
        self.treeWidget.headerItem().setText(0, _fromUtf8("1"))
        self.verticalLayout.addWidget(self.treeWidget)
        self.Dataset_properties = QtGui.QPlainTextEdit(self.centralwidget)
        self.Dataset_properties.setReadOnly(True)
        self.Dataset_properties.setObjectName(_fromUtf8("Dataset_properties"))
        self.verticalLayout.addWidget(self.Dataset_properties)
        self.gridLayout_2.addLayout(self.verticalLayout, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 271, 22))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow", None))
        self.FileButton.setText(_translate("MainWindow", "File", None))
        self.liveCheckBox.setText(_translate("MainWindow", "live", None))
        self.updateButton.setText(_translate("MainWindow", "Update", None))