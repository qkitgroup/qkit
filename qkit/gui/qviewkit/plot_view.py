# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'plot_view.ui'
#
# Created: Thu Jul 23 07:27:53 2015
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
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.addPlotSelector = QtGui.QComboBox(Form)
        self.addPlotSelector.setObjectName(_fromUtf8("addPlotSelector"))
        self.horizontalLayout.addWidget(self.addPlotSelector)
        self.gridLayout_2.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 1, 0, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(_translate("Form", "Form", None))
        self.PlotTypeSelector.setItemText(0, _translate("Form", "Color Plot", None))
        self.PlotTypeSelector.setItemText(1, _translate("Form", "Line Plot", None))
        self.TraceSelector.setPrefix(_translate("Form", "Trace: ", None))

