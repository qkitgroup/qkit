# MP@KIT 07/2015
# HR@KIT 2015
#import h5py
import numpy as np

from qkit.storage import hdf_lib
from qkit.analysis.circle_fit import resonator_tools_xtras as rtx
from scipy.optimize import leastsq


class Resonator(object):

    '''
    usage:
    
    '''
    
    def __init__(self, hf=None, hdf_x=None, hdf_y=None):

        self._hf = hf
        self._hdf_x = hdf_x
        self._hdf_y = hdf_y
        
        self._first_circle = True
        self._first_lorentz = True
        self._first_fano = True
        
    def set_file(name):
        self.hf = name
    def set_x_coord(x_co):
        self.hdf_x = x_co
    def set_y_coord(y_co):
        self.hdf_y = y_co
        
    def fit_circle(fit_all = False):
        '''
        Calls circle fit from resonator_tools_xtras.py and resonator_tools.py in the qkit/analysis folder
        '''
        self._fit_all = fit_all

        if self._first_circle:
            self._prepare_circle()

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
            self._amp_gen.append(error_data_array)
            self._pha_gen.append(error_data_array)
            for key in self._result_keys.iterkeys():
                self._results[str(key)].append(0.)

        else:
            z_data_gen = np.array([A2 * (f - frcal) + rtx.S21(f, fr=float(results["fr"]), Qr=float(results["Qr"]), Qc=float(results["absQc"]), phi=float(results["phi0"]), a= amp_norm, alpha= alpha, delay=delay) for f in self._freqpoints])
            self._amp_gen.append(np.absolute(z_data_gen))
            self._pha_gen.append(np.angle(z_data_gen))
            self._real_gen.append(np.real(z_data_gen))
            self._imag_gen.append(np.imag(z_data_gen))
            self._real_gen.append(z_data_gen.real)
            self._imag_gen.append(z_data_gen.imag)

            for key in self._results.iterkeys():
                self._results[str(key)].append(float(results[str(key)]))
    

    



    def _prepare_circle(self):
            self._result_keys = {"Qi_dia_corr":'', "Qi_no_corr":'', "absQc":'', "Qc_dia_corr":'', "Qr":'', "fr":'', "theta0":'', "phi0":'', "phi0_err":'', "Qr_err":'', "absQc_err":'', "fr_err":'', "chi_square":'', "Qi_no_corr_err":'', "Qi_dia_corr_err":''}
            self._results = {}
            
            #self._x = self._hf.get_dataset("")            
            
            self._amp_gen = self._hf.add_value_matrix('amplitude_gen', folder = 'analysis', x = self._hdf_x, y = self._hdf_y, unit = 'V')
            self._pha_gen = self._hf.add_value_matrix('phase_gen', folder = 'analysis', x = self._hdf_x, y = self._hdf_y, unit='rad')
            self._real_gen = self._hf.add_value_matrix('real_gen', folder = 'analysis', x = self._hdf_x, y = self._hdf_y, unit='')
            self._imag_gen = self._hf.add_value_matrix('imag_gen', folder = 'analysis', x = self._hdf_x, y = self._hdf_y, unit='')

            for key in self._result_keys.iterkeys():
               self._results[str(key)] = self._hf.add_value_vector(str(key), folder = 'analysis', x = self._hdf_x, unit ='')
            self._real_gen = self._hf.add_value_vector('real', folder = 'analysis', x = self._hdf_y, unit = '')
            self._imag_gen = self._hf.add_value_vector('imag', folder = 'analysis', x = self._hdf_y, unit = '')
            
    def _get_data_circle(self):
        self._z_data_raw = np.array([])
        self._freqpoints = np.array([])
        am_ds = self._hf['/entry/data0/amplitude']
        ph_ds = self._hf['/entry/data0/phase']
        if self._fit_all:
            for i, amplitude in enumerate(am_ds[:]):
                self._z_data_raw = np.append(self._z_data_raw,amplitude*np.exp(1j*ph_ds[i]))
        else:
            self._z_data_raw = am_ds[-1]*np.exp(1j*ph_ds[-1])
        freq_ds = self._hf['/entry/data0/frequency']
        for i, frequency in enumerate(freq_ds[:]):
            self._freqpoints = np.append(self._freqpoints, frequency)


    def fit_lorentz(self,fit_all = False):
        self._fit_all = fit_all

        if self._first_lorentz:
            self._prepare_lorentz()

        self._get_data_lorentz()
        
        
    def fit_skewed_lorentzian(frequencies,amplitudes):
        "fits a skewed lorenzian to reflection amplitudes of a resonator"
        amplitudes = np.absolute(amplitudes)
        amplitudes_sq = amplitudes**2
        
        A1a = np.minimum(amplitudes_sq[0],amplitudes_sq[-1])
        A3a = -np.max(amplitudes_sq)
        fra = frequencies[np.argmin(amplitudes_sq)]
        
        def residuals(p,x,y):
            A2, A4, Qr = p
            err = y -(A1a+A2*(x-fra)+(A3a+A4*(x-fra))/(1.+4.*Qr**2*((x-fra)/fra)**2))
            return err
            
        p0 = [0., 0., 1e3]
        
        p_final = leastsq(residuals,p0,args=(np.array(frequencies),np.array(amplitudes_sq)))
        print p_final[0]
        A2a, A4a, Qra = p_final[0]
    
        def residuals2(p,x,y):
            A1, A2, A3, A4, fr, Qr = p
            err = y -(A1+A2*(x-fr)+(A3+A4*(x-fr))/(1.+4.*Qr**2*((x-fr)/fr)**2))
            return err
        
        p0 = [A1a, A2a , A3a, A4a, fra, Qra]
        p_final = leastsq(residuals2,p0,args=(np.array(frequencies),np.array(amplitudes_sq)))
        #A1, A2, A3, A4, fr, Qr = p_final[0]
        #print p_final[0][5]
        return p_final[0]
        
    def _prepare_lorentz(self):
        pass

    def _get_data_lorentz(self):
        pass
    
    def fit_fano(self,fit_all = False):
        self._fit_all = fit_all

        if self._first_fano:
            self._prepare_fano()
            self._first_fano = False
            
        #self._get_data_fano()
        self.frequencies  = self._hf['/entry/data0/frequency']
        frequencies=self.frequencies
        self.amplitudes  = self._hf['/entry/data0/amplitude']
        
        if fit_all:
            traces = self.amplitudes[:]
        else:
            traces = [self.amplitudes[0]]
            
        for amplitudes in traces:
            fit = self.do_fit_fano(frequencies,amplitudes)
            amplitudes_gen = self.fano_reflection_from_fit(frequencies,fit)
            # calculate the chi2 of fit and data
            chi2 = self.fano_fit_chi2(frequencies,fit,amplitudes)
            print chi2
            # save the fitted data to the hdf_file
            self._fano_amp_gen.append(np.array(amplitudes_gen))
            
            self._fano_q_fit.append(float(fit[0]))
            self._fano_bw_fit.append(float(fit[1])) 
            self._fano_fr_fit.append(float(fit[2])) 
            self._fano_a_fit.append(float(fit[3]))
            self._fano_chi2_fit.append(float(chi2))
                


    def _prepare_fano(self):
        "create the datasets in the hdf-file"
        # self._hdf_y : frequency
        #self._hdf_x = self._hf.add_coordinate("Power", unit = "dBm", comment = "",folder="analysis")
        #self._hdf_y = self._hf.add_coordinate("freq",  unit = "Hz", comment = "",folder="analysis")
        self._x_co  = self._hf.get_dataset("/entry/data0/power")
        self._y_co  = self._hf.get_dataset("/entry/data0/frequency")
        
        self._fano_amp_gen = self._hf.add_value_matrix('fano_amp_gen', folder = 'analysis', x = self._x_co, 
                                                       y = self._y_co, unit = 'a.u.')
        self._fano_q_fit  = self._hf.add_value_vector('fano_q_fit' , folder = 'analysis', x = self._x_co, unit = '')
        self._fano_bw_fit = self._hf.add_value_vector('fano_bw_fit', folder = 'analysis', x = self._x_co, unit = 'Hz')
        self._fano_fr_fit = self._hf.add_value_vector('fano_fr_fit', folder = 'analysis', x = self._x_co, unit = 'Hz')
        self._fano_a_fit  = self._hf.add_value_vector('fano_a_fit' , folder = 'analysis', x = self._x_co, unit = '')
        
        self._fano_chi2_fit  = self._hf.add_value_vector('fano_chi2_fit' , folder = 'analysis', x = self._x_co, unit = '')
        
    def fano_reflection(self,f,q,bw,fr,a=1,b=1):
        """
        evaluates the fano function in reflection at the 
        frequency f
        with 
        resonator frequency fr
        attenuation a (linear)
        fano-factor q
        bandwidth bw
        
        """
        return a*(1 - self.fano_transmission(f,q,bw,fr))
        

    def fano_transmission(self,f,q,bw,fr,a=1,b=1):
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
    
    
    def do_fit_fano(self,frequencies,amplitudes):
        amplitudes = np.absolute(amplitudes)
        amplitudes_sq = amplitudes**2
        fr = frequencies[np.argmax(amplitudes_sq)]            
        #print fr
        # initial guess
        bw = 1e6
        q  = 1#np.sqrt(1-amplitudes_sq).min()  # 1-Amp_sq = 1-1+q^2  => A_min = q
        fr = frequencies[np.argmin(amplitudes_sq)]
        a  = amplitudes_sq.max()

        p0 = [q, bw, fr, a]

            
        def fano_residuals(p,frequency,amplitude):
            q, bw, fr , a = p
            err = amplitude-self.fano_reflection(frequency,q,bw,fr=fr,a=a)
            return err
        
        
        p_fit = leastsq(fano_residuals,p0,args=(np.array(frequencies),np.array(amplitudes_sq)))
        print ("q:%g bw:%g fr:%g a:%g")% (p_fit[0][0],p_fit[0][1],p_fit[0][2],p_fit[0][3])
        return p_fit[0]
        

        
    def fano_reflection_from_fit(self,fs,fit):
        return self.fano_reflection(fs,fit[0],fit[1],fit[2],fit[3])
        
    def fano_fit_chi2(self,fs,fit,amplitudes_sq):
        chi2 = np.sum((self.fano_reflection_from_fit(fs,fit)-amplitudes_sq)**2) / (len(amplitudes_sq)-len(fit))
        return chi2
        
        

        

    def _get_data_fano(self):
        pass


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="resonator.py hdf-based simple resonator fit frontend / KIT 2015")

    parser.add_argument('-f','--file',     type=str, help='hdf filename to open')
    #parser.add_argument('-ds','--datasets', type=str, help='(optional) datasets opened by default')
    parser.add_argument('-lf','--lorentz-fit',  default=False,action='store_true', help='(optional) lorentzian fit')
    parser.add_argument('-ff','--fano-fit',     default=False,action='store_true', help='(optional) fano fit')
    parser.add_argument('-cf','--circle-fit',   default=False,action='store_true', help='(optional) circle fit')

    args=parser.parse_args()
    hf=None
    if args.file:
        hf = hdf_lib.Data(path=args.file)
        R = Resonator(hf)
        if args.circle_fit:
            R.fit_circle()
        if args.lorentz_fit:
            R.fit_lorentz()
        if args.fano_fit:
            R.fit_fano(fit_all=True)
    else:
        print "no file supplied. type -h for help"
    if hf:
        hf.close()
