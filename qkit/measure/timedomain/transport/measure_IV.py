import numpy as np
import logging
import matplotlib.pylab as plt
from time import sleep
import qt

from qkit.storage import hdf_lib as hdf
#from qkit.gui.plot import plot as qviewkit
from qkit.gui.notebook.Progress_Bar import Progress_Bar

#ttip = qt.instruments.get('ttip')
#vcoil = qt.instruments.get('vcoil')

##################################################################

class transport(object):

    '''
    useage:
    
    m = transport(daq = 'DAQ')
    
    m.set_voltage_bias('True')
    m.set_measurement_setup_parameters(conversion_IV = 1e7, V_amp=1, I_div=1, V_divider=1000)
    m.set_measurement_parameters(start=-100e-6, stop=100e-7, sample_count=1000, sample_rate=200, sweeps=5)
    m.set_x_parameters(arange(0.,1.5,0.05),'magnetic coil current', yoko.set_current, 'A')
    #m.set_y_parameters(arange(4e9,7e9,10e6),'excitation frequency', mw_src.set_frequency, 'Hz')
        
    m.measure_IV_2D()
    '''

    def __init__(self, daq, exp_name = ''):

        self.daq = daq
        self._chan_Iout = self.daq._ins._get_output_channels()[0]
        self._chan_Vin = self.daq._ins._get_input_channels()[0]

        self.tdx = 0.002
        self.tdy = 0.002

        self.plotlive = True
        self.comment = ''
        self.exp_name = exp_name

        self._voltage_bias = False
        self._current_bias = True
        
        self._voltage_offset = 0.
        self._current_offset = 0.
        
        self.save_dat = True
        self.save_hdf = False

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
    
    def set_measurement_parameters(self, start, stop, sample_count, sample_rate, sweeps):
        self._start = start
        self._stop = stop
        self._sample_count = sample_count
        self._sample_rate = sample_rate
        self._sweeps = sweeps
        self._vec_fw = np.linspace(start, stop, sample_count)
        self._vec_bw = np.linspace(stop, start, sample_count)
        self._set_measurement_parameters = True
    
    def set_voltage_bias(self, voltage_bias):
        self._voltage_bias = voltage_bias
        self._current_bias = not voltage_bias
        
    def set_current_bias(self, current_bias):
        self._current_bias = current_bias
        self._voltage_bias = not current_bias
    
    def set_voltage_offset(self, voltage_offset):
        self._voltage_offset = voltage_offset

    def set_current_offset(self, voltage_offset):
        self._current_offset = voltage_offset        
    
    def _check_measurement(self):
        if not self._voltage_bias and not self._current_bias:
            logging.error('Please specify current- or voltage-bias...aborting')
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
            name_settings = (self._data.get_filepath().split(self._data.get_filename())[0])+self._scan_name+"_SETTINGS.txt"
            settings = open(name_settings, "w")

            settings.write("## Settings for measurement, "+self._scan_name)
            settings.write("\nA per V = %f\nV_amp = %f\nI_div = %f\nV_div = %f\nsamples = %f\nrate = %f\nsweeps = %f\n" % (float(self._conversion_factor), float(self._V_amp), float(self._I_div), float(self._V_div), float(self._sample_count), float(self._sample_rate), float(self._sweeps)))
            settings.write('Voltage bias = %s, Current bias = %s' %(str(self._voltage_bias), str(self._current_bias)))
            settings.write("\nMin = %f \nMax = %f \n" % (self._start, self._stop))
            if not self._measure_IV:
                settings.write("\n%s, %f-%f %s, step = %f " % (self.x_instrument, self.x_vec[0], self.x_vec[len(self.x_vec)-1], (self.x_vec[len(self.x_vec)-1]-self.x_vec[0])/(len(self.x_vec)-1)))
            if self._measure_IV_3D:
                settings.write("\n%s, %f-%f %s, step = %f " % (self.y_instrument, self.y_vec[0], self.y_vec[len(self.y_vec)-1], (self.y_vec[len(self.y_vec)-1]-self.y_vec[0])/(len(self.y_vec)-1)))
            if self._current_offset: settings.write("Current offset %f\n" %(self._current_offset))
            if self._voltage_offset: settings.write("Voltage offset %f\n" %(self._voltage_offset))

            settings.close()
        
    def measure_IV(self):
        self._measure_IV = True
        self._measure_IV_2D = False
        self._measure_IV_3D = False
        if not self._check_measurement: 
            return
            
        self._scan_name = 'IV'
        if self.exp_name: 
            self._scan_name += '_' + self.exp_name
        self._p = Progress_Bar(len(self.x_vec))

        self._save_settings()
        if self.save_dat:
            self._prepare_measurement_dat_file()
        if self.save_hdf:        
            self._prepare_measurement_hdf_file() 
            #qviewkit.plot_hdf(self._data_hdf.get_filepath(), datasets=['amplitude', 'ahase'])

        self._measure()
        self._end_measurement()


    def measure_IV_2D(self):
        self._measure_IV = False
        self._measure_IV_2D = True
        self._measure_IV_3D = False
        if not self._check_measurement: 
            return
            
        self._scan_name = 'IV_vs_'+ self.x_coordname
        if self.exp_name: 
            self._scan_name += '_' + self.exp_name
        self._p = Progress_Bar(len(self.x_vec))

        self._save_settings()
        if self.save_dat:
            self._prepare_measurement_dat_file()
        if self.save_hdf:
            self._prepare_measurement_hdf_file()
            #qviewkit.plot_hdf(self._data_hdf.get_filepath())#, datasets=['amplitude', 'ahase'])

        self._measure()
        
        self._end_measurement()


    def measure_IV_3D(self):
        self._measure_IV = False
        self._measure_IV_2D = False
        self._measure_IV_3D = True
        if not self._check_measurement: 
            return
            
        self._scan_name = 'IV_vs_'+ self.x_coordname + '_' + self.y_coordname
        if self.exp_name: 
            self._scan_name += '_' + self.exp_name
        self._p = Progress_Bar(len(self.x_vec)*len(self.y_vec))
        
        self._save_settings()
        if self.save_dat:
            self._prepare_measurement_dat_file()
        if self.save_hdf:
            self._prepare_measurement_hdf_file()
            #gui.plot.plot(self._data_hdf.filepath(), datasets=['Amplitude', 'Phase'])

        self._measure()

        self._end_measurement()

    def _prepare_measurement_dat_file(self):
        self._data_dat = qt.Data(name=self._scan_name)
        if self.voltage_bias:
            self._data_dat.add_coordinate('V [V]')
        else:
            self._data_dat.add_coordinate('I [A]')
        if not self._measure_IV:
            self._data_dat.add_coordinate(self.x_coordname+'['+self.x_unit+']')
        if self._measure_IV_3D:
            self._data_dat.add_coordinate(self.y_coordname+'['+self.y_unit+']')
        if self.voltage_bias:
            self._data_dat.add_value('I [A]')
        else:
            self._data_dat.add_value('V [V]')

        if self.comment:
            self._data_dat.add_comment(self.comment)
        self._data_dat.create_file()
    
    def _prepare_measurement_hdf_file(self):
        filename = str(self._data_dat.get_filepath()).replace('.dat','.h5')
        self._data_hdf = hdf.Data(name=self._scan_name, path=filename)
        if self._voltage_bias:
            self._hdf_bias = self._data_hdf.add_coordinate('Voltage', unit = 'V')
            self._hdf_bias.add(self._vec_fw)
            self._hdf_bias.add(self._vec_bw)
            if self._measure_IV:
                self._hdf_measure = self._data_hdf.add_value_vector('Current', x = self._hdf_bias, unit = 'A')
            if self._measure_IV_2D:
                self._hdf_x = self._data_hdf.add_coordinate(self.x_coordname, unit = self.x_unit)
                self._hdf_x.add(self.x_vec) 
                self._hdf_measure = self._data_hdf.add_value_matrix('Current', x = self._hdf_bias, y = self._hdf_x, unit = 'A')
            if self._measure_IV_3D:
                self._hdf_x = self._data_hdf.add_coordinate(self.x_coordname, unit = self.x_unit)
                self._hdf_x.add(self.x_vec) 
                self._hdf_y = self._data_hdf.add_coordinate(self.y_coordname, unit = self.y_unit)
                self._hdf_y.add(self.y_vec) 
                self._hdf_measure = self._data_hdf.add_value_box('Current', x = self._hdf_bias, y = self._hdf_x, z = self._hdf_y, unit = 'A')               
        else:
            self._hdf_bias = self._data_hdf.add_coordinate('Current', unit = 'A')
            self._hdf_bias.add(self._vec_fw)
            self._hdf_bias.add(self._vec_bw)
            if self._measure_IV:
                self._hdf_measure = self._data_hdf.add_value_vector('Voltage', x = self._hdf_bias, unit = 'V')
            if self._measure_IV_2D:
                self._hdf_x = self._data_hdf.add_coordinate(self.x_coordname, unit = self.x_unit)
                self._hdf_x.add(self.x_vec) 
                self._hdf_measure = self._data_hdf.add_value_matrix('Voltage', x = self._hdf_bias, y = self._hdf_x, unit = 'V')
            if self._measure_IV_3D:
                self._hdf_x = self._data_hdf.add_coordinate(self.x_coordname, unit = self.x_unit)
                self._hdf_x.add(self.x_vec) 
                self._hdf_y = self._data_hdf.add_coordinate(self.y_coordname, unit = self.y_unit)
                self._hdf_y.add(self.y_vec) 
                self._hdf_measure = self._data_hdf.add_value_box('Voltage', x = self._hdf_bias, y = self._hdf_x, z = self._hdf_y, unit = 'V')  

        if self.comment:
            self._data_hdf.add_comment(self.comment) 

    def _measure(self):
        qt.mstart()
        plt.gca().set_xlabel("V [uV]")
        plt.gca().set_ylabel("I [nA]")
        try:
            if not self.measure:
                for self._x in self.x_vec:
                    self.x_set_obj(self._x)
                    sleep(self.tdx)
                    
                    if self._measure_3D:
                        for self._y in self.y_vec:
                            self.y_set_obj(self._y)
                            sleep(self.tdy)
                            for i in np.arange(self._sweeps):
                                if self._current_bias: self._take_IV(out_conversion_factor = self._conversion_IV, in_amplification = self._V_amp, out_divider = self._V_divider, in_offset=0)
                                if self._voltage_bias: self._take_IV(out_conversion_factor = 1, in_amplification = self._conversion_IV, out_divider = self._V_divider, in_offset=0)
                                self._data_dat.new_block()
                            self._p.iterate()
                    else:
                        for i in np.arange(self._sweeps):
                            if self._current_bias: self._take_IV(out_conversion_factor = self._conversion_IV, in_amplification = self._V_amp, out_divider = self._V_divider, in_offset=0)
                            if self._voltage_bias: self._take_IV(out_conversion_factor = 1, in_amplification = self._conversion_IV, out_divider = self._V_divider, in_offset=0)
                            self._data_dat.new_block()
                        self._p.iterate()
            else:
                for i in np.arange(self._sweeps):
                    self._take_IV()
                    self._data_dat.new_block()
                self._p_iterate()

        finally:
            self._daq.set_ao1(0)
            qt.mend()

    def _end_measurement(self):
        print self._data_dat.get_filepath()
        self._data_dat.close_file()
        if self.save_hdf:
            print self._data_hdf.get_filepath()
            self._data_hdf.close_file()

    def take_IV(self, out_conversion_factor,in_amplification,out_divider=1, in_offset=0):
        """ IV measurement with current or voltage (vec_fw, vec_bw) and a second parameter (vec_2) """
        mydata=self.daq.sync_output_input(self._chan_Iout,self._chan_Vin,self._vec_fw*out_divider/out_conversion_factor,rate=self._sample_rate)
        if self._measure_IV:
            self._data_dat.add_data_point(self.vec_fw, mydata/in_amplification)
        if self._measure_IV_2D:
            self._data_dat.add_data_point(self.vec_fw, [self._x for v in self._vec_fw], mydata/in_amplification)
        if self._measure_IV_3D:
            x_vec = []
            y_vec = []
            for v in self._vec_fw:
                x_vec.append(self._x)
                y_vec.append(self._y)
            self._data_dat.add_data_point(self.vec_fw, x_vec, y_vec, mydata/in_amplification)
        hdf_measure = []
        hdf_measure = np.append(hdf_measure, mydata/in_amplification)

        if self._current_bias:
            self._pl1 = plt.plot((mydata/in_amplification)*1e6,self._vec_fw*1e6,"o")
        else:
            self._pl1 = plt.plot(self._vec_fw*1e6, (mydata/in_amplification)*1e9,"-")
        qt.msleep(0.1)
        
        mydata=self.daq.sync_output_input(self._chan_Iout,self._chan_Vin,self._vec_bw*out_divider/out_conversion_factor,rate=self._sample_rate)
        if self._measure_IV:
            self._data_dat.add_data_point(self.vec_bw, mydata/in_amplification)
        if self._measure_IV_2D:
            x_vec = []
            for v in self._vec_bw:
                x_vec.append(self._x)
            self._data_dat.add_data_point(self.vec_bw, x_vec, mydata/in_amplification)
        if self._measure_IV_3D:
            x_vec = []
            y_vec = []
            for v in self._vec_bw:
                x_vec.append(self._x)
                y_vec.append(self._y)
            self._data_dat.add_data_point(self.vec_bw, x_vec, y_vec, mydata/in_amplification)
        hdf_measure = np.append(hdf_measure, mydata/in_amplification)
        self._hdf_measure.append(np.array(hdf_measure))
        
        if self._current_bias:
            self._pl1 = plt.plot((mydata/in_amplification)*1e6,self._vec_bw*1e6,"+")
        if self._voltage_bias:
            self._pl1 = plt.plot(self._vec_bw*1e6, (mydata/in_amplification)*1e9,"-")
        qt.msleep(0.1)


    def set_tdx(self, tdx):
        self.tdx = tdx

    def set_tdy(self, tdy):
        self.tdy = tdy

    def get_tdx(self):
        return self.tdx

    def get_tdy(self):
        return self.tdy