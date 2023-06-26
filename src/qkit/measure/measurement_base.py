# Base class for QKIT measurements to simplify and unify
# S1@KIT 2020

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


import logging
import threading

import numpy as np

import qkit
import qkit.measure.write_additional_files as waf
from qkit.gui.notebook.Progress_Bar import Progress_Bar
from qkit.gui.plot import plot as qviewkit
from qkit.measure.measurement_class import Measurement
from qkit.storage import store as hdf


##################################################################

class MeasureBase(object):
    """
    Baseclass for measurements.
    """

    def __init__(self, sample=None):
        self.set_sample(sample)
        
        self.comment = ''
        self.measurement_name = None
        
        self._x_parameter = None
        self._y_parameter = None
        
        self.progress_bar = True
        self._pb = Progress_Bar(0, dummy=True)
        
        self._file_name = ""
        
        self.log_functions = []
        
        self.open_qviewkit = True
        self.qviewkit_singleInstance = False
        self._qvk_process = False
        
        self._measurement_object = Measurement()
        self._measurement_object.measurement_type = 'defaultMeasurement'
        self.web_visible = True

    def __getattr__(self, item):
        if item == "x_vec":
            return self._x_parameter.values
        elif item == "y_vec":
            return self._y_parameter.values
        else:
            raise AttributeError("Measurement object has no attribute '{}'".format(item))
    
    def set_sample(self,sample):
        if sample is None:
            self._sample = None
        elif not isinstance(sample,qkit.measure.samples_class.Sample):
            raise ValueError(__name__ + ": The given sample '{!s}' is not a qkit sample object.".format(sample))
        self._sample = sample
    
    def add_log_function(self, func, name, unit="", log_dtype=float):
        """
        A function (object) can be passed to the measurement loop which is excecuted before every x iteration
        but after executing the x_object setter in 2D measurements and before every line (but after setting
        the x value) in 3D measurements.
        The return value of the function of type float or similar is stored in a value vector in the h5 file.
        
        To add multiple log functions, execute this function multiple times.

        func: function object
        name: name of logging parameter appearing in h5 file
        unit: unit of logging parameter, default: ''
        log_dtype: h5 data type, default: float
        """
        
        if not callable(func):
            raise ValueError('{:s}: Cannot set {!s} as log-function: callable object needed'.format(__name__, func))
        if type(name) is not str:
            raise ValueError('{:s}: Cannot set {!s} as log-name: string needed'.format(__name__, name))
        if type(unit) is not str:
            raise ValueError('{:s}: Cannot set {!s} as log-unit: string needed'.format(__name__, unit))
        
        self.log_functions.append([func, name, unit, log_dtype])
    
    def remove_log_function(self, index=None):
        """
        Remove the index-th log function.
        If no index is given, all log functions are removed.
        """
        if index is None:
            self.log_functions = []
        else:
            self.log_functions.pop(index)
    
    class Coordinate:
        def __init__(self, name, unit="", values=None, set_function=None, wait_time=0):
            if type(name) is not str:
                raise TypeError('{:s}: Cannot set {!s} as name for coordinate: string needed'.format(__name__, self.name))
            self.name = name
            self.unit = unit
            self.values = values
            if callable(set_function):
                self.set_function = set_function
            else:
                self.set_function = lambda x: True
            self.wait_time = wait_time if wait_time is not None else 0
            self.hdf_dataset = None
        
        def validate_parameters(self):
            if type(self.name) is not str:
                raise TypeError('{:s}: Cannot set {!s} as name for coordinate: string needed'.format(__name__, self.name))
            if type(self.unit) is not str:
                raise TypeError('{:s}: Cannot set {!s} as unit for coordinate {!s}: string needed'.format(__name__, self.unit, self.name))
            if np.iterable(self.values):
                try:
                    self.values = np.array(self.values, dtype=float)
                    if len(self.values) == 0:
                        logging.warning("{:s}: Setting zero-length vector for coordinate {!s}. Please check if this is intended.".format(__name__, self.name))
                except Exception as e:
                    raise type(e)(
                            '{:s}: Cannot set {!s} as vector for coordinate {!s}: Array conversion failed:{!s}'.format(__name__, self.values, self.name, e))
            else:
                raise TypeError('{:s}: Cannot set {!s} as vector for coordinate {!s}: iterable object needed'.format(__name__, self.values, self.name))
            if not callable(self.set_function):
                raise TypeError('{:s}:  Cannot set {!s} as function for coordinate {!s}: callable object needed'.format(__name__, self.set_function, self.name))
            if type(self.wait_time) in [int, float]:
                self.wait_time = float(self.wait_time)
            else:
                raise TypeError('{:s}:  Cannot set {!s} as wait time for coordinate {!s}: float needed'.format(__name__, self.wait_time, self.name))
            return True

        def create_dataset(self, hdf_file):
            if self.hdf_dataset is None or self.hdf_dataset.hf != hdf_file.hf: # If dataset not yet created or belongs to old hdf file
                self.validate_parameters()
                self.hdf_dataset = hdf_file.add_coordinate(self.name, unit=self.unit)
                self.hdf_dataset.add(self.values)
            else:
                logging.info(__name__ + ": Dataset for coordinate '{}' was already created.".format(self.name))
            return self.hdf_dataset

    class Data:
        def __init__(self, name, coords, unit="", save_timestamp=False, average_over=None, **kwargs):
            if type(name) is not str:
                raise TypeError('{:s}: Cannot set {!s} as name for Data: string needed'.format(__name__, name))
            if type(coords) not in (list, tuple):
                raise TypeError('{:s}: Cannot set {!s} as coordinates for data {!s}: list or tuple of Coordinates needed'.format(__name__, coords, name))
            for c in coords:
                if not isinstance(c,MeasureBase.Coordinate):
                    raise TypeError(
                            '{:s}: Cannot set {!s} as coordinate for data {!s}: Please use the qkit.measure.MeasureBase.Coordinate type'.format(__name__, c,
                                                                                                                                                name))
            self.name = name
            self.coordinates = coords
            self.dim = len(coords)
            self.unit = unit
            self.kwargs = kwargs
            self.kwargs.update({"save_timestamp": save_timestamp, "average_over": average_over})
            self.hdf_dataset = None
    
        def validate_parameters(self):
            if type(self.name) is not str:
                raise TypeError('{:s}: Cannot set {!s} as name for Data: string needed'.format(__name__, self.name))
            if type(self.coordinates) not in (list, tuple):
                raise TypeError(
                        '{:s}: Cannot set {!s} as coordinates for data {!s}: list or tuple of Coordinates needed'.format(__name__, self.coordinates, self.name))
            for c in self.coordinates:
                if not isinstance(c,MeasureBase.Coordinate):
                    raise TypeError(
                            '{:s}: Cannot set {!s} as coordinate for data {!s}: Please use the qkit.measure.MeasureBase.Coordinate type'.format(__name__, c,
                                                                                                                                                self.name))
            self.dim = len(self.coordinates)
            if type(self.unit) is not str:
                raise TypeError('{:s}: Cannot set {!s} as unit for data {!s}: string needed'.format(__name__, self.unit, self.name))
            return True
    
        def create_dataset(self, hdf_file):
            if self.hdf_dataset is None or self.hdf_dataset.hf != hdf_file.hf: # If dataset not yet created or belongs to old hdf file
                self.validate_parameters()
                c = [co.create_dataset(hdf_file) for co in self.coordinates]
                if self.dim == 1:
                    self.hdf_dataset = hdf_file.add_value_vector(self.name, x=c[0], unit = self.unit, **self.kwargs)
                elif self.dim == 2:
                    self.hdf_dataset = hdf_file.add_value_matrix(self.name, x=c[0], y=c[1], unit = self.unit, **self.kwargs)
                elif self.dim == 3:
                    self.hdf_dataset = hdf_file.add_value_box(self.name, x=c[0], y=c[1], z=c[2], unit = self.unit, **self.kwargs)
            else:
                logging.info(__name__ + ": Dataset for coordinate '{}' was already created.".format(self.name))
            return self.hdf_dataset
    
    def set_x_parameters(self, vec, coordname, set_obj, unit, dt=None):
        """
        Sets x-parameters for 2D and 3D scan.
        In a 3D measurement, the x-parameters will be the "outer" sweep meaning for every x value all y values are swept and for each (x,y) value the bias is swept according to the set sweep parameters.

        Parameters
        ----------
        vec: array_likes
            An N-dimensional array that contains the sweep values.
        coordname: string
            The coordinate name to be created as data series in the .h5 file.
        set_obj: obj
            An callable object to execute with vec-values.
        unit: string
            The unit name to be used in data series in the .h5 file.
        dt: float, optional
            The sleep time between x-iterations.

        Returns
        -------
        None
        """
        # vec
        try:
            self._x_parameter = self.Coordinate(coordname, unit, np.array(vec, dtype=float), set_obj, dt)
            self._x_parameter.validate_parameters()
        except Exception as e:
            self._x_parameter = None
            raise e
    
    def set_y_parameters(self, vec, coordname, set_obj, unit, dt=None):
        """
        Sets y-parameters for 2D and 3D scan.
        In a 3D measurement, the y-parameters will be the "outer" sweep meaning for every y value all y values are swept and for each (y,y) value the bias is swept according to the set sweep parameters.

        Parameters
        ----------
        vec: array_likes
            An N-dimensional array that contains the sweep values.
        coordname: string
            The coordinate name to be created as data series in the .h5 file.
        set_obj: obj
            An callable object to execute with vec-values.
        unit: string
            The unit name to be used in data series in the .h5 file.
        dt: float, optional
            The sleep time between y-iterations.

        Returns
        -------
        None
        """
        # vec
        try:
            self._y_parameter = self.Coordinate(coordname, unit, np.array(vec, dtype=float), set_obj, dt)
            self._y_parameter.validate_parameters()
        except Exception as e:
            self._y_parameter = None
            raise e
    
    def _prepare_measurement_devices(self):
        """
        Perform all relevant device settings.
        This is a placeholder function and should be overwritten in the individual measurement scripts.
        """
        pass

    def _create_file_name(self, data):
        coordinates = set()
        self._dim = 0
        for d in data:
            for c in d.coordinates:
                coordinates.add(c.name.rstrip("_0123456789")) # removes indices like frequency_0 from the file name
            self._dim = max(self._dim, len(d.coordinates))  # if you have several 2D scans, the dimension is still 2D
        if not self.measurement_name:
            self.measurement_name = ", ".join(coordinates)
        self._file_name = '{}D_'.format(self._dim) + self.measurement_name.replace(' ', '').replace(',', '_')

    def _prepare_measurement_file(self, data, coords=()):
        """
        creates the output .h5-file with distinct dataset structures for each measurement type.
        at this point all measurement parameters are known and put in the output file
        All nacessary coordinates are alread included in the data instances, but you can supply a list of additional coords, which will be created.
        """
        for c in coords:
            if not isinstance(c, self.Coordinate):
                raise TypeError('{:s}:  {!s} is no valid coordinate object'.format(__name__, c))
        self._create_file_name(data)
        
        self._data_file = hdf.Data(name=self._file_name, mode='a')
        self._datasets = {}
        self._coordinates = {}
        for d in data:
            self._datasets[d.name] = d.create_dataset(self._data_file)
            for c in d.coordinates:
                self._coordinates[c.name] = c.create_dataset(self._data_file)  # it doesn't matter if you call create_dataset multiple times.
        for c in coords:
            self._coordinates[c.name] = c.create_dataset(self._data_file)  # the additional coordinates

        self._measurement_object.coordinates = list(self._coordinates.keys())
        self._measurement_object.data = list(self._datasets.keys())
        self._measurement_object.web_visible = self.web_visible
        
        self._measurement_object.instruments = qkit.instruments.get_instrument_names()
        self._measurement_object.sample = self._sample
        self._measurement_object.write_to_hdf(self._data_file)
        self._measurement_object.save()
        
        # write logfile and instrument settings
        self._settings = self._data_file.add_textlist('settings')
        settings = waf.get_instrument_settings(self._data_file.get_filepath())
        self._settings.append(settings)
        self._log = waf.open_log_file(self._data_file.get_filepath())

        if self._dim > 1:
            self._log_datasets = []
            for [func, name, unit, log_dtype] in self.log_functions:
                self._log_datasets.append([self._data_file.add_value_vector(name, x=data[0].coordinates[0].create_dataset(self._data_file), unit=unit,
                                                                            dtype=log_dtype), func])
        
        if self.comment:
            self._data_file.add_comment(self.comment)
    
    def _open_qviewkit(self, datasets=None):
        """
        Closes the old qvk process if needed and creates a new one.
        You can specify e.g. datasets=['amplitude','phase'] which will be openend by default and saved as an attribute to the h5 file
        as default, the self._datasets you created are opened.
        """
        if self.qviewkit_singleInstance and self.open_qviewkit and self._qvk_process:
            self._qvk_process.terminate()  # terminate an old qviewkit instance
        
        if 'default_ds' in self._data_file.hf.hf.attrs and datasets is None:
            datasets = list(self._data_file.hf.hf.attrs['default_ds'])
        if datasets is None:
            datasets = list(self._datasets.keys())
        self._data_file.hf.hf.attrs['default_ds'] = datasets
        
        if self.open_qviewkit:
            self._qvk_process = qviewkit.plot(self._data_file.get_filepath(), datasets=datasets)
    
    def _acquire_log_functions(self):
        for [ds, func] in self._log_datasets:
            ds.append([func()])
    
    def _end_measurement(self):
        """
        the data file is closed and filepath is printed
        """
        print(self._data_file.get_filepath())
        threading.Thread(target=qviewkit.save_plots, args=[self._data_file.get_filepath()]).start()
        self._data_file.close_file()
        waf.close_log_file(self._log)
        self.measurement_name = None
        qkit.flow.end()
