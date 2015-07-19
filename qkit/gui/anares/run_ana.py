import os
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *
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

import h5py
import numpy as np
import copy
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import tools as to
import res_ana
import resonator_tools as rt

application = QApplication(sys.argv)  
frame=loadUi('gr_el.ui')
    
global data_cut
data_cut=False

global it_notch,it_lorentz
it_notch=0
it_lorentz=0

def get_filename():
    global directory,fileExtension
    
    directory=QFileDialog.getOpenFileName()
    fileName,fileExtension=os.path.splitext(str(directory))
    frame.lineEdit.clear()    
    frame.lineEdit.insert(directory)
    
def load_data():
    global i_data,f_data,z_data
    
    if fileExtension=='.h5':
        global x0,dx,y0,dy,x_name,x_unit,y_name,y_unit,fill
        f=h5py.File(str(directory),'r')
        
        try:
            dset_x=f['/entry/data/amplitude']
            dset_y=f['/entry/data/phase']
            
            if dset_x.attrs['z_unit']=='dB':
                z_data=to.convert_to_complex_array(dset_x,dset_y,sformat='Amp[dB]/Phase')
            else:
                z_data=to.convert_to_complex_array(dset_x,dset_y,sformat='Amp/Phase')
            
            ni,nf=dset_x.shape
            
        except KeyError:
            dset_x=f['/entry/data/re']
            dset_y=f['/entry/data/im']
            
            z_data=to.convert_to_complex_array(dset_x,dset_y,sformat='Real/Imag')
            ni,nf=dset_x.shape
            
        x0=dset_x.attrs['x0']
        dx=dset_x.attrs['dx']
        y0=dset_x.attrs['y0']
        dy=dset_x.attrs['dy'] 
        x_name=dset_x.attrs['x_name']
        x_unit=dset_x.attrs['x_unit']
        y_name=dset_x.attrs['y_name']
        y_unit=dset_x.attrs['y_unit']
        x_unit=dset_x.attrs['x_unit']
        fill=dset_x.attrs['fill']
           
        f.close()
            
        i_data=[]
        for i in range(0,ni): 
            i_data.append(x0+i*dx)
        f_data=[]
        for i in range(0,nf):
            f_data.append(y0+i*dy)
        
    else:
        i_data,f_data,z_data=to.loadspecdata2(filename=directory,y1_col=frame.comboBox_4.currentIndex(),
                                              y2_col=frame.comboBox_5.currentIndex(),
                                              sformat=frame.comboBox.currentText())
    i_data = np.array(i_data)
    f_data = np.array(f_data) 
    z_data = np.array(z_data)                                             
    fit_data()
    comboBoxes_set_items()
    initialize_gui()
        
def fit_data():
    
    frame.label_2.show()
    bar.show()
    bar.setMinimum(1) 

    global data_fit
    
    if frame.radioButton.isChecked():
        data_fit=res_ana.notch(f_data,z_data,progress_bar=bar)
    if frame.radioButton_2.isChecked():
        data_fit=res_ana.skewed_lorentzian_fit(f_data,z_data,progress_bar=bar)
            
    if (not data_cut):
        global f_data_copy,z_data_copy,data_fit_copy
        f_data_copy=copy.deepcopy(f_data)
        data_fit_copy=copy.deepcopy(data_fit)
        z_data_copy=copy.deepcopy(z_data)
        
    frame.label_2.hide()
    bar.hide()
    
def comboBoxes_set_items():
    
    frame.comboBox_2.clear()
    frame.comboBox_3.clear()
        
    if frame.radioButton.isChecked():
        frame.comboBox_3.addItem(_fromUtf8(""))
        frame.comboBox_3.addItem(_fromUtf8(""))
        frame.comboBox_3.addItem(_fromUtf8(""))
        frame.comboBox_3.addItem(_fromUtf8(""))
        frame.comboBox_3.addItem(_fromUtf8(""))
        frame.comboBox_3.addItem(_fromUtf8(""))
        frame.comboBox_3.addItem(_fromUtf8(""))
        frame.comboBox_3.addItem(_fromUtf8(""))
        frame.comboBox_3.setItemText(0, _translate("MainWindow", "Amp (data)", None))
        frame.comboBox_3.setItemText(1, _translate("MainWindow", "Amp (fit)", None))
        frame.comboBox_3.setItemText(2, _translate("MainWindow", "Phase (data)", None))
        frame.comboBox_3.setItemText(3, _translate("MainWindow", "Phase (fit)", None))
        frame.comboBox_3.setItemText(4, _translate("MainWindow", "Phase, delay removed (fit)", None))
        frame.comboBox_3.setItemText(5, _translate("MainWindow", "Phase, delay removed (data)", None))
        frame.comboBox_3.setItemText(6, _translate("MainWindow", "Residuals, Amp", None))
        frame.comboBox_3.setItemText(7, _translate("MainWindow", "Residuals, Phase", None))
        
        frame.comboBox_2.addItem(_fromUtf8(""))
        frame.comboBox_2.addItem(_fromUtf8(""))
        frame.comboBox_2.addItem(_fromUtf8(""))
        frame.comboBox_2.addItem(_fromUtf8(""))
        frame.comboBox_2.addItem(_fromUtf8(""))
        frame.comboBox_2.addItem(_fromUtf8(""))
        frame.comboBox_2.addItem(_fromUtf8(""))
        frame.comboBox_2.addItem(_fromUtf8(""))
        frame.comboBox_2.addItem(_fromUtf8(""))
        frame.comboBox_2.addItem(_fromUtf8(""))
        frame.comboBox_2.addItem(_fromUtf8(""))
        frame.comboBox_2.addItem(_fromUtf8(""))
        frame.comboBox_2.addItem(_fromUtf8(""))
        frame.comboBox_2.setItemText(0, _translate("MainWindow", "Amp", None))
        frame.comboBox_2.setItemText(1, _translate("MainWindow", "Phase", None))
        frame.comboBox_2.setItemText(2, _translate("MainWindow", "Circle", None))
        frame.comboBox_2.setItemText(3, _translate("MainWindow", "Deviation, Amp", None))
        frame.comboBox_2.setItemText(4, _translate("MainWindow", "Deviation, Phase", None))
        frame.comboBox_2.setItemText(5, _translate("MainWindow", "Phase, delay removed", None))
        frame.comboBox_2.setItemText(6, _translate("MainWindow", "fr", None))
        frame.comboBox_2.setItemText(7, _translate("MainWindow", "Qr", None))
        frame.comboBox_2.setItemText(8, _translate("MainWindow", "Qi", None))
        frame.comboBox_2.setItemText(9, _translate("MainWindow", "absQc", None))
        frame.comboBox_2.setItemText(10, _translate("MainWindow", "phi0", None))
        frame.comboBox_2.setItemText(11, _translate("MainWindow", "Qi_err", None))
        frame.comboBox_2.setItemText(12, _translate("MainWindow", "Qr_err", None))
    
    if frame.radioButton_2.isChecked():
        frame.comboBox_3.addItem(_fromUtf8(""))
        frame.comboBox_3.addItem(_fromUtf8(""))
        frame.comboBox_3.addItem(_fromUtf8(""))
        frame.comboBox_3.addItem(_fromUtf8(""))
        frame.comboBox_3.setItemText(0, _translate("MainWindow", "Amp (data)", None))
        frame.comboBox_3.setItemText(1, _translate("MainWindow", "Amp (fit)", None))
        frame.comboBox_3.setItemText(2, _translate("MainWindow", "Phase (data)", None))
        frame.comboBox_3.setItemText(3, _translate("MainWindow", "Residuals, Amp", None))
        
        frame.comboBox_2.addItem(_fromUtf8(""))
        frame.comboBox_2.addItem(_fromUtf8(""))
        frame.comboBox_2.addItem(_fromUtf8(""))
        frame.comboBox_2.addItem(_fromUtf8(""))
        frame.comboBox_2.setItemText(0, _translate("MainWindow", "Amp", None))
        frame.comboBox_2.setItemText(1, _translate("MainWindow", "Phase", None))
        frame.comboBox_2.setItemText(2, _translate("MainWindow", "fr", None))
        frame.comboBox_2.setItemText(3, _translate("MainWindow", "Qr", None))
        
def initialize_gui():
        
    data_length=len(i_data)
    z_0=z_data[frame.spinBox.value()-1]

    frame.spinBox.setMaximum(data_length)
    frame.spinBox_2.setMaximum(data_length)
    
    plot3d(current_text=frame.comboBox_3.currentText())

    
    z_sim=data_fit["z_sim"][frame.spinBox.value()-1]
    
    plot2d(current_text=frame.comboBox_2.currentText(),z_0=z_0,z_sim=z_sim)
    
    frame.lineEdit_12.clear()
    frame.lineEdit_12.insert(str(i_data[0])+' ['+frame.lineEdit_4.text()+']')
    frame.lineEdit_2.clear()
    frame.lineEdit_2.insert("scans: "+str(len(i_data))+ ", val/scan: "+str(len(f_data)))
    'Enable widgets'
    frame.lineEdit_11.setEnabled(True)
    frame.lineEdit_4.setEnabled(True)
    frame.lineEdit_5.setEnabled(True)
    frame.lineEdit_6.setEnabled(True)
    frame.lineEdit_9.setEnabled(True)
    frame.lineEdit_10.setEnabled(True)
    frame.lineEdit_2.setEnabled(True)
    frame.pushButton_3.setEnabled(True)
    frame.pushButton_6.setEnabled(True)
    frame.pushButton_9.setEnabled(True)
    frame.comboBox_3.setEnabled(True)
    frame.comboBox_2.setEnabled(True)
    frame.spinBox.setEnabled(True)
    frame.spinBox_2.setEnabled(True)
    
    if fileExtension=='.h5':
        frame.lineEdit_11.clear()
        frame.lineEdit_11.insert(x_name)
        frame.lineEdit_4.clear()
        frame.lineEdit_4.insert(x_unit)
        frame.lineEdit_5.clear()
        frame.lineEdit_5.insert(y_name)
        frame.lineEdit_6.clear()
        frame.lineEdit_6.insert(y_unit)
        
    
def cut_data():
    
    global data_cut
    data_cut=True
    global f_data,z_data
        
    try:
        x_min=float(frame.lineEdit_10.text())
        x_max=float(frame.lineEdit_9.text())
    except ValueError:
        error_message()
        return 0
        
    if x_min>=x_max or x_min<min(f_data_copy) or x_max>max(f_data_copy):
        error_message()
        return 0

    f_data,z_data=to.cut_f_range(f_data_copy,z_data_copy,f_min=x_min,f_max=x_max)
    fit_data()
    initialize_gui()
    
def initial_data():
    global z_data,data_fit,f_data 
  
    z_data=copy.deepcopy(z_data_copy)
    data_fit=copy.deepcopy(data_fit_copy)
    f_data=copy.deepcopy(f_data_copy)
    initialize_gui()
   
def error_message():
    frame.Message = QtGui.QMessageBox()
    frame.Message.setText('      Invalid Input!!      ')
    frame.Message.show()

def show_message():
    frame.Message = QtGui.QMessageBox()
    frame.Message.setText('cuts data in x (usually frequency) and performs a fit within the limits entered by the user')
    frame.Message.show()
    
def set_new_label1():
    mw1.figure.add_subplot(111).set_ylabel(frame.lineEdit_5.text()+' ['+frame.lineEdit_6.text()+']')
    mw1.draw()
    mw2.figure.add_subplot(111).set_xlabel(frame.lineEdit_5.text()+' ['+frame.lineEdit_6.text()+']')
    mw2.draw()
    
def set_new_label2():
    frame.lineEdit_12.clear()
    frame.lineEdit_12.insert(str(i_data[frame.spinBox.value()-1])+' ['+frame.lineEdit_4.text()+']')
    mw1.figure.add_subplot(111).set_xlabel(frame.lineEdit_11.text()+' ['+frame.lineEdit_4.text()+']')
    mw1.draw()
    
def set_new_label3():
    frame.lineEdit_12.clear()
    frame.lineEdit_12.insert(str(i_data[frame.spinBox.value()-1])+' ['+frame.lineEdit_4.text()+']')

def update_2d_plot():
    z_sim=data_fit["z_sim"][frame.spinBox.value()-1]
    z_0=z_data[frame.spinBox.value()-1]
    plot2d(current_text=frame.comboBox_2.currentText(),z_0=z_0,z_sim=z_sim)
        
def update_3d_plot():
    plot3d(current_text=frame.comboBox_3.currentText())
        
def save_parameters():
    
    if fileExtension=='.h5':
        frame.Message = QtGui.QMessageBox()
        frame.Message.setText('press "save all" to save data in your hdf5-file')
        frame.Message.show()
        return
    
    param=data_fit["parameters"][frame.spinBox_2.value()-1]
    FileName2=str(QFileDialog.getSaveFileName())

    f_out=open(FileName2,'w')
    
    if frame.radioButton.isChecked():
        wr=[str(param["fr"]),str(param["Qr"]),str(param["Qi_dia_corr"]),str(param["absQc"]),str(param["phi0"]),str(data_fit["amp_norm"]),str(data_fit["alpha"]),str(data_fit["delay"])]
        tag=['fr:         ','Qr:         ','Qi_dia_corr:','absQc:      ','phi0:       ','amp_norm:   ','alpha:      ','delay:      ']
    
        for i in range(0,8):
            f_out.write(tag[i])
            f_out.write(wr[i].rjust(24))
            f_out.write('\n')
            
    if frame.radioButton_2.isChecked():
        wr=[str(param[4]),str(param[5])]
        tag=['fr:         ','Qr:         ']
    
        for i in range(0,2):
            f_out.write(tag[i])
            f_out.write(wr[i].rjust(24))
            f_out.write('\n')

    f_out.close()
    
def save_all_parameters():
    
    if fileExtension=='.h5':
        f=h5py.File(str(directory),'r+')
        
        if frame.radioButton.isChecked():
            param_dim=9 #we get 9+3 parameters for the circle fit and only 2 for lorentz
            
            path='/entry/analysis/notch resonator'
            _x='/re'
            _y='/im'
            
        if frame.radioButton_2.isChecked():
            param_dim=6
            
            path='/entry/analysis/lorentz'
            _x='/amplitude'
            
        # in case the dataset already exists at e.g. /entry/data/notch_res/re create a new one at /entry/data/notch_res 2/re etc.   
        try: 
            dset_x_sim=f.create_dataset(path+_x,(len(i_data),len(f_data)))
            dset_parameters=f.create_dataset(path+'/param',(len(i_data),param_dim))
            if frame.radioButton.isChecked(): 
                #notch res: amplitude and phase therefore two datasets
                dset_y_sim=f.create_dataset(path+_y,(len(i_data),len(f_data)))
        except RuntimeError:
            #iterate datasets .../re 1, ../re 2 ,......
            it=2
            while True:
                try:
                    dset_x_sim=f.create_dataset(path+' '+str(it)+_x,(len(i_data),len(f_data))) 
                    dset_parameters=f.create_dataset(path+' '+str(it)+'/param',(len(i_data),param_dim))
                    if frame.radioButton.isChecked():
                        dset_y_sim=f.create_dataset(path+' '+str(it)+_y,(len(i_data),len(f_data)))
                    break
                except RuntimeError:
                    it+=1
                
        
            
        dset_x_sim.attrs.create('y_unit',y_unit)
        dset_x_sim.attrs.create('x_name',x_name)
        dset_x_sim.attrs.create('y_name',y_name)
        dset_x_sim.attrs.create('x_unit',x_unit)
        dset_x_sim.attrs.create('dx',dx)
        dset_x_sim.attrs.create('dy',dy)
        dset_x_sim.attrs.create('y0',f_data[0])
        dset_x_sim.attrs.create('x0',x0)
        dset_x_sim.attrs.create('fill',fill)
        
        if frame.radioButton.isChecked():
            dset_y_sim.attrs.create('y_unit',y_unit)
            dset_y_sim.attrs.create('x_name',x_name)
            dset_y_sim.attrs.create('y_name',y_name)
            dset_y_sim.attrs.create('x_unit',x_unit)
            dset_y_sim.attrs.create('dx',dx)
            dset_y_sim.attrs.create('dy',dy)
            dset_y_sim.attrs.create('y0',f_data[0])
            dset_y_sim.attrs.create('x0',x0)
            dset_y_sim.attrs.create('fill',fill)
        
            dset_parameters.attrs.create("amp_norm",data_fit["amp_norm"])
            dset_parameters.attrs.create("alpha",data_fit["alpha"])
            dset_parameters.attrs.create("delay",data_fit["delay"])
            dset_parameters.attrs.create("order of parameters:","fr, Qr, absQc, Qi_no_corr, Qi_dia_corr, Qc_dia_corr, phi0, theta0, chi_square")
        
        if frame.radioButton_2.isChecked():
            dset_parameters.attrs.create("order of parameters:","A1, A2, A3, A4, fr, Qr")
        
        param=data_fit["parameters"]
        i=0
        
        if frame.radioButton.isChecked():
            for z in z_data:
                dset_x_sim[i]=np.real(z)
                dset_y_sim[i]=np.imag(z)
                p=param[i]
                dset_parameters[i]=np.array([p["fr"],p["Qr"],p["absQc"],p["Qi_no_corr"],p["Qi_dia_corr"],p["Qc_dia_corr"],p["phi0"],p["theta0"],p["chi_square"]])
                i+=1  
        if frame.radioButton_2.isChecked():
            for z in z_data:
                dset_x_sim[i]=np.absolute(z)
                p=param[i]
                dset_parameters[i]=np.array([p[0],p[1],p[2],p[3],p[4],p[5]])
                i+=1
        f.close()
        return
    
    FileName3=str(QFileDialog.getSaveFileName())
    f_out=open(FileName3,'w')
    
    if frame.radioButton.isChecked():
        label1='#'+str(frame.lineEdit_11.text())+' ['+str(frame.lineEdit_4.text())+']:'
        label2='fr'+' ['+str(frame.lineEdit_6.text())+']:'
        
        tag=[label1+(20-len(label1))*' ',label2+(20-len(label2))*' ','Qr:                 ','Qi_dia_corr:        ','absQc:              ','phi0:               ']
        
        f_out.write(tag[0])
        f_out.write(tag[1])
        f_out.write(tag[2])
        f_out.write(tag[3])
        f_out.write(tag[4])
        f_out.write(tag[5])
        
        f_out.write('\n')
    
        i=0
        for res in data_fit["parameters"]:
            f_out.write(str(i_data[i]))
            f_out.write((20-len(str(i_data[i])))*' ')
            f_out.write(str(res["fr"]))
            f_out.write((20-len(str(res["fr"])))*' ')
            f_out.write(str(res["Qr"]))
            f_out.write((20-len(str(res["Qr"])))*' ')
            f_out.write(str(res["Qi_dia_corr"]))
            f_out.write((20-len(str(res["Qi_dia_corr"])))*' ')
            f_out.write(str(res["absQc"]))
            f_out.write((20-len(str(res["absQc"])))*' ')
            f_out.write(str(res["phi0"]))
            f_out.write((20-len(str(res["phi0"])))*' ')
            
            i+=1
            f_out.write('\n')   
            
    if frame.radioButton_2.isChecked():
        label1='#'+str(frame.lineEdit_11.text())+' ['+str(frame.lineEdit_4.text())+']:'
        label2='fr'+' ['+str(frame.lineEdit_6.text())+']:'
        
        tag=[label1+(20-len(label1))*' ',label2+(20-len(label2))*' ','Qr:                 ']
        
        f_out.write(tag[0])
        f_out.write(tag[1])
        f_out.write(tag[2])
        
        f_out.write('\n')
    
        i=0
        for res in data_fit["parameters"]:
            f_out.write(str(i_data[i]))
            f_out.write((20-len(str(i_data[i])))*' ')
            f_out.write(str(res[4]))
            f_out.write((20-len(str(res[4])))*' ')
            f_out.write(str(res[5]))
            f_out.write((20-len(str(res[5])))*' ')
            i+=1
            f_out.write('\n')   
        
    f_out.close()
    
def plot3d(current_text):
    
    if frame.radioButton_2.isChecked():
        h1='lin'
        h2=''
    else:
        h1='log'
        h2='dB'
            
    if current_text=='Amp (data)':
        mw1.resDataScan(i_data,f_data,z_data,
                        xlabel=frame.lineEdit_11.text(),
                        xunit=frame.lineEdit_4.text(),ylabel=frame.lineEdit_5.text(),
                        yunit=frame.lineEdit_6.text(),zlabel='Amp',zunit=h2,
                        plottype='amp',ampformat=h1)
                        
    if current_text=='Amp (fit)':
        mw1.resDataScan(i_data,f_data,data_fit["z_sim"],
                        xlabel=frame.lineEdit_11.text(),
                        xunit=frame.lineEdit_4.text(),ylabel=frame.lineEdit_5.text(),
                        yunit=frame.lineEdit_6.text(),zlabel='Amp',zunit=h2,
                        plottype='amp',ampformat=h1)
                        
    if current_text=='Phase (data)':
        mw1.resDataScan(i_data,f_data,z_data,
                        xlabel=frame.lineEdit_11.text(),
                        xunit=frame.lineEdit_4.text(),ylabel=frame.lineEdit_5.text(),
                        yunit=frame.lineEdit_6.text(),zlabel='Phase',zunit='rad',
                        plottype='phase')
                        
    if current_text=='Phase (fit)':
        mw1.resDataScan(i_data,f_data,data_fit["z_sim"],
                        xlabel=frame.lineEdit_11.text(),
                        xunit=frame.lineEdit_4.text(),ylabel=frame.lineEdit_5.text(),
                        yunit=frame.lineEdit_6.text(),zlabel='Phase',zunit='rad',
                        plottype='phase')
                        
    if current_text=='Phase, delay removed (fit)': 
        
        zi=to.remove_cable_delay_2d(f_data,data_fit["z_sim"],data_fit["delay"])
        
        mw1.resDataScan(i_data,f_data,zi,
                        xlabel=frame.lineEdit_11.text(),
                        xunit=frame.lineEdit_4.text(),ylabel=frame.lineEdit_5.text(),
                        yunit=frame.lineEdit_6.text(),zlabel='Phase (fit), delay removed',zunit='rad',
                        plottype='phase')
                        
    if current_text=='Phase, delay removed (data)':
        
        zi=to.remove_cable_delay_2d(f_data,z_data,data_fit["delay"])   
        
        mw1.resDataScan(i_data,f_data,zi,xlabel=frame.lineEdit_11.text(),
                        xunit=frame.lineEdit_4.text(),ylabel=frame.lineEdit_5.text(),
                        yunit=frame.lineEdit_6.text(),zlabel='Phase (data), delay removed',zunit='rad',
                        plottype='phase')
                        
    if current_text=='Residuals, Amp':
        mw1.resDataScan(i_data,f_data,data_fit["res_amp"],xlabel=frame.lineEdit_11.text(),
                        xunit=frame.lineEdit_4.text(),ylabel=frame.lineEdit_5.text(),
                        yunit=frame.lineEdit_6.text(),zlabel='Residuals, Amp',zunit='',
                        plottype='std')
                        
    if current_text=='Residuals, Phase':
        mw1.resDataScan(i_data,f_data,data_fit["res_phase"],xlabel=frame.lineEdit_11.text(),
                        xunit=frame.lineEdit_4.text(),ylabel=frame.lineEdit_5.text(),
                        yunit=frame.lineEdit_6.text(),zlabel='Residuals, Phase',zunit='',
                        plottype='std') 
                        
def plot2d(current_text,z_0,z_sim):
    if current_text=='Amp':
        if frame.radioButton.isChecked():
            mw2.resData2(f_data,z_0,z_sim,xlabel=frame.lineEdit_5.text(),xunit=frame.lineEdit_6.text(),plottype='amp')
                        
        if frame.radioButton_2.isChecked():
            mw2.resData2(f_data,z_0,z_sim,xlabel=frame.lineEdit_5.text(),xunit=frame.lineEdit_6.text(),plottype='amp',ampformat='lin')
                                   
    if current_text=='Phase':
        if frame.radioButton.isChecked():
            mw2.resData2(f_data,z_0,z_sim,xlabel=frame.lineEdit_5.text(),xunit=frame.lineEdit_6.text(),plottype='phase')
        
        if frame.radioButton_2.isChecked():
            mw2.resData2(f_data,z_0,xlabel=frame.lineEdit_5.text(),xunit=frame.lineEdit_6.text(),plottype='phase')
        
    if current_text=='Circle':
        mw2.resData2(f_data,z_0,z_sim,xlabel=frame.lineEdit_5.text(),xunit=frame.lineEdit_6.text(),plottype='real/imag')
                    
    if current_text=='Phase, delay removed':
        z_0=to.remove_cable_delay(f_data,z_0,data_fit["delay"])
        z_sim0=to.remove_cable_delay(f_data,z_sim,data_fit["delay"])
        
        mw2.resData2(f_data,z_0,z_sim0,xlabel=frame.lineEdit_5.text(),xunit=frame.lineEdit_6.text(),plottype='phase')
        mw2.figure.add_subplot(111).set_ylabel('Phase, delay removed [rad]')

    if current_text=='Deviation, Amp':
        zi=to.st_deviation(data_fit["res_amp"])
        
        mw2.plot(i_data,zi,xlabel=frame.lineEdit_11.text(),xunit=frame.lineEdit_4.text(),ylabel='Deviation, Amp',yunit='-')
        
    if current_text=='Deviation, Phase':
        zi=to.st_deviation(data_fit["res_phase"])
        
        mw2.plot(i_data,zi,xlabel=frame.lineEdit_11.text(),xunit=frame.lineEdit_4.text(),ylabel='st. dev, Phase',yunit='rad')
      
    if current_text=='fr':
        if frame.radioButton.isChecked():
            z_0=[]
            for z0 in data_fit["parameters"]:
                z_0.append(z0["fr"])
        if frame.radioButton_2.isChecked():
            z_0=to.column(data_fit["parameters"],4)
            
        mw2.plot(i_data,z_0,xlabel=frame.lineEdit_11.text(),xunit=frame.lineEdit_4.text(),ylabel='fr',yunit=frame.lineEdit_6.text())

    if current_text=='Qr':
        if frame.radioButton.isChecked():
            z_0=[]
            for z0 in data_fit["parameters"]:
                z_0.append(z0["Qr"])
        if frame.radioButton_2.isChecked():
            z_0=to.column(data_fit["parameters"],5)
            
        mw2.plot(i_data,z_0,xlabel=frame.lineEdit_11.text(),xunit=frame.lineEdit_4.text(),ylabel='Qr')
        
    if current_text=='Qi':
        z_0=[]
        for z0 in data_fit["parameters"]:
            z_0.append(z0["Qi_dia_corr"])
        mw2.plot(i_data,z_0,xlabel=frame.lineEdit_11.text(),xunit=frame.lineEdit_4.text(),ylabel='Qi_dia_corr')

    if current_text=='absQc':
        z_0=[]
        for z0 in data_fit["parameters"]:
            z_0.append(z0["absQc"])
        mw2.plot(i_data,z_0,xlabel=frame.lineEdit_11.text(),xunit=frame.lineEdit_4.text(),ylabel='absQc')
        
    if current_text=='phi0':
        z_0=[]
        for z0 in data_fit["parameters"]:
            z_0.append(z0["phi0"])
        mw2.plot(i_data,z_0,xlabel=frame.lineEdit_11.text(),xunit=frame.lineEdit_4.text(),ylabel='phi0',yunit='rad')
        
    if current_text=='Qi_err':
        z_0=[]
        for z0 in data_fit["parameters"]:
            z_0.append(z0["Qi_dia_corr_err"])
        mw2.plot(i_data,z_0,xlabel=frame.lineEdit_11.text(),xunit=frame.lineEdit_4.text(),ylabel='Qi_err',yunit='')
        
    if current_text=='Qr_err':
        z_0=[]
        for z0 in data_fit["parameters"]:
            z_0.append(z0["Qr_err"])
        mw2.plot(i_data,z_0,xlabel=frame.lineEdit_11.text(),xunit=frame.lineEdit_4.text(),ylabel='Qr_err',yunit='')
        
        

frame.pushButton.clicked.connect(get_filename)
frame.pushButton_2.clicked.connect(load_data)
frame.pushButton_4.clicked.connect(frame.lineEdit.clear) 
frame.pushButton_7.clicked.connect(show_message)

bar=frame.progressBar
bar.hide()
frame.label_2.hide()

frame.connect(frame.lineEdit_5,SIGNAL('textEdited(QString)'),set_new_label1)
frame.connect(frame.lineEdit_6,SIGNAL('textEdited(QString)'),set_new_label1)

frame.connect(frame.lineEdit_11,SIGNAL('textEdited(QString)'),set_new_label2)
frame.connect(frame.lineEdit_4,SIGNAL('textEdited(QString)'),set_new_label2)

frame.connect(frame.spinBox,SIGNAL('valueChanged(int)'),update_2d_plot)
frame.connect(frame.spinBox,SIGNAL('valueChanged(int)'),set_new_label3)

frame.connect(frame.comboBox_2,SIGNAL('activated(int)'),update_2d_plot)

frame.connect(frame.comboBox_3,SIGNAL('activated(int)'),update_3d_plot)

frame.pushButton_3.clicked.connect(cut_data)
frame.pushButton_5.clicked.connect(initial_data)

frame.pushButton_6.clicked.connect(save_parameters)
frame.pushButton_9.clicked.connect(save_all_parameters)

mw1=frame.mplwidget_3
mw1.figure.add_subplot(111).set_axis_off()

mw2=frame.mplwidget_2
mw2.figure.add_subplot(111).set_axis_off()
    
frame.show()
application.exec_()        



    
    
