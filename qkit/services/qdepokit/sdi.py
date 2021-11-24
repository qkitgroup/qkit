# sdi.py Sputter Deposition Investigator
# module to monitor and control sputter deposition
# derived from measure/spectroscopy.py by AS@KIT and others
# YS,JNV,HR@KIT 05/2018 

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

from __future__ import print_function

import qkit

from qkit.measure.measurement_class import Measurement
import qkit.measure.write_additional_files as waf
from qkit.storage import store as hdf
from qkit.gui.notebook.Progress_Bar import Progress_Bar
from qkit.gui.notebook.Stopwatch import Stopwatch
from qkit.gui.plot import plot as qviewkit

import sys
import time
import threading
from threading import Thread

try:  # In Python 2 the following command works only with python-future installed
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty

import numpy as np
from scipy.optimize import curve_fit


class SputterMonitor(object):
    """
    Sputter monitoring class, derived from spectroscopy.py
    monitors and stores sputter parameters live during deposition
    facilitates dynamic flow adjustment

    Example:
        m = SPUTTER_Monitor(quartz, ohmmeter, film_name, sample)
        m.set_filmparameters() ... see in corresponding docstring
        m.monitor_depo()

    Args:
        quartz (Instrument): The quartz oscillator instrument measuring thickness and rate.
        ohmmeter (Instrument): The resistance measurement instrument.
        mfc (Instrument): The mass flow controller instrument.
        film_name (str): A name can be given, that is added to the directory and filename.
        sample (Sample): A sample object can be given that is stored in the h5 file.

    Attributes:
        Should be listed here... Until then, use tabbing.
    """

    def __init__(self, quartz=None, ohmmeter=None, mfc=None, film_name='', sample=None):
        self.quartz = quartz
        self.ohmmeter = ohmmeter
        self.mfc = mfc

        self.film_name = film_name
        self._sample = sample

        self.comment = ''
        self.dirname = None

        self.x_set_obj = None
        self.y_set_obj = None

        self.progress_bar = False
        self.stopwatch = False

        self._show_ideal = False

        self._fit_resistance = False
        self._fit_every = 1
        self._fit_points = 5
        self._p0 = None

        self._reference_uid = None

        self._plot_comment = ""

        self.open_qviewkit = True
        self.qviewkit_singleInstance = False

        self._measurement_object = Measurement()
        self._measurement_object.measurement_type = 'sputter_deposition'
        self._measurement_object.sample = self._sample

        self._qvk_process = True

        self._duration = 60.  # Duration of monitoring
        self._resolution = 2.  # How often values should be taken

        self._target_resistance = 1000.
        self._target_thickness = 20.
        self._target_marker = False

        self._depmon_queue = Queue()  # for communication with the depmon thread

    def set_duration(self, duration=60.):
        """
        Set the duration for the monitoring. Better too long than too short.

        Args:
            duration (float): Monitoring duration in seconds.
        """
        self._duration = duration

    def get_duration(self):
        """
        Get the duration for the monitoring.

        Returns:
            duration (float): Monitoring duration in seconds.
        """
        return self._duration

    def set_resolution(self, resolution=2.0):
        """
        Set the resolution for the monitoring.
        Every x second, the parameters will be read and stored.

        Args:
            resolution (float): Monitoring resolution in seconds.
        """
        self._resolution = resolution

    def get_resolution(self):
        """
        Get the resolution for the monitoring.
        Every x second, the parameters will be read and stored.

        Returns:
            resolution (float): Monitoring resolution in seconds.
        """
        return self._resolution

    def set_filmparameters(self, resistance=1000., thickness=20., target_marker=False):
        """
        Set the target parameters of the film to be deposited.
        They are used to calculate the ideal trend of the measured parameters and their deviation from the ideal.

        Args:
            resistance (float): The target sheet resistance in Ohm.
            thickness (float): The target thickness in nm.
            target_marker (bool): Display a cross marking the target resistance and thickness.
        """
        self._target_resistance = resistance
        self._target_thickness = thickness
        self._target_marker = target_marker

    def get_filmparameters(self):
        """
        Get the set film parameters.

        Returns:
            Tuple containing:
                [0]: target_resistance (float): The target sheet resistance in Ohm.
                [1]: target_thickness (float): The target thickness in nm.
        """
        return self._target_resistance, self._target_thickness

    def ideal_resistance(self, thickness):
        """
        Calculates the ideal resistance at a given thickness depending on the set film parameters.

        Args:
            thickness (float): Film thickness in nm for which the ideal resistance should be calculated.

        Returns:
            The ideal resistance as a float.
        """
        try:
            return 1. / (thickness * (1. / self._target_resistance) / self._target_thickness)
        except:
            return np.nan

    def ideal_trend(self):
        """
        Calculates a list of ideal resistances that is used as comparison in a view together with the real values.
        """
        t = np.linspace(1, self._target_thickness, 300)
        return [t, self.ideal_resistance(t)]

    def set_fit(self, fit=False, fit_every=1, fit_points=5, p0=None):
        """
        Settings for the fit used to estimate final resistance at target thickness and thickness at target resistance.

        Args:
            fit (bool): Turn on the fit.
            fit_every (int): Fit after every x measurement.
            fit_points (int): Fit to the last x points.
            p0 (list): Provide initial values for the curvefit.
        """
        self._fit_resistance = fit
        self._fit_every = fit_every
        self._fit_points = fit_points
        self._p0 = p0

    def set_reference_uid(self, uid=None):
        """
        Set a UID to be shown as a reference trace in the "resistance_thickness" view.

        Args:
            uid (str): The UID of the h5 file from which the resistance and thickness data is to be displayed.
        """
        try:
            ref = hdf.Data(qkit.fid[uid])
            self._ref_resistance = ref.data.resistance[:]
            self._ref_thickness = ref.data.thickness[:]
            self._reference_uid = uid
            ref.close()
            return self._reference_uid
        except:
            self._reference_uid = None
            return "Invalid UID"

    def set_resistance_4W(self, four_wire=False):
        """
        Sets 2 (default) or 4 wire measurement mode, if the device supports it.

        Args:
            four_wire = False
        """
        self.ohmmeter.set_measure_4W(four_wire)

    def get_rate(self, test_thickness):
        """
        Tests deposition rate.

        Args:
            test_thickness (in nm)
        """
        self.quartz.set_timer_zero()
        self.quartz.set_thickness_zero()
        time.sleep(3)
        while self.quartz.get_thickness() < test_thickness * 1e-2:
            time.sleep(1)
        mins, secs = self.quartz.get_time().split(':')
        t = 60 * float(mins) + float(secs)
        rate = test_thickness / t
        return rate, t

    def _theory(self, thickness, thickness_start, conductivity, cond_per_layer):
        """
        Calculate a prediction for the resistance at a certain film thickness,
        given the current thickness, current conductivity and added conductivity per layer.

        Args:
            thickness (float): Film thickness for which the resistance shall be predicted
            thickness_start (float): Film thickness at the start of the prediction.
            conductivity (float): Film conductivity at the start of the prediction.
            cond_per_layer (float): Added conductivity per layer for the remaining film growth.

        Returns:
            The projected film resistance (float).
        """
        t_added = thickness - thickness_start
        try:
            return 1. / (conductivity + t_added * cond_per_layer)
        except:
            return np.nan

    def _linear(self, x, a, b):
        """
        Helper function providing a linear fitting function.
        """
        return a * x + b

    def _fit_layer(self, t_points, R_points):
        """
        Fit the changing film resistance to extract the gained conductivity per layer.
        This is then used to project the final film resistance with the provided target film parameters.

        Args:
            t_points (numpy array): Thickness data from which the conductivity per layer is to be extracted.
            R_points (numpy array): Resistance data from which the conductivity per layer is to be extracted.

        Returns:
            Tuple containing:
                [0]: t_final (float): The predicted thickness at which the target resistance will be reached.
                [1]: R_final (float): The predicted resistance that will be reached at the target thickness.
                [2]: popt[0] (float): Conductivity per layer as obtained by linear fit.
        """
        # ToDo: Store all fits, Store time of fit to sync it to other datasets, revise theory.
        for i in R_points:
            if i == 0:
                return [np.nan, np.nan, np.nan]

        try:
            c_target = 1. / self._target_resistance
            c_points = 1. / R_points
            popt, _ = curve_fit(self._linear, t_points, c_points, p0=self._p0)
            R_final = self._theory(self._target_thickness, t_points[0], c_points[0], popt[0])
            t_final = ((c_target - c_points[-1]) / popt[0]) + t_points[-1]
            return [t_final, R_final, popt[0]]

        except:
            return [np.nan, np.nan, np.nan]

    def _reciprocal(self, thickness, cond_per_layer):
        """
        Function used by the curvefit routine.

        Args:
            thickness: Film thickness in nm.
            cond_per_layer: Film conductance per layer.

        Returns:
            The resistance for the given parameters as a float.
        """
        try:
            return 1. / (thickness * cond_per_layer)
        except:
            return np.nan

    def _fit_trend(self, t_points, R_points):
        """
        Do the fit used to estimate final resistance at target thickness and thickness at target resistance.

        Args:
            t_points: The last x points of film thickness in nm.
            R_points: The last x points of film resistivity in Ohm.

        Returns:
            List of [R_final, t_final] with
            R_final (float): Estimated final resistance at target thickness.
            t_final (float): Estimated thickness at target resistance.
        """
        for i in t_points:
            if i == 0:
                return [np.nan, np.nan]

        try:
            self._popt, _ = curve_fit(self._reciprocal, t_points, R_points, p0=self._p0)

            t_final = 1. / (self._target_resistance * self._popt[0])
            R_final = 1. / (self._target_thickness * self._popt[0])

            return [t_final, R_final]

        except:
            return [np.nan, np.nan]

    def _prepare_measurement_quartz(self):
        """
        All the relevant settings from the quartz are updated and called.
        """
        # self.quartz.get_all()
        # self.quartz.get_frequency() # Store it somewhere
        pass

    def _prepare_measurement_ohmmeter(self):
        """
        All the relevant settings from the ohmmeter are updated and called.
        """
        # self.ohmmeter.get_all()
        pass

    def _prepare_measurement_mfc(self):
        """
        All the relevant settings from the ohmmeter are updated and called.
        """
        # self.mfc.get_all()
        self.Ar_channel = self.mfc.predef_channels['Ar']
        self.ArO_channel = self.mfc.predef_channels['ArO']

        pass

    def _prepare_monitoring_file(self):
        """
        Creates the output .h5-file with distinct the required datasets and views.
        At this point all measurement parameters are known and put in the output file.
        """
        self._data_file = hdf.Data(name=self._file_name, mode='a')
        self._measurement_object.uuid = self._data_file._uuid
        self._measurement_object.hdf_relpath = self._data_file._relpath
        self._measurement_object.instruments = qkit.instruments.get_instrument_names()

        self._measurement_object.save()
        self._mo = self._data_file.add_textlist('measurement')
        self._mo.append(self._measurement_object.get_JSON())

        # write logfile and instrument settings
        self._write_settings_dataset()
        self._log = waf.open_log_file(self._data_file.get_filepath())

        '''
        Time record
        '''
        self._data_time = self._data_file.add_value_vector('time', x=None, unit='s')

        '''
        Quartz datasets
        '''
        self._data_rate = self._data_file.add_value_vector('rate',
                                                           x=self._data_time,
                                                           unit='nm/s',
                                                           save_timestamp=False)
        self._data_thickness = self._data_file.add_value_vector('thickness',
                                                                x=self._data_time,
                                                                unit='nm',
                                                                save_timestamp=False)

        '''
        Ohmmeter datasets
        '''
        self._data_resistance = self._data_file.add_value_vector('resistance',
                                                                 x=self._data_time,
                                                                 unit='Ohm',
                                                                 save_timestamp=False)
        self._data_conductance = self._data_file.add_value_vector('conductance',
                                                                  x=self._data_time,
                                                                  unit='S',
                                                                  save_timestamp=False)
        self._data_deviation_abs = self._data_file.add_value_vector('deviation_absolute',
                                                                    x=self._data_time,
                                                                    unit='Ohm',
                                                                    save_timestamp=False)
        self._data_deviation_rel = self._data_file.add_value_vector('deviation_relative',
                                                                    x=self._data_time,
                                                                    unit='relative',
                                                                    save_timestamp=False)

        '''
        MFC datasets
        '''
        # FIXME: units?
        if self.mfc:
            self._data_pressure = self._data_file.add_value_vector('pressure',
                                                                   x=self._data_time,
                                                                   unit='ubar',
                                                                   save_timestamp=False)
            self._data_Ar_flow = self._data_file.add_value_vector('Ar_flow',
                                                                  x=self._data_time,
                                                                  unit='sccm',
                                                                  save_timestamp=False)
            self._data_ArO_flow = self._data_file.add_value_vector('ArO_flow',
                                                                   x=self._data_time,
                                                                   unit='sccm',
                                                                   save_timestamp=False)

        '''
        Calculate ideal trend and create record
        '''
        self._thickness_coord = self._data_file.add_coordinate('thickness_coord', unit='nm')
        self._thickness_coord.add(self.ideal_trend()[0])
        if self._show_ideal:
            self._data_ideal = self._data_file.add_value_vector('ideal_resistance',
                                                                x=self._thickness_coord,
                                                                unit='Ohm',
                                                                save_timestamp=False)
            self._data_ideal.append(self.ideal_trend()[1])

        '''
        Create target marker
        '''
        if self._target_marker:
            self._target_thickness_line = self._data_file.add_value_vector('target_thickness',
                                                                           x=None,
                                                                           unit='nm',
                                                                           save_timestamp=False)
            self._target_thickness_line.append([0.8 * self._target_thickness,
                                                self._target_thickness, self._target_thickness,
                                                self._target_thickness, self._target_thickness,
                                                1.2 * self._target_thickness])
            self._target_resistance_line = self._data_file.add_value_vector('target_resistance',
                                                                            x=None,
                                                                            unit='Ohm',
                                                                            save_timestamp=False)
            self._target_resistance_line.append([self._target_resistance, self._target_resistance,
                                                 1.2 * self._target_resistance, 0.8 * self._target_resistance,
                                                 self._target_resistance, self._target_resistance])
            self._target_conductance_line = self._data_file.add_value_vector('target_conductance',
                                                                             x=None,
                                                                             unit='S',
                                                                             save_timestamp=False)
            self._target_conductance_line.append([1. / self._target_resistance, 1. / self._target_resistance,
                                                  1. / 1.2 / self._target_resistance,
                                                  1. / 0.8 / self._target_resistance,
                                                  1. / self._target_resistance, 1. / self._target_resistance])

        '''
        Estimation datasets
        '''
        if self._fit_resistance:
            self._thickness_estimation = self._data_file.add_value_vector('thickness_estimation',
                                                                          x=None,
                                                                          unit='nm',
                                                                          save_timestamp=False)
            self._resistance_estimation = self._data_file.add_value_vector('resistance_estimation',
                                                                           x=None,
                                                                           unit='Ohm',
                                                                           save_timestamp=False)
            self._last_resistance_fit = self._data_file.add_value_vector('last_resistance_fit',
                                                                         x=None,
                                                                         unit='Ohm',
                                                                         save_timestamp=False)

        '''
        Reference dataset
        '''
        if not self._reference_uid == None:
            self._thickness_reference = self._data_file.add_value_vector('thickness_reference',
                                                                         x=None,
                                                                         unit='nm',
                                                                         save_timestamp=False)
            self._thickness_reference.append(self._ref_thickness)
            self._resistance_reference = self._data_file.add_value_vector('reference_' + self._reference_uid,
                                                                          x=None,
                                                                          unit='Ohm',
                                                                          save_timestamp=False)
            self._resistance_reference.append(self._ref_resistance)

        '''
        Create Views
        '''
        self._resist_view = self._data_file.add_view('resistance_thickness',
                                                     x=self._data_thickness,
                                                     y=self._data_resistance)
        if self._show_ideal:
            self._resist_view.add(x=self._thickness_coord, y=self._data_ideal)
        if self._target_marker:
            self._resist_view.add(x=self._target_thickness_line, y=self._target_resistance_line)
        if not self._reference_uid == None:
            self._resist_view.add(x=self._thickness_reference, y=self._resistance_reference)
        if self._fit_resistance:
            self._resist_view.add(x=self._thickness_coord, y=self._last_resistance_fit)

        self._conductance_view = self._data_file.add_view('conductance_thickness',
                                                          x=self._data_thickness,
                                                          y=self._data_conductance)
        if self._target_marker:
            self._conductance_view.add(x=self._target_thickness_line, y=self._target_conductance_line)

        self._deviation_abs_view = self._data_file.add_view('deviation_absolute',
                                                            x=self._data_thickness,
                                                            y=self._data_deviation_abs)

        self._deviation_rel_view = self._data_file.add_view('deviation_relative',
                                                            x=self._data_thickness,
                                                            y=self._data_deviation_rel)

        '''
        Create comment
        '''
        if self.comment:
            self._data_file.add_comment(self.comment)

        '''
        Open GUI
        '''
        if self.qviewkit_singleInstance and self.open_qviewkit and self._qvk_process:
            self._qvk_process.terminate()  # terminate an old qviewkit instance

    def _write_settings_dataset(self):
        """
        Writes a dataset containing the settings of the measurement instruments.
        """
        self._settings = self._data_file.add_textlist('settings')
        settings = waf.get_instrument_settings(self._data_file.get_filepath())
        self._settings.append(settings)

    def _init_depmon(self):
        """
        Initializes the measurement, the required files and instruments.
        Should only be called by the main functions monitor_depo or start_depmon.
        """
        self._measurement_object.measurement_func = 'sputter_monitoring'
        self._measurement_object.x_axis = 'time'
        self._measurement_object.y_axis = ''
        self._measurement_object.z_axis = ''
        self._measurement_object.web_visible = True

        if not self.dirname:
            self.dirname = 'SPUTTER_monitoring'
        self._file_name = self.dirname.replace(' ', '').replace(',', '_')
        if self.film_name:
            self._file_name += '_' + self.film_name

        self.x_vec = np.arange(0, self._duration, self._resolution)

        self._prepare_measurement_quartz()
        self._prepare_measurement_ohmmeter()
        if self.mfc:
            self._prepare_measurement_mfc()

        self._prepare_monitoring_file()

    def _acquire(self, mon_data):
        """
        Acquires and stores current information from the instruments.
        Should only be called by main functions monitor_depo or start_depmon.
        """
        self._data_time.append(time.time() - mon_data.t0)

        # mon_data.resistance.append(self.ohmmeter.get_resistance())
        mon_data.resistance = np.append(mon_data.resistance, self.ohmmeter.get_resistance())
        if self.quartz:
            rate = self.quartz.get_rate(nm=True)
            # mon_data.thickness.append(self.quartz.get_thickness(nm=True))
            mon_data.thickness = np.append(mon_data.thickness, self.quartz.get_thickness(nm=True))
        if self.mfc:
            pressure = self.mfc.get_pressure()
            Ar_flow = self.mfc.get_flow(self.Ar_channel)
            ArO_flow = self.mfc.get_flow(self.ArO_channel)

        if mon_data.resistance[-1] > 1.e9:
            mon_data.resistance[-1] = np.nan
        self._data_resistance.append(mon_data.resistance[-1])
        if not mon_data.resistance[-1] == 0:
            self._data_conductance.append(1. / mon_data.resistance[-1])
        else:
            self._data_conductance.append(np.nan)
        if self.quartz:
            self._data_rate.append(rate)
            self._data_thickness.append(mon_data.thickness[-1])
        if self.mfc:
            self._data_pressure.append(pressure)
            self._data_Ar_flow.append(Ar_flow)
            self._data_ArO_flow.append(ArO_flow)
        if self.quartz:
            deviation_abs = mon_data.resistance[-1] - self.ideal_resistance(mon_data.thickness[-1])
            deviation_rel = deviation_abs / self._target_resistance

            self._data_deviation_abs.append(deviation_abs)
            self._data_deviation_rel.append(deviation_rel)

        if ((self._fit_resistance) and (mon_data.it % self._fit_every == 0) and (
                len(mon_data.resistance) >= self._fit_points)):
            """
            # OLD ROUTINE
            estimation = self._fit_trend(mon_data.thickness[-self._fit_points:None],
                                         mon_data.resistance[-self._fit_points:None])
            self._thickness_estimation.append(estimation[0])
            self._resistance_estimation.append(estimation[1])
            self._last_resistance_fit.append(self._reciprocal(self.ideal_trend()[0],self._popt[0]), reset=True)
            """
            estimation = self._fit_layer(mon_data.thickness[-self._fit_points:None],
                                         mon_data.resistance[-self._fit_points:None])
            self._thickness_estimation.append(estimation[0])
            self._resistance_estimation.append(estimation[1])
            self._last_resistance_fit.append(self._theory(self.ideal_trend()[0], mon_data.thickness[-1],
                                                          1. / mon_data.resistance[-1], estimation[2]),
                                             reset=True)

    def monitor_depo(self):
        """
        Main sputter deposition monitoring function.

        Consider using the threaded version by calling start_depmon().

        Records the film resistance, thickness and deposition rate live during the sputter process.
        Stores everything into a h5 file.
        Provides measures to estimate the resulting resistance of the final film and thereby
        facilitates live adjustments to the sputter parameters.

        Note:
            set_duration and set_resolution should be called before to set the monitoring length and time resolution.
            set_filmparameters should be called before to provide the actual target values.
        """
        
        self._init_depmon()

        if self.progress_bar:
            self._p = Progress_Bar(self._duration / self._resolution,
                                   'EVAP_timetrace ' + self.dirname,
                                   self._resolution)  # FIXME: Doesn't make much sense...
        
        if self.stopwatch:
            self._sw = Stopwatch()

        print('Monitoring deposition...')
        sys.stdout.flush()

        if self.open_qviewkit:
            self._qvk_process = qviewkit.plot(self._data_file.get_filepath(), datasets=['views/resistance_thickness'])

        try:
            """
            Initialize the data lists.
            """

            class MonData(object):
                resistance = np.array([])
                thickness = np.array([])

            mon_data = MonData()

            """
            Main loop:
            """
            mon_data.t0 = time.time()  # note: Windows has limitations on time precision (about 16ms)
            for mon_data.it, _ in enumerate(self.x_vec):
                self._acquire(mon_data)

                if self.progress_bar:
                    self._p.iterate()
                
                if self.stopwatch:
                    self._sw.update(time.time() - mon_data.t0)

                # calculate the time when the next iteration should take place
                ti = mon_data.t0 + (float(mon_data.it) + 1) * self._resolution
                # wait until the total dt(iteration) has elapsed
                while time.time() < ti:
                    time.sleep(0.05)

        except KeyboardInterrupt:
            print('Monitoring interrupted by user.')

        except Exception as e:
            print(e)
            print(e.__doc__)
            print(e.message)

        finally:
            self._end_measurement()

    def _monitor_depo_bg(self):
        """
        Main sputter deposition monitoring function, threaded version

        Should only be called by main function start_depmon.

        Records the film resistance, thickness and deposition rate live during the sputter process.
        Stores everything into a h5 file.
        Provides measures to estimate the resulting resistance of the final film and thereby
        facilitates live adjustments to the sputter parameters.

        Note:
            set_duration and set_resolution should be called before to set the monitoring length and time resolution.
            set_filmparameters should be called before to provide the actual target values.
        """

        class StopPauseExeption(Exception):
            pass

        class StartPauseExeption(Exception):
            pass

        """
        A few boilerplate functions for the thread management:
        continue, stop, status, etc...
        """

        def stop():
            raise StopIteration

        def do_nothing():
            pass

        def status():
            self._depmon_queue.put(loop_status)

        def cont():
            raise StopPauseExeption

        def pause():
            raise StartPauseExeption

        loop_status = 0
        tasks = {}
        tasks[0] = stop
        tasks[1] = do_nothing
        tasks[2] = status
        tasks[3] = pause
        tasks[4] = cont

        """
        Initialize the data lists.
        """

        class MonData(object):
            resistance = np.array([])
            thickness = np.array([])

        mon_data = MonData()

        """
        Main loop:
        """
        mon_data.it = 0
        mon_data.t0 = time.time()  # note: Windows has limitations on time precision (about 16ms)?
        while True:
            self._acquire(mon_data)
                
            if self.stopwatch:
                self._sw.update(time.time() - mon_data.t0)

            # Handle external commands
            try:
                tasks.get(self._depmon_queue.get(False), do_nothing)()
                self._depmon_queue.task_done()
            except Empty:
                pass
            except StartPauseExeption:
                print('monitoring paused')
                while True:
                    try:
                        time.sleep(0.1)
                        tasks.get(self._depmon_queue.get(False), do_nothing)()
                        self._depmon_queue.task_done()
                    except StopPauseExeption:
                        print('monitoring restarted')
                        break
                    except Empty:
                        pass
            except StopPauseExeption:
                pass
            except StopIteration:
                break

            # calculate the time when the next iteration should take place
            mon_data.it += 1
            ti = mon_data.t0 + (float(mon_data.it)) * self._resolution
            loop_status = ti  # for now we simply return the runtime
            # wait until the total dt(iteration) has elapsed
            while time.time() < ti:
                time.sleep(0.05)

        self._end_measurement()

    def start_depmon(self):
        """
        Starts the main sputter deposition monitoring function background process (depmon).

        Records the film resistance, thickness and deposition rate live during the sputter process.
        Stores everything into a h5 file.
        Provides measures to estimate the resulting resistance of the final film and thereby
        facilitates live adjustments to the sputter parameters.

        Note:
            set_duration and set_resolution should be called before to set the monitoring length and time resolution.
            set_filmparameters should be called before to provide the actual target values.

        Hint:
            Check with 'list_depmon_threads()'
            Stop with 'stop_depmon()'
        """
        print('Monitoring deposition...')
        sys.stdout.flush()

        self._init_depmon()
        
        if self.stopwatch:
            self._sw = Stopwatch()

        if self.open_qviewkit:
            self._qvk_process = qviewkit.plot(self._data_file.get_filepath(), datasets=['views/resistance_thickness'],
                                              refresh=1.)

        self._depmon = Thread(target=self._monitor_depo_bg, name="depmon-1")
        self._depmon.daemon = True
        self._depmon.start()

    def stop_depmon(self):
        """
        Stop the deposition monitoring thread.
        Can be executed several times if more than one monitoring thread is running.

        Hint:
            Check with 'list_depmon_threads()'
        """
        self._depmon_queue.put(0)

    def status_depmon(self):
        """
        Give a heartbeat of the deposition monitoring thread (in the moment just the runtime).
        """
        self._depmon_queue.put(2)
        print(self._depmon_queue.get())
        self._depmon_queue.task_done()

    def pause_depmon(self):
        print('Pause Monitoring deposition...')
        self._depmon_queue.put(3)

    def continue_depmon(self):
        print('Continue Monitoring deposition...')
        self._depmon_queue.put(4)

    def list_depmon_threads(self):
        """
        List all bg deposition monitoring threads.
        """
        for thread in threading.enumerate():
            if thread.getName()[:3] == "dep":
                print(thread)

    def _end_measurement(self):
        """
        The data file is closed and file path is printed.
        """
        print(self._data_file.get_filepath())
        # qviewkit.save_plots(self._data_file.get_filepath(),comment=self._plot_comment)
        # #old version where we have to wait for the plots
        t = threading.Thread(target=qviewkit.save_plots,
                             args=[self._data_file.get_filepath(), self._plot_comment])
        t.start()
        self._data_file.close_file()
        waf.close_log_file(self._log)
        self.dirname = None

    # FIXME: Use flow.sleep? Code there looks rather bulky and maybe not suited for high speed measurements


class SputterControl(object):
    pass
