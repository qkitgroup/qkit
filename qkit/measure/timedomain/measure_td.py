# modified and adapted by JB@KIT 04/2015, 09/2015
# time domain measurement class

import qt
import numpy as np
import os.path
import time
import logging
import sys

from qkit.gui.notebook.Progress_Bar import Progress_Bar
from qkit.storage import hdf_lib as hdf
from qkit.analysis import resonator
from qkit.gui.plot import plot as qviewkit

readout = qt.instruments.get('readout')
mspec = qt.instruments.get('mspec')

class Measure_td(object):
    
    '''
    useage:
    
    m = Measure_td()
    
    m.set_x_parameters(arange(-0.05,0.05,0.01),'flux coil current (mA)',coil.set_current)
    m.set_y_parameters(arange(4e9,7e9,10e6),'excitation frequency (Hz)',mw_src1.set_frequency)
    
    m.measure_XX()
    '''
    
    def __init__(self):
    
        self.comment = None
        self.time_data = False
        
        self.x_set_obj = None
        self.y_set_obj = None
        
        self.dirname = None
        self.plotSuffix = ''
        self.hold = False
        
        self.show_progress_bar = True
        
        self.save_dat = True
        self.save_hdf = True
        
        self.open_qviewkit = False
        
    def set_x_parameters(self, x_vec, x_coordname, x_set_obj, x_unit = ''):
        self.x_vec = x_vec
        self.x_coordname = x_coordname
        self.x_set_obj = x_set_obj
        self.x_unit = x_unit
        
    def set_y_parameters(self, y_vec, y_coordname, y_set_obj, y_unit = ''):
        self.y_vec = y_vec
        self.y_coordname = y_coordname
        self.y_set_obj = y_set_obj
        self.y_unit = y_unit
        
    def measure_1D(self):
    
        if self.x_set_obj == None:
            print 'axes parameters not properly set...aborting'
            return

        #self.time_data = False
        qt.mstart()
        self._prepare_measurement_dat_file(mode='1d')
        self._create_dat_plots(mode='1d')

        if self.show_progress_bar: p = Progress_Bar(len(self.x_vec),name=self.dirname)
        try:
            # measurement loop
            for x in self.x_vec:
                self.x_set_obj(x)
                qt.msleep() # better done during measurement (waiting for trigger)
                self._append_data([x],trace=self.time_data)
                self._update_plots()
                if self.show_progress_bar: p.iterate()
        finally:
            self._safe_plots()
            self._close_files()
            qt.mend()


    def measure_2D(self):

        if self.x_set_obj == None or self.y_set_obj == None:
            print 'axes parameters not properly set...aborting'
            return
        
        qt.mstart()
        self._prepare_measurement_dat_file(mode='2d')
        self._create_dat_plots(mode='2d')

        if self.show_progress_bar: p = Progress_Bar(len(self.x_vec)*len(self.y_vec),name=self.dirname)
        try:
            # measurement loop
            for x in self.x_vec:
                self.x_set_obj(x)
                if self.save_dat: self.data_raw.new_block()
                for y in self.y_vec:
                    qt.msleep() # better done during measurement (waiting for trigge
                    self.y_set_obj(y)
                    #sleep(self.tdy)
                    qt.msleep() # better done during measurement (waiting for trigger)
                    self._append_data([x,y],trace=False)
                    self._update_plots()
                    if self.show_progress_bar: p.iterate()
        finally:
            self._safe_plots()
            self._close_files()
            qt.mend()


    def measure_1D_AWG(self, iterations = 100):
        '''
        use AWG sequence for x_vec, averaging over iterations
        '''
        self.y_vec = range(iterations)
        self.y_coordname = '#iteration'
        self.y_set_obj = lambda y: True
        self.y_unit = ''
        return self.measure_2D_AWG()


    def measure_2D_AWG(self):
        '''
        x_vec is sequence in AWG
        '''
        
        if self.y_set_obj == None:
            print 'axes parameters not properly set...aborting'
            return
    
        qt.mstart()
        qt.msleep()   #if stop button was pressed by now, abort without creating data files
        
        self._prepare_measurement_dat_file(mode='2dAWG')
        self._create_dat_plots(mode='2dAWG')

        if self.show_progress_bar: p = Progress_Bar(len(self.y_vec),name=self.dirname)
        try:
            # measurement loop
            for it in range(len(self.y_vec)):
                qt.msleep() # better done during measurement (waiting for trigger)
                self.y_set_obj(self.y_vec[it])
                self._append_data([self.y_vec[it]],trace=True,it=it)
                self._update_plots()
                if self.show_progress_bar: p.iterate()
        #except Exception as e:
        #   print e
        
        finally:
            self._safe_plots()
            self._generate_avg_data(final=True)
            self._close_files()
        
            qt.mend()


    def _prepare_measurement_dat_file(self,mode):
    
        if self.dirname == None:
            self.dirname = self.x_coordname
            
        if self.save_dat:
            self.data_raw = qt.Data(name='%s_%s'%(mode,self.dirname))
            
            if mode == '2dAWG':
                self.data_raw.add_coordinate(self.y_coordname)
            
            if self.comment:
                self.data_raw.add_comment(self.comment)
                
            self.data_raw.add_coordinate(self.x_coordname)
            self.ndev = len(readout.get_tone_freq())   #returns array of readout frequencies (=1 for non-multiplexed readout)
            for i in range(self.ndev):
                self.data_raw.add_value('amp_%d'%i)
            for i in range(self.ndev):
                self.data_raw.add_value('pha_%d'%i)
            self.data_raw.add_value('timestamp')
            self.data_raw.create_file()
            
            self.data_fn, self.data_fext = os.path.splitext(self.data_raw.get_filepath())
            if mode == '2dAWG':
                self.data_avg = qt.Data(name='avga_%s'%self.dirname)
                if self.comment:
                    self.data_avg.add_comment(self.comment)
                self.data_avg.add_coordinate(self.x_coordname)
                for i in range(self.ndev):
                    self.data_avg.add_value('amp_%d'%i)
                for i in range(self.ndev):
                    self.data_avg.add_value('pha_%d'%i)
                #self.data_avg.create_file(None, '%s_avg.dat'%self.data_fn, False)
            
            if self.time_data:
                self.data_time = qt.Data(name='avgt_%s'%self.dirname)
                # data_time columns: [iteration, coordinate, Is[nSamples], Qs[nSamples], timestamp]
                if self.comment:
                    self.data_time.add_comment(self.comment)
                self.data_time.add_coordinate(self.x_coordname)
                if mode == '2d' or mode == '2dAWG': self.data_time.add_coordinate(self.y_coordname)
                for i in range(mspec.get_samples()):
                    self.data_time.add_coordinate('I%3d'%i)
                for i in range(mspec.get_samples()):
                    self.data_time.add_coordinate('Q%3d'%i)
                self.data_time.add_value('timestamp')
                if self.save_dat: self.data_time.create_file(None, '%s_time.dat'%self.data_fn, False)
                
        if self.save_hdf:
            if self.save_dat:
                filename = str(self.data_raw.get_filepath()).replace('.dat','.h5')   #get same filename as in dat file
            else:
                filename = str(self.dirname) + '.h5'
            self._data_hdf = hdf.Data(name=self.dirname, path=filename)
            self._hdf_x = self._data_hdf.add_coordinate(self.x_coordname, unit = self.x_unit)
            self._hdf_x.add(self.x_vec)
            if mode == '2d' or mode == '2dAWG':
                self._hdf_y = self._data_hdf.add_coordinate(self.y_coordname, unit = self.y_unit)
                self._hdf_y.add(self.y_vec)
                self._hdf_amp = self._data_hdf.add_value_matrix('amplitude', x = self._hdf_y, y = self._hdf_x, unit = 'V')
                self._hdf_pha = self._data_hdf.add_value_matrix('phase', x = self._hdf_y, y = self._hdf_x, unit='rad')
            else:   #1d
                self._hdf_amp = self._data_hdf.add_value_vector('amplitude', x = self._hdf_x, unit = 'V')
                self._hdf_pha = self._data_hdf.add_value_vector('phase', x = self._hdf_x, unit='rad')
            if self.comment:
                self._data_hdf.add_comment(self.comment)
            #qviewkit.close('all') #as20160202
            if self.open_qviewkit:
                qviewkit.plot(self._data_hdf.get_filepath(), datasets=['amplitude', 'phase'])
            
    def _create_dat_plots(self,mode):
        
        self.plots = []
        if mode == '1d':
            for i in range(self.ndev):
                plot_amp = qt.plots.get('amplitude_%d%s'%(i, self.plotSuffix))
                plot_pha = qt.plots.get('phase_%d%s'%(i, self.plotSuffix))
                if not plot_amp or not plot_pha:
                    plot_amp = qt.Plot2D(name='amplitude_%d%s'%(i, self.plotSuffix))
                    plot_pha = qt.Plot2D(name='phase_%d%s'%(i, self.plotSuffix))
                elif not self.hold:
                    plot_amp.clear()
                    plot_pha.clear()
                plot_amp.add(self.data_raw, name='amplitude_%d%s'%(i, self.plotSuffix), coorddim=0, valdim=1+i)
                plot_pha.add(self.data_raw, name='phase_%d%s'%(i, self.plotSuffix), coorddim=0, valdim=1+self.ndev+i)
                self.plots.append(plot_amp)
                self.plots.append(plot_pha)
        elif mode == '2d' or mode == '2dAWG':
            for i in range(self.ndev):
                #3d plot
                plot_amp = qt.Plot3D(self.data_raw, name='amplitude_%d_3d%s'%(i, self.plotSuffix), coorddims=(0,1), valdim=2+i)
                plot_amp.set_palette('bluewhitered')
                self.plots.append(plot_amp)
                plot_pha = qt.Plot3D(self.data_raw, name='phase_%d_3d%s'%(i, self.plotSuffix), coorddims=(0,1), valdim=2+self.ndev+i)
                plot_pha.set_palette('bluewhitered')
                self.plots.append(plot_pha)
                
                if mode == '2dAWG':
                    #averaged plot
                    plot_amp = qt.Plot2D(self.data_avg, name='amplitude_%d%s'%(i, self.plotSuffix), coorddim=0, valdim=1+i, maxtraces = 2)
                    plot_pha = qt.Plot2D(self.data_avg, name='phase_%d%s'%(i, self.plotSuffix), coorddim=0, valdim=1+self.ndev+i, maxtraces = 2)
                    self.plots.append(plot_amp)
                    self.plots.append(plot_pha)

            if mode == '2dAWG':
                # buffer successive sum for averaged plot
                self.dat_cmpls = np.zeros((len(self.x_vec), self.ndev), np.complex128)
                self.dat_ampa = np.zeros_like((len(self.x_vec), self.ndev))
                self.dat_phaa = np.zeros_like(self.dat_ampa)
        
    def _append_data(self,it_v,trace=True,it=None):

        if trace:
            dat_amp, dat_pha, Is, Qs = readout.readout(timeTrace = trace)
        else:
            dat_amp, dat_pha = readout.readout(timeTrace = trace)
        timestamp = time.time()
        
        if self.save_hdf:
            #print np.array(dat_amp).flatten()
            if len(np.array(dat_amp).flatten()) == 1:
                self._hdf_amp.append(float(np.array(dat_amp).flatten()))
                self._hdf_pha.append(float(np.array(dat_pha).flatten()))
            else:
                self._hdf_amp.append(np.array(dat_amp).flatten())
                self._hdf_pha.append(np.array(dat_pha).flatten())
        
        if not trace:
            if isinstance(it_v, (list, tuple, np.ndarray)):   #2d
                dat = np.array(it_v)
            else:   #1d
                dat = np.array([it_v[0]])
            dat = np.append(dat, dat_amp)
            dat = np.append(dat, dat_pha)
            dat = np.append(dat, time.time())   #add time stamp
            self.data_raw.add_data_point(*dat)
            
            #time domain data
            if self.time_data and isinstance(it_v, (list, tuple, np.ndarray)):
                dat = np.array(it_v)
                dat = np.append(dat, Is[:])
                dat = np.append(dat, Qs[:])
                dat = np.append(dat, timestamp)
                self.data_time.add_data_point(*dat)
            
        else:   #2dAWG
            #raw data
            self.data_raw.new_block()
            for xi in range(len(self.x_vec)):
                dat = np.array([it_v[0], self.x_vec[xi]])
                dat = np.append(dat, dat_amp[xi, :])
                dat = np.append(dat, dat_pha[xi, :])
                dat = np.append(dat, timestamp)
                self.data_raw.add_data_point(*dat)
            
            #averaged data
            self.dat_cmpls += dat_amp * np.exp(1j*dat_pha)
            self.dat_ampa = np.abs(self.dat_cmpls/(it+1))
            self.dat_phaa = np.angle(self.dat_cmpls/(it+1))
            self._generate_avg_data()
            
            #time domain data
            if self.time_data:
                self.data_time.new_block()
                for xi in range(len(self.x_vec)):
                    dat = np.array([it_v[0], self.x_vec[xi]])
                    dat = np.append(dat, Is[:, xi])
                    dat = np.append(dat, Qs[:, xi])
                    dat = np.append(dat, timestamp)
                    self.data_time.add_data_point(*dat)
        
    def _update_plots(self):
        #print len(self.plots)
        for plot in self.plots:
            plot.update()
                
    def _safe_plots(self):
        for plot in self.plots:
            plot.update()
            plot.save_gp()
            plot.save_png()
            
    def _generate_avg_data(self,final=False):
        # save averaged data in a separate file
        self.data_avg.create_file(None, '%s_avg.dat'%self.data_fn, False)
        dat = np.concatenate((np.atleast_2d(self.x_vec).transpose(), self.dat_ampa, self.dat_phaa), 1)
        for xi in range(dat.shape[0]):
            self.data_avg.add_data_point(*dat[xi, :])
        self.data_avg.close_file()
        
        if final and self.save_hdf:
            self._hdf_amp_avg = self._data_hdf.add_value_vector('amplitude_avg', x = self._hdf_x, unit = 'V')
            self._hdf_pha_avg = self._data_hdf.add_value_vector('phase_avg', x = self._hdf_x, unit='rad')
            self._hdf_amp_avg.append(np.array(dat[:,1]))
            self._hdf_pha_avg.append(np.array(dat[:,2]))

    def _close_files(self):
        if self.time_data: self.data_time.close_file()
        try:
            self.data_avg.close_file()
        except AttributeError:
            pass
        finally:
            self.data_raw.close_file()
            if self.save_hdf: self._data_hdf.close_file()
