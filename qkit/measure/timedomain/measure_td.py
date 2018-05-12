# modified and adapted by JB@KIT 04/2015, 09/2015
# time domain measurement class

import qt
import numpy as np
import os.path
import time
import logging
import threading

import qkit
from qkit.gui.notebook.Progress_Bar import Progress_Bar
from qkit.storage import store as hdf
from qkit.gui.plot import plot as qviewkit
import qkit.measure.write_additional_files as waf
from qkit.measure.timedomain.initialize import InitializeTimeDomain as iniTD

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
    
    def __init__(self, sample):
        self.sample = sample
        self.readout = sample.readout
        self.mspec = sample.mspec

        self.comment = None
        self.mode = None
        self.x_set_obj = None
        self.y_set_obj = None
        
        self.dirname = None
        self.plotSuffix = ''
        self.hold = False
        
        self.show_progress_bar = True
        
        self.ReadoutTrace = False
        
        self.open_qviewkit = True
        self.create_averaged_data = False
        
        self.qviewkit_singleInstance = True
        self._qvk_process = False
        self._plot_comment = ''
        self.multiplex_attribute = "readout pulse frequency"
        self.multiplex_unit = "Hz"
        self.init = iniTD(sample)

        
    def set_x_parameters(self, x_vec, x_coordname, x_set_obj, x_unit = None):
        self.x_vec = x_vec
        self.x_coordname = x_coordname
        self.x_set_obj = x_set_obj
        if x_unit == None:
            logging.warning(__name__ + ': Unit of the x-axis is not set.')
            self.x_unit = ''
        else:
            self.x_unit = x_unit
        
    def set_y_parameters(self, y_vec, y_coordname, y_set_obj, y_unit = ''):
        self.y_vec = y_vec
        self.y_coordname = y_coordname
        self.y_set_obj = y_set_obj
        if y_unit == None:
            logging.warning(__name__ + ': Unit of the y-axis is not set.')
            self.y_unit = ''
        else:
            self.y_unit = y_unit
        
    def measure_1D(self):
    
        if self.x_set_obj == None:
            print 'axes parameters not properly set...aborting'
            return

        qt.mstart()
        self.mode = 1 #1: 1D, 2: 2D, 3:1D_AWG/2D_AWG
        self._prepare_measurement_file()
        
        if self.show_progress_bar: p = Progress_Bar(len(self.x_vec),name=self.dirname)
        try:
            # measurement loop
            for x in self.x_vec:
                self.x_set_obj(x)
                qt.msleep() # better done during measurement (waiting for trigger)
                self._append_data()
                if self.show_progress_bar: p.iterate()
        finally:
            #self._safe_plots()
            self._end_measurement()
            qt.mend()


    def measure_2D(self):

        if self.x_set_obj is None or self.y_set_obj is None:
            print 'axes parameters not properly set...aborting'
            return
        if self.ReadoutTrace:
            raise ValueError('ReadoutTrace is currently not supported for 2D measurements')
        
        qt.mstart()
        self.mode = 2 #1: 1D, 2: 2D, 3:1D_AWG/2D_AWG
        self._prepare_measurement_file()

        if self.show_progress_bar: p = Progress_Bar(len(self.x_vec)*len(self.y_vec),name=self.dirname)
        try:
            # measurement loop
            for x in self.x_vec:
                self.x_set_obj(x)
                for y in self.y_vec:
                    qt.msleep() 
                    self.y_set_obj(y)
                    qt.msleep() 
                    self._append_data()
                    if self.show_progress_bar: p.iterate()
        finally:
            self._end_measurement()
            qt.mend()


    def measure_1D_AWG(self, iterations = 100):
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
            return self.measure_2D_AWG()
        finally:
            self.create_averaged_data = False #This is ALWAYS done after the return! Looks strange and it really is, but it works.


    def measure_2D_AWG(self):
        '''
        x_vec is sequence in AWG
        '''
        
        if self.y_set_obj == None:
            print 'axes parameters not properly set...aborting'
            return
    
        qt.mstart()
        qt.msleep()   # if stop button was pressed by now, abort without creating data files
        
        self.mode = 3  # 1: 1D, 2: 2D, 3:1D_AWG/2D_AWG
        self._prepare_measurement_file()
        
        if self.show_progress_bar: 
            p = Progress_Bar(len(self.y_vec),name=self.dirname)
        try:
            # measurement loop
            for it in range(len(self.y_vec)):
                qt.msleep() # better done during measurement (waiting for trigger)
                self.y_set_obj(self.y_vec[it])
                self._append_data(iteration=it)
                if self.show_progress_bar: p.iterate()
        finally:
            self._end_measurement()
        
            qt.mend()

    def measure_1D_ddc_time_trace(self):
        """
        measures the time evolution of your transmission / reflection
        in your network by performing a digital down conversion
        :return: None
        """
        time_end = float(self.mspec.get_samples())/self.mspec.get_samplerate()
        time_array = np.linspace(0, time_end, self.mspec.get_samples())
        self.set_x_parameters(time_array, 'time', True, 'sec')
        self.mode = 1  # 1: 1D, 2: 2D, 3:1D_AWG/2D_AWG
        self._prepare_measurement_file()
        try:
            qt.msleep()
            self._append_data(ddc=True)
        finally:
            self._end_measurement()
            qt.mend()

    def measure_2D_ddc_time_trace(self):
        """
        Performs a digital down conversion for exactly one value in your awg sequence. But you can sweep other
        parameters, such as mw-power or so.
        :return:
        """
        if self.y_set_obj is None:
            print 'axes parameters not properly set...aborting'
            return
        time_end = float(self.mspec.get_samples())/self.mspec.get_samplerate()
        time_array = np.linspace(0, time_end, self.mspec.get_samples())
        self.set_x_parameters(time_array, 'time', True, 'sec')

        self.mode = 2  # 1: 1D, 2: 2D, 3:1D_AWG/2D_AWG
        self._prepare_measurement_file()

        if self.show_progress_bar:
            p = Progress_Bar(len(self.y_vec),name=self.dirname)
        try:
            for y in self.y_vec:
                qt.msleep()
                self.y_set_obj(y)
                qt.msleep()
                self._append_data(ddc=True)
                if self.show_progress_bar: p.iterate()
        finally:
            self._end_measurement()
            qt.mend()

    def measure_1D_awg_ddc_timetrace(self):
        """
        Performs a digital down conversion of your readout trace for every value in your y-vector,
        whereas y_vec should be awg sequence. This function is useful for magnon cavity experiments.
        x-vec is automatically set by acquisition window.
        (Also, all data are there at once as iteration is not yet implemented)
        :return:
        """
        if self.y_vec is None:
            print 'axes parameters not properly set...aborting'
            return
        time_end = float(self.mspec.get_samples())/self.mspec.get_samplerate()
        time_array = np.linspace(0, time_end, self.mspec.get_samples())
        self.set_x_parameters(time_array, 'time', True, 'sec')

        self.mode = 2  # 1: 1D, 2: 2D, 3:1D_AWG/2D_AWG (2D, since iterations is not yet implemented)
        self._prepare_measurement_file()

        try:
            qt.msleep()
            self._append_data(ddc=True)
        finally:
            self._end_measurement()
            qt.mend()


    def _prepare_measurement_file(self):
        if self.dirname == None:
            self.dirname = self.x_coordname

        self.ndev = len(self.readout.get_tone_freq())  # returns array of readout freqs (=1 for non-multiplexed readout)
        
        self._hdf = hdf.Data(name=self.dirname, mode='a')
        self._hdf_x = self._hdf.add_coordinate(self.x_coordname, unit = self.x_unit)
        self._hdf_x.add(self.x_vec)
        
        self._settings = self._hdf.add_textlist('settings')
        settings = waf.get_instrument_settings(self._hdf.get_filepath())
        self._settings.append(settings)
        
        self._log = waf.open_log_file(self._hdf.get_filepath())

        self._hdf_readout_frequencies = self._hdf.add_value_vector(self.multiplex_attribute, unit = self.multiplex_unit)
        self._hdf_readout_frequencies.append(self.readout.get_tone_freq())
        
        if self.ReadoutTrace:
            self._hdf_TimeTraceAxis = self._hdf.add_coordinate('recorded timepoint', unit = 's')
            self._hdf_TimeTraceAxis.add(np.arange(self.mspec.get_samples())/self.readout.get_adc_clock())
        
        if self.mode == 1: #1D
            self._hdf_amp = []
            self._hdf_pha = []
            for i in range(self.ndev):
                self._hdf_amp.append(self._hdf.add_value_vector('amplitude_%i'%i, x = self._hdf_x, unit = 'a.u.'))
                self._hdf_pha.append(self._hdf.add_value_vector('phase_%i'%i, x = self._hdf_x, unit='rad'))
            if self.ReadoutTrace:
                self._hdf_I = self._hdf.add_value_matrix('I_TimeTrace', x = self._hdf_x, y = self._hdf_TimeTraceAxis,
                                                         unit = 'V', save_timestamp = False)
                self._hdf_Q = self._hdf.add_value_matrix('Q_TimeTrace', x = self._hdf_x, y = self._hdf_TimeTraceAxis,
                                                         unit = 'V', save_timestamp = False)
        
        elif self.mode == 2: #2D
            self._hdf_y = self._hdf.add_coordinate(self.y_coordname, unit = self.y_unit)
            self._hdf_y.add(self.y_vec)
            self._hdf_amp = []
            self._hdf_pha = []
            for i in range(self.ndev):
                self._hdf_amp.append(self._hdf.add_value_matrix('amplitude_%i'%i, x = self._hdf_y, y = self._hdf_x, unit = 'a.u.'))
                self._hdf_pha.append(self._hdf.add_value_matrix('phase_%i'%i, x = self._hdf_y, y = self._hdf_x, unit = 'rad'))
            if self.ReadoutTrace:
                self._hdf_I = self._hdf.add_value_matrix('I_TimeTrace', x = self._hdf_y, y = self._hdf_TimeTraceAxis,
                                                         unit = 'V', save_timestamp = False)
                self._hdf_Q = self._hdf.add_value_matrix('Q_TimeTrace', x = self._hdf_y, y = self._hdf_TimeTraceAxis,
                                                         unit = 'V', save_timestamp = False)
                
                
        elif self.mode == 3: #1D_AWG/2D_AWG
            self._hdf_y = self._hdf.add_coordinate(self.y_coordname, unit = self.y_unit)
            self._hdf_y.add(self.y_vec)
            self._hdf_amp = []
            self._hdf_pha = []
            for i in range(self.ndev):
                self._hdf_amp.append(self._hdf.add_value_matrix('amplitude_%i'%i,
                                                                x = self._hdf_y, y = self._hdf_x, unit = 'a.u.'))
                self._hdf_pha.append(self._hdf.add_value_matrix('phase_%i'%i,
                                                                x = self._hdf_y, y = self._hdf_x, unit='rad'))
            if self.ReadoutTrace:
                self._hdf_I = self._hdf.add_value_box('I_TimeTrace', x = self._hdf_y, y = self._hdf_x,
                                                      z = self._hdf_TimeTraceAxis, unit = 'V', save_timestamp = False)
                self._hdf_Q = self._hdf.add_value_box('Q_TimeTrace', x = self._hdf_y, y = self._hdf_x,
                                                      z = self._hdf_TimeTraceAxis, unit = 'V', save_timestamp = False)
        
        if self.create_averaged_data:
            self._hdf_amp_avg = []
            self._hdf_pha_avg = []
            for i in range(self.ndev):
                self._hdf_amp_avg.append(self._hdf.add_value_vector('amplitude_avg_%i'%i, x = self._hdf_x, unit = 'a.u.'))
                self._hdf_pha_avg.append(self._hdf.add_value_vector('phase_avg_%i'%i, x = self._hdf_x, unit='rad'))

        if self.comment:
            self._hdf.add_comment(self.comment)
        if self.qviewkit_singleInstance and self.open_qviewkit and self._qvk_process:
            self._qvk_process.terminate() #terminate an old qviewkit instance
        if self.open_qviewkit:
            self._qvk_process = qviewkit.plot(self._hdf.get_filepath(), datasets=['amplitude', 'phase'])
        
    def _append_data(self, iteration=0, ddc=None):
        if self.ReadoutTrace:
            ampliData, phaseData, Is, Qs = self.readout.readout(timeTrace=True, ddc=ddc)
        else:
            ampliData, phaseData = self.readout.readout(timeTrace=False, ddc=ddc)
            
        if len(ampliData.shape) < 3:  # "normal" measurements
            for i in range(self.ndev):
                self._hdf_amp[i].append(np.atleast_1d(ampliData.T[i]))
                self._hdf_pha[i].append(np.atleast_1d(phaseData.T[i]))
            if self.ReadoutTrace:
                if self.mode < 3:  # mode 2 not yet fully supported but working for DDC timetrace experiments
                    self._hdf_I.append(Is)
                    self._hdf_Q.append(Qs)
                if self.mode == 3:
                    for ix in range(len(self.x_vec)):
                        self._hdf_I.append(Is[:, ix])
                        self._hdf_Q.append(Qs[:, ix])
                    self._hdf_I.next_matrix()
                    self._hdf_Q.next_matrix()
        
        else:  # for AWG DDC ReadoutTrace, all data are there at once
            for i in range(self.ndev):
                for j in range(ampliData.T.shape[2]):
                    self._hdf_amp[i].append(np.atleast_1d(ampliData.T[i,:,j]))
                    self._hdf_pha[i].append(np.atleast_1d(phaseData.T[i,:,j]))
                    if self.ReadoutTrace:
                        self._hdf_I.append(Is[:,j])
                        self._hdf_Q.append(Qs[:,j])
                        
        if self.create_averaged_data:
            if iteration == 0:
                self.avg_complex_sum = ampliData * np.exp(1j*phaseData)
                for i in range(self.ndev):
                    self._hdf_amp_avg[i].append(np.atleast_1d(ampliData.T[i]))
                    self._hdf_pha_avg[i].append(np.atleast_1d(phaseData.T[i]))
            else:
                self.avg_complex_sum += ampliData * np.exp(1j*phaseData)
                amp_avg = np.abs(self.avg_complex_sum/(iteration+1))
                pha_avg = np.angle(self.avg_complex_sum/(iteration+1))
                for i in range(self.ndev):
                    self._hdf_amp_avg[i].ds.write_direct(np.ascontiguousarray(np.atleast_1d(amp_avg.T[i])))
                    self._hdf_pha_avg[i].ds.write_direct(np.ascontiguousarray(np.atleast_1d(pha_avg.T[i])))
                    self._hdf_pha_avg[i].ds.attrs['iteration'] = iteration+1
                    self._hdf_amp_avg[i].ds.attrs['iteration'] = iteration+1
                self._hdf.flush()
    

    def _end_measurement(self):
        t = threading.Thread(target=qviewkit.save_plots,args=[self._hdf.get_filepath(),self._plot_comment])
        t.start()
        self._hdf.close_file()
        waf.close_log_file(self._log)
        qkit.store_db.add(self._hdf.get_filepath())
        
    def set_plot_comment(self, comment):
        '''
        Small comment to add at the end of plot pics for more information i.e. good for wiki entries.
        '''
        self._plot_comment=comment