# -*- coding: utf-8 -*-



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
        Form.resize(750, 450)
        self.gridLayout_Top = QtGui.QGridLayout(Form)
        self.gridLayout_Top.setMargin(0)
        self.gridLayout_Top.setObjectName(_fromUtf8("gridLayout_Top"))
        # we push for a tight layout
        self.gridLayout_Top.setMargin(0);
        self.gridLayout_Top.setContentsMargins(QtCore.QMargins(0,0,0,0));
        self.gridLayout_Top.setSpacing(0);
        
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSizeConstraint(QtGui.QLayout.SetMinimumSize)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        # we push for a tight layout
        self.horizontalLayout.setMargin(0);
        self.horizontalLayout.setContentsMargins(QtCore.QMargins(0,0,0,0));
        self.horizontalLayout.setSpacing(0);
        
        #spacerItem = QtGui.QSpacerItem(40, 1, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        #self.horizontalLayout.addItem(spacerItem)
        self.gridLayout_Top.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        
        self.gridLayout_Top.addLayout(self.gridLayout, 1, 0, 1, 1)

        Form.setWindowTitle(_translate("Form", "Form", None))
        QtCore.QMetaObject.connectSlotsByName(Form)        
        
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
        
    def setupCoordinate(self,Form):
        self.setupVector(Form)

    def setupVector(self,Form):
        self.PlotTypeSelector = QtGui.QComboBox(Form)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
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
        
        

        spacerItem = QtGui.QSpacerItem(40, 1, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self._addIndicatorLabels(Form,sizePolicy,indicators=["PointX","PointY"])
        #self.horizontalLayout.addLayout(self.IndicatorLayout,stretch = -10)
        
        
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
        
        

        #spacerItem = QtGui.QSpacerItem(40, 1, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        #self.horizontalLayout.addItem(spacerItem)
        
        #self.IndicatorLayout = self._addIndicatorLabels(Form,sizePolicy,indicators=["PointX","PointY","PointZ"])
        #self.horizontalLayout.addLayout(self.IndicatorLayout,stretch = -10)

    def setupTxt(self,Form):
        pass
        #self.setupMatrix()

    def setupView(self,Form):
        self.TraceSelector = QtGui.QSpinBox(Form)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.TraceSelector.sizePolicy().hasHeightForWidth())
        
        self._addTraceSelectorIndicator(Form,sizePolicy,TraceSelector = "TraceSelector", TraceIndicator="TraceValue")
        """
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
        """
        
        #The indicators should be located at the most right side of the bar
        spacerItem = QtGui.QSpacerItem(40, 1, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.IndicatorLayout = self._addIndicatorLabels(Form,indicators=["PointX","PointY"])
        self.horizontalLayout.addLayout(self.IndicatorLayout,stretch = -10)

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
        self.PlotTypeSelector.setItemText(0, _translate("Form", "Color Plot", None))
        self.PlotTypeSelector.setItemText(1, _translate("Form", "Line Plot", None))
        self.PlotTypeSelector.setItemText(2, _translate("Form", "Table", None))
        
        
        self.PlotTypeLayout = QtGui.QVBoxLayout()
        self.PlotTypeLayout.addWidget(self.PlotTypeSelector)
        # add a empty label to move the PlotTypeSelector to the top
        emptyL = QtGui.QLabel(Form)
        self.PlotTypeLayout.addWidget(emptyL)
        self.horizontalLayout.addLayout(self.PlotTypeLayout,stretch = -10)
        
        self._addTraceSelectorIndicator(Form,sizePolicy,TraceSelector = "TraceSelector", TraceIndicator="TraceValue")
        
        #The indicators should be located at the most right side of the bar
        spacerItem = QtGui.QSpacerItem(40, 1, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)        
        self.IndicatorLayout = self._addIndicatorLabels(Form,sizePolicy,indicators=["PointX","PointY","PointZ"])

        
    def _addIndicatorLabels(self,Form,sizePolicy,indicators=[]):
        self.IndicatorLayout = QtGui.QVBoxLayout()
        self.IndicatorLayout.setSizeConstraint(QtGui.QLayout.SetMinimumSize)
        self.IndicatorLayout.setObjectName(_fromUtf8("horizontalLayout"))

        self.IndicatorLayout.setMargin(0);
        self.IndicatorLayout.setContentsMargins(QtCore.QMargins(0,0,0,0));
        self.IndicatorLayout.setSpacing(3);
        
        for indicator in indicators:
            setattr(self,indicator,QtGui.QLabel(Form))
            temp_indicator = getattr(self,indicator)
            temp_indicator.setSizePolicy(sizePolicy)
            temp_indicator.setObjectName(_fromUtf8(indicator))
            self.IndicatorLayout.addWidget(temp_indicator)
            
        self.horizontalLayout.addLayout(self.IndicatorLayout,stretch = -10)


    def _addTraceSelectorIndicator(self,Form,sizePolicy,TraceSelector = "", TraceIndicator=""):
        self.TraceSelIndLayout = QtGui.QVBoxLayout()
        self.TraceSelIndLayout.setSizeConstraint(QtGui.QLayout.SetMinimumSize)
        self.TraceSelIndLayout.setObjectName(_fromUtf8("TraceSelIndLayout"))

        self.TraceSelIndLayout.setMargin(0);
        self.TraceSelIndLayout.setContentsMargins(QtCore.QMargins(0,0,0,0));
        self.TraceSelIndLayout.setSpacing(1);


        setattr(self,TraceSelector,QtGui.QSpinBox(Form))
        temp_SelInd = getattr(self,TraceSelector)
        temp_SelInd.setSizePolicy(sizePolicy)
        temp_SelInd.setSuffix(_fromUtf8(""))
        temp_SelInd.setMinimum(-99999)
        temp_SelInd.setMaximum(99999)
        temp_SelInd.setProperty("value", -1)
        temp_SelInd.setObjectName(_fromUtf8(TraceSelector))
        temp_SelInd.setPrefix(_translate("Form", "Trace: ", None))
        
        self.TraceSelIndLayout.addWidget(temp_SelInd)
            
        setattr(self,TraceIndicator,QtGui.QLineEdit(Form))
        temp_SelInd = getattr(self,TraceIndicator)
        temp_SelInd.setSizePolicy(sizePolicy)
        temp_SelInd.setReadOnly(False)
        temp_SelInd.setObjectName(_fromUtf8("TraceValue"))
        self.TraceSelIndLayout.addWidget(temp_SelInd)
        self.horizontalLayout.addLayout(self.TraceSelIndLayout,stretch = -10)
        #return self.TraceSelIndLayout
        