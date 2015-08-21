# MP@KIT 2015
# HR@KIT 2015
#import h5py
import numpy as np

from qkit.storage import hdf_lib
from qkit.analysis.circle_fit import resonator_tools_xtras as rtx
from scipy.optimize import leastsq, curve_fit


class Resonator(object):

    '''
    usage:
    
    '''
    
    def __init__(self, h_file):
        self._hf_path =  h_file
        self._hf = None
        self._hf = hdf_lib.Data(path=self._hf_path)
        
        self._first_circle = True
        self._first_lorentz = True
        self._first_fano = True
        self._first_skewed_lorentzian = True
        
        self._refresh()
        
    def _refresh(self,live = False):
        if live:
            if self._hf:
                self._hf.close()
            self._hf = hdf_lib.Data(path=self._hf_path)
        self._prepare()

    def set_x_coord(self,x_co):
        self._x_co = x_co
    def set_y_coord(self,y_co):
        self.y_co = y_co

    def _set_data_range(self, data):
        return data[(self._frequency >= self._f_min) & (self._frequency <= self._f_max)]

    def _prepare(self):
        # these ds_url should always be present in a resonator measurement
        ds_url_amp   = "/entry/data0/amplitude"
        ds_url_phase = "/entry/data0/phase"
        ds_url_freq  = "/entry/data0/frequency"

        # these ds_url depend on the measurement and may not exist
        ds_url_power  = "/entry/data0/power"
        ds_url_temp   = "/entry/data0/temperature"

        self._ds_amp = self._hf.get_dataset(ds_url_amp)

        self._amplitude  = np.array(self._hf[ds_url_amp])
        self._phase      = np.array(self._hf[ds_url_phase])
        self._frequency  = np.array(self._hf[ds_url_freq])
        
        try:
            self._x_co = self._hf.get_dataset(self._ds_amp.x_ds_url)
            self._y_co = self._hf.get_dataset(self._ds_amp.y_ds_url)
        except AttributeError:
            # hardcode a std url
            self._x_co = self._hf.get_dataset(ds_url_power)
            self._y_co = self._hf.get_dataset(ds_url_freq)
            
    def _global_prepare(self,fit_all,fmin,fmax):
        self._fit_all = fit_all

        if fmin and fmax:
            self._f_min = fmin
            self._f_max = fmax
        else:
            self._f_min = np.min(self._frequency)
            self._f_max = np.max(self._frequency)
        
        self._fit_frequency = self._set_dat_range(self._frequency)

        self._frequency_co = self._hf.add_coordinate('frequency_fit',folder='analysis', unit = 'Hz')
        self._frequency_co.add(self._fit_frequency)
       
    def _get_amplitude(self):
        self._refresh()
        if not self._fit_all:
            return self._set_dat_range(self._amplitude[-1])
        else:
            return self._set_dat_range(self._amplitude)
            
    def _get_phase(self, i):
        self._refresh()
        if not self._fit_all:
            return self._set_dat_range(self._phase[-1])
        else:
            return self._set_dat_range(self._phase)
        
        """
        self._fit_amplitude = np.empty((self._amplitude.shape[0],self._fit_frequency.shape))
        self._fit_phase = np.empty((self._phase.shape[0],self._fit_frequency.shape))
        
        for i, amplitude in enumerate(self._amplitude):
            self._fit_amplitude[i]=self._set_data_range(amplitude)
        for i, phase in enumerate(self._phase):
            self._fit_phase[i]=self._set_data_range(phase)

        if not self._fit_all:
            self._fit_amplitude = self._fit_amplitude[-1]
            self._fit_phase = self._fit_phase[-1]
        """
    def fit_circle(self,fit_all = False, fmin = None, fmax=None):
        '''
        Calls circle fit from resonator_tools_xtras.py and resonator_tools.py in the qkit/analysis folder
        '''
        self._global_prepare(fit_all,fmin,fmax)
        if self._first_circle:
            self._prepare_circle()
            self._first_circle = False

        self._get_data_circle()
        for z_data_raw in self._z_data_raw:
            z_data_raw = self._set_data_range(z_data_raw)

            try:
                delay, amp_norm, alpha, fr, Qr, A2, frcal = rtx.do_calibration(self._fit_frequency, z_data_raw,ignoreslope=True)
                z_data = rtx.do_normalization(self._fit_frequency, z_data_raw,delay,amp_norm,alpha,A2,frcal)
                results = rtx.circlefit(self._fit_frequency,z_data,fr,Qr,refine_results=False,calc_errors=True)

            except:
                pass
                """
                '''If the fit does not converge due to bad data, the "bad" x_values get stored in a comment in the hdf file's analysis folder. All the fitting data for these values are set to 0.'''
                error_data_array = np.zeros(len(self._fit_frequency))
                self._amp_gen.append(error_data_array)
                self._pha_gen.append(error_data_array)
                for key in self._result_keys.iterkeys():
                    self._results[str(key)].append(0.)
                    """
            else:
                z_data_gen = np.array([A2 * (f - frcal) + rtx.S21(f, fr=float(results["fr"]), Qr=float(results["Qr"]), Qc=float(results["absQc"]), phi=float(results["phi0"]), a= amp_norm, alpha= alpha, delay=delay) for f in self._fit_frequency])
                self._amp_gen.append(np.absolute(z_data_gen))
                self._pha_gen.append(np.angle(z_data_gen))
                self._real_gen.append(np.real(z_data_gen))
                self._imag_gen.append(np.imag(z_data_gen))

                for key in self._results.iterkeys():
                    self._results[str(key)].append(float(results[str(key)]))

    def _prepare_circle(self):
        self._result_keys = {"Qi_dia_corr":'', "Qi_no_corr":'', "absQc":'', "Qc_dia_corr":'', "Qr":'', "fr":'', "theta0":'', "phi0":'', "phi0_err":'', "Qr_err":'', "absQc_err":'', "fr_err":'', "chi_square":'', "Qi_no_corr_err":'', "Qi_dia_corr_err":''}
        self._results = {}

        self._amp_gen = self._hf.add_value_matrix('amplitude_gen', folder = 'analysis', x = self._x_co, y = self._frequency_co, unit = 'V')
        self._pha_gen = self._hf.add_value_matrix('phase_gen', folder = 'analysis', x = self._x_co, y = self._frequency_co, unit='rad')
        self._real_gen = self._hf.add_value_matrix('real_gen', folder = 'analysis', x = self._x_co, y = self._frequency_co, unit='')
        self._imag_gen = self._hf.add_value_matrix('imag_gen', folder = 'analysis', x = self._x_co, y = self._frequency_co, unit='')

        for key in self._result_keys.iterkeys():
           self._results[str(key)] = self._hf.add_value_vector(str(key), folder = 'analysis', x = self._x_co, unit ='')

    def _get_data_circle(self):
        self._z_data_raw = np.empty((self._fit_amplitude.shape), dtype=np.complex64)
        for i, amplitude in enumerate(self._fit_amplitude):
            self._z_data_raw[i] = self._fit_amplitude*np.exp(1j*self._fit_phase[i])

    def fit_lorentz(self,fit_all = False,fmin=None,fmax=None):
        self._global_prepare(fit_all,fmin,fmax)
        

        def f_Lorentzian(f, f0, k, a, offs):
            return np.sign(a) * np.sqrt(np.abs(a**2*(k/2.)**2/((k/2.)**2+((f-f0)**2))))+offs


        if self._first_lorentz:
            self._prepare_lorentz()
            self._first_lorentz=False

        for amplitudes in self._get_amplitude():
            '''extract starting parameter for lorentzian from data'''
            
            s_offs = np.mean(np.array([amplitudes[:int(len(amplitudes)*.1)], amplitudes[int(len(amplitudes)-int(len(amplitudes)*.1)):]]))
            '''offset is calculated from the fist and last 10% of the data to improve fitting on tight windows'''
            
            if np.abs(np.max(amplitudes)-np.mean(amplitudes)) > np.abs(np.min(amplitudes)-np.mean(amplitudes)):
                '''peak is expected'''
                s_a = np.abs((np.max(amplitudes)-np.mean(amplitudes)))
                s_f0 = self._fit_frequency[np.argmax(amplitudes)]
            else:
                '''dip is expected'''
                s_a = -np.abs((np.min(amplitudes)-np.mean(amplitudes)))
                s_f0 = self._fit_frequency[np.argmin(amplitudes)]
                
            '''estimate peak/dip width'''
            mid = s_offs + .5*s_a #estimated mid region between base line and peak/dip
            m = [] #mid points
            for i in range(len(amplitudes)-1):
                if np.sign(amplitudes[i]-mid) != np.sign(amplitudes[i+1] - mid):#mid level crossing
                    m.append(i)
            if len(m)>1:
                s_k = self._fit_frequency[m[-1]]-self._fit_frequency[m[0]]
            else:
                s_k = .15*(self.fit_frequency[-1]-self._fit_frequency[0]) #try 15% of window
    
            p0=[s_f0, s_k, s_a, s_offs]
    
            try:
                popt, pcov = curve_fit(f_Lorentzian, self._fit_frequency, amplitudes, p0=p0)
            except:
                pass
            else:
                chi2 = self._lorentz_fit_chi2(popt,amplitudes)

                #self._lorentz_amp_gen.append(np.sqrt(np.absolute(f_Lorentzian(self._frequency, *popt))))
                self._lorentz_amp_gen.append(f_Lorentzian(self._fit_frequency, *popt))
                self._lorentz_f0.append(float(popt[0]))
                self._lorentz_k.append(float(popt[1]))
                self._lorentz_a.append(float(popt[2]))
                self._lorentz_offs.append(float(popt[3]))
                self._lorentz_Ql.append(float(popt[0])/float(popt[1]))
                self._lorentz_chi2_fit.append(float(chi2))

    def _prepare_lorentz(self):
        self._lorentz_amp_gen = self._hf.add_value_matrix('lorentz_amp_gen', folder = 'analysis', x = self._x_co, y = self._frequency_co, unit = 'dB')
        self._lorentz_f0 = self._hf.add_value_vector('lorentz_f0_fit', folder = 'analysis', x = self._x_co, unit = 'Hz')
        self._lorentz_k = self._hf.add_value_vector('lorentz_k_fit', folder = 'analysis', x = self._x_co, unit = 'Hz')
        self._lorentz_a = self._hf.add_value_vector('lorentz_a_fit', folder = 'analysis', x = self._x_co, unit = 'V')
        self._lorentz_offs = self._hf.add_value_vector('lorentz_offs_fit', folder = 'analysis', x = self._x_co, unit = 'V')
        self._lorentz_Ql = self._hf.add_value_vector('lorentz_ql_fit', folder = 'analysis', x = self._x_co, unit = '')

        self._lorentz_chi2_fit  = self._hf.add_value_vector('lorentz_chi2_fit' , folder = 'analysis', x = self._x_co, unit = '')

        lorentz_view = self._hf.add_view("lorentz_fit", x = self._y_co, y = self._ds_amp, y_axis=1)
        lorentz_view.add(x=self._frequency_co, y=self._lorentz_amp_gen, y_axis=1)

    def _lorentz_from_fit(self,fit):
        return np.sign(fit[2]) * np.sqrt(np.abs(fit[2] ** 2 * (fit[1]/2.) ** 2 / ((fit[1]/2.) ** 2 + ((self._fit_frequency-fit[0]) ** 2)))) + fit[3]
        
    def _lorentz_fit_chi2(self, fit, amplitudes):
        chi2 = np.sum((self._lorentz_from_fit(fit)-amplitudes)**2) / (len(amplitudes)-len(fit))
        return chi2

    def fit_skewed_lorentzian(self, fit_all = False, fmin=None, fmax=None):
        def residuals(p,x,y):
            A2, A4, Qr = p
            err = y -(A1a+A2*(x-fra)+(A3a+A4*(x-fra))/(1.+4.*Qr**2*((x-fra)/fra)**2))
            return err
        def residuals2(p,x,y):
            A1, A2, A3, A4, fr, Qr = p
            err = y -(A1+A2*(x-fr)+(A3+A4*(x-fr))/(1.+4.*Qr**2*((x-fr)/fr)**2))
            return err

        self._global_prepare(fit_all,fmin,fmax)
        if self._first_skewed_lorentzian:
            self._prepare_skewed_lorentzian()
            self._first_skewed_lorentzian = False

        for amplitudes in self._fit_amplitudes:
            "fits a skewed lorenzian to reflection amplitudes of a resonator"
            amplitudes = np.absolute(amplitudes)
            amplitudes_sq = amplitudes**2

            A1a = np.minimum(amplitudes_sq[0],amplitudes_sq[-1])
            A3a = -np.max(amplitudes_sq)
            fra = self._fit_frequencies[np.argmin(amplitudes_sq)]
                
            p0 = [0., 0., 1e3]

            try:
                p_final = leastsq(residuals,p0,args=(np.array(self._fit_frequencies),np.array(amplitudes_sq)))
                A2a, A4a, Qra = p_final[0]

                p0 = [A1a, A2a , A3a, A4a, fra, Qra]
                p_final = leastsq(residuals2,p0,args=(np.array(self._fit_frequencies),np.array(amplitudes_sq)))

            except:
                pass
            else:
                pass
                #A1, A2, A3, A4, fr, Qr = p_final[0]
                #print p_final[0][5]
            return p_final[0]
    
    def _prepare_skewed_lorentzian(self):
        pass
    

    def _prepare_fano(self):
        "create the datasets in the hdf-file"
        
        self._fano_amp_gen = self._hf.add_value_matrix('fano_amp_gen', folder = 'analysis', x = self._x_co, y = self._frequency_co, unit = 'a.u.')
        self._fano_q_fit  = self._hf.add_value_vector('fano_q_fit' , folder = 'analysis', x = self._x_co, unit = '')
        self._fano_bw_fit = self._hf.add_value_vector('fano_bw_fit', folder = 'analysis', x = self._x_co, unit = 'Hz')
        self._fano_fr_fit = self._hf.add_value_vector('fano_fr_fit', folder = 'analysis', x = self._x_co, unit = 'Hz')
        self._fano_a_fit  = self._hf.add_value_vector('fano_a_fit' , folder = 'analysis', x = self._x_co, unit = '')
        
        self._fano_chi2_fit  = self._hf.add_value_vector('fano_chi2_fit' , folder = 'analysis', x = self._x_co, unit = '')
        self._fano_Ql_fit    = self._hf.add_value_vector('fano_Ql_fit' , folder = 'analysis', x = self._x_co, unit = '')

        fano_view = self._hf.add_view("fano_fit", x = self._y_co, y = self._ds_amp, y_axis=1)
        fano_view.add(x=self._frequency_co, y=self._fano_amp_gen, y_axis=1)
    
    def fit_fano(self,fit_all = False, fmin=None, fmax=None):
        self._global_prepare(fit_all,fmin,fmax)
        if self._first_fano:
            self._prepare_fano()
            self._first_fano = False

        for amplitudes in self._fit_amplitude:
            amplitude_sq = (np.absolute(amplitudes))**2
            try:
                fit = self._do_fit_fano(amplitude_sq)
                amplitudes_gen = self._fano_reflection_from_fit(fit)

                '''calculate the chi2 of fit and data'''
                chi2 = self._fano_fit_chi2(fit, amplitude_sq)

            except:
                pass

            else:
                ''' save the fitted data to the hdf_file'''
                self._fano_amp_gen.append(np.sqrt(np.absolute(amplitudes_gen)))
                self._fano_q_fit.append(float(fit[0]))
                self._fano_bw_fit.append(float(fit[1])) 
                self._fano_fr_fit.append(float(fit[2])) 
                self._fano_a_fit.append(float(fit[3]))
                self._fano_chi2_fit.append(float(chi2))
                self._fano_Ql_fit.append(float(fit[2])/float(fit[1]))

    def _fano_reflection(self,f,q,bw,fr,a=1,b=1):
        """
        evaluates the fano function in reflection at the 
        frequency f
        with 
        resonator frequency fr
        attenuation a (linear)
        fano-factor q
        bandwidth bw
        
        """
        return a*(1 - self._fano_transmission(f,q,bw,fr))

    def _fano_transmission(self,f,q,bw,fr,a=1,b=1):
        """
        evaluates the normalized transmission fano function at the 
        frequency f
        with 
        resonator frequency fr
        attenuation a (linear)
        fano-factor q
        bandwidth bw
        
        """
        F = 2*(f-fr)/bw
        return ( 1/(1+q**2) * (F+q)**2 / (F**2+1))

    def _do_fit_fano(self, amplitudes_sq):
        #amplitudes = np.absolute(amplitudes)
        #amplitudes_sq = amplitudes**2
        #print fr
        # initial guess
        bw = 1e6
        q  = 1#np.sqrt(1-amplitudes_sq).min()  # 1-Amp_sq = 1-1+q^2  => A_min = q
        fr = self._fit_frequency[np.argmin(amplitudes_sq)]
        a  = amplitudes_sq.max()

        p0 = [q, bw, fr, a]

        def fano_residuals(p,frequency,amplitude_sq):
            q, bw, fr, a = p
            err = amplitude_sq-self._fano_reflection(frequency,q,bw,fr=fr,a=a)
            return err

        p_fit = leastsq(fano_residuals,p0,args=(self._fit_frequency,np.array(amplitudes_sq)))
        print ("q:%g bw:%g fr:%g a:%g")% (p_fit[0][0],p_fit[0][1],p_fit[0][2],p_fit[0][3])
        return p_fit[0]

    def _fano_reflection_from_fit(self,fit):
        return self._fano_reflection(self._fit_frequency,fit[0],fit[1],fit[2],fit[3])

    def _fano_fit_chi2(self,fit,amplitudes_sq):
        chi2 = np.sum((self._fano_reflection_from_fit(fit)-amplitudes_sq)**2) / (len(amplitudes_sq)-len(fit))
        return chi2


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="resonator.py hdf-based simple resonator fit frontend / KIT 2015")

    parser.add_argument('-f','--file',     type=str, help='hdf filename to open')
    #parser.add_argument('-ds','--datasets', type=str, help='(optional) datasets opened by default')
    parser.add_argument('-lf','--lorentz-fit',  default=False,action='store_true', help='(optional) lorentzian fit')
    parser.add_argument('-ff','--fano-fit',     default=False,action='store_true', help='(optional) fano fit')
    parser.add_argument('-cf','--circle-fit',   default=False,action='store_true', help='(optional) circle fit')
    parser.add_argument('-slf','--skewed-lorentz-fit', default=False,action='store_true',help='(optional) skewed lorentzian fit')
    parser.add_argument('-all','--fit-all', default=False,action='store_true',help='(optional) fit all entries in dataset')
    parser.add_argument('-fr','--frequency-range', type=str, help='(optional) frequency range for fitting, comma separated')

    args=parser.parse_args()
    #argsfile=None
    if args.file:
        
        R = Resonator(args.file)
        fit_all = args.fit_all

        if args.frequency_range:
            freq_range=args.frequency_range.split(',')
            f0=int(freq_range[0])
            f1=int(freq_range[1])
        else:
            f0=None
            f1=None
            
        if args.circle_fit:
            R.fit_circle(fit_all=fit_all, f0=f0,f1=f1)
        if args.lorentz_fit:
            R.fit_lorentz(fit_all=fit_all, f0=f0,f1=f1)
        if args.skewed_lorentz_fit:
            R.fit_skewed_lorentzian(fit_all=fit_all, f0=f0,f1=f1)
        if args.fano_fit:
            R.fit_fano(fit_all=fit_all, f0=f0,f1=f1)
    else:
        print "no file supplied. type -h for help"
    if hf:
        hf.close()
