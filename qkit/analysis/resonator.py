# MP@KIT 07/2015

import numpy as np

from qkit.analysis.circle_fit import resonator_tools_xtras as rtx
from scipy.optimize import leastsq


class Resonator(object):

    '''
    usage:
    
    '''
    
    def __init__(self, hdf_file, hdf_x, hdf_y):

        self._hdf_file = hdf_file
        self._hdf_x = hdf_x
        self._hdf_y = hdf_y
        
        self._first_circle = True
        self._first_lorentz = True
        self._first_fano = True
        
        def fit_circle(fit_all = False):
            '''
            Calls circle fit from resonator_tools_xtras.py and resonator_tools.py in the qkit/analysis folder
            '''
            self._fit_all = fit_all

            if self._first_circle:
                self._prepare_hdf_circle()

            self._get_data_circle()

            try:
                delay, amp_norm, alpha, fr, Qr, A2, frcal = rtx.do_calibration(self._freqpoints, self._z_data_raw,ignoreslope=True)
                z_data = rtx.do_normalization(self._freqpoints, self._z_data_raw,delay,amp_norm,alpha,A2,frcal)
                results = rtx.circlefit(self._freqpoints,z_data,fr,Qr,refine_results=False,calc_errors=True)

            except:
                '''
                If the fit does not converge due to bad data, the "bad" x_values get stored in a comment in the hdf file's analysis folder. All the fitting data for these values are set to 0.
                '''
                error_data_array = np.zeros(len(self._freqpoints))
                self._hdf_amp_gen.append(error_data_array)
                self._hdf_pha_gen.append(error_data_array)
                for key in self._result_keys.iterkeys():
                    self._results[str(key)].append(0.)
    
            else:
                z_data_gen = np.array([A2 * (f - frcal) + rtx.S21(f, fr=float(results["fr"]), Qr=float(results["Qr"]), Qc=float(results["absQc"]), phi=float(results["phi0"]), a= amp_norm, alpha= alpha, delay=delay) for f in self._freqpoints])
                self._hdf_amp_gen.append(np.absolute(z_data_gen))
                self._hdf_pha_gen.append(np.angle(z_data_gen))
                self._hdf_real_gen.append(np.real(z_data_gen))
                self._hdf_imag_gen.append(np.imag(z_data_gen))
                self._hdf_real_gen.append(z_data_gen.real)
                self._hdf_imag_gen.append(z_data_gen.imag)

                for key in self._results.iterkeys():
                    self._results[str(key)].append(float(results[str(key)]))
        
        def fit_lorentz(fit_all = False):
            self._fit_all = fit_all

            if self._first_lorentz:
                self._prepare_hdf_lorentz()

            self._get_data_lorentz()
            
            
        def fit_skewed_lorentzian(f_data,z_data):
            amplitude = np.absolute(z_data)
            amplitude_sqr = amplitude**2
            A1a = np.minimum(amplitude_sqr[0],amplitude_sqr[-1])
            A3a = -np.max(amplitude_sqr)
            fra = f_data[np.argmin(amplitude_sqr)]
            def residuals(p,x,y):
                A2, A4, Qr = p
                err = y -(A1a+A2*(x-fra)+(A3a+A4*(x-fra))/(1.+4.*Qr**2*((x-fra)/fra)**2))
                return err
            p0 = [0., 0., 1e3]
            p_final = leastsq(residuals,p0,args=(np.array(f_data),np.array(amplitude_sqr)))
            A2a, A4a, Qra = p_final[0]
        
            def residuals2(p,x,y):
                A1, A2, A3, A4, fr, Qr = p
                err = y -(A1+A2*(x-fr)+(A3+A4*(x-fr))/(1.+4.*Qr**2*((x-fr)/fr)**2))
                return err
            p0 = [A1a, A2a , A3a, A4a, fra, Qra]
            p_final = leastsq(residuals2,p0,args=(np.array(f_data),np.array(amplitude_sqr)))
            #A1, A2, A3, A4, fr, Qr = p_final[0]
            #print p_final[0][5]
            return p_final[0]
        
        def fit_fano(fit_all = False):
            self._fit_all = fit_all

            if self._first_fano:
                self._prepare_hdf_fano()

            self._get_data_fano()


        def _prepare_hdf_circle(self):
                self._result_keys = {"Qi_dia_corr":'', "Qi_no_corr":'', "absQc":'', "Qc_dia_corr":'', "Qr":'', "fr":'', "theta0":'', "phi0":'', "phi0_err":'', "Qr_err":'', "absQc_err":'', "fr_err":'', "chi_square":'', "Qi_no_corr_err":'', "Qi_dia_corr_err":''}
                self._results = {}

                self._hdf_amp_gen = self._hdf_file.add_value_matrix('amplitude gen', folder = 'analysis', x = self._hdf_x, y = self._hdf_y, unit = 'V')
                self._hdf_pha_gen = self._hdf_file.add_value_matrix('phase gen', folder = 'analysis', x = self._hdf_x, y = self._hdf_y, unit='rad')
                self._hdf_real_gen = self._hdf_file.add_value_matrix('real gen', folder = 'analysis', x = self._hdf_x, y = self._hdf_y, unit='')
                self._hdf_imag_gen = self._hdf_file.add_value_matrix('imag gen', folder = 'analysis', x = self._hdf_x, y = self._hdf_y, unit='')

                for key in self._result_keys.iterkeys():
                   self._results[str(key)] = self._hdf_file.add_value_vector(str(key), folder = 'analysis', x = self._hdf_x, unit ='')
                self._hdf_real_gen = self._hdf_file.add_value_vector('real', folder = 'analysis', x = self._hdf_y, unit = '')
                self._hdf_imag_gen = self._hdf_file.add_value_vector('imag', folder = 'analysis', x = self._hdf_y, unit = '')
                
        def _get_data_circle(self):
            self._z_data_raw = np.array([])
            self._freqpoints = np.array([])
            am_ds = self._hdf_file['/entry/data0/amplitude']
            ph_ds = self._hdf_file['/entry/data0/phase']
            if self._fit_all:
                for i, amplitude in enumerate(am_ds[:]):
                    self._z_data_raw = np.append(self._z_data_raw,amplitude*np.exp(1j*ph_ds[i]))
            else:
                self._z_data_raw = am_ds[-1]*np.exp(1j*ph_ds[-1])
            freq_ds = self._hdf_file['/entry/data0/frequency']
            for i, frequency in enumerate(freq_ds[:]):
                self._freqpoints = np.append(self._freqpoints, frequency)

        def _prepare_hdf_lorentz(self):
            pass

        def _get_data_lorentz(self):
            pass

        def _prepare_hdf_fano(self):
            pass

        def _get_data_fano(self):
            pass
