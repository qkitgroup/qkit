# oscilloscope.py measurement class
# Joao Barbosa, j.barbosa.1@research.gla.ac.uk 2021

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

import time
import logging
import numpy as np
import threading

import qkit
from qkit.storage import store as hdf
from qkit.gui.plot import plot as qviewkit
from qkit.gui.notebook.Progress_Bar import Progress_Bar
from qkit.measure.measurement_class import Measurement 
import qkit.measure.write_additional_files as waf

class scope_class(object):
    '''
    Measurement class for automated oscilloscope measurements.
    Measure_1D() and Measure_2D() functions are used to get data from scope.

    Usage:
        from qkit.measure.oscilloscope import oscilloscope

        scope=qkit.instruments.create("scope", <driver_name>, address=<TCPIP address>)
        scope.set_meas_channel([list])
        <set scope parameters>

        scope_meas_class=oscilloscope.scope_class(scope)
        scope_meas_class.measure_1D()
        ...
        <set 2d measurement>
        scope_meas_class.measure_2D()
    
    Scope drivers should implement the following functions (WIP:create alternatives for drivers which don't have these functions):
        scope.set_meas_channels()
        scope.ready()
        scope.start_measurement()

    '''
    def __init__(self, scope_device):

        self.scope=scope_device
        self.has_flowcontrol_func = all(x in self.scope.get_function_names() for x in ["ready","_start_measurement"])
        self.manual_trigger_control=0

        self._measurement_object=Measurement()
        self._measurement_object.measurement_type = 'oscilloscope'
        self.measurement_object_axis_name = 'time'
        self._dirname = None
        #self._filename = None
        self._expname = None
        self._comment = None
        self._plot_comment=""

        self.progress_bar = True
        self.open_qviewkit = True

        self._scan_dim = None 

        self.x_set_obj = None
        self.x_vec=None
        self.x_coordname = None
        self.x_unit = None
        
        self.y_set_obj = None #for 3D sweeps
        self.y_vec=None
        self.y_coordname = None
        self.y_unit = None
    
        self.log_function=None



    def set_filename(self, filename):
        self._filename=filename
        return

    def get_filename(self):
        return self._filename

    def set_expname(self, expname):
        self._expname=expname
        return
    def get_expname(self):
        return self._expname
    
    def set_comment(self, comment):
        self._comment=comment
        return
    def get_comment(self):
        return self._comment

    def set_log_function(self, func=None, name=None, unit=None, log_dtype=None):
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
                name = ['log_param'] * len(func)
            except Exception:
                name = None
        if unit == None:
            try:
                unit = [''] * len(func)
            except Exception:
                unit = None
        if log_dtype == None:
            try:
                log_dtype = ['f'] * len(func)
            except Exception:
                log_dtype = None

        self.log_function = []
        self.log_name = []
        self.log_unit = []
        self.log_dtype = []

        if func != None:
            for i, f in enumerate(func):
                self.log_function.append(f)
                self.log_name.append(name[i])
                self.log_unit.append(unit[i])
                self.log_dtype.append(log_dtype[i])

    def set_x_parameters(self, x_vec, x_coordname, x_set_obj, x_unit=""):
        '''
        Same functionality as seen on spectroscopy class
        '''
        self.x_vec = x_vec
        self.x_coordname = x_coordname
        self.x_unit = x_unit
        self.x_set_obj = x_set_obj
        return
    
    def set_y_parameters(self, y_vec, y_coordname, y_set_obj, y_unit=""):
        """
        Sets parameters for sweep. In a 3D measurement, the x-parameters will be the "outer" sweep.
        For every x value all y values are swept
        Same functionality as seen on spectroscopy class
        """
        self.y_vec = y_vec
        self.y_coordname = y_coordname
        self.y_set_obj = y_set_obj
        self.y_unit = y_unit
        return


    def _prepare_measurement_file(self):
        #data.h5 file
        self._data_file = hdf.Data(name=self._filename, mode="a")
        self._measurement_object.uuid = self._data_file._uuid
        self._measurement_object.hdf_relpath = self._data_file._relpath
        self._measurement_object.instruments = qkit.instruments.get_instrument_names()
        

        self._measurement_object.save()
        self._mo = self._data_file.add_textlist('measurement')
        self._mo.append(self._measurement_object.get_JSON())

        #settings file
        self._settings = self._data_file.add_textlist('settings')
        settings = waf.get_instrument_settings(self._data_file.get_filepath())
        self._settings.append(settings)
        
        #log file
        self._log_file = waf.open_log_file(self._data_file.get_filepath())

        #data variables
        self._hdf_time = [0]
        self._hdf_voltage = [0]

        self._data_V = []
        #add data variables to h5
        if self._scan_dim == 1:
            self._data_t = self._data_file.add_coordinate("time", unit="s")
            for ind,ch in enumerate(self.scope._meas_channel):
                self._data_V.append(self._data_file.add_value_vector("voltage_ch{}".format(ch),x=self._data_t, unit="V"))

        if self._scan_dim == 2:
            self._data_x = self._data_file.add_coordinate(self.x_coordname, unit=self.x_unit)
            self._data_x.add(self.x_vec)
            
            self._data_t = self._data_file.add_coordinate("time", unit="s")
            self._data_t.add(self._timepoints)
            for ind,ch in enumerate(self.scope._meas_channel):
                self._data_V.append(self._data_file.add_value_matrix("voltage_ch{}".format(ch),x=self._data_x, y=self._data_t, unit="V",save_timestamp=True))
            
            if self.log_function != None:  # use logging
                self._log_value = []
                for i in range(len(self.log_function)):
                    self._log_value.append(
                        self._data_file.add_value_vector(self.log_name[i], x=self._data_x, unit=self.log_unit[i],
                                                         dtype=self.log_dtype[i]))

            #self._data_V = self._data_file.add_value_matrix("voltage", x=self._data_x, y=self.data_t, unit="V", save_timestamp=True)

        if self._scan_dim == 3: #3D sweep (WIP)
            self._data_x = self._data_file.add_coordinate(self.x_coordname, unit=self.x_unit)
            self._data_x.add(self.x_vec)
            self._data_y = self._data_file.add_coordinate(self.y_coordname, unit=self.y_unit)
            self._data_y.add(self.y_vec)

            self._data_t = self._data_file.add_coordinate("time", unit="s")
            self._data_t.add(self._timepoints)
            for ind,ch in enumerate(self.scope._meas_channel):
                self._data_V.append(self._data_file.add_value_box('voltage_ch{}'.format(ch), x=self._data_y, y=self._data_x,
                                                           z=self._data_t, unit='V',
                                                           save_timestamp=False))


        #add view 
        #self._hdf_t_view = self._data_file.add_view("data", x=self._data_t, y=self._data_V, 
        #                                            view_params={"labels" : ("t","V"), "plot_style": 1, "markersize":5})

        if self._comment:
            self._data_file.add_comment(self._comment)
        return

    def _prepare_measurement_scope(self):
        self._nop = self.scope.get_nop()
        self._timepoints=self.scope.get_time_data()
        if self.has_flowcontrol_func:
            self.scope._pre_measurement()
        return

    def _end_measurement(self):
        print(self._data_file.get_filepath())
        t = threading.Thread(target=qviewkit.save_plots, args=[self._data_file.get_filepath(), self._plot_comment])
        t.start()
        self._data_file.close_file()
        waf.close_log_file(self._log_file)
        self._dirname = None
        if self.has_flowcontrol_func: self.scope._post_measurement()

    def measure_1D(self):
        '''
        Measures the active channel on the oscilloscope
        '''
        self._scan_dim = 1
        self._measurement_object.measurement_func = 'measure_1D'
        self._measurement_object.x_axis=self.measurement_object_axis_name
        self._measurement_object.y_axis=""
        self._measurement_object.z_axis=""

        if not self._dirname:
            self._dirname="Scope_Tracedata"
        self._filename = self._dirname.replace(" ","").replace(",","_")
        
        self._prepare_measurement_scope() 
        self._prepare_measurement_file()

        if self.open_qviewkit:
            open_ds=["voltage_ch{}".format(i) for i in self.scope._meas_channel]
            self._qvk_process = qviewkit.plot(self._data_file.get_filepath(), datasets=open_ds)
        
        qkit.flow.start()

        if self.scope.ready():
            self.scope._start_measurement()
            x,y = self.scope.get_data()
            self._data_t.append(x[0])
            for ind,ch in enumerate(self.scope._meas_channel):
                self._data_V[ind].append(y[ind])

        qkit.flow.end()
        self._end_measurement()

        return
    
    def measure_2D(self):
        '''
        Measures the active channel on the oscilloscope for all parameters x_vec in x_obj
        '''
        if not self.x_set_obj:
            logging.error('axes parameters not properly set...aborting')
            return
        if len(self.x_vec) == 0:
            logging.error('No points to measure given. Check your x vector... aborting')
            return
        self._scan_dim = 2

        self._measurement_object.measurement_func = 'measure_2D'
        self._measurement_object.x_axis = self.x_coordname
        self._measurement_object.y_axis = self.measurement_object_axis_name
        self._measurement_object.z_axis = '' 

        if not self._dirname:
            self._dirname = "Scope_Tracedata_"+self.x_coordname
        self._filename = '2D_' + self._dirname.replace(' ', '').replace(',', '_')

        self._prepare_measurement_scope()
        self._prepare_measurement_file()

        if self.open_qviewkit:
            open_ds=["voltage_ch{}".format(i) for i in self.scope._meas_channel]
            self._qvk_process = qviewkit.plot(self._data_file.get_filepath(), datasets=open_ds)

        qkit.flow.start()
        try:
            for i, x in enumerate(self.x_vec):

                if self.log_function != None:
                    for i, f in enumerate(self.log_function):
                        self._log_value[i].append(float(f()))

                self.scope.clear()
                self.x_set_obj(x)
                if self.scope.ready():
                    if(not self.manual_trigger_control):
                        self.scope._start_measurement()
                    else:
                        self.scope._start_measurement_manual_trigger()
                    time.sleep(0.01)
                    t,y = self.scope.get_data()
                    for ind,ch in enumerate(self.scope._meas_channel):
                        self._data_V[ind].append(y[ind])
                time.sleep(0.1)
        except Exception as e:
            print(e)
        finally:
            qkit.flow.end()
            self._end_measurement()

        return

    def measure_3D(self):
        '''
        Measures the active channels on the oscilloscope for all parameters x_vec in x_obj and y_vec in y_obj. Sweep over y_vec is outer and x_vec inner, for every y_vec[i], all values of x_vec are considered
        '''
        if not self.x_set_obj:
            logging.error('axes parameters not properly set...aborting')
            return
        if len(self.x_vec) * len(self.y_vec) == 0:
            logging.error('No points to measure given. Check your x vector... aborting')
            return
        self._scan_dim = 3

        self._measurement_object.measurement_func = 'measure_2D'
        self._measurement_object.x_axis = self.x_coordname
        self._measurement_object.y_axis = self.measurement_object_axis_name
        self._measurement_object.z_axis = self.y_coordname

        if not self._dirname:
            self._dirname = "Scope_Tracedata_"+self.x_coordname+"-"+self.y_coordname
        self._filename = '3D_' + self._dirname.replace(' ', '').replace(',', '_')

        self._prepare_measurement_scope()
        self._prepare_measurement_file()

        if self.open_qviewkit:
            open_ds=["voltage_ch{}".format(i) for i in self.scope._meas_channel]
            self._qvk_process = qviewkit.plot(self._data_file.get_filepath(), datasets=open_ds)

        qkit.flow.start()
        try:
            for j,y in enumerate(self.y_vec):
                self.y_set_obj(y)

                for i, x in enumerate(self.x_vec):
                    self.scope.clear()
                    self.x_set_obj(x)
                    if self.scope.ready():
                        if(not self.manual_trigger_control):
                            self.scope._start_measurement()
                        else:
                            self.scope._start_measurement_manual_trigger()
                        time.sleep(0.01)
                        t,y = self.scope.get_data()
                        for ind,ch in enumerate(self.scope._meas_channel):
                            self._data_V[ind].append(y[ind])
                    time.sleep(0.1)
                
                for ind,ch in enumerate(self.scope._meas_channel):
                    self._data_V[ind].next_matrix()
                
        # except Exception as e:
        #     print(e)
        finally:
            qkit.flow.end()
            self._end_measurement()

        return