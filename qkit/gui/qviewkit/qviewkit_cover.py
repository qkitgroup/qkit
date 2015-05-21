# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qviewkit.ui'
#
# Created: Mon May 11 17:06:48 2015
#      by: PyQt4 UI code generator 4.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

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
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(800, 600)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.gridLayout = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setSpacing(-1)
        self.verticalLayout.setContentsMargins(-1, -1, -1, 0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(-1, 0, -1, -1)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.FileButton = QtGui.QPushButton(self.centralwidget)
        self.FileButton.setObjectName(_fromUtf8("FileButton"))
        self.horizontalLayout.addWidget(self.FileButton)
        self.data_list = QtGui.QComboBox(self.centralwidget)
        self.data_list.setObjectName(_fromUtf8("data_list"))
        self.horizontalLayout.addWidget(self.data_list)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.updateButton = QtGui.QPushButton(self.centralwidget)
        self.updateButton.setObjectName(_fromUtf8("updateButton"))
        self.horizontalLayout.addWidget(self.updateButton)
        self.liveCheckBox = QtGui.QCheckBox(self.centralwidget)
        self.liveCheckBox.setObjectName(_fromUtf8("liveCheckBox"))
        self.horizontalLayout.addWidget(self.liveCheckBox)
        self.liveBeat = QtGui.QRadioButton(self.centralwidget)
        self.liveBeat.setEnabled(True)
        self.liveBeat.setObjectName(_fromUtf8("liveBeat"))
        self.horizontalLayout.addWidget(self.liveBeat)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow", None))
        self.FileButton.setText(_translate("MainWindow", "Data", None))
        self.updateButton.setText(_translate("MainWindow", "Update", None))
        self.liveCheckBox.setText(_translate("MainWindow", "Live", None))
        self.liveBeat.setText(_translate("MainWindow", "live beat", None))

