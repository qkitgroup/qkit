import numpy as np
import logging
import matplotlib.pylab as plt
from time import sleep
import qt

from qkit.storage import hdf_lib as hdf
#from qkit.gui.plot import plot as qviewkit
from qkit.gui.notebook.Progress_Bar import Progress_Bar

##################################################################

class transport(object):

    '''
    useage:
    
    m = transport(daq = 'DAQ')
    
    m.set_voltage_bias('True')
    m.set_measurement_setup_parameters(conversion_IV = 1e7, V_amp=1, I_div=1, V_divider=1000)
    m.set_measurement_parameters(start=-100e-6, stop=100e-7, sample_count=1000, sample_rate=200, sweeps = 3)
    m.set_x_parameters(arange(0.,1.5,0.05),'magnetic coil current', yoko.set_current, 'A')
    #m.set_y_parameters(arange(4e9,7e9,10e6),'excitation frequency', mw_src.set_frequency, 'Hz')
    #sweep-parameter only active for x.measure_IV()!!
    m.measure_IV_2D()
    '''

    def __init__(self, daq, exp_name = ''):

        self.daq = daq
        self._chan_out = self.daq._ins._get_output_channels()[0]
        self._chan_in = self.daq._ins._get_input_channels()[0]

        self._tdx = 0.002
        self._tdy = 0.002

        self.plotlive = True
        self.comment = ''
        self.exp_name = exp_name

        self._voltage_bias = False
        self._current_bias = True

        self._voltage_offset = 0.
        self._current_offset = 0.

    def set_x_parameters(self, x_vec, x_coordname, x_instrument, x_unit):
        self.x_vec = x_vec
        self.x_coordname = x_coordname
        self.x_set_obj = x_instrument
        self.x_unit = x_unit
        self._set_x_parameters = True

    def set_y_parameters(self, y_vec, y_coordname, y_instrument, y_unit):
        self.y_vec = y_vec
        self.y_coordname = y_coordname
        self.y_set_obj = y_instrument
        self.y_unit = y_unit
        self._set_y_parameters = True

    def set_measurement_setup_parameters(self, conversion_IV, V_amp, I_div, V_divider):
        self._conversion_IV = conversion_IV
        self._V_amp = V_amp
        self._I_div = I_div
        self._V_divider = V_divider
        self._set_measurement_setup_parameters = True

    def set_measurement_parameters(self, start, stop, sample_count, sample_rate, sweeps=1):
        self._start = start
        self._stop = stop
        self._sample_count = sample_count
        self._sample_rate = sample_rate
        self._sweeps = sweeps
        self._vec_fw = np.linspace(start, stop, sample_count)
        self._vec_bw = np.linspace(stop, start, sample_count)
        self._set_measurement_parameters = True

    def _check_measurement(self):
        if self._voltage_bias == self._current_bias:
            logging.error('Please specify current- or voltage-bias, both are %s...aborting' % (str(self._voltage_bias)))
            return False
        if not self._set_measurement_setup_parameters:
            logging.error('Please set_measurement_setup_parameters...aborting')
            return False          
        if not self._set_measurement_parameters:
            logging.error('Please set_measurement_parameters...aborting')
            return False     
        if self._measure_IV_2D or self._measure_IV_3D and not self._set_x_parameters:
            logging.error('Please set_x_parameters...aborting')
            return False
        if self._measure_IV_3D and not self._set_y_parameters:
            logging.error('Please set_y_parameters...aborting')
            return False
        return True

    def _save_settings(self):
            name_settings = str(self._data.get_filepath()).replace('.h5', '_SETTINGS.txt')
            settings = open(name_settings, "w")

            settings.write("## Settings for measurement, "+self._scan_name)
            settings.write("\nA per V = %f\nV_amp = %f\nI_div = %f\nV_div = %f\nsamples = %f\nrate = %f\nsweeps = %f\n" % (float(self._conversion_factor), float(self._V_amp), float(self._I_div), float(self._V_div), float(self._sample_count), float(self._sample_rate), float(self._sweeps)))
            settings.write('Voltage bias = %s, Current bias = %s' %(str(self._voltage_bias), str(self._current_bias)))
            settings.write("\nMin = %f \nMax = %f \n" % (self._start, self._stop))
            if not self._measure_IV:
                settings.write("\n%s, %f-%f %s, step = %f " % (self.x_instrument, self.x_vec[0], self.x_vec[len(self.x_vec)-1], (self.x_vec[len(self.x_vec)-1]-self.x_vec[0])/(len(self.x_vec)-1)))
            if self._measure_IV_3D:
                settings.write("\n%s, %f-%f %s, step = %f " % (self.y_instrument, self.y_vec[0], self.y_vec[len(self.y_vec)-1], (self.y_vec[len(self.y_vec)-1]-self.y_vec[0])/(len(self.y_vec)-1)))
            settings.write("Current offset %f A\n" %(self._current_offset))
            settings.write("Voltage offset %f V\n" %(self._voltage_offset))

            settings.close()

    def measure_IV(self):
        self._measure_IV_1D = True
        self._measure_IV_2D = False
        self._measure_IV_3D = False
        if not self._check_measurement: 
            return

        self._scan_name = 'IV'
        if self.exp_name: 
            self._scan_name += '_' + self.exp_name
        self._p = Progress_Bar(self._sweeps)

        self._prepare_measurement_file() 
        self._save_settings()
        #qviewkit.plot_hdf(self._data.get_filepath()

        self._measure()
        self._end_measurement()


    def measure_IV_2D(self):
        self._measure_IV_1D = False
        self._measure_IV_2D = True
        self._measure_IV_3D = False
        if not self._check_measurement: 
            return

        self._scan_name = 'IV_vs_'+ self.x_coordname
        if self.exp_name: 
            self._scan_name += '_' + self.exp_name
        self._p = Progress_Bar(len(self.x_vec))

        self._prepare_measurement_file()
        self._save_settings()
        #qviewkit.plot_hdf(self._data.get_filepath())

        self._measure()
        self._end_measurement()


    def measure_IV_3D(self):
        self._measure_IV_1D = False
        self._measure_IV_2D = False
        self._measure_IV_3D = True
        if not self._check_measurement: 
            return

        self._scan_name = 'IV_vs_'+ self.x_coordname + '_' + self.y_coordname
        if self.exp_name: 
            self._scan_name += '_' + self.exp_name
        self._p = Progress_Bar(len(self.x_vec)*len(self.y_vec))

        self._prepare_measurement_file()
        self._save_settings()
        #qviewkit.plot_hdf(self._data.filepath())

        self._measure()
        self._end_measurement()

    def _prepare_measurement_file(self):
        self._data = hdf.Data(name=self._scan_name)

        if self._voltage_bias:
            bias_name = 'Voltage'
            bias_unit = 'V'
            measurement_name = 'Current'
            measurement_unit = 'A'
        if self._current_bias:
            bias_name = 'Current'
            bias_unit = 'A'
            measurement_name = 'Voltage'
            measurement_unit = 'V'

        self._data_bias = self._data.add_coordinate(bias_name, unit = bias_unit)
        bias_vec = np.append(self._vec_fw, self._vec_bw)
        self._data_bias.add(bias_vec)

        if self._measure_IV_1D:
            if self._sweeps == 1:
                self._data_measure = self._data.add_value_vector(measurement_name, x = self._hdf_bias, unit = measurement_unit)
            else:
                self._data_sweep = self._data.add_coordinate('sweep')
                self._data_sweep.add([sweep for sweep in self._sweeps])
                self._data_measure = self._data.add_value_matrix(measurement_name, x = self._data_sweep, y = self._hdf_bias, unit = measurement_unit)
        if self._measure_IV_2D:
            self._data_x = self._dat.add_coordinate(self.x_coordname, unit = self.x_unit)
            self._data_x.add(self.x_vec)
            self._data_measure = self._data.add_value_matrix(measurement_name, x = self._x, y = self._hdf_bias, unit = measurement_unit)

        if self._measure_IV_3D:
            self._data_x = self._data.add_coordinate(self.x_coordname, unit = self.x_unit)
            self._data_x.add(self.x_vec) 
            self._data_y = self._data.add_coordinate(self.y_coordname, unit = self.y_unit)
            self._data_y.add(self.y_vec) 
            self._data_measure = self._data.add_value_box(measurement_name, x = self._data_x, y = self._data_y, z = self._hdf_bias, unit = measurement_unit)

        if self.comment:
            self._data.add_comment(self.comment)

    def _measure(self):
        qt.mstart()
        plt.gca().set_xlabel("V [uV]")
        plt.gca().set_ylabel("I [nA]")
        try:
            if self._measure_IV_1D:
                for self._sweep in np.arange(self._sweeps):
                    if self._current_bias:
                        self._take_IV(out_conversion_factor = self._conversion_IV, in_amplification = self._V_amp, out_divider = self._V_divider)
                    if self._voltage_bias:
                        self._take_IV(out_conversion_factor = 1, in_amplification = self._conversion_IV, out_divider = self._V_divider)
                    self._p_iterate()

            if self._measure_IV_2D or self._measure_IV_3D:
                for self._x in self.x_vec:
                    self.x_set_obj(self._x)
                    sleep(self._tdx)

                    if self._measure_IV_2D:
                        if self._current_bias:
                            self._take_IV(out_conversion_factor = self._conversion_IV, in_amplification = self._V_amp, out_divider = self._V_divider)
                        if self._voltage_bias:
                            self._take_IV(out_conversion_factor = 1, in_amplification = self._conversion_IV, out_divider = self._V_divider)
                        self._p.iterate()

                    if self._measure_IV_3D:
                        for self._y in self.y_vec:
                            self.y_set_obj(self._y)
                            sleep(self._tdy)
                            if self._current_bias:
                                self._take_IV(out_conversion_factor = self._conversion_IV, in_amplification = self._V_amp, out_divider = self._V_divider)
                            if self._voltage_bias:
                                self._take_IV(out_conversion_factor = 1, in_amplification = self._conversion_IV, out_divider = self._V_divider)
                            self._p.iterate()

        finally:
            self.daq.set_ao1(0)
            qt.mend()

    def _end_measurement(self):
        print self._data.get_filepath()
        self._data.close_file()

    def _take_IV(self, out_conversion_factor,in_amplification,out_divider=1):
        """ IV measurement with current or voltage (vec_fw, vec_bw)!"""
        data_IV = self.daq.sync_output_input(self._chan_out, self._chan_in, self._vec_fw * out_divider / out_conversion_factor, rate=self._sample_rate)
        if self._current_bias:
            self._pl1 = plt.plot((data_IV/in_amplification)*1e6,self._vec_fw*1e6,"o")
        else:
            self._pl1 = plt.plot(self._vec_fw*1e6, (data_IV/in_amplification)*1e9,"-")
        qt.msleep(0.1)

        data_measure = []
        data_measure = np.append(data_measure, data_IV/in_amplification)

        data_IV = self.daq.sync_output_input(self._chan_out, self._chan_in, self._vec_bw * out_divider / out_conversion_factor, rate=self._sample_rate)
        if self._current_bias:
            self._pl1 = plt.plot((data_IV/in_amplification)*1e6,self._vec_fw*1e6,"o")
        else:
            self._pl1 = plt.plot(self._vec_fw*1e6, (data_IV/in_amplification)*1e9,"-")
        qt.msleep(0.1)

        data_measure = np.append(data_measure, data_IV/in_amplification)
        self._data_measure.append(data_measure)

    def set_tdx(self, tdx):
        self._tdx = tdx

    def set_tdy(self, tdy):
        self._tdy = tdy

    def get_tdx(self):
        return self.tdx

    def get_tdy(self):
        return self.tdy

    def set_voltage_bias(self, voltage_bias):
        self._voltage_bias = voltage_bias
        self._current_bias = not voltage_bias

    def get_voltage_bias(self):
        return self._voltage_bias

    def set_current_bias(self, current_bias):
        self._current_bias = current_bias
        self._voltage_bias = not current_bias

    def get_current_bias(self):
        return self._current_bias

    def set_voltage_offset(self, voltage_offset):
        self._voltage_offset = voltage_offset

    def set_current_offset(self, voltage_offset):
        self._current_offset = voltage_offset

    def get_voltage_offset(self):
        return self._voltgae_offset

    def get_current_offset(self):
        return self._current_offset