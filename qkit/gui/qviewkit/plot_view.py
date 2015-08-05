# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'plot_view.ui'
#
# Created: Sun Aug  2 23:08:30 2015
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

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName(_fromUtf8("Form"))
        Form.resize(746, 452)
        self.gridLayout_2 = QtGui.QGridLayout(Form)
        self.gridLayout_2.setMargin(2)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSizeConstraint(QtGui.QLayout.SetMinimumSize)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.PlotTypeSelector = QtGui.QComboBox(Form)
        self.PlotTypeSelector.setObjectName(_fromUtf8("PlotTypeSelector"))
        self.PlotTypeSelector.addItem(_fromUtf8(""))
        self.PlotTypeSelector.addItem(_fromUtf8(""))
        self.horizontalLayout.addWidget(self.PlotTypeSelector)
        self.TraceSelector = QtGui.QSpinBox(Form)
        self.TraceSelector.setSuffix(_fromUtf8(""))
        self.TraceSelector.setMinimum(-99999)
        self.TraceSelector.setMaximum(99999)
        self.TraceSelector.setProperty("value", -1)
        self.TraceSelector.setObjectName(_fromUtf8("TraceSelector"))
        self.horizontalLayout.addWidget(self.TraceSelector)
        spacerItem = QtGui.QSpacerItem(40, 1, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.label = QtGui.QLabel(Form)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout.addWidget(self.label)
        self.addXPlotSelector = QtGui.QComboBox(Form)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.addXPlotSelector.sizePolicy().hasHeightForWidth())
        self.addXPlotSelector.setSizePolicy(sizePolicy)
        self.addXPlotSelector.setMaximumSize(QtCore.QSize(150, 16777215))
        self.addXPlotSelector.setBaseSize(QtCore.QSize(0, 0))
        self.addXPlotSelector.setObjectName(_fromUtf8("addXPlotSelector"))
        self.horizontalLayout.addWidget(self.addXPlotSelector)
        self.label_2 = QtGui.QLabel(Form)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.horizontalLayout.addWidget(self.label_2)
        self.addYPlotSelector = QtGui.QComboBox(Form)
        self.addYPlotSelector.setMaximumSize(QtCore.QSize(150, 16777215))
        self.addYPlotSelector.setObjectName(_fromUtf8("addYPlotSelector"))
        self.horizontalLayout.addWidget(self.addYPlotSelector)
        self.addPlotBut = QtGui.QPushButton(Form)
        self.addPlotBut.setObjectName(_fromUtf8("addPlotBut"))
        self.horizontalLayout.addWidget(self.addPlotBut)
        self.gridLayout_2.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.gridLayout_2.addLayout(self.gridLayout, 1, 0, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(_translate("Form", "Form", None))
        self.PlotTypeSelector.setItemText(0, _translate("Form", "Color Plot", None))
        self.PlotTypeSelector.setItemText(1, _translate("Form", "Line Plot", None))
        self.TraceSelector.setPrefix(_translate("Form", "Trace: ", None))
        self.label.setText(_translate("Form", "X:", None))
        self.label_2.setText(_translate("Form", "Y:", None))
        self.addPlotBut.setText(_translate("Form", "Add", None))

