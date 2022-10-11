# spectroscopy.py spectroscopy measurement class for use with a vector network analyzer
# JB/MP/AS@KIT 04/2015, 08/2015, 01/2016

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
from time import time

import numpy as np

import qkit

if qkit.module_available("matplotlib"):
    import matplotlib.pylab as plt
if qkit.module_available("scipy"):
    from scipy.optimize import curve_fit
    from scipy.interpolate import interp1d, UnivariateSpline
from qkit.analysis.resonator import Resonator as resonator
from qkit.gui.notebook.Progress_Bar import Progress_Bar
from qkit.measure.measurement_base import MeasureBase


##################################################################

class spectrum(MeasureBase):
    """
    Class for spectroscopy measurements with a VNA
    usage:
    m = spectrum(vna=vna1, sample=yoursample)

    m.set_x_parameters(arange(-0.05,0.05,0.01),'flux_coil_current',coil.set_current, unit = 'mA')  outer scan in 3D
    m.set_y_parameters(arange(4e9,7e9,10e6),'excitation_frequency',mw_src1.set_frequency, unit = 'Hz')

    m.landscape.generate_fit_function_xy(...) for 3D scan, can be called several times and appends the current landscape
    m.landscape.generate_fit_function_xz(...) for 2D or 3D scan, adjusts the vna freqs with respect to x

    m.measure_XX()
    """

    def __init__(self, vna, sample=None):
        super(spectrum, self).__init__(sample)
        
        self.vna = vna
        self.averaging_start_ready = "start_measurement" in self.vna.get_function_names() and "ready" in self.vna.get_function_names()
        if not self.averaging_start_ready: logging.warning(
                __name__ + ': With your VNA instrument driver (' + self.vna.get_type() + '), I can not see when a measurement is complete. So I only wait for a specific time and hope the VNA has finished. Please consider implemeting the necessary functions into your driver.')
        
        self.landscape = Landscape(vna=vna, spec=self)
        self._fit_resonator = False
        self._measurement_object.measurement_type = 'SpectroscopyMeasurement'
        self._views = []
        self._scan_time = False
        self._segments = [] # bool([]) == False
    
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
        super(spectrum, self).set_x_parameters(vec, coordname, set_obj, unit, dt)
        if self.landscape.xylandscapes:
            self.landscape.delete_landscape_function_xy()
            logging.warning('xy landscape has been deleted')
        if self.landscape.xzlandscape_func:
            self.landscape.delete_landscape_function_xz()
            logging.warning('xz landscape has been deleted')
    
    def set_y_parameters(self, vec, coordname, set_obj, unit, dt=None):
        """
        Sets y-parameters for 2D and 3D scan.
        In a 3D measurement, the y-parameters will be the "inner" sweep meaning for every x value all y values are swept

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
        super(spectrum, self).set_y_parameters(vec, coordname, set_obj, unit, dt)
        if self.landscape.xylandscapes:
            self.landscape.delete_landscape_function_xy()
            logging.warning('xy landscape has been deleted')
        if self.landscape.xzlandscape_func:
            self.landscape.delete_landscape_function_xz()
            logging.warning('xz landscape has been deleted. You can switch this off if you whish.')
    
    def _prepare_measurement_devices(self):
        """
        all the relevant settings from the vna are updated and called
        """
        self.vna.get_all()
        self._nop = self.vna.get_nop()
        self._sweeptime_averages = self.vna.get_sweeptime_averages()
        try:
            self._segments = self.vna.get_segments()
        except AttributeError:
            self._segments = []
        if self._dim == 1 or not self.landscape.xzlandscape_func:  # normal scan
            self._freqpoints = self.vna.get_freqpoints()
        else:
            self._freqpoints = self.landscape.get_freqpoints_xz()
        if self.averaging_start_ready:
            self.vna.pre_measurement()

    # def _prepare_measurement_file_(self):
    #
    #     if not self._scan_time:
    #         self._data_freq = self._data_file.add_coordinate('frequency', unit='Hz')
    #         self._data_freq.add(self._freqpoints)
    #
    #     if self._scan_2D:
    #         if self._nop < 10:
    #             """creates view: plot middle point vs x-parameter, for qubit measurements"""
    #             self._views = [self._data_file.add_view("amplitude_midpoint", x=self._data_x, y=self._data_amp,
    #                                                     view_params=dict(transpose=True, default_trace=self._nop // 2, linecolors=[(200, 200, 100)])),
    #                            self._data_file.add_view("phase_midpoint", x=self._data_x, y=self._data_pha,
    #                                                     view_params=dict(transpose=True, default_trace=self._nop // 2, linecolors=[(200, 200, 100)]))]
    #
    #     if self._scan_time:
    #         self._data_x = self._data_file.add_coordinate('trace_number', unit='')
    #         self._data_x.add(np.arange(0, self.number_of_timetraces, 1))
    #
    #         self._data_amp = self._data_file.add_value_matrix('amplitude', x=self._data_x, y=self._data_time, unit='lin. mag.', save_timestamp=False)
    #         self._data_pha = self._data_file.add_value_matrix('phase', x=self._data_x, y=self._data_time, unit='rad.', save_timestamp=False)
    
    def measure_1D(self, rescan=True):
        """
        measure method to record a single (averaged) VNA trace, S11 or S21 according to the setting on the VNA
        rescan: If True (default), the averages on the VNA are cleared and a new measurement is started.
                If False, it will directly take the data from the VNA without waiting.
        """
        self._dim =1
        self._measurement_object.measurement_func = 'measure_1D'
        
        self._prepare_measurement_devices()
        if self._segments:
            f =  [self.Coordinate('frequency_%i' % i, unit='Hz', values=self._freqpoints[0 if i == 0 else self._segments[i - 1]:self._segments[i]]) for i in range(len(self._segments))]
            self._prepare_measurement_file(
                    [self.Data(P[0] % i, [f[i]], P[1], save_timestamp=P[2] and not i)
                     for i in range(len(self._segments)) for P in [["amplitude_%i","arb. unit",True],["phase_%i","rad",False],["real_%i","",False],["imag_%i","",False]]])
        else:
            f = self.Coordinate('frequency', unit='Hz', values=self._freqpoints)
    
            self._prepare_measurement_file([self.Data("real", [f], ""), self.Data("imag", [f], ""), self.Data("amplitude", [f], "arb. unit", save_timestamp=True),
                self.Data("phase", [f], "rad")])
        
        self._open_qviewkit(datasets=[] if len(self._segments)>4 else None)
        
        qkit.flow.start()
        if rescan:
            self._pb = Progress_Bar(self.vna.get_averages(), self.measurement_name, self.vna.get_sweeptime(), dummy=not self.progress_bar)
            if self.averaging_start_ready:
                self.vna.start_measurement()
                ti = time()
                qkit.flow.sleep(.2)
                while not self.vna.ready():
                    if time() - ti > self.vna.get_sweeptime(query=False):
                        self._pb.iterate()
                        ti = time()
                    qkit.flow.sleep(.2)
                while self._pb.progr < self._pb.max_it:
                    self._pb.iterate()
            else:
                self.vna.avg_clear()
                if self.vna.get_averages() == 1 or self.vna.get_Average() == False:  # no averaging
                    qkit.flow.sleep(self.vna.get_sweeptime())  # wait single sweep
                    self._pb.iterate()
                else:  # with averaging
                    if "avg_status" in self.vna.get_function_names():
                        for a in range(self.vna.get_averages()):
                            while self.vna.avg_status() <= a:
                                qkit.flow.sleep(.2)  # maybe one would like to adjust this at a later point
                            self._pb.iterate()
                    else:  # old style
                        for a in range(self.vna.get_averages()):
                            qkit.flow.sleep(self.vna.get_sweeptime())  # wait single sweep time
                            self._pb.iterate()
        
        data_amp, data_pha = self.vna.get_tracedata()
        data_real, data_imag = self.vna.get_tracedata('RealImag')
        
        self._append(data_amp,data_pha,data_real,data_imag)
        if self._fit_resonator:
            self._do_fit_resonator()
        self._end_measurement()
    
    def measure_2D(self):
        """
        measure method to record a (averaged) VNA trace, S11 or S21 according to the setting on the VNA
        for all parameters x_vec in x_obj
        """
        
        if self.landscape.xzlandscape_func:  # The vna limits need to be adjusted, happens in the frequency wrapper
            self._x_parameter.set_function = self.landscape.vna_frequency_wrapper(self._x_parameter.set_function)
        
        self._dim = 2
        self._measurement_object.measurement_func = 'measure_2D'
        
        self._prepare_measurement_devices()
        if self._segments:
            f =  [self.Coordinate('frequency_%i' % i, unit='Hz', values=self._freqpoints[0 if i == 0 else self._segments[i - 1]:self._segments[i]]) for i in range(len(self._segments))]
            self._prepare_measurement_file(
                    [self.Data(P[0] % i, [self._x_parameter,f[i]], P[1], save_timestamp=P[2] and not i)
                     for i in range(len(self._segments)) for P in [["amplitude_%i","arb. unit",True],["phase_%i","rad",False],["real_%i","",False],["imag_%i","",False]]])
        else:
            f = self.Coordinate('frequency', unit='Hz', values=self._freqpoints)
    
            self._prepare_measurement_file(
                    [self.Data("amplitude", [self._x_parameter, f], "arb. unit", save_timestamp=True), self.Data("phase", [self._x_parameter, f], "rad")])
       
        self._pb = Progress_Bar(len(self._x_parameter.values), '2D VNA sweep ' + self.measurement_name, self.vna.get_sweeptime_averages(),
                                dummy=not self.progress_bar)
        
        if self._nop < 10:
            # creates view: plot middle point vs x-parameter, for qubit measurements
            self._views = [self._data_file.add_view("amplitude_midpoint", x=self._x_parameter.hdf_dataset, y=self._datasets['amplitude'],
                                                    view_params=dict(transpose=True, default_trace=self._nop // 2, linecolors=[(200, 200, 100)])),
                self._data_file.add_view("phase_midpoint", x=self._x_parameter.hdf_dataset, y=self._datasets['phase'],
                                         view_params=dict(transpose=True, default_trace=self._nop // 2, linecolors=[(200, 200, 100)]))]
            self._open_qviewkit(['views/amplitude_midpoint', 'views/phase_midpoint'])
        else:
            self._views = []
            self._open_qviewkit(datasets=[] if len(self._segments)>4 else None)
        
        if self._fit_resonator:
            self._resonator = resonator(self._data_file.get_filepath())
        self._measure()
    
    def measure_3D(self):
        """
        measure full window of vna while sweeping x_set_obj and y_set_obj with parameters x_vec/y_vec. sweep over y_set_obj is the inner loop, for every value x_vec[i] all values y_vec are measured.

        optional: measure method to perform the measurement according to landscape, if set
        self.span is the range (in units of the vertical plot axis) data is taken around the specified funtion(s)
        note: make sure to have properly set x,y vectors before generating traces
        """
        if self.landscape.xzlandscape_func:  # The vna limits need to be adjusted, happens in the frequency wrapper
            self._x_parameter.set_function = self.landscape.vna_frequency_wrapper(self._x_parameter.set_function)

        self._dim = 3
        self._measurement_object.measurement_func = 'measure_3D'
        
        self._prepare_measurement_devices()
        if self._segments:
            f =  [self.Coordinate('frequency_%i' % i, unit='Hz', values=self._freqpoints[0 if i == 0 else self._segments[i - 1]:self._segments[i]]) for i in range(len(self._segments))]
            self._prepare_measurement_file(
                    [self.Data(P[0] % i, [self._x_parameter, self._y_parameter,f[i]], P[1], save_timestamp=P[2] and not i)
                     for i in range(len(self._segments)) for P in [["amplitude_%i","arb. unit",True],["phase_%i","rad",False],["real_%i","",False],["imag_%i","",False]]])
        else:
            f = self.Coordinate('frequency', unit='Hz', values=self._freqpoints)
            self._prepare_measurement_file([self.Data("amplitude", [self._x_parameter, self._y_parameter, f], "arb. unit", save_timestamp=True),
                self.Data("phase", [self._x_parameter, self._y_parameter, f], "rad")])
        
        self._open_qviewkit(datasets=[] if len(self._segments)>4 else None)
        
        if self._fit_resonator:
            self._resonator = resonator(self._data_file.get_filepath())
        
        if self.progress_bar:
            if self.landscape.xylandscapes:  # ToDo: This part could be part of the Landscape class
                truth = np.full((len(self._y_parameter.values), len(self._x_parameter.values)), False)  # first, nothing is selected:
                for e in self.landscape.xylandscapes:
                    if not e['blacklist']:
                        truth = np.logical_or(truth, (np.abs(self._y_parameter.values[:, np.newaxis] - e['center_points']) <= e['y_span'] / 2) *  # check y span
                                              (e['x_range'][0] <= self._x_parameter.values) * (self._x_parameter.values <= e['x_range'][1]))  # check x range
                
                for e in self.landscape.xylandscapes:
                    if e['blacklist']:  # exclude blacklisted areas
                        truth = np.logical_and(truth, np.logical_not(
                                (np.abs(self._y_parameter.values[:, np.newaxis] - e['center_points']) <= e['y_span'] / 2) * (
                                    e['x_range'][0] <= self._x_parameter.values) * (self._x_parameter.values <= e['x_range'][1])))
                points = np.sum(truth)
            else:
                points = len(self._x_parameter.values) * len(self._y_parameter.values)
            self._pb = Progress_Bar(points, '3D VNA sweep ' + self.measurement_name, self.vna.get_sweeptime_averages())
        else:
            self._pb = Progress_Bar(1, dummy=True)
        
        self._measure()
    
    def measure_timetrace(self):
        """
        measure method to record a single VNA timetrace, this only makes sense when span is set to 0 Hz!,
        tested only with KEYSIGHT E5071C ENA and its corresponding qkit driver
        LGruenhaupt 11/2016
        """
        #ToDo: move this to regular sweeps
        if self.vna.get_span() > 0:
            raise ValueError(__name__ + ': For timetrace scans, VNA span needs to be 0 Hz')
        if self.vna.get_Average():
            raise ValueError(__name__ + ': For timetrace scans, Averaging needs to be turned off.')
        self.vna.get_centerfreq()
        self._scan_time = True
        
        self._measurement_object.measurement_func = 'measure_timetrace'
        
        self._prepare_measurement_devices()
        
        t = self.Coordinate('time', unit='s', values=np.arange(0, self._nop, 1) * self.vna.get_sweeptime() / (self._nop - 1))
        f = self.Coordinate('frequency', unit='Hz', values=[self.vna.get_centerfreq()])
        iteration = self.Coordinate("trace_number", unit="", values=np.arange(0, self.number_of_timetraces, 1))

        self._prepare_measurement_file([self.Data("amplitude", [iteration, t], "arb. unit", save_timestamp=True), self.Data("phase", [iteration, t], "rad")],
                coords=f)

        self._pb = Progress_Bar(self.number_of_timetraces, 'VNA timetrace ' + self.measurement_name, self.vna.get_sweeptime_averages(),
                                dummy=not self.progress_bar)
        
        qkit.flow.start()
        try:
            """
            loop: x_obj with parameters from x_vec
            """

            for i, x in enumerate(self._x_parameter.values):
                self._x_parameter.set_function(x)
                qkit.flow.sleep(self._x_parameter.wait_time)
                
                self._acquire_log_functions()
                
                data_amp, data_pha = self._acquire_vna_data()
                self._datasets['amplitude'].append(data_amp)
                self._datasets['phase'].append(data_pha)
                qkit.flow.sleep()
                self._pb.iterate()
        finally:
            self._end_measurement()
            self._scan_time = False
    
    def _acquire_vna_data(self):
        if self.averaging_start_ready:
            self.vna.start_measurement()
            if self._scan_time:
                qkit.flow.sleep(self.vna.get_sweeptime(query=False))  # to prevent timeouts in time scan
            elif self.vna.ready():
                logging.debug("VNA STILL ready... Adding delay")
                qkit.flow.sleep(.2)  # just to make sure, the ready command does not *still* show ready
            
            while not self.vna.ready():
                qkit.flow.sleep(min(self.vna.get_sweeptime_averages(query=False) / 11., .2))
        else:
            self.vna.avg_clear()
            qkit.flow.sleep(self._sweeptime_averages)
        
        """ measurement """
        return self.vna.get_tracedata()
    
    def _append(self,amplitude,phase,real=None,imag=None):
        if self._segments:
            for i in range(len(self._segments)):
                self._datasets['amplitude_%i' % i].append(amplitude[0 if i == 0 else self._segments[i - 1]:self._segments[i]])
                self._datasets['phase_%i' % i].append(phase[0 if i == 0 else self._segments[i - 1]:self._segments[i]])
                if real is not None and imag is not None:
                    self._datasets['real_%i' % i].append(real[0 if i == 0 else self._segments[i - 1]:self._segments[i]])
                    self._datasets['imag_%i' % i].append(imag[0 if i == 0 else self._segments[i - 1]:self._segments[i]])
        else:
            self._datasets['amplitude'].append(amplitude)
            self._datasets['phase'].append(phase)
            if real is not None and imag is not None:
                self._datasets['real'].append(real)
                self._datasets['imag'].append(imag)
        
    def _measure(self):
        """
        measures and plots the data depending on the measurement type.
        the measurement loops feature the setting of the objects and saving the data in the .h5 file.
        """
        qkit.flow.start()
        try:
            """
            loop: x_obj with parameters from x_vec
            """
            for ix, x in enumerate(self._x_parameter.values):
                self._x_parameter.set_function(x)
                qkit.flow.sleep(self._x_parameter.wait_time)
                
                self._acquire_log_functions()
    
                if self._dim == 3:
                    for y in self._y_parameter.values:
                        # loop: y_obj with parameters from y_vec (only 3D measurement)
                        if self.landscape.xylandscapes and not self.landscape.perform_measurement_at_point(x, y, ix):
                            # if point is not of interest (not close to one of the functions)
                            data_amp = np.full(int(self._nop), np.NaN, dtype=np.float16)
                            data_pha = np.full(int(self._nop), np.NaN, dtype=np.float16)  # fill with NaNs
                        else:
                            self._y_parameter.set_function(y)
                            qkit.flow.sleep(self._y_parameter.wait_time)
                            if not self.landscape.xzlandscape_func:  # normal scan
                                data_amp, data_pha = self._acquire_vna_data()
                            else:
                                data_amp, data_pha = self.landscape.get_tracedata_xz(x)
                            self._pb.iterate()
                        self._append(data_amp,data_pha)
                        if self._fit_resonator:
                            self._do_fit_resonator()
                        qkit.flow.sleep()
                    """
                    filling of value-box is done here.
                    after every y-loop the data is stored the next 2d structure
                    """
                    [d.next_matrix() for d in self._datasets.values()]
    
                if self._dim == 2:
                    data_amp, data_pha = self._acquire_vna_data()
                    self._append(data_amp, data_pha)
                    
                    if self._fit_resonator:
                        self._do_fit_resonator()
                    self._pb.iterate()
                    qkit.flow.sleep()
        finally:
            self._end_measurement()
    
    def _end_measurement(self):
        super(spectrum, self)._end_measurement()
        if self.averaging_start_ready: self.vna.post_measurement()
    
    def set_resonator_fit(self, fit_resonator=True, fit_function='', f_min=None, f_max=None):
        """
        sets fit parameter for resonator

        fit_resonator (bool): True or False, default: True (optional)
        fit_function (string): function which will be fitted to the data (optional)
        f_min (float): lower frequency boundary for the fitting function, default: None (optional)
        f_max (float): upper frequency boundary for the fitting function, default: None (optional)
        fit types: 'lorentzian','skewed_lorentzian','circle_fit_reflection', 'circle_fit_notch','fano'
        """
        if not fit_resonator:
            self._fit_resonator = False
            return
        self._functions = {'lorentzian': 0, 'skewed_lorentzian': 1, 'circle_fit_reflection': 2, 'circle_fit_notch': 3, 'fano': 5, 'all_fits': 5}
        try:
            self._fit_function = self._functions[fit_function]
        except KeyError:
            logging.error(
                    'Fit function not properly set. Must be either \'lorentzian\', \'skewed_lorentzian\', \'circle_fit_reflection\', \'circle_fit_notch\', \'fano\', or \'all_fits\'.')
        else:
            self._fit_resonator = True
            self._f_min = f_min
            self._f_max = f_max
    
    def _do_fit_resonator(self):
        """
        calls fit function in resonator class
        fit function is specified in self.set_fit, with boundaries f_mim and f_max
        only the last 'slice' of data is fitted, since we fit live while measuring.
        """
        
        if self._fit_function == 0:  # lorentzian
            self._resonator.fit_lorentzian(f_min=self._f_min, f_max=self._f_max)
        if self._fit_function == 1:  # skewed_lorentzian
            self._resonator.fit_skewed_lorentzian(f_min=self._f_min, f_max=self._f_max)
        if self._fit_function == 2:  # circle_reflection
            self._resonator.fit_circle(reflection=True, f_min=self._f_min, f_max=self._f_max)
        if self._fit_function == 3:  # circle_notch
            self._resonator.fit_circle(notch=True, f_min=self._f_min, f_max=self._f_max)
        if self._fit_function == 4:  # fano
            self._resonator.fit_fano(f_min=self._f_min, f_max=self._f_max)
            # if self._fit_function == 5: #all fits
            # self._resonator.fit_all_fits(f_min=self._f_min, f_max = self._f_max)
    
    def set_plot_comment(self, comment):
        """
        Small comment to add at the end of plot pics for more information i.e. good for wiki entries.
        """
        self._plot_comment = comment
    
    def gen_fit_function(self, curve_f, curve_p, x_range=None, span=None, p0=[-1, 0.1, 7], units=''):
        """
        Generates an xy landscape fit for 3D scan. Function is deprecated and calls landscape.generate_fit_function
        curve_f: 'spline', '2pt' 'lin, 'parab', 'hyp', specifies the fit function to be employed
        curve_p: set of points that are the basis for the fit in the format [[x1,x2,x3,...],[y1,y2,y3,...]], frequencies in Hz
        span: specify span for the generated fit_function, if not given default of self.span is used
        x_range: specify x_range for the function in the format [x_min, x_max]
        p0 (optional): start parameters for the fit, must be an 1D array of length 3 ([a,b,c,d]),
           where for the parabula p0[3] will be ignored
        units: set this to 'Hz' in order to avoid large values that cause the fit routine to diverge
        The parabolic function takes the form  y = a*(x-b)**2 + c , where (a,b,c) = p0
        The hyperbolic function takes the form y = sqrt[ a*(x-b)**2 + c ], where (a,b,c) = p0

        adds a trace to landscape
        """
        logging.warning("This function is deprecated. Better to use landscape.generate_fit_function_xy")
        self.landscape.generate_fit_function_xy(curve_f=curve_f, curve_p=curve_p, x_range=x_range, y_span=span, p0=p0, units=units)
    
    def delete_fit_function(self, n=None):
        """
        legacy support for delete_xy_landscape_function. Please use the other function in the future
        delete single fit function n (with 0 being the first one generated) or the complete landscape for n not specified
        :param n: index of single fit function to be deleted
        :return:
        """
        logging.warning('This function is deprecated for clarity purposes.'
                        ' Please use delete_xy_landscape_function in the future')
        self.landscape.delete_landscape_function_xy(n=n)
    
    def plot_fit_function(self):
        """
        legeacy support for landscape.plot_fit_function_xy. Please use the other function in the future.
        Plots the landscape
        :return:
        """
        self.landscape.plot_xy_landscape()


class Landscape:
    """
    Class for landscape scans in combination with spectroscopy. spectrum gnerates an instance of Landscape in __init__
    Use this instance to generate your fit_functions/landscape for your measurement.
    Instance stores the landscape(functions), lets you plot them, checks if points are to be measured and adjusts
    the vna frequencies.
    """
    
    def __init__(self, vna, spec):
        self.vna = vna
        self.spec = spec  # The spectroscopy object
        self.xylandscapes = []  # List containing dicts
        self.xzlandscape_func = None
        self.xz_freqpoints = None
        self.y_span_default = 200e6  # this is for the xy landscape scan, i.e., span of your y_parameter, e.g, mw_frequency
        self.z_span = self.vna.get_span()  # This is for the xz landscape scan i.e. span of vna is adjusted w/ resp to x
    
    def generate_fit_function_xy(self, curve_f, curve_p, x_range=None, y_span=None, blacklist=False, p0=[-1, 0.1, 7], units=''):
        """
        Use this function if you keep your vna span fixed but want to add a landscape to your x and y parameter.
        I.e., for given x parameter not all y parameters are swept but only those that lie within the specified y-span
        around the fit function.
        Adds a trace to landscape
        curve_f: 'spline', 'lin_spline' 'lin, 'parab', 'hyp', 'transmon' specifies the fit function to be employed
        curve_p: set of points that are the basis for the fit in the format [[x1,x2,x3,...],[y1,y2,y3,...]], frequencies in Hz
        x_range: specify x_range for the function in the format [x_min, x_max]
        y_span: specify the span of your y_axis for the generated fit_function,
                if not given default of self.span is used, if negative the span will be excluded from the measurement
                interesting for overlaping regions
        blacklist: Use this parameter to explicitly exclude a section from the measurement (previously done by negative span)
        p0 (optional): start parameters for the fit, must be an 1D array of length 3 ([a,b,c,d]),
           where for the parabula p0[3] will be ignored
        units: set this to 'Hz' in order to avoid large values that cause the fit routine to diverge

        The parabolic function takes the form  y = a*(x-b)**2 + c , where (a,b,c) = p0
        The hyperbolic function takes the form y = sqrt[ a*(x-b)**2 + c ], where (a,b,c) = p0

        """
        if not qkit.module_available("scipy"):
            raise ImportError('scipy not available.')
        
        if units == 'Hz':
            multiplier = 1e9
        else:
            multiplier = 1
        x_fit = np.array(curve_p[0])
        y_fit = np.array(curve_p[1])
        if x_range is None:
            x_range = [self.spec.x_vec[0], self.spec.x_vec[-1]]
        if y_span is None:
            y_span = self.y_span_default
        if y_span < 0:
            y_span = -y_span
            blacklist = True
            logging.warning('Using a negative span in generate_fit_function_xy is deprecated. Please use blacklist = True instead for more clarity.')
        
        try:
            if curve_f == 'lin_spline':
                f = interp1d(x_fit, y_fit)
                center_points = f(self.spec.x_vec)
            elif curve_f == 'spline':
                center_points = UnivariateSpline(x_fit, y_fit)(self.spec.x_vec)
            else:  # curve_fit procedure differs from splines
                if curve_f == 'parab':
                    fit_fct = self.f_parab
                elif curve_f == 'hyp':
                    fit_fct = self.f_hyp
                elif curve_f == 'lin':
                    fit_fct = self.f_lin
                    p0 = p0[:2]
                elif curve_f == 'transmon':
                    fit_fct = self.f_transmon
                else:
                    raise ValueError('function type not known...aborting')
                popt, pcov = curve_fit(fit_fct, x_fit, y_fit / multiplier, p0=p0)
                center_points = multiplier * fit_fct(self.spec.x_vec, *popt)
        except Exception as message:
            print('fit not successful:', message)
        else:
            self.xylandscapes.append({'center_points': center_points, 'y_span': y_span, 'x_range': [np.min(x_range), np.max(x_range)], 'blacklist': blacklist})
    
    def generate_fit_function_xz(self, curve_f, curve_p, z_span=None, p0=[-1, 0.1, 7]):
        """
        Use this function if you want to adjust your vna span with respect to your x-values, useful if you want to
        track your fresonator, e.g., shifting resonance due qubit resonator coupling or fmr measurements. It works
        in a 2d and 3d scan.
        :param curve_f: fit_function (str) such as 'lin_spline', 'spline', 'parab', 'hyp', 'lin'
        :param curve_p: Valeus to fit in the form [[x0,x1,..xn],[z0,z1,..zn]]
        :param z_span: If None, span from VNA is used. If specified, vna span will be updated.
        :param p0: intial fit parameters
        :return:
        """
        if not qkit.module_available("scipy"):
            raise ImportError('scipy not available.')
        
        if curve_p[1][-1] > 1e6:  # test if z_values are given in Hz or GHz
            multiplier = 1e9
        else:
            multiplier = 1
        if z_span is not None:
            self.z_span = z_span
            self.vna.set_span(z_span)
        else:
            self.z_span = self.vna.get_span()
        x_fit = np.array(curve_p[0])
        z_fit = np.array(curve_p[1])
        try:
            if curve_f == 'lin_spline':
                self.xzlandscape_func = interp1d(x_fit, z_fit)
            elif curve_f == 'spline':
                self.xzlandscape_func = UnivariateSpline(x_fit, z_fit)
            else:  # curve_fit procedure differs from splines
                if curve_f == 'parab':
                    fit_fct = self.f_parab
                elif curve_f == 'hyp':
                    fit_fct = self.f_hyp
                elif curve_f == 'lin':
                    fit_fct = self.f_lin
                    p0 = p0[:2]
                else:
                    raise ValueError('function type not known...aborting')
                popt, pcov = curve_fit(fit_fct, x_fit, z_fit / multiplier, p0=p0)
                self.xzlandscape_func = lambda x: multiplier * fit_fct(x, *popt)
            
            self.xz_freqpoints = np.arange(self.xzlandscape_func(self.spec.x_vec[0]) - self.z_span / 2,
                                           self.xzlandscape_func(self.spec.x_vec[-1]) + self.z_span / 2, self.vna.get_span() / self.vna.get_nop())
        except Exception as message:
            print('fit not successful:', message)
    
    def delete_landscape_function_xy(self, n=None):
        """
        delete single xy landscape function n (with 0 being the first one generated)
        or the complete landscape for n not specified
        """
        if n is not None:
            del self.xylandscapes[n]
        else:
            self.xylandscapes = []
    
    def delete_landscape_function_xz(self):
        """
        delets the xz_landscape_function incl. the xz_freqpoints
        :return: None
        """
        self.xzlandscape_func = None
        self.xz_freqpoints = None
        print('xz_landscape deleted')
    
    def plot_xy_landscape(self):
        """
        Plots the xy landscape(s) (for 3D scan, z-axis (vna) is not plotted
        :return:
        """
        if not qkit.module_available("matplotlib"):
            raise ImportError("matplotlib not found.")
        
        if self.xylandscapes:
            for i in self.xylandscapes:
                try:
                    arg = np.where((i['x_range'][0] <= self.spec.x_vec) & (self.spec.x_vec <= i['x_range'][1]))
                    x = self.spec.x_vec[arg]
                    t = i['center_points'][arg]
                    plt.plot(x, t, color='C1')
                    if i['blacklist']:
                        plt.fill_between(x, t + i['y_span'] / 2., t - i['y_span'] / 2., color='C3', alpha=0.5)
                    else:
                        plt.fill_between(x, t + i['y_span'] / 2., t - i['y_span'] / 2., color='C0', alpha=0.5)
                except Exception as e:
                    print(e)
                    print('invalid trace...skip')
            plt.axhspan(np.min(self.spec.y_vec), np.max(self.spec.y_vec), facecolor='0.5', alpha=0.5)
            plt.xlim(np.min(self.spec.x_vec), np.max(self.spec.x_vec))
            plt.show()
        else:
            print('No trace generated. Use landscape.generate_xy_function')
    
    def plot_xz_landscape(self):
        """
        plots the xz landscape, i.e., how your vna frequency span changes with respect to the x vector
        :return: None
        """
        if not qkit.module_available("matplotlib"):
            raise ImportError("matplotlib not found.")
        
        if self.xzlandscape_func:
            y_values = self.xzlandscape_func(self.spec.x_vec)
            plt.plot(self.spec.x_vec, y_values, 'C1')
            plt.fill_between(self.spec.x_vec, y_values + self.z_span / 2., y_values - self.z_span / 2., color='C0', alpha=0.5)
            plt.xlim((self.spec.x_vec[0], self.spec.x_vec[-1]))
            plt.ylim((self.xz_freqpoints[0], self.xz_freqpoints[-1]))
            plt.show()
        else:
            print('No xz funcion generated. Use landscape.generate_xz_function')
    
    def set_y_span(self, y_span, n=None):
        if not self.xylandscapes:
            self.y_span_default = y_span
        else:
            if n is not None:
                self.xylandscapes[n]['y_span'] = y_span
            else:
                for e in self.xylandscapes:
                    e['y_span'] = y_span
    
    def get_y_span(self):
        return self.y_span_default
    
    def get_y_span_list(self):
        return [e['y_span'] for e in self.xylandscapes]
    
    def vna_frequency_wrapper(self, x_set_obj):
        """
        Function wraps the x_set_obj function for a landscape_xy scan such that the vna frequencies are automatically
        adjusted
        :param x_set_obj: as given by the user
        :return: the wrapped function
        """
        
        def vna_wrapper(x):
            start_freq = self.xz_freqpoints[np.argmin(np.abs(self.xz_freqpoints - (self.xzlandscape_func(x) - self.z_span / 2)))]
            self.vna.set_startfreq(start_freq)
            self.vna.set_stopfreq(start_freq + self.z_span)
            x_set_obj(x)
        
        return vna_wrapper
    
    def perform_measurement_at_point(self, x, y, ix):
        """
        Looks if the point is of interest and returns True or False
        :param x: point in the x-vector
        :param y: point in the y-vector
        :param ix: index of x-vector
        :return: measure_bool, whether or not the point should be measured
        """
        # looks strange but works
        measure = False
        for e in self.xylandscapes:
            if np.abs(e['center_points'][ix] - y) <= e['y_span'] / 2 and e['x_range'][0] <= x <= e['x_range'][1]:  # The point is covered by this span
                if e['blacklist']:
                    return False  # if the point is blacklisted anywhere, we don't need to look further
                else:
                    measure = True
        return measure
    
    def get_tracedata_xz(self, x):
        """
        Function to fill the tracedata with NaNs outside the scan region
        :param x: x_value where we perform the scan
        :return:
        """
        amp = np.full_like(self.xz_freqpoints, np.NaN, dtype=np.float16)
        pha = np.full_like(self.xz_freqpoints, np.NaN, dtype=np.float16)
        startarg = np.argmin(np.abs(self.xz_freqpoints - (self.xzlandscape_func(x) - self.z_span / 2)))
        stoparg = startarg + self.vna.get_nop()
        a, p = self.spec._acquire_vna_data()
        amp[startarg:stoparg] = a
        pha[startarg:stoparg] = p
        return amp, pha
    
    def get_freqpoints_xz(self):
        return self.xz_freqpoints
    
    def f_parab(self, x, a, b, c):
        return a * (x - b) ** 2 + c
    
    def f_hyp(self, x, a, b, c):
        """hyperbolic function with the form y = sqrt[ a*(x-b)**2 + c ]"""
        return np.sqrt(a * (x - b) ** 2 + c)
    
    def f_lin(self, x, a, b):
        return a * x + b
    
    def f_transmon(self, x, w_max, L, I_ext, djj):
        """
        Dispersion of a tunable transmon qubit with junction asymmetry.

        Args:
            x:     x-value
            w_max:    Maximum qubit frequency without detuning.
            L:     Oscillation period in current/x-value.
            I_ext: Offset current/x offset.
            djj:   Josephson junction asymmetry (Ic1 - Ic2)/(Ic1 + Ic2)

        Returns:
            Primal transition frequency of a transmon qubit.
        """
        return w_max * (np.abs(np.cos(np.pi / L * (x - I_ext))) * (1 + djj ** 2 * np.tan(np.pi / L * (x - I_ext)) ** 2) ** .5) ** 0.5
