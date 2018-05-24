from __future__ import print_function

import qkit

from qkit.measure.measurement_class import Measurement
import qkit.measure.write_additional_files as waf
from qkit.storage import store as hdf
from qkit.gui.notebook.Progress_Bar import Progress_Bar

import sys
import time
import threading

import numpy as np
from scipy.optimize import curve_fit


class EVAP_Monitor(object):
    def __init__(self, quartz=None, ohmmeter=None, exp_name='', sample=None):
        self.quartz = quartz
        self.ohmmeter = ohmmeter

        self.exp_name = exp_name
        self._sample = sample

        self.comment = ''
        self.dirname = None

        self.x_set_obj = None
        self.y_set_obj = None

        self.progress_bar = True
        self._fit_resistance = False
        self._fit_every = 1
        self._fit_points = 5
        self._p0 = None

        self._plot_comment = ""

        # self.set_log_function()

        self.open_qviewkit = True
        self.qviewkit_singleInstance = False

        self._measurement_object = Measurement()
        self._measurement_object.measurement_type = 'evaporation'
        self._measurement_object.sample = self._sample

        self._qvk_process = False

        self._duration = 60.  # Duration of monitoring
        self._resolution = 0.5  # How often values should be taken

        self._target_resistance = 1000.
        self._target_thickness = 20.

    def set_duration(self, duration=60.):
        self._duration = duration

    def get_duration(self):
        return self._duration

    def set_resolution(self, resolution=0.5):
        self._resolution = resolution

    def get_resolution(self):
        return self._resolution

    def set_filmparameters(self, name=None, Rn=1000., d=20.):
        self._film = name  # TODO: should be stored somewhere --> Sample object
        self._target_resistance = Rn
        self._target_thickness = d

    def get_filmparameters(self):
        pass  # FIXME: How to format return?

    def ideal_resistance(self, thickness):
        return 1. / (thickness * (1. / self._target_resistance) / self._target_thickness)

    def ideal_trend(self):
        t = np.linspace(1, self._target_thickness, 300)
        return [t, self.ideal_resistance(t)]

    def set_fit(self, fit=False, fit_every=1, fit_points=5, p0=None):
        self._fit_resistance = fit
        self._fit_every = fit_every
        self._fit_points = fit_points
        self._p0 = p0

    def _reciprocal(self, thickness, cond_per_layer):
        return 1. / (thickness * cond_per_layer)

    def _fit_trend(self, t_points, R_points):
        popt, pcov = curve_fit(self._reciprocal, t_points, R_points, p0=self._p0)

        R_final = 1. / (self._target_thickness * popt[0])
        t_final = 1. / (self._target_resistance * popt[0])

        return [R_final, t_final]

    def _prepare_measurement_quartz(self):
        '''
        all the relevant settings from the quartz are updated and called
        '''
        # self.quartz.get_all()
        # self.quartz.get_frequency() # Store it somewhere
        pass

    def _prepare_measurement_ohmmeter(self):
        '''
        all the relevant settings from the ohmmeter are updated and called
        '''
        # self.ohmmeter.get_all()
        pass

    def _prepare_measurement_file(self):
        '''
        creates the output .h5-file with distinct dataset structures for each measurement type.
        at this point all measurement parameters are known and put in the output file
        '''

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

        if self._scan_time:
            self._time_coord = self._data_file.add_value_vector('time', x=None, unit='s')

            self._data_rate = self._data_file.add_value_vector('rate',
                                                               x=self._time_coord,
                                                               unit='nm/s',
                                                               save_timestamp=False)
            self._data_thickness = self._data_file.add_value_vector('thickness',
                                                                    x=self._time_coord,
                                                                    unit='nm',
                                                                    save_timestamp=False)
            self._data_resistance = self._data_file.add_value_vector('resistance',
                                                                     x=self._time_coord,
                                                                     unit='Ohm',
                                                                     save_timestamp=False)
            self._data_deviation_abs = self._data_file.add_value_vector('deviation_absolute',
                                                                        x=self._time_coord,
                                                                        unit='Ohm',
                                                                        save_timestamp=False)
            self._data_deviation_rel = self._data_file.add_value_vector('deviation_relative',
                                                                        x=self._time_coord,
                                                                        unit='relative',
                                                                        save_timestamp=False)
            # TODO: Add flow and pressure

            self._resist_view = self._data_file.add_view('resistance_thickness',
                                                         x=self._data_thickness,
                                                         y=self._data_resistance)

            self._thickness_coord = self._data_file.add_coordinate('thickness_coord', unit='nm')
            self._thickness_coord.add(self.ideal_trend()[0])

            self._data_ideal = self._data_file.add_value_vector('ideal_resistance',
                                                                x=self._thickness_coord,
                                                                unit='Ohm',
                                                                save_timestamp=False)
            self._data_ideal.append(self.ideal_trend()[1])

            self._resist_view.add(x=self._thickness_coord, y=self._data_ideal)

            self._deviation_abs_view = self._data_file.add_view('deviation_absolute',
                                                                x=self._data_thickness,
                                                                y=self._data_deviation_abs)
            self._deviation_rel_view = self._data_file.add_view('deviation_relative',
                                                                x=self._data_thickness,
                                                                y=self._data_deviation_rel)

            if self.comment:
                self._data_file.add_comment(self.comment)

            if self.qviewkit_singleInstance and self.open_qviewkit and self._qvk_process:
                self._qvk_process.terminate()  # terminate an old qviewkit instance

    def _write_settings_dataset(self):
        self._settings = self._data_file.add_textlist('settings')
        settings = waf.get_instrument_settings(self._data_file.get_filepath())
        self._settings.append(settings)

    def measure_timetrace(self, web_visible=True):
        '''
        measure method to record a single VNA timetrace, this only makes sense when span is set to 0 Hz!,
        tested only with KEYSIGHT E5071C ENA and its corresponding qkit driver
        LGruenhaupt 11/2016
        '''
        self._scan_1D = False
        self._scan_2D = False
        self._scan_3D = False
        self._scan_time = True

        self._measurement_object.measurement_func = 'measure_timetrace'  # FIXME: What is _measurement good for?
        self._measurement_object.x_axis = 'time'
        self._measurement_object.y_axis = ''
        self._measurement_object.z_axis = ''
        self._measurement_object.web_visible = web_visible  # FIXME: What is it good for?

        if not self.dirname:
            self.dirname = 'EVAP_timetrace'
        self._file_name = self.dirname.replace(' ', '').replace(',', '_')
        if self.exp_name:
            self._file_name += '_' + self.exp_name

        self.x_vec = np.arange(0, self._duration, self._resolution)

        self._prepare_measurement_quartz()
        self._prepare_measurement_ohmmeter()
        self._prepare_measurement_file()

        if self.progress_bar: self._p = Progress_Bar(self._duration / self._resolution,
                                                     'EVAP_timetrace ' + self.dirname,
                                                     self._resolution)  # FIXME: Doesn't make much sense...

        print('recording timetrace...')
        sys.stdout.flush()

        qt.mstart()
        try:
            """
            loop: x_obj with parameters from x_vec
            """

            t0 = time.time()  # FIXME: Windows has limitations on time precision (about 16ms)

            for i, x in enumerate(self.x_vec):
                ti = t0 + float(i) * self._resolution

                while time.time() < ti:
                    time.sleep(0.05)
                # FIXME: Use flow.sleep? Code there looks rather bulky and maybe not suited for high speed measurements

                self._time_coord.append(time.time() - t0)

                resistance = self.ohmmeter.get_resistance()
                rate = self.quartz.get_rate(nm=True)
                thickness = self.quartz.get_thickness(nm=True)

                self._data_rate.append(resistance)
                self._data_resistance.append(rate)
                self._data_thickness.append(thickness)

                deviation_abs = resistance - self.ideal_resistance(thickness)
                deviation_rel = deviation_abs / self._target_resistance

                self._data_deviation_abs.append(deviation_abs)
                self._data_deviation_rel.append(deviation_rel)

                # if (self._fit_resistance and i % self._fit_every == 0 and len(
                #        self._data_resistance[:]) >= self._fit_points):
                #    estimation = self._fit_trend(self._data_thickness[-self._fit_points:None],
                #                                 self._data_resistance[-self._fit_points:None])
                #    print("Estimated final resistance: " + str(estimation[0]) +
                #          "Estimated ideal thickness: " + str(estimation[1]), end='\r')

                if self.progress_bar:
                    self._p.iterate()

        except IOError as e:
            print(e.__doc__)
            print(e.message)

        finally:
            self._end_measurement()
            qt.mend()

    def _end_measurement(self):
        '''
        the data file is closed and filepath is printed
        '''
        print(self._data_file.get_filepath())
        # qviewkit.save_plots(self._data_file.get_filepath(),comment=self._plot_comment) #old version where we have to wait for the plots
        t = threading.Thread(target=qviewkit.save_plots,
                             args=[self._data_file.get_filepath(), self._plot_comment])
        t.start()
        self._data_file.close_file()
        waf.close_log_file(self._log)
        self.dirname = None


class EVAP_Control(object):
    pass
