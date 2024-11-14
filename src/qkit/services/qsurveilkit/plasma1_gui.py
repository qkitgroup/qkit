# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'plasma1_gui.ui'
#
# Created: Tue Jan 10 22:45:21 2017
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
        MainWindow.setEnabled(True)
        MainWindow.resize(1292, 451)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.graph_MC = PlotWidget(self.centralwidget)
        self.graph_MC.setGeometry(QtCore.QRect(650, 10, 630, 350))
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.graph_MC.sizePolicy().hasHeightForWidth())
        self.graph_MC.setSizePolicy(sizePolicy)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        self.graph_MC.setBackgroundBrush(brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.NoBrush)
        self.graph_MC.setForegroundBrush(brush)
        self.graph_MC.setObjectName(_fromUtf8("graph_MC"))
        self.graph_LL = PlotWidget(self.centralwidget)
        self.graph_LL.setGeometry(QtCore.QRect(10, 10, 630, 350))
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.graph_LL.sizePolicy().hasHeightForWidth())
        self.graph_LL.setSizePolicy(sizePolicy)
        self.graph_LL.setFrameShadow(QtGui.QFrame.Sunken)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.SolidPattern)
        self.graph_LL.setBackgroundBrush(brush)
        brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
        brush.setStyle(QtCore.Qt.NoBrush)
        self.graph_LL.setForegroundBrush(brush)
        self.graph_LL.setObjectName(_fromUtf8("graph_LL"))
        self.label_LL = QtGui.QLabel(self.centralwidget)
        self.label_LL.setGeometry(QtCore.QRect(220, 380, 211, 31))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("LM Sans 10"))
        font.setPointSize(16)
        self.label_LL.setFont(font)
        self.label_LL.setTextFormat(QtCore.Qt.PlainText)
        self.label_LL.setObjectName(_fromUtf8("label_LL"))
        self.label_MC = QtGui.QLabel(self.centralwidget)
        self.label_MC.setGeometry(QtCore.QRect(860, 380, 231, 31))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("LM Sans 10"))
        font.setPointSize(16)
        self.label_MC.setFont(font)
        self.label_MC.setTextFormat(QtCore.Qt.PlainText)
        self.label_MC.setObjectName(_fromUtf8("label_MC"))
        self.cb_scale = QtGui.QComboBox(self.centralwidget)
        self.cb_scale.setGeometry(QtCore.QRect(620, 390, 74, 21))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("LM Sans 10"))
        font.setPointSize(11)
        self.cb_scale.setFont(font)
        self.cb_scale.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
        self.cb_scale.setObjectName(_fromUtf8("cb_scale"))
        self.cb_scale.addItem(_fromUtf8(""))
        self.cb_scale.addItem(_fromUtf8(""))
        self.cb_scale.addItem(_fromUtf8(""))
        self.cb_scale.addItem(_fromUtf8(""))
        self.label = QtGui.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(560, 390, 71, 21))
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("LM Sans 10"))
        font.setPointSize(11)
        self.label.setFont(font)
        self.label.setObjectName(_fromUtf8("label"))
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setEnabled(True)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)
        self.actionQuit = QtGui.QAction(MainWindow)
        self.actionQuit.setObjectName(_fromUtf8("actionQuit"))
        self.actionStart = QtGui.QAction(MainWindow)
        self.actionStart.setObjectName(_fromUtf8("actionStart"))
        self.b_auto = QtGui.QAction(MainWindow)
        self.b_auto.setObjectName(_fromUtf8("b_auto"))
        self.b_24 = QtGui.QAction(MainWindow)
        self.b_24.setObjectName(_fromUtf8("b_24"))
        self.b_12 = QtGui.QAction(MainWindow)
        self.b_12.setObjectName(_fromUtf8("b_12"))
        self.b_6 = QtGui.QAction(MainWindow)
        self.b_6.setObjectName(_fromUtf8("b_6"))
        self.b_2 = QtGui.QAction(MainWindow)
        self.b_2.setObjectName(_fromUtf8("b_2"))
        self.b_1 = QtGui.QAction(MainWindow)
        self.b_1.setObjectName(_fromUtf8("b_1"))
        self.m_poll = QtGui.QAction(MainWindow)
        self.m_poll.setEnabled(False)
        self.m_poll.setObjectName(_fromUtf8("m_poll"))

        self.retranslateUi(MainWindow)
        self.cb_scale.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "Plasma 1 monitor", None))
        self.label_LL.setText(_translate("MainWindow", "LL: 3.85e-8 mbar", None))
        self.label_MC.setText(_translate("MainWindow", "MC: 3.45e-9 mbar", None))
        self.cb_scale.setItemText(0, _translate("MainWindow", "today", None))
        self.cb_scale.setItemText(1, _translate("MainWindow", "2h", None))
        self.cb_scale.setItemText(2, _translate("MainWindow", "1h", None))
        self.cb_scale.setItemText(3, _translate("MainWindow", "10min", None))
        self.label.setText(_translate("MainWindow", "Scale:", None))
        self.actionQuit.setText(_translate("MainWindow", "Quit", None))
        self.actionStart.setText(_translate("MainWindow", "Start", None))
        self.b_auto.setText(_translate("MainWindow", "Autoscale", None))
        self.b_24.setText(_translate("MainWindow", "24h", None))
        self.b_12.setText(_translate("MainWindow", "12h", None))
        self.b_6.setText(_translate("MainWindow", "6h", None))
        self.b_2.setText(_translate("MainWindow", "2h", None))
        self.b_1.setText(_translate("MainWindow", "1h", None))
        self.m_poll.setText(_translate("MainWindow", "Measure all channels", None))

from pyqtgraph import PlotWidget
