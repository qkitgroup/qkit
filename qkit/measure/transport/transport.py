# transport.py  measurement class for IV like transport measurements
# MMW/HR@KIT 11/2017

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


import numpy as np
import logging
#import matplotlib.pylab as plt
#from scipy.optimize import curve_fit
from time import sleep,time
import sys
import qt
import threading

import qkit
from qkit.storage import store as hdf
from qkit.analysis.IV_curve import IV_curve
from qkit.gui.plot import plot as qviewkit
from qkit.gui.notebook.Progress_Bar import Progress_Bar
from qkit.measure.measurement_class import Measurement 
import qkit.measure.write_additional_files as waf

##################################################################

class transport(object):
    '''
    usage:
        tr = transport.transport(IV_Device = IVD)
        
        tr.set_dVdI(<bool>)
        tr.sweep.reset_sweeps()
        tr.add_sweep_4quadrants(start=<start>, stop=<stop>, step=<step>, offset=<offset>)
        
        tr.measure_XX()
    '''
    
    def __init__(self, IV_Device, exp_name = '', sample = None):
        
        self.IVD = IV_Device
        self.exp_name = exp_name
        self._sample = sample
        
        self.comment = ''
        self.dirname = None

        self.x_set_obj = None
        self.y_set_obj = None
        self.tdx = 2e-3   # (s)
        self.tdy = 2e-3   # (s)

        self.progress_bar = True

        self._plot_comment=""

        self.set_log_function()
        
        self.open_qviewkit = True
        self.qviewkit_singleInstance = False
        
        self._measurement_object = Measurement()
        self._measurement_object.measurement_type = 'transport'
        self._measurement_object.sample = self._sample
        
        self._qvk_process = False
        
        self._web_visible = True
        
        self.sweep = self.sweeps()
        
        self._dVdI = False              # adds dV/dI data series, views, ...
        self._Fraunhofer = False
        
        
    def add_sweep_4quadrants(self, start, stop, step, offset=0):
        self.sweep.add_sweep(start+offset, +stop+offset, step)
        self.sweep.add_sweep(+stop+offset, start+offset, step)
        self.sweep.add_sweep(start+offset, -stop+offset, step)
        self.sweep.add_sweep(-stop+offset, start+offset, step)
        

    def set_log_function(self, func=None, name = None, unit = None, log_dtype = None):
        '''
        A function (object) can be passed to the measurement loop which is excecuted before every x iteration 
        but after executing the x_object setter in 2D measurements and before every line (but after setting 
        the x value) in 3D measurements.
        The return value of the function of type float or similar is stored in a value vector in the h5 file.

        Call without any arguments to delete all log functions. The timestamp is automatically saved.

        func: function object in list form
        name: name of logging parameter appearing in h5 file, default: 'log_param'
        unit: unit of logging parameter, default: ''
        log_dtype: h5 data type, default: 'f' (float32)
        '''

        if name == None:
            try:
                name = ['log_param']*len(func)
            except Exception:
                name = None
        if unit == None:
            try:
                unit = ['']*len(func)
            except Exception:
                unit = None
        if log_dtype == None:
            try:
                log_dtype = ['f']*len(func)
            except Exception:
                log_dtype = None

        self.log_function = []
        self.log_name = []
        self.log_unit = []
        self.log_dtype = []

        if func != None:
            for i,f in enumerate(func):
                self.log_function.append(f)
                self.log_name.append(name[i])
                self.log_unit.append(unit[i])
                self.log_dtype.append(log_dtype[i])

    def set_x_parameters(self, x_vec, x_coordname, x_set_obj, x_unit = ""):
        '''
        Sets parameters for sweep. In a 3D measurement, the x-parameters will be the "outer" sweep.
        For every x value all y values are swept
        
        Input:
            x_vec (array): conains the sweeping values
            x_coordname (string)
            x_instrument (obj): callable object to execute with x_vec-values (i.e. vna.set_power())
            x_unit (string): optional
        Output:
            None
        '''
        self.x_vec = x_vec
        self.x_coordname = x_coordname
        self.x_set_obj = x_set_obj
        #self.delete_fit_function()
        self.x_unit = x_unit

    def set_tdx(self, tdx):
        self.tdx = tdx

    def set_tdy(self, tdy):
        self.tdy = tdy

    def set_y_parameters(self, y_vec, y_coordname, y_set_obj, y_unit = ""):
        '''
        Sets parameters for sweep. In a 3D measurement, the x-parameters will be the "outer" sweep.
        For every x value all y values are swept
        
        Input:
            y_vec (array): contains the sweeping values
            y_coordname (string)
            y_instrument (obj): callable object to execute with x_vec-values (i.e. vna.set_power())
            y_unit (string): optional
        Output:
            None
        '''
        self.y_vec = y_vec
        self.y_coordname = y_coordname
        self.y_set_obj = y_set_obj
        #self.delete_fit_function()
        self.y_unit = y_unit

    def get_tdx(self):
        return self.tdx

    def get_tdy(self):
        return self.tdy

    def set_web_visible(self, web_visible = True):
        '''
        Sets the web_visible parameter for the measurement class
        
        Input:
            web_visible = True (Default) | False
        Output:
            None
        '''
        self._web_visible = web_visible
    
    
    def set_dVdI(self, status=True):
        '''
        Sets the dVdI parameter for the transport class, meaning weather differential resistance is calulated or not
        
        Input:
            status (bool)
        Output:
            None
        '''
        self._dVdI = status
    
    
    def get_dVdI(self):
        '''
        Gets the dVdI parameter for the transport class, meaning weather differential resistance is calulated or not
        
        Input:
            None
        Output:
            status (bool)
        '''
        return self._dVdI
    
    
    def set_Fraunhofer(self, status=False):
        '''
        Sets the Fraunhofer parameter for the transport class, meaning weather critical current is calulated or not
        
        Input:
            status (bool)
        Output:
            None
        '''
        self._Fraunhofer = status
    
    
    def get_Fraunhofer(self):
        '''
        Gets the Fraunhofer parameter for the transport class, meaning weather critical current is calulated or not
        
        Input:
            None
        Output:
            status (bool)
        '''
        return self._Fraunhofer
    
    
    def _prepare_measurement_IVD(self):
        '''
        All the relevant settings from the IVD are updated and called
        
        Input:
            None
        Output:
            None
        '''
        self._sweep_mode       = self.IVD.get_sweep_mode()                     # 0 (VV-mode) | 1 (IV-mode) | 2 (VI-mode)
        self._pseudo_bias_mode = self.IVD.get_pseudo_bias_mode()               # 0 (current bias) | 1 (voltage bias)
        self._bias             = self.IVD.get_bias()                           # 0 (current bias) | 1 (voltage bias)
        self._IV_modes         = {0:'I', 1:'V'}
        self._IV_units         = {0:'A', 1:'V'}
    
    
    def _prepare_measurement_file(self):
        '''
        creates the output .h5-file with distinct dataset structures for each measurement type.
        at this point all measurement parameters are known and put in the output file
        '''
        print ('filename '+self._file_name)
        self._data_file                      = hdf.Data(name=self._file_name, mode='a')
        self._measurement_object.uuid        = self._data_file._uuid
        self._measurement_object.hdf_relpath = self._data_file._relpath
        self._measurement_object.instruments = qt.instruments.get_instruments()

        #self._measurement_object.save()
        self._mo = self._data_file.add_textlist('measurement')
        self._mo.append(self._measurement_object.get_JSON())

        # write logfile and instrument settings
        #self._write_settings_dataset()
        #self._log = waf.open_log_file(self._data_file.get_filepath())
        
        self._data_bias = []
        self._data_I  = []
        self._data_V  = []
        if self._dVdI: self._data_dVdI  = []
        if self._scan_1D:
            ## add data variables
            self.sweep.create_iterator()
            for i in range(self.sweep.get_nos()):
                self._data_bias.append(self._data_file.add_coordinate('{:s}_b_{!s}'.format(self._IV_modes[self._bias], i), unit=self._IV_units[self._bias]))
                self._data_bias[i].add(self.get_bias_values(sweep=self.sweep.get_sweep()))
                self._data_I.append(self._data_file.add_value_vector('I_{!s}'.format(i), x=self._data_bias[i], unit = 'A', save_timestamp = False))
                self._data_V.append(self._data_file.add_value_vector('V_{!s}'.format(i), x=self._data_bias[i], unit = 'V', save_timestamp = False))
                if self._dVdI: self._data_dVdI.append(self._data_file.add_value_vector('dVdI_{!s}'.format(i), x=self._data_bias[i], unit = 'V/A', save_timestamp = False))
            ## add views
            IV   = self._data_file.add_view('IV', x=self._data_V[0], y=self._data_I[0])
            if self._dVdI: dVdI = self._data_file.add_view('dVdI', x=self._data_I[0] , y=self._data_dVdI[0])
            for i in range(1, self.sweep.get_nos()):
                IV.add(x=self._data_V[i],y=self._data_I[i])
                if self._dVdI: dVdI.add(x=self._data_I[i],y=self._data_dVdI[i])

        if self._scan_2D:
            self._data_x = self._data_file.add_coordinate(self.x_coordname, unit = self.x_unit)
            self._data_x.add(self.x_vec)
            
            ## add data variables
            self.sweep.create_iterator()
            for i in range(self.sweep.get_nos()):
                self._data_bias.append(self._data_file.add_coordinate('{:s}_b_{!s}'.format(self._IV_modes[self._bias], i), unit = 'A'))
                self._data_bias[i].add(self.get_bias_values(sweep=self.sweep.get_sweep()))
                self._data_I.append(self._data_file.add_value_matrix('I_{!s}'.format(i), x=self._data_x, y=self._data_bias[i], unit = 'A', save_timestamp = False))
                self._data_V.append(self._data_file.add_value_matrix('V_{!s}'.format(i), x=self._data_x, y=self._data_bias[i], unit = 'V', save_timestamp = False))
                if self._dVdI: self._data_dVdI.append(self._data_file.add_value_matrix('dVdI_{!s}'.format(i), x=self._data_x, y=self._data_bias[i], unit = 'V/A', save_timestamp = False))
#            if self._Fraunhofer:
#                    self._data_Ic = []
#                    for i in range(self.sweep.get_nos()):
#                        self._data_Ic.append(self._data_file.add_value_vector('Ic_'+str(i), x=self._data_x, unit = 'A', save_timestamp = False))
#                    Fraunhofer = self._data_file.add_view('Fraunhofer', x=self._data_x, y=self._data_Ic[0])
#                    for i in range(1, self.sweep.get_nos()):
#                        Fraunhofer.add(x=self._data_x, y=self._data_Ic[i])
            ## add views
            IV = self._data_file.add_view('IV', x=self._data_V[0], y=self._data_I[0])
            if self._dVdI: dVdI = self._data_file.add_view('dVdI', x=self._data_I[0] , y=self._data_dVdI[0])
            for i in range(1, self.sweep.get_nos()):
                IV.add(x=self._data_V[i],y=self._data_I[i])
                if self._dVdI: dVdI.add(x=eval('self._data_{:s}'.format(self._IV_modes[self._bias]))[i], y=self._data_dVdI[i])
#            if self._Fraunhofer:
#                self._data_Ic = []
#                for i in range(self.sweep.get_nos()):
#                    self._data_Ic.append(self._data_file.add_value_vector('Ic_'+str(i), x=self._data_x, unit = 'A', save_timestamp = False))
#                Fraunhofer = self._data_file.add_view('Fraunhofer', x=self._data_x, y=self._data_Ic[0])
#                for i in range(1, self.sweep.get_nos()):
#                    Fraunhofer.add(x=self._data_x, y=self._data_Ic[i])
                
            #if self.log_function != None:   #use logging
            #    self._log_value = []
            #    for i in range(len(self.log_function)):
            #        self._log_value.append(self._data_file.add_value_vector(self.log_name[i], x=self._data_x, unit = self.log_unit[i], dtype=self.log_dtype[i]))
                
        if self._scan_3D:
            self._data_x = self._data_file.add_coordinate(self.x_coordname, unit = self.x_unit)
            self._data_x.add(self.x_vec)
            self._data_y = self._data_file.add_coordinate(self.y_coordname, unit = self.y_unit)
            self._data_y.add(self.y_vec)
            
            ## add data variables
            self.sweep.create_iterator()
            for i in range(self.sweep.get_nos()):
                self._data_bias.append(self._data_file.add_coordinate('{:s}_b_{!s}'.format(self._IV_modes[self._bias], i), unit = 'A'))
                self._data_bias[i].add(self.get_bias_values(sweep=self.sweep.get_sweep()))
                self._data_I.append(self._data_file.add_value_box('I_{!s}'.format(i), x=self._data_x, y=self._data_y, z=self._data_bias[i], unit = 'A', save_timestamp = False))
                self._data_V.append(self._data_file.add_value_box('V_{!s}'.format(i), x=self._data_x, y=self._data_y, z=self._data_bias[i], unit = 'V', save_timestamp = False))
                if self._dVdI: self._data_dVdI.append(self._data_file.add_value_box('dVdI_{!s}'.format(i), x=self._data_x, y=self._data_y, z=self._data_bias[i], unit = 'V/A', save_timestamp = False))
            ## add views
            IV = self._data_file.add_view('IV', x=self._data_V[0], y=self._data_I[0])
            if self._dVdI: dVdI = self._data_file.add_view('dVdI', x=self._data_I[0] , y=self._data_dVdI[0])
            for i in range(1, self.sweep.get_nos()):
                IV.add(x=self._data_V[i],y=self._data_I[i])
                if self._dVdI: dVdI.add(x=eval('self._data_{:s}'.format(self._IV_modes[self._bias]))[i], y=self._data_dVdI[i])
#            
#            if self.log_function != None:   #use logging
#                self._log_value = []
#                for i in range(len(self.log_function)):
#                    self._log_value.append(self._data_file.add_value_vector(self.log_name[i], x=self._data_x, unit = self.log_unit[i], dtype=self.log_dtype[i]))
                    
        if self.comment:
            self._data_file.add_comment(self.comment)
            
        if self.qviewkit_singleInstance and self.open_qviewkit and self._qvk_process:
            self._qvk_process.terminate() #terminate an old qviewkit instance

    def _write_settings_dataset(self):
        self._settings = self._data_file.add_textlist('settings')
        settings = waf.get_instrument_settings(self._data_file.get_filepath())
        self._settings.append(settings)

    def _wait_progress_bar(self):
        ti = time()
        if self.progress_bar: 
            self._pb = Progress_Bar(self.IVD.get_averages(),self.dirname,self.IVD.get_sweeptime())
        qt.msleep(.2)
        # wait for data
        while not self.IVD.ready():
            if time()-ti > self.IVD.get_sweeptime(query=False):
                if self.progress_bar: self._pb.iterate()
                ti = time()
            qt.msleep(.2)
        
        if self.progress_bar:
            while self._pb.progr < self._pb.max_it:
                self._pb.iterate()
                
    def measure_1D(self):
        '''
        Measure method to record a single set of IV curves, according to the sweep and IV Device settings
        '''
        
        self._scan_1D = True
        self._scan_2D = False
        self._scan_3D = False
        self._scan_time = False
        
        self._measurement_object.measurement_func = sys._getframe().f_code.co_name
        self._measurement_object.x_axis = 'voltage'
        self._measurement_object.y_axis = ''
        self._measurement_object.z_axis = ''
        self._measurement_object.web_visible = self._web_visible
        if not self.dirname:
            self.dirname = 'IVD_tracedata'
        self._file_name = self.dirname.replace(' ', '').replace(',','_')
        if self.exp_name:
            self._file_name += '_' + self.exp_name
        
        # progress bar
        if self.progress_bar: self._pb = Progress_Bar(max_it=self.sweep.get_nos(), name='1D IVD sweep '+self.dirname)
        
        # prepare storage
        self._prepare_measurement_IVD()
        self._prepare_measurement_file()
        
        '''opens qviewkit to plot measurement, sense values are opened by default'''
        if self.open_qviewkit:
            self._qvk_process = qviewkit.plot(self._data_file.get_filepath(), datasets=['{:s}_{:d}'.format(self._IV_modes[not(self._bias)].lower(), i) for i in range(self.sweep.get_nos())])
        print('recording trace...')
        sys.stdout.flush()
        
        qt.mstart()
        
        
        # turn on IVD
        if self.IVD.get_sweep_mode() == 0: self.IVD.set_stati(True)
        elif self.IVD.get_sweep_mode() in [1, 2]: self.IVD.set_status(True)
        # interate sweeps
        self.sweep.create_iterator()
        for i in range(self.sweep.get_nos()):
            # take data
            I_values, V_values = self.IVD.take_IV(sweep=self.sweep.get_sweep())
            self._data_I[i].append(I_values)
            self._data_V[i].append(V_values)
            if self._dVdI: self._data_dVdI[i].append(np.array(np.gradient(V_values))/np.array(np.gradient(I_values)))
            # progress bar
            if self.progress_bar:
                self._pb.iterate()
            qt.msleep()
        # turn off IVD
        if self.IVD.get_sweep_mode() == 0: self.IVD.set_stati(False)
        elif self.IVD.get_sweep_mode() in [1, 2]: self.IVD.set_status(False)
        # end measurement
        qt.mend()
        self._end_measurement()



    def measure_2D(self):
        '''
        measure method to record a (averaged) VNA trace, S11 or S21 according to the setting on the VNA
        for all parameters x_vec in x_obj
        '''

        if not self.x_set_obj:
            logging.error('axes parameters not properly set...aborting')
            return
        self._scan_1D = False
        self._scan_2D = True
        self._scan_3D = False
        
        
        self._measurement_object.measurement_func = sys._getframe().f_code.co_name
        self._measurement_object.x_axis = self.x_coordname
        self._measurement_object.y_axis = 'current'
        self._measurement_object.z_axis = ''
        self._measurement_object.web_visible = self._web_visible

        if not self.dirname:
            self.dirname = self.x_coordname
        self._file_name = '2D_' + self.dirname.replace(' ', '').replace(',','_')
        if self.exp_name:
            self._file_name += '_' + self.exp_name

        if self.progress_bar: self._pb = Progress_Bar(max_it=len(self.x_vec)*self.sweep.get_nos(), name='2D IVD sweep '+self.dirname)

        self._prepare_measurement_IVD()
        self._prepare_measurement_file()

        '''opens qviewkit to plot measurement, sense values are opened by default'''
        if self.open_qviewkit:
            self._qvk_process = qviewkit.plot(self._data_file.get_filepath(), datasets=['{:s}_{:d}'.format(self._IV_modes[not(self._bias)].lower(), i) for i in range(self.sweep.get_nos())])
        
        self._measure()


    def measure_3D(self):
        '''
        measure full window of vna while sweeping x_set_obj and y_set_obj with parameters x_vec/y_vec. sweep over y_set_obj is the inner loop, for every value x_vec[i] all values y_vec are measured.
        
        optional: measure method to perform the measurement according to landscape, if set
        self.span is the range (in units of the vertical plot axis) data is taken around the specified funtion(s)
        note: make sure to have properly set x,y vectors before generating traces
        '''
        if not self.x_set_obj or not self.y_set_obj:
            logging.error('axes parameters not properly set...aborting')
            return
        self._scan_1D = False
        self._scan_2D = False
        self._scan_3D = True
        
        self._measurement_object.measurement_func = sys._getframe().f_code.co_name
        self._measurement_object.x_axis           = self.x_coordname
        self._measurement_object.y_axis           = self.y_coordname
        self._measurement_object.z_axis           = 'current'
        self._measurement_object.web_visible      = self._web_visible
        
        if not self.dirname:
            self.dirname = self.x_coordname + ', ' + self.y_coordname
        self._file_name = '3D_' + self.dirname.replace(' ', '').replace(',','_')
        if self.exp_name:
            self._file_name += '_' + self.exp_name
        
        if self.progress_bar: self._pb = Progress_Bar(max_it=len(self.x_vec)*len(self.y_vec)*self.sweep.get_nos(), name='2D IVD sweep '+self.dirname)
        
        self._prepare_measurement_IVD()
        self._prepare_measurement_file()
        '''opens qviewkit to plot measurement, sense values are opened by default'''
        if self.open_qviewkit:
            self._qvk_process = qviewkit.plot(self._data_file.get_filepath(), datasets=['{:s}_{:d}'.format(self._IV_modes[not(self._bias)].lower(), i) for i in range(self.sweep.get_nos())])
        
        self._measure()
    
    
    def _measure(self):
        '''
        measures and plots the data depending on the measurement type.
        the measurement loops feature the setting of the objects and saving the data in the .h5 file.
        '''
        qt.mstart()
        try:
            '''
            loop: x_obj with parameters from x_vec
            '''
            if self.IVD.get_sweep_mode() == 0: self.IVD.set_stati(True)
            elif self.IVD.get_sweep_mode() in [1, 2]: self.IVD.set_status(True)
            for ix, x in enumerate(self.x_vec):
                self.x_set_obj(x)
                sleep(self.tdx)
                
                #if self.log_function != None:
                #    for i,f in enumerate(self.log_function):
                #        self._log_value[i].append(float(f()))

                if self._scan_3D:
                    for y in self.y_vec:
                        '''
                        loop: y_obj with parameters from y_vec (only 3D measurement)
                        '''
                        self.y_set_obj(y)
                        sleep(self.tdy)
                        ''' measurement '''
                        self.sweep.create_iterator()
                        for i in range(self.sweep.get_nos()):
                            I_values, V_values = self.IVD.take_IV(sweep=self.sweep.get_sweep())
                            self._data_I[i].append(I_values)
                            self._data_V[i].append(V_values)
                            if self._dVdI: self._data_dVdI[i].append(np.array(np.gradient(V_values))/np.array(np.gradient(I_values)))
                            
                            if self.progress_bar:
                                self._pb.iterate()
                            qt.msleep()
                    '''
                    filling of value-box is done here.
                    after every y-loop the data is stored the next 2d structure
                    '''
                    for i in range(self.sweep.get_nos()):
                        self._data_I[i].next_matrix()
                        self._data_V[i].next_matrix()
                        if self._dVdI: self._data_dVdI[i].next_matrix()
                
                if self._scan_2D:
                    ''' measurement '''
                    self.sweep.create_iterator()
                    for i in range(self.sweep.get_nos()):
                        I_values, V_values = self.IVD.take_IV(sweep=self.sweep.get_sweep())
                        self._data_I[i].append(I_values)
                        self._data_V[i].append(V_values)
                        if self._dVdI: self._data_dVdI[i].append(np.array(np.gradient(V_values))/np.array(np.gradient(I_values)))
#                        if self._Fraunhofer:
#                            self._IVC = IV_curve()
#                            self._data_Ic[i].append(self._IVC.get_Ic(V=V_values, I=I_values, direction=self.IVD.direction))
#                        
                        if self.progress_bar:
                            self._pb.iterate()
                        qt.msleep()
                    
            if self.IVD.get_sweep_mode() == 0: self.IVD.set_stati(False)
            elif self.IVD.get_sweep_mode() in [1, 2]: self.IVD.set_status(False)
        except Exception as e:
            print e.__doc__
            print e.message        
        finally:
            self._end_measurement()
            self.IVD.set_stati(False)
            qt.mend()
    
    
    def _end_measurement(self):
        '''
        the data file is closed and filepath is printed
        '''
        print self._data_file.get_filepath()
        t = threading.Thread(target=qviewkit.save_plots,args=[self._data_file.get_filepath(),self._plot_comment])
        t.start()
        self._data_file.close_file()
        qkit.store_db.add(self._data_file.get_filepath())
        #waf.close_log_file(self._log)
        self.dirname = None
    
    
    def get_bias_values(self, sweep):
        '''
        Gets a linear distributed numpy-array of set bias values
        
        Input:
            sweep obj(float) : start, stop, step
        Output
            bias_values (numpy.array)
        '''
        start       = float(sweep[0])
        stop        = float(sweep[1])
        step        = float(sweep[2])
        step_signed = np.sign(stop-start)*np.abs(step)
        return np.arange(start, stop+step_signed/2., step_signed)
    
    
    def set_plot_comment(self, comment):
        '''
        Small comment to add at the end of plot pics for more information i.e. good for wiki entries.
        '''
        self._plot_comment=comment
    
    
    class sweeps(object):
        def __init__(self, name='default'):
            self._starts = []
            self._stops  = []
            self._steps  = []
            self.create_iterator()
        
        def create_iterator(self):
            self._start_iter = iter(self._starts)
            self._stop_iter = iter(self._stops)
            self._step_iter = iter(self._steps)
            
            
        def add_sweep(self, start, stop, step):
            self._starts.append(start)
            self._stops.append(stop)
            self._steps.append(step)
            
            
        def reset_sweeps(self):
            self._starts = []
            self._stops  = []
            self._steps  = []
            
        
        def get_sweep(self):
            return (self._start_iter.next(),
                    self._stop_iter.next(),
                    self._step_iter.next())
                    
        def get_nos(self):
            return len(self._starts)
            
            
        def print_sweeps(self):
            print(self._starts, self._stops, self._steps)
            
            