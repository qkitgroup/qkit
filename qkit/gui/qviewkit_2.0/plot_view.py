# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'plot_view.ui'
#
# Created: Thu Sep 24 16:09:52 2015
#      by: PyQt4 UI code generator 4.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui
from qkit.storage.hdf_constants import ds_types
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
    def setupUi(self, Form,ds_type):
        Form.setObjectName(_fromUtf8("Form"))
        Form.resize(746, 452)
        self.gridLayout_2 = QtGui.QGridLayout(Form)
        self.gridLayout_2.setMargin(2)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSizeConstraint(QtGui.QLayout.SetMinimumSize)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        if ds_type == ds_types['coordinate']:
            self.setupCoordinate(Form)
        if ds_type == ds_types['vector']:
            self.setupVector(Form)
        if ds_type == ds_types['matrix'] or ds_type == -1:
            self.setupMatrix(Form)
        if ds_type == ds_types['box']:
            self.setupBox(Form)
        if ds_type == ds_types['txt']:
            self.setupTxt(Form)
        if ds_type == ds_types['view']:
            self.setupView(Form)
        
        spacerItem = QtGui.QSpacerItem(40, 1, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.gridLayout_2.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.gridLayout_2.addLayout(self.gridLayout, 1, 0, 1, 1)

        Form.setWindowTitle(_translate("Form", "Form", None))
        QtCore.QMetaObject.connectSlotsByName(Form)

    def setupCoordinate(self):
        self.setupMatrix()

    def setupVector(self,Form):
        self.PlotTypeSelector = QtGui.QComboBox(Form)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.PlotTypeSelector.sizePolicy().hasHeightForWidth())
        self.PlotTypeSelector.setSizePolicy(sizePolicy)
        self.PlotTypeSelector.setObjectName(_fromUtf8("PlotTypeSelector"))
        self.PlotTypeSelector.addItem(_fromUtf8(""))
        self.PlotTypeSelector.addItem(_fromUtf8(""))
        self.horizontalLayout.addWidget(self.PlotTypeSelector)
        self.PlotTypeSelector.setItemText(0, _translate("Form", "Line Plot", None))
        self.PlotTypeSelector.setItemText(1, _translate("Form", "Table", None))
        
        
    def setupBox(self,Form):
        self.PlotTypeSelector = QtGui.QComboBox(Form)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.PlotTypeSelector.sizePolicy().hasHeightForWidth())
        self.PlotTypeSelector.setSizePolicy(sizePolicy)
        self.PlotTypeSelector.setObjectName(_fromUtf8("PlotTypeSelector"))
        self.PlotTypeSelector.addItem(_fromUtf8(""))
        self.PlotTypeSelector.addItem(_fromUtf8(""))
        self.PlotTypeSelector.addItem(_fromUtf8(""))
        self.PlotTypeSelector.addItem(_fromUtf8(""))
        self.horizontalLayout.addWidget(self.PlotTypeSelector)
        self.PlotTypeSelector.setItemText(0, _translate("Form", "Color 3D Plot", None))
        self.PlotTypeSelector.setItemText(1, _translate("Form", "Color X Plot", None))
        self.PlotTypeSelector.setItemText(2, _translate("Form", "Color Y Plot", None))
        self.PlotTypeSelector.setItemText(3, _translate("Form", "Line Plot", None))

        self.SliceSelector = QtGui.QSpinBox(Form)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.SliceSelector.sizePolicy().hasHeightForWidth())
        self.SliceSelector.setSizePolicy(sizePolicy)
        self.SliceSelector.setSuffix(_fromUtf8(""))
        self.SliceSelector.setMinimum(-99999)
        self.SliceSelector.setMaximum(99999)
        self.SliceSelector.setProperty("value", -1)
        self.SliceSelector.setObjectName(_fromUtf8("SliceSelector"))
        self.horizontalLayout.addWidget(self.SliceSelector)
        self.SliceSelector.setPrefix(_translate("Form", "Slice: ", None))
        
        self.SliceValue = QtGui.QLineEdit(Form)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.SliceValue.sizePolicy().hasHeightForWidth())
        self.SliceValue.setSizePolicy(sizePolicy)
        self.SliceValue.setReadOnly(False)
        self.SliceValue.setObjectName(_fromUtf8("SliceValue"))
        self.horizontalLayout.addWidget(self.SliceValue)

        self.TraceXSelector = QtGui.QSpinBox(Form)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.TraceXSelector.sizePolicy().hasHeightForWidth())
        self.TraceXSelector.setSizePolicy(sizePolicy)
        self.TraceXSelector.setSuffix(_fromUtf8(""))
        self.TraceXSelector.setMinimum(-99999)
        self.TraceXSelector.setMaximum(99999)
        self.TraceXSelector.setProperty("value", -1)
        self.TraceXSelector.setObjectName(_fromUtf8("TraceXSelector"))
        self.horizontalLayout.addWidget(self.TraceXSelector)
        self.TraceXSelector.setPrefix(_translate("Form", "TraceX: ", None))
        self.TraceXValue = QtGui.QLineEdit(Form)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.TraceXValue.sizePolicy().hasHeightForWidth())
        self.TraceXValue.setSizePolicy(sizePolicy)
        self.TraceXValue.setReadOnly(False)
        self.TraceXValue.setObjectName(_fromUtf8("TraceXValue"))
        self.horizontalLayout.addWidget(self.TraceXValue)
        
        self.TraceYSelector = QtGui.QSpinBox(Form)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.TraceYSelector.sizePolicy().hasHeightForWidth())
        self.TraceYSelector.setSizePolicy(sizePolicy)
        self.TraceYSelector.setSuffix(_fromUtf8(""))
        self.TraceYSelector.setMinimum(-99999)
        self.TraceYSelector.setMaximum(99999)
        self.TraceYSelector.setProperty("value", -1)
        self.TraceYSelector.setObjectName(_fromUtf8("TraceYSelector"))
        self.horizontalLayout.addWidget(self.TraceYSelector)
        self.TraceYSelector.setPrefix(_translate("Form", "TraceY: ", None))
        self.TraceYValue = QtGui.QLineEdit(Form)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.TraceYValue.sizePolicy().hasHeightForWidth())
        self.TraceYValue.setSizePolicy(sizePolicy)
        self.TraceYValue.setReadOnly(False)
        self.TraceYValue.setObjectName(_fromUtf8("TraceYValue"))
        self.horizontalLayout.addWidget(self.TraceYValue)
        
    def setupTxt(self):
        self.setupMatrix()

    def setupView(self,Form):
        self.TraceSelector = QtGui.QSpinBox(Form)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.TraceSelector.sizePolicy().hasHeightForWidth())
        self.TraceSelector.setSizePolicy(sizePolicy)
        self.TraceSelector.setSuffix(_fromUtf8(""))
        self.TraceSelector.setMinimum(-99999)
        self.TraceSelector.setMaximum(99999)
        self.TraceSelector.setProperty("value", -1)
        self.TraceSelector.setObjectName(_fromUtf8("TraceSelector"))
        self.horizontalLayout.addWidget(self.TraceSelector)
        self.TraceSelector.setPrefix(_translate("Form", "Trace: ", None))
        self.TraceValue = QtGui.QLineEdit(Form)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.TraceValue.sizePolicy().hasHeightForWidth())
        self.TraceValue.setSizePolicy(sizePolicy)
        self.TraceValue.setReadOnly(False)
        self.TraceValue.setObjectName(_fromUtf8("TraceValue"))
        self.horizontalLayout.addWidget(self.TraceValue)
        
    def setupMatrix(self,Form):
        self.PlotTypeSelector = QtGui.QComboBox(Form)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.PlotTypeSelector.sizePolicy().hasHeightForWidth())
        self.PlotTypeSelector.setSizePolicy(sizePolicy)
        self.PlotTypeSelector.setObjectName(_fromUtf8("PlotTypeSelector"))
        self.PlotTypeSelector.addItem(_fromUtf8(""))
        self.PlotTypeSelector.addItem(_fromUtf8(""))
        self.PlotTypeSelector.addItem(_fromUtf8(""))
        self.horizontalLayout.addWidget(self.PlotTypeSelector)
        self.PlotTypeSelector.setItemText(0, _translate("Form", "Color Plot", None))
        self.PlotTypeSelector.setItemText(1, _translate("Form", "Line Plot", None))
        self.PlotTypeSelector.setItemText(2, _translate("Form", "Table", None))
        self.TraceSelector = QtGui.QSpinBox(Form)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.TraceSelector.sizePolicy().hasHeightForWidth())
        self.TraceSelector.setSizePolicy(sizePolicy)
        self.TraceSelector.setSuffix(_fromUtf8(""))
        self.TraceSelector.setMinimum(-99999)
        self.TraceSelector.setMaximum(99999)
        self.TraceSelector.setProperty("value", -1)
        self.TraceSelector.setObjectName(_fromUtf8("TraceSelector"))
        self.horizontalLayout.addWidget(self.TraceSelector)
        self.TraceSelector.setPrefix(_translate("Form", "Trace: ", None))
        self.TraceValue = QtGui.QLineEdit(Form)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.TraceValue.sizePolicy().hasHeightForWidth())
        self.TraceValue.setSizePolicy(sizePolicy)
        self.TraceValue.setReadOnly(False)
        self.TraceValue.setObjectName(_fromUtf8("TraceValue"))
        self.horizontalLayout.addWidget(self.TraceValue)