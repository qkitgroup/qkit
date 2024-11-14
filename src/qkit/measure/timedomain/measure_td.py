# modified and adapted by JB@KIT 04/2015, 09/2015
# modified by MK@KIT 09/2018
# time domain measurement class

import numpy as np
import logging
import threading

import qkit
from qkit.gui.notebook.Progress_Bar import Progress_Bar
from qkit.storage import store as hdf
from qkit.gui.plot import plot as qviewkit
import qkit.measure.write_additional_files as waf
from qkit.measure.timedomain.initialize import InitializeTimeDomain as iniTD
from qkit.measure.measurement_class import Measurement


class Measure_td(object):
    '''
    useage:

    m = Measure_td()

    m.set_x_parameters(arange(-0.05,0.05,0.01),'flux coil current (mA)',coil.set_current)
    m.set_y_parameters(arange(4e9,7e9,10e6),'excitation frequency (Hz)',mw_src1.set_frequency)

    m.measure_XX()
    Generally, we want to use
    ReadoutTrace = True -> if we want to record the readout pulse or
    AWGTrace = True -> if we have a N different time steps in the AWG (Not used, this is done via the mode variable now.)

    ToDO (S1, 09/2017):
        - Include LogFunctions
        - Include 2D_AWG with pre-averaging
        - Check multi-tone readout
    '''
    
    def __init__(self, sample, readout=None):
        self.sample = sample
        if readout is None:
            self.readout = sample.readout
        else:
            self.readout = readout
        
        self.comment = None
        self.mode = None
        self.x_set_obj = None
        self.y_set_obj = None
        self.z_set_obj = None
        
        self.dirname = None
        self.data_dir = None
        self.plotSuffix = ''
        self.hold = False
        
        self.show_progress_bar = True
        
        self.ReadoutTrace = False
        
        self.open_qviewkit = True
        self.create_averaged_data = False
        
        self.qviewkit_singleInstance = True
        self._qvk_process = False
        self._plot_comment = ''
        self.multiplex_attribute = "readout_pulse_frequency"
        self.multiplex_unit = "Hz"
        self.init = iniTD(sample)

        self._measurement_object = Measurement()
        self._measurement_object.measurement_type = 'timedomain'
        self._measurement_object.sample = self.sample
        
    
    def set_x_parameters(self, x_vec, x_coordname, x_set_obj, x_unit=None):
        self.x_vec = x_vec
        self.x_coordname = x_coordname
        self.x_set_obj = x_set_obj
        if x_unit is None:
            logging.warning(__name__ + ': Unit of the x-axis is not set.')
            self.x_unit = ''
        else:
            self.x_unit = x_unit
    
    def set_y_parameters(self, y_vec, y_coordname, y_set_obj, y_unit=None):
        self.y_vec = y_vec
        self.y_coordname = y_coordname
        self.y_set_obj = y_set_obj
        if y_unit is None:
            logging.warning(__name__ + ': Unit of the y-axis is not set.')
            self.y_unit = ''
        else:
            self.y_unit = y_unit
    
    def set_z_parameters(self, z_vec, z_coordname, z_set_obj, z_unit=None):
        self.z_vec = z_vec
        self.z_coordname = z_coordname
        self.z_set_obj = z_set_obj
        if z_unit is None:
            logging.warning(__name__ + ': Unit of the z-axis is not set.')
            self.z_unit = ''
        else:
            self.z_unit = z_unit
    
    def measure_1D(self):
        if self.x_set_obj is None:
            raise ValueError('x-axes parameters not properly set')
        
        self.mode = 1  # 1: 1D, 2: 2D, 3:1D_AWG/2D_AWG, 4:3D_AWG
        self._prepare_measurement_file()
        
        if self.show_progress_bar: p = Progress_Bar(len(self.x_vec), name=self.dirname)
        try:
            # measurement loop
            for x in self.x_vec:
                self.x_set_obj(x)
                qkit.flow.sleep()
                self._append_data()
                if self.show_progress_bar: p.iterate()
        finally:
            self._end_measurement()
    
    def measure_2D(self):
        if self.x_set_obj is None or self.y_set_obj is None:
            raise ValueError('Axes parameters not properly set')
        if self.ReadoutTrace:
            raise ValueError('ReadoutTrace is currently not supported for 2D measurements')
        
        self.mode = 2  # 1: 1D, 2: 2D, 3:1D_AWG/2D_AWG, 4:3D_AWG
        self._prepare_measurement_file()
        
        if self.show_progress_bar: p = Progress_Bar(len(self.x_vec) * len(self.y_vec), name=self.dirname)
        try:
            # measurement loop
            for x in self.x_vec:
                self.x_set_obj(x)
                for y in self.y_vec:
                    qkit.flow.sleep()
                    self.y_set_obj(y)
                    qkit.flow.sleep()
                    self._append_data()
                    if self.show_progress_bar: p.iterate()
                for i in range(self.ndev):
                    self._hdf_amp[i].next_matrix()
                    self._hdf_pha[i].next_matrix()
        finally:
            self._end_measurement()
    
    def measure_1D_AWG(self, iterations=100):
        '''
        use AWG sequence for x_vec, averaging over iterations
        '''
        self.y_vec = range(iterations)
        self.y_coordname = 'iteration'
        self.y_set_obj = lambda y: True
        self.y_unit = ''
        self.create_averaged_data = True
        self.avg_complex_sum = np.zeros_like(self.x_vec)
        try:
            return self.measure_2D_AWG(iterations=1)
        finally:
            self.create_averaged_data = False  # This is ALWAYS done after the return! Looks strange and it really is, but it works.
    
    def measure_2D_AWG(self, iterations=1):
        '''
        x_vec is sequence in AWG
        '''
        
        if self.y_set_obj is None:
            raise ValueError('y-axes parameters not properly set')
        
        qkit.flow.sleep()  # if stop button was pressed by now, abort without creating data files
        
        if iterations > 1:
            self.z_vec = range(iterations)
            self.z_coordname = 'iteration'
            self.z_set_obj = lambda z: True
            self.z_unit = ''
            
            self.measure_3D_AWG()
            
            # For 3D measurements with iterations, averages are only created at the end to get a consistent averaging base.
            hdf_file = hdf.Data(self._hdf.get_filepath())
            for j in range(self.ndev):
                amp = np.array(hdf_file["/entry/data0/amplitude_%i" % j])
                pha = np.array(hdf_file["/entry/data0/phase_%i" % j])
                amp_avg = sum(amp[i] for i in range(iterations)) / iterations
                pha_avg = sum(pha[i] for i in range(iterations)) / iterations
                hdf_amp_avg = hdf_file.add_value_matrix('amplitude_avg_%i' % i, x=self._hdf_y, y=self._hdf_x, unit='a.u.')
                hdf_pha_avg = hdf_file.add_value_matrix('phase_avg_%i' % i, x=self._hdf_y, y=self._hdf_x, unit='rad')
                
                for i in range(len(self.y_vec)):
                    hdf_amp_avg.append(amp_avg[i], pointwise=True)
                    hdf_pha_avg.append(pha_avg[i], pointwise=True)
            hdf_file.close_file()
        
        else:
            self.mode = 3  # 1: 1D, 2: 2D, 3:1D_AWG/2D_AWG, 4:3D_AWG
            self._prepare_measurement_file()
            # if self.ndev > 1: raise ValueError('Multiplexed readout is currently not supported for 2D measurements')
            if self.show_progress_bar:
                p = Progress_Bar(len(self.y_vec), name=self.dirname)
            try:
                # measurement loop
                for it in range(len(self.y_vec)):
                    qkit.flow.sleep()  # better done during measurement (waiting for trigger)
                    self.y_set_obj(self.y_vec[it])
                    self._append_data(iteration=it)
                    if self.show_progress_bar: p.iterate()
            finally:
                self._end_measurement()
    
    def measure_3D_AWG(self):
        '''
        x_vec is sequence in AWG
        '''
        
        if self.z_set_obj is None or self.y_set_obj is None:
            raise ValueError('x-axes parameters not properly set')
        if self.ReadoutTrace:
            raise ValueError('ReadoutTrace is currently not supported for 3D_AWG measurements')
        
        self.mode = 4  # 1: 1D, 2: 2D, 3:1D_AWG/2D_AWG, 4:3D_AWG
        self._prepare_measurement_file()
        
        if self.show_progress_bar: p = Progress_Bar(len(self.y_vec) * len(self.z_vec), name=self.dirname)
        try:
            # measurement loop
            for z in self.z_vec:
                self.z_set_obj(z)
                for y in self.y_vec:
                    qkit.flow.sleep()
                    self.y_set_obj(y)
                    qkit.flow.sleep()
                    self._append_data()
                    if self.show_progress_bar: p.iterate()
                for i in range(self.ndev):
                    self._hdf_amp[i].next_matrix()
                    self._hdf_pha[i].next_matrix()
        finally:
            self._end_measurement()
    
    def measure_1D_ddc_time_trace(self):
        """
        measures the time evolution of your transmission / reflection
        in your network by performing a digital down conversion
        :return: None
        """
        time_end = float(self.sample.mspec.get_samples()) / self.sample.mspec.get_samplerate()
        time_array = np.linspace(0, time_end, self.sample.mspec.get_samples())
        self.set_x_parameters(time_array, 'time', True, 'sec')
        self.mode = 1  # 1: 1D, 2: 2D, 3:1D_AWG/2D_AWG
        self._prepare_measurement_file()
        try:
            qkit.flow.sleep()
            self._append_data(ddc=True)
        finally:
            self._end_measurement()
    
    def measure_2D_ddc_time_trace(self):
        """
        Performs a digital down conversion for exactly one value in your awg sequence. But you can sweep other
        parameters, such as mw-power or so.
        :return:
        """
        if self.y_set_obj is None:
            raise ValueError('y-axes parameters not properly set')
        time_end = float(self.sample.mspec.get_samples()) / self.sample.mspec.get_samplerate()
        time_array = np.linspace(0, time_end, self.sample.mspec.get_samples())
        self.set_x_parameters(time_array, 'time', True, 'sec')
        
        self.mode = 2  # 1: 1D, 2: 2D, 3:1D_AWG/2D_AWG
        self._prepare_measurement_file()
        
        if self.show_progress_bar:
            p = Progress_Bar(len(self.y_vec), name=self.dirname)
        try:
            for y in self.y_vec:
                qkit.flow.sleep()
                self.y_set_obj(y)
                qkit.flow.sleep()
                self._append_data(ddc=True)
                if self.show_progress_bar: p.iterate()
        finally:
            self._end_measurement()
    
    def measure_1D_awg_ddc_timetrace(self):
        """
        Performs a digital down conversion of your readout trace for every value in your y-vector,
        whereas y_vec should be awg sequence. This function is useful for magnon cavity experiments.
        x-vec is automatically set by acquisition window.
        (Also, all data are there at once)
        :return:
        """
        if self.y_vec is None:
            raise ValueError('y-axes parameters not properly set')
        time_end = float(self.sample.mspec.get_samples()) / self.sample.mspec.get_samplerate()
        time_array = np.linspace(0, time_end, self.sample.mspec.get_samples())
        self.set_x_parameters(time_array, 'time', True, 'sec')
        
        self.mode = 2  # 1: 1D, 2: 2D, 3:1D_AWG/2D_AWG
        self._prepare_measurement_file()
        
        try:
            qkit.flow.sleep()
            self._append_data(ddc=True)
        finally:
            self._end_measurement()
    
    def measure_1D_awg_1D_ddc_timetrace(self):
        """
        Performs a digital down conversion of your readout trace for every value in your y-vector
        while also sweeping another parameter. y_vec should be awg sequence and z_vec/obj the sweeping parameter.
        x-vec is automatically set by acquisition window.
        :return:
        """
        if (self.y_vec is None) or (self.z_set_obj is None):
            raise ValueError('Axes parameters not properly set')
        time_end = float(self.sample.mspec.get_samples()) / self.sample.mspec.get_samplerate()
        time_array = np.linspace(0, time_end, self.sample.mspec.get_samples())
        self.set_x_parameters(time_array, 'time', True, 'sec')
        self.mode = 4
        self._prepare_measurement_file()
        try:
            for z in self.z_vec:
                self.z_set_obj(z)
                qkit.flow.sleep()
                self._append_data(ddc=True)
                for i in range(self.ndev):
                    self._hdf_amp[i].next_matrix()
                    self._hdf_pha[i].next_matrix()
                if self.ReadoutTrace:
                    self._hdf_I.next_matrix()
                    self._hdf_Q.next_matrix()
        finally:
            self._end_measurement()
    
    def _prepare_measurement_file(self):
        qkit.flow.start()
        if self.dirname is None:
            self.dirname = self.x_coordname
        
        self.ndev = len(self.readout.get_tone_freq())  # returns array of readout freqs (=1 for non-multiplexed readout)
        
        self._hdf = hdf.Data(name=self.dirname, mode='a')
        self._hdf_x = self._hdf.add_coordinate(self.x_coordname, unit=self.x_unit)
        self._hdf_x.add(self.x_vec)

        self._measurement_object.uuid = self._hdf._uuid
        self._measurement_object.hdf_relpath = self._hdf._relpath
        self._measurement_object.instruments = qkit.instruments.get_instrument_names()

        self._measurement_object.save()
        self._mo = self._hdf.add_textlist('measurement')
        self._mo.append(self._measurement_object.get_JSON())

        self._settings = self._hdf.add_textlist('settings')
        settings = waf.get_instrument_settings(self._hdf.get_filepath())
        self._settings.append(settings)
        
        self._log = waf.open_log_file(self._hdf.get_filepath())
        
        self._hdf_readout_frequencies = self._hdf.add_coordinate(self.multiplex_attribute, unit=self.multiplex_unit)
        self._hdf_readout_frequencies.add(self.readout.get_tone_freq())
        
        if self.ReadoutTrace:
            self._hdf_TimeTraceAxis = self._hdf.add_coordinate('recorded timepoint', unit='s')
            self._hdf_TimeTraceAxis.add(np.arange(self.sample.mspec.get_samples()) / self.readout.get_adc_clock())
        
        if self.mode == 1:  # 1D
            self._hdf_amp = []
            self._hdf_pha = []
            for i in range(self.ndev):
                self._hdf_amp.append(self._hdf.add_value_vector('amplitude_%i' % i, x=self._hdf_x, unit='a.u.'))
                self._hdf_pha.append(self._hdf.add_value_vector('phase_%i' % i, x=self._hdf_x, unit='rad'))
            if self.ReadoutTrace:
                self._hdf_I = self._hdf.add_value_matrix('I_TimeTrace', x=self._hdf_x, y=self._hdf_TimeTraceAxis,
                                                         unit='V', save_timestamp=False)
                self._hdf_Q = self._hdf.add_value_matrix('Q_TimeTrace', x=self._hdf_x, y=self._hdf_TimeTraceAxis,
                                                         unit='V', save_timestamp=False)
        
        elif self.mode == 2:  # 2D
            self._hdf_y = self._hdf.add_coordinate(self.y_coordname, unit=self.y_unit)
            self._hdf_y.add(self.y_vec)
            self._hdf_amp = []
            self._hdf_pha = []
            for i in range(self.ndev):
                self._hdf_amp.append(self._hdf.add_value_matrix('amplitude_%i' % i, x=self._hdf_x, y=self._hdf_y, unit='a.u.'))
                self._hdf_pha.append(self._hdf.add_value_matrix('phase_%i' % i, x=self._hdf_x, y=self._hdf_y, unit='rad'))
            if self.ReadoutTrace:
                # TODO: One dimension missing here?
                self._hdf_I = self._hdf.add_value_matrix('I_TimeTrace', x=self._hdf_y, y=self._hdf_TimeTraceAxis,
                                                         unit='V', save_timestamp=False)
                self._hdf_Q = self._hdf.add_value_matrix('Q_TimeTrace', x=self._hdf_y, y=self._hdf_TimeTraceAxis,
                                                         unit='V', save_timestamp=False)
        
        elif self.mode == 3:  # 1D_AWG/2D_AWG
            self._hdf_y = self._hdf.add_coordinate(self.y_coordname, unit=self.y_unit)
            self._hdf_y.add(self.y_vec)
            self._hdf_amp = []
            self._hdf_pha = []
            for i in range(self.ndev):
                self._hdf_amp.append(self._hdf.add_value_matrix('amplitude_%i' % i,
                                                                x=self._hdf_y, y=self._hdf_x, unit='a.u.'))
                self._hdf_pha.append(self._hdf.add_value_matrix('phase_%i' % i,
                                                                x=self._hdf_y, y=self._hdf_x, unit='rad'))
            if self.ReadoutTrace:
                self._hdf_I = self._hdf.add_value_box('I_TimeTrace', x=self._hdf_y, y=self._hdf_x,
                                                      z=self._hdf_TimeTraceAxis, unit='V', save_timestamp=False)
                self._hdf_Q = self._hdf.add_value_box('Q_TimeTrace', x=self._hdf_y, y=self._hdf_x,
                                                      z=self._hdf_TimeTraceAxis, unit='V', save_timestamp=False)
        
        elif self.mode == 4:  # 3D_AWG
            self._hdf_y = self._hdf.add_coordinate(self.y_coordname, unit=self.y_unit)
            self._hdf_y.add(self.y_vec)
            self._hdf_z = self._hdf.add_coordinate(self.z_coordname, unit=self.z_unit)
            self._hdf_z.add(self.z_vec)
            self._hdf_amp = []
            self._hdf_pha = []
            for i in range(self.ndev):
                self._hdf_amp.append(self._hdf.add_value_box('amplitude_%i' % i, x=self._hdf_z, y=self._hdf_y,
                                                             z=self._hdf_x, unit='a.u.'))
                self._hdf_pha.append(self._hdf.add_value_box('phase_%i' % i, x=self._hdf_z, y=self._hdf_y,
                                                             z=self._hdf_x, unit='rad'))
            if self.ReadoutTrace:
                self._hdf_I = self._hdf.add_value_box('I_TimeTrace', x=self._hdf_z, y=self._hdf_y,
                                                      z=self._hdf_TimeTraceAxis, unit='V', save_timestamp=False)
                self._hdf_Q = self._hdf.add_value_box('Q_TimeTrace', x=self._hdf_y, y=self._hdf_y,
                                                      z=self._hdf_TimeTraceAxis, unit='V', save_timestamp=False)
        
        if self.create_averaged_data:
            self._hdf_amp_avg = []
            self._hdf_pha_avg = []
            for i in range(self.ndev):
                self._hdf_amp_avg.append(self._hdf.add_value_vector('amplitude_avg_%i' % i, x=self._hdf_x, unit='a.u.'))
                self._hdf_pha_avg.append(self._hdf.add_value_vector('phase_avg_%i' % i, x=self._hdf_x, unit='rad'))
        
        if self.comment:
            self._hdf.add_comment(self.comment)
        self._hdf.hf.hf.attrs['default_ds'] = ['data0/amplitude_%i' % i for i in range(min(5,self.ndev))] +\
                                              ['data0/phase_%i' % i for i in range(min(5,self.ndev))]
        if self.qviewkit_singleInstance and self.open_qviewkit and self._qvk_process:
            self._qvk_process.terminate()  # terminate an old qviewkit instance
        if self.open_qviewkit:
            self._qvk_process = qviewkit.plot(self._hdf.get_filepath(),
                                              datasets=['amplitude_%i' % i for i in range(min(5,self.ndev))] + ['phase_%i' % i for i in range(min(5,self.ndev))]
                                              )
    
        try:
            self.readout.start()
        except AttributeError:
            pass
    
    def _append_data(self, iteration=0, ddc=None):
        if self.ReadoutTrace:
            ampliData, phaseData, Is, Qs = self.readout.readout(timeTrace=True, ddc=ddc)
        else:
            ampliData, phaseData = self.readout.readout(timeTrace=False, ddc=ddc)
        
        if len(ampliData.shape) < 3:  # "normal" measurements
            for i in range(self.ndev):
                self._hdf_amp[i].append(np.atleast_1d(ampliData.T[i]), pointwise=True)
                self._hdf_pha[i].append(np.atleast_1d(phaseData.T[i]), pointwise=True)
            if self.ReadoutTrace:
                if self.mode < 3:  # mode 2 not yet fully supported but working for DDC timetrace experiments
                    self._hdf_I.append(Is, pointwise=True)
                    self._hdf_Q.append(Qs, pointwise=True)
                elif self.mode == 3:  # mode 4 not supported for 3D_awg yet
                    for ix in range(len(self.x_vec)):
                        self._hdf_I.append(Is[:, ix], pointwise=True)
                        self._hdf_Q.append(Qs[:, ix], pointwise=True)
                    self._hdf_I.next_matrix()
                    self._hdf_Q.next_matrix()
        
        else:  # for AWG DDC ReadoutTrace, all data are there at once
            for i in range(self.ndev):
                for j in range(ampliData.T.shape[2]):
                    self._hdf_amp[i].append(np.atleast_1d(ampliData.T[i, :, j]), pointwise=True)
                    self._hdf_pha[i].append(np.atleast_1d(phaseData.T[i, :, j]), pointwise=True)
                    if self.ReadoutTrace:
                        self._hdf_I.append(Is[:, j], pointwise=True)
                        self._hdf_Q.append(Qs[:, j], pointwise=True)
        
        if self.create_averaged_data:
            if iteration == 0:
                self.avg_complex_sum = ampliData * np.exp(1j * phaseData)
                for i in range(self.ndev):
                    self._hdf_amp_avg[i].append(np.atleast_1d(ampliData.T[i]), pointwise=True)
                    self._hdf_pha_avg[i].append(np.atleast_1d(phaseData.T[i]), pointwise=True)
            else:
                self.avg_complex_sum += ampliData * np.exp(1j * phaseData)
                amp_avg = np.abs(self.avg_complex_sum / (iteration + 1))
                pha_avg = np.angle(self.avg_complex_sum / (iteration + 1))
                for i in range(self.ndev):
                    self._hdf_amp_avg[i].ds.write_direct(np.ascontiguousarray(np.atleast_1d(amp_avg.T[i])))
                    self._hdf_pha_avg[i].ds.write_direct(np.ascontiguousarray(np.atleast_1d(pha_avg.T[i])))
                    self._hdf_pha_avg[i].ds.attrs['iteration'] = iteration + 1
                    self._hdf_amp_avg[i].ds.attrs['iteration'] = iteration + 1
                self._hdf.flush()
    
    def _end_measurement(self):
        try:
            self.readout.cleanup()
        except AttributeError:
            pass
        t = threading.Thread(target=qviewkit.save_plots, args=[self._hdf.get_filepath(), self._plot_comment])
        t.start()
        self._hdf.close_file()
        waf.close_log_file(self._log)
        qkit.flow.end()
    
    def set_plot_comment(self, comment):
        '''
        Small comment to add at the end of plot pics for more information i.e. good for wiki entries.
        '''
        self._plot_comment = comment