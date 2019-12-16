import warnings
import numpy as np
import scipy.optimize as spopt
from scipy.constants import hbar

from .utilities import plotting, save_load, Watt2dBm, dBm2Watt
from .circlefit import circlefit
from .calibration import calibration

##
## z_data_raw denotes the raw data
## z_data denotes the normalized data
##        
    
class reflection_port(circlefit, save_load, plotting, calibration):
    '''
    normal direct port probed in reflection
    '''
    def __init__(self, f_data=None, z_data_raw=None):
        self.porttype = 'direct'
        self.fitresults = {}
        self.z_data = None
        if f_data is not None:
            self.f_data = np.array(f_data)
        else:
            self.f_data=None
        if z_data_raw is not None:
            self.z_data_raw = np.array(z_data_raw)
        else:
            self.z_data=None
    
    def _S11(self,f,fr,k_c,k_i):
        '''
        use either frequency or angular frequency units
        for all quantities
        k_l=k_c+k_i: total (loaded) coupling rate
        k_c: coupling rate
        k_i: internal loss rate
        '''
        return ((k_c-k_i)+2j*(f-fr))/((k_c+k_i)-2j*(f-fr))
    
    def get_delay(self,f_data,z_data,delay=None,ignoreslope=True,guess=True):
        '''
        ignoreslope option not used here
        retrieves the cable delay assuming the ideal resonance has a circular shape
        modifies the cable delay until the shape Im(S21) vs Re(S21) is circular
        see "do_calibration"
        '''
        maxval = np.max(np.absolute(z_data))
        z_data = z_data/maxval
        A1, A2, A3, A4, fr, Ql = self._fit_skewed_lorentzian(f_data,z_data)
        if ignoreslope==True:
            A2 = 0
        else:
            z_data = (np.sqrt(np.absolute(z_data)**2-A2*(f_data-fr))) * np.exp(np.angle(z_data)*1j)  #usually not necessary
        if delay==None:
            if guess==True:
                delay = self._guess_delay(f_data,z_data)
            else:
                delay=0.
            delay = self._fit_delay(f_data,z_data,delay,maxiter=200)
        params = [A1, A2, A3, A4, fr, Ql]
        return delay, params 
    
    def do_calibration(self,f_data,z_data,ignoreslope=True,guessdelay=True):
        '''
        calculating parameters for normalization
        '''
        delay, params = self.get_delay(f_data,z_data,ignoreslope=ignoreslope,guess=guessdelay)
        z_data = np.sqrt(np.absolute(z_data)**2-params[1]*(f_data-params[4]))*np.exp(2.*1j*np.pi*delay*f_data)*np.exp(1j*np.angle(z_data))
        xc, yc, r0 = self._fit_circle(z_data)
        zc = np.complex(xc,yc)
        fitparams = self._phase_fit(f_data,self._center(z_data,zc),0.,np.absolute(params[5]),params[4])
        theta, Ql, fr = fitparams
        beta = self._periodic_boundary(theta+np.pi,np.pi) ###
        offrespoint = np.complex((xc+r0*np.cos(beta)),(yc+r0*np.sin(beta)))
        alpha = self._periodic_boundary(np.angle(offrespoint)+np.pi,np.pi)
        #a = np.absolute(offrespoint)
        #alpha = np.angle(zc)
        a = r0 + np.absolute(zc)
        return delay, a, alpha, fr, Ql, params[1], params[4]
    
    def do_normalization(self,f_data,z_data,delay,amp_norm,alpha,A2,frcal):
        '''
        transforming resonator into canonical position
        '''
        return (np.sqrt(np.absolute(z_data)**2-A2*(f_data-frcal)))/amp_norm*np.exp(1j*(-alpha+2.*np.pi*delay*f_data))*np.exp(1j*np.angle(z_data))
    
    def circlefit(self,f_data,z_data,fr=None,Ql=None,refine_results=False,calc_errors=True):
        '''
        S11 version of the circlefit
        '''
    
        if fr==None: fr=f_data[np.argmin(np.absolute(z_data))]
        if Ql==None: Ql=1e6
        xc, yc, r0 = self._fit_circle(z_data,refine_results=refine_results)
        phi0 = -np.arcsin(yc/r0)
        theta0 = self._periodic_boundary(phi0+np.pi,np.pi)
        z_data_corr = self._center(z_data,np.complex(xc,yc))
        theta0, Ql, fr = self._phase_fit(f_data,z_data_corr,theta0,Ql,fr)
        #print("Ql from phasefit is: " + str(Ql))
        Qi = Ql/(1.-r0)
        Qc = 1./(1./Ql-1./Qi)
    
        results = {"Qi":Qi,"Qc":Qc,"Ql":Ql,"fr":fr,"theta0":theta0}
    
        #calculation of the error
        p = [fr,Qc,Ql]
        #chi_square, errors = rt.get_errors(rt.residuals_notch_ideal,f_data,z_data,p)
        if calc_errors==True:
            chi_square, cov = self._get_cov_fast_directrefl(f_data,z_data,p)
            #chi_square, cov = rt.get_cov(rt.residuals_notch_ideal,f_data,z_data,p)
    
            if cov is not None:
                errors = np.sqrt(np.diagonal(cov))
                fr_err,Qc_err,Ql_err = errors
                #calc Qi with error prop (sum the squares of the variances and covariaces)
                dQl = 1./((1./Ql-1./Qc)**2*Ql**2)
                dQc = - 1./((1./Ql-1./Qc)**2*Qc**2)
                Qi_err = np.sqrt((dQl**2*cov[2][2]) + (dQc**2*cov[1][1])+(2*dQl*dQc*cov[2][1]))  #with correlations
                errors = {"Ql_err":Ql_err, "Qc_err":Qc_err, "fr_err":fr_err,"chi_square":chi_square,"Qi_err":Qi_err}
                results.update( errors )
            else:
                print("WARNING: Error calculation failed!")
        else:
            #just calc chisquared:
            fun2 = lambda x: self._residuals_notch_ideal(x,f_data,z_data)**2
            chi_square = 1./float(len(f_data)-len(p)) * (fun2(p)).sum()
            errors = {"chi_square":chi_square}
            results.update(errors)
    
        return results
        
    
    def autofit(self):
        '''
        automatic calibration and fitting
        '''
        delay, amp_norm, alpha, fr, Ql, A2, frcal =\
                self.do_calibration(self.f_data,self.z_data_raw,ignoreslope=True,guessdelay=False)
        self.z_data = self.do_normalization(self.f_data,self.z_data_raw,delay,amp_norm,alpha,A2,frcal)
        self.fitresults = self.circlefit(self.f_data,self.z_data,fr,Ql,refine_results=False,calc_errors=True)
        self.z_data_sim = A2*(self.f_data-frcal)+self._S11_directrefl(self.f_data,fr=self.fitresults["fr"],Ql=self.fitresults["Ql"],Qc=self.fitresults["Qc"],a=amp_norm,alpha=alpha,delay=delay)

    def _S11_directrefl(self,f,fr=10e9,Ql=900,Qc=1000.,a=1.,alpha=0.,delay=.0):
        '''
        full model for notch type resonances
        '''
        return a*np.exp(np.complex(0,alpha))*np.exp(-2j*np.pi*f*delay) * ( 2.*Ql/Qc - 1. + 2j*Ql*(fr-f)/fr ) / ( 1. - 2j*Ql*(fr-f)/fr )    
        
    def get_single_photon_limit(self,unit='dBm'):
        '''
        returns the amout of power in units of W necessary
        to maintain one photon on average in the cavity
        unit can be 'dbm' or 'watt'
        '''
        if self.fitresults!={}:
            fr = self.fitresults['fr']
            k_c = fr/self.fitresults['Qc']
            k_i = fr/self.fitresults['Qi']
            if unit=='dBm':
                return Watt2dBm(1./(4.*k_c/(2.*np.pi*hbar*fr*(k_c+k_i)**2)))
            elif unit=='watt':
                return 1./(4.*k_c/(2.*np.pi*hbar*fr*(k_c+k_i)**2))
                
        else:
            warnings.warn('Please perform the fit first',UserWarning)
            return None
        
    def get_photons_in_resonator(self,power,unit='dBm'):
        '''
        returns the average number of photons
        for a given power (defaul unit is 'dbm')
        unit can be 'dBm' or 'watt'
        '''
        if self.fitresults!={}:
            if unit=='dBm':
                power = dBm2Watt(power)
            fr = self.fitresults['fr']
            k_c = fr/self.fitresults['Qc']
            k_i = fr/self.fitresults['Qi']
            return 4.*k_c/(2.*np.pi*hbar*fr*(k_c+k_i)**2) * power
        else:
            warnings.warn('Please perform the fit first',UserWarning)
            return None
    
class notch_port(circlefit, save_load, plotting, calibration):
    '''
    notch type port probed in transmission
    '''
    def __init__(self, f_data=None, z_data_raw=None):
        self.porttype = 'notch'
        self.fitresults = {}
        self.z_data = None
        if f_data is not None:
            self.f_data = np.array(f_data)
        else:
            self.f_data=None
        if z_data_raw is not None:
            self.z_data_raw = np.array(z_data_raw)
        else:
            self.z_data_raw=None
    
    def get_delay(self,f_data,z_data,delay=None,ignoreslope=True,guess=True):
        '''
        retrieves the cable delay assuming the ideal resonance has a circular shape
        modifies the cable delay until the shape Im(S21) vs Re(S21) is circular
        see "do_calibration"
        '''
        maxval = np.max(np.absolute(z_data))
        z_data = z_data/maxval
        A1, A2, A3, A4, fr, Ql = self._fit_skewed_lorentzian(f_data,z_data)
        if ignoreslope==True:
            A2 = 0
        else:
            z_data = (np.absolute(z_data)-A2*(f_data-fr)) * np.exp(np.angle(z_data)*1j)  #usually not necessary
        if delay==None:
            if guess==True:
                delay = self._guess_delay(f_data,z_data)
            else:
                delay=0.
            delay = self._fit_delay(f_data,z_data,delay,maxiter=200)
        params = [A1, A2, A3, A4, fr, Ql]
        return delay, params    
    
    def do_calibration(self,f_data,z_data,ignoreslope=True,guessdelay=True):
        '''
        performs an automated calibration and tries to determine the prefactors a, alpha, delay
        fr, Ql, and a possible slope are extra information, which can be used as start parameters for subsequent fits
        see also "do_normalization"
        the calibration procedure works for transmission line resonators as well
        '''
        delay, params = self.get_delay(f_data,z_data,ignoreslope=ignoreslope,guess=guessdelay)
        z_data = (z_data-params[1]*(f_data-params[4]))*np.exp(2.*1j*np.pi*delay*f_data)
        xc, yc, r0 = self._fit_circle(z_data)
        zc = np.complex(xc,yc)
        fitparams = self._phase_fit(f_data,self._center(z_data,zc),0.,np.absolute(params[5]),params[4])
        theta, Ql, fr = fitparams
        beta = self._periodic_boundary(theta+np.pi,np.pi)
        offrespoint = np.complex((xc+r0*np.cos(beta)),(yc+r0*np.sin(beta)))
        alpha = np.angle(offrespoint)
        a = np.absolute(offrespoint)
        return delay, a, alpha, fr, Ql, params[1], params[4]
    
    def do_normalization(self,f_data,z_data,delay,amp_norm,alpha,A2,frcal):
        '''
        removes the prefactors a, alpha, delay and returns the calibrated data, see also "do_calibration"
        works also for transmission line resonators
        '''
        return (z_data-A2*(f_data-frcal))/amp_norm*np.exp(1j*(-alpha+2.*np.pi*delay*f_data))

    def circlefit(self,f_data,z_data,fr=None,Ql=None,refine_results=False,calc_errors=True):
        '''
        performs a circle fit on a frequency vs. complex resonator scattering data set
        Data has to be normalized!!
        INPUT:
        f_data,z_data: input data (frequency, complex S21 data)
        OUTPUT:
        outpus a dictionary {key:value} consisting of the fit values, errors and status information about the fit
        values: {"phi0":phi0, "Ql":Ql, "absolute(Qc)":absQc, "Qi": Qi, "electronic_delay":delay, "complexQc":complQc, "resonance_freq":fr, "prefactor_a":a, "prefactor_alpha":alpha}
        errors: {"phi0_err":phi0_err, "Ql_err":Ql_err, "absolute(Qc)_err":absQc_err, "Qi_err": Qi_err, "electronic_delay_err":delay_err, "resonance_freq_err":fr_err, "prefactor_a_err":a_err, "prefactor_alpha_err":alpha_err}
        for details, see:
            [1] (not diameter corrected) Jiansong Gao, "The Physics of Superconducting Microwave Resonators" (PhD Thesis), Appendix E, California Institute of Technology, (2008)
            [2] (diameter corrected) M. S. Khalil, et. al., J. Appl. Phys. 111, 054510 (2012)
            [3] (fitting techniques) N. CHERNOV AND C. LESORT, "Least Squares Fitting of Circles", Journal of Mathematical Imaging and Vision 23, 239, (2005)
            [4] (further fitting techniques) P. J. Petersan, S. M. Anlage, J. Appl. Phys, 84, 3392 (1998)
        the program fits the circle with the algebraic technique described in [3], the rest of the fitting is done with the scipy.optimize least square fitting toolbox
        also, check out [5] S. Probst et al. "Efficient and reliable analysis of noisy complex scatterung resonator data for superconducting quantum circuits" (in preparation)
        '''
    
        if fr==None: fr=f_data[np.argmin(np.absolute(z_data))]
        if Ql==None: Ql=1e6
        xc, yc, r0 = self._fit_circle(z_data,refine_results=refine_results)
        phi0 = -np.arcsin(yc/r0)
        theta0 = self._periodic_boundary(phi0+np.pi,np.pi)
        z_data_corr = self._center(z_data,np.complex(xc,yc))
        theta0, Ql, fr = self._phase_fit(f_data,z_data_corr,theta0,Ql,fr)
        #print("Ql from phasefit is: " + str(Ql))
        absQc = Ql/(2.*r0)
        complQc = absQc*np.exp(1j*((-1.)*phi0))
        Qc = 1./(1./complQc).real   # here, taking the real part of (1/complQc) from diameter correction method
        Qi_dia_corr = 1./(1./Ql-1./Qc)
        Qi_no_corr = 1./(1./Ql-1./absQc)
    
        results = {"Qi_dia_corr":Qi_dia_corr,"Qi_no_corr":Qi_no_corr,"absQc":absQc,"Qc_dia_corr":Qc,"Ql":Ql,"fr":fr,"theta0":theta0,"phi0":phi0}
    
        #calculation of the error
        p = [fr,absQc,Ql,phi0]
        #chi_square, errors = rt.get_errors(rt.residuals_notch_ideal,f_data,z_data,p)
        if calc_errors==True:
            chi_square, cov = self._get_cov_fast_notch(f_data,z_data,p)
            #chi_square, cov = rt.get_cov(rt.residuals_notch_ideal,f_data,z_data,p)
    
            if cov is not None:
                errors = np.sqrt(np.diagonal(cov))
                fr_err,absQc_err,Ql_err,phi0_err = errors
                #calc Qi with error prop (sum the squares of the variances and covariaces)
                dQl = 1./((1./Ql-1./absQc)**2*Ql**2)
                dabsQc = - 1./((1./Ql-1./absQc)**2*absQc**2)
                Qi_no_corr_err = np.sqrt((dQl**2*cov[2][2]) + (dabsQc**2*cov[1][1])+(2*dQl*dabsQc*cov[2][1]))  #with correlations
                #calc Qi dia corr with error prop
                dQl = 1/((1/Ql-np.cos(phi0)/absQc)**2 *Ql**2)
                dabsQc = -np.cos(phi0)/((1/Ql-np.cos(phi0)/absQc)**2 *absQc**2)
                dphi0 = -np.sin(phi0)/((1/Ql-np.cos(phi0)/absQc)**2 *absQc)
                ##err1 = ( (dQl*cov[2][2])**2 + (dabsQc*cov[1][1])**2 + (dphi0*cov[3][3])**2 )
                err1 = ( (dQl**2*cov[2][2]) + (dabsQc**2*cov[1][1]) + (dphi0**2*cov[3][3]) )
                err2 = ( dQl*dabsQc*cov[2][1] + dQl*dphi0*cov[2][3] + dabsQc*dphi0*cov[1][3] )
                Qi_dia_corr_err =  np.sqrt(err1+2*err2)  # including correlations
                errors = {"phi0_err":phi0_err, "Ql_err":Ql_err, "absQc_err":absQc_err, "fr_err":fr_err,"chi_square":chi_square,"Qi_no_corr_err":Qi_no_corr_err,"Qi_dia_corr_err": Qi_dia_corr_err}
                results.update( errors )
            else:
                print("WARNING: Error calculation failed!")
        else:
            #just calc chisquared:
            fun2 = lambda x: self._residuals_notch_ideal(x,f_data,z_data)**2
            chi_square = 1./float(len(f_data)-len(p)) * (fun2(p)).sum()
            errors = {"chi_square":chi_square}
            results.update(errors)
    
        return results
        
    def autofit(self):
        '''
        automatic calibration and fitting
        '''
        delay, amp_norm, alpha, fr, Ql, A2, frcal =\
                self.do_calibration(self.f_data,self.z_data_raw,ignoreslope=True,guessdelay=True)
        self.z_data = self.do_normalization(self.f_data,self.z_data_raw,delay,amp_norm,alpha,A2,frcal)
        self.fitresults = self.circlefit(self.f_data,self.z_data,fr,Ql,refine_results=False,calc_errors=True)
        self.z_data_sim = A2*(self.f_data-frcal)+self._S21_notch(self.f_data,fr=self.fitresults["fr"],Ql=self.fitresults["Ql"],Qc=self.fitresults["absQc"],phi=self.fitresults["phi0"],a=amp_norm,alpha=alpha,delay=delay)
    
    def _S21_notch(self,f,fr=10e9,Ql=900,Qc=1000.,phi=0.,a=1.,alpha=0.,delay=.0):
        '''
        full model for notch type resonances
        '''
        return a*np.exp(np.complex(0,alpha))*np.exp(-2j*np.pi*f*delay)*(1.-Ql/Qc*np.exp(1j*phi)/(1.+2j*Ql*(f-fr)/fr))    
    
    def get_single_photon_limit(self,unit='dBm'):
        '''
        returns the amout of power in units of W necessary
        to maintain one photon on average in the cavity
        unit can be 'dBm' or 'watt'
        '''
        if self.fitresults!={}:
            fr = self.fitresults['fr']
            k_c = fr/self.fitresults['absQc']
            k_i = fr/self.fitresults['Qi_dia_corr']
            if unit=='dBm':
                return Watt2dBm(1./(4.*k_c/(2.*np.pi*hbar*fr*(k_c+k_i)**2)))
            elif unit=='watt':
                return 1./(4.*k_c/(2.*np.pi*hbar*fr*(k_c+k_i)**2))                
        else:
            warnings.warn('Please perform the fit first',UserWarning)
            return None
        
    def get_photons_in_resonator(self,power,unit='dBm'):
        '''
        returns the average number of photons
        for a given power in units of W
        unit can be 'dBm' or 'watt'
        '''
        if self.fitresults!={}:
            if unit=='dBm':
                power = dBm2Watt(power)
            fr = self.fitresults['fr']
            k_c = fr/self.fitresults['Qc']
            k_i = fr/self.fitresults['Qi']
            return 4.*k_c/(2.*np.pi*hbar*fr*(k_c+k_i)**2) * power
        else:
            warnings.warn('Please perform the fit first',UserWarning)
            return None   

class transmission_port(circlefit,save_load,plotting):
    '''
    a class for handling transmission measurements
    '''
    
    def __init__(self,f_data=None,z_data_raw=None):
        self.porttype = 'transm'
        self.fitresults = {}
        if f_data!=None:
            self.f_data = np.array(f_data)
        else:
            self.f_data=None
        if z_data_raw!=None:
            self.z_data_raw = np.array(z_data_raw)
        else:
            self.z_data=None
        
    def _S21(self,f,fr,Ql,A):
        return A**2/(1.+4.*Ql**2*((f-fr)/fr)**2) 
        
    def fit(self):
        self.ampsqr = (np.absolute(self.z_data_raw))**2
        p = [self.f_data[np.argmax(self.ampsqr)],1000.,np.amax(self.ampsqr)]
        popt, pcov = spopt.curve_fit(self._S21, self.f_data, self.ampsqr,p)
        errors = np.sqrt(np.diag(pcov))
        self.fitresults = {'fr':popt[0],'fr_err':errors[0],'Ql':popt[1],'Ql_err':errors[1],'Ampsqr':popt[2],'Ampsqr_err':errors[2]} 
    
class resonator(object):
    '''
    Universal resonator analysis class
    It can handle different kinds of ports and assymetric resonators.
    '''
    def __init__(self, ports = {}, comment = None):
        '''
        initializes the resonator class object
        ports (dictionary {key:value}): specify the name and properties of the coupling ports
            e.g. ports = {'1':'direct', '2':'notch'}
        comment: add a comment
        '''
        self.comment = comment
        self.port = {}
        self.transm = {}
        if len(ports) > 0:
            for key, pname in ports.iteritems():
                if pname=='direct':
                    self.port.update({key:reflection_port()})
                elif pname=='notch':
                    self.port.update({key:notch_port()})
                else:
                    warnings.warn("Undefined input type! Use 'direct' or 'notch'.", SyntaxWarning)
        if len(self.port) == 0: warnings.warn("Resonator has no coupling ports!", UserWarning)
            
    def add_port(self,key,pname):
        if pname=='direct':
            self.port.update({key:reflection_port()})
        elif pname=='notch':
            self.port.update({key:notch_port()})
        else:
            warnings.warn("Undefined input type! Use 'direct' or 'notch'.", SyntaxWarning)
        if len(self.port) == 0: warnings.warn("Resonator has no coupling ports!", UserWarning)
            
    def delete_port(self,key):
        del self.port[key]
        if len(self.port) == 0: warnings.warn("Resonator has no coupling ports!", UserWarning)
        
    def get_Qi(self):
        '''
        based on the number of ports and the corresponding measurements
        it calculates the internal losses
        '''
        pass
    
    def get_single_photon_limit(self,port):
        '''
        returns the amout of power necessary to maintain one photon 
        on average in the cavity
        '''
        pass
    
    def get_photons_in_resonator(self,power,port):
        '''
        returns the average number of photons
        for a given power
        '''
        pass
        
    def add_transm_meas(self,port1, port2):
        '''
        input: port1
        output: port2
        adds a transmission measurement 
        connecting two direct ports S21
        '''
        key = port1 + " -> " + port2
        self.port.update({key:transm()})
        pass

   
class batch_processing(object):
    '''
    A class for batch processing of resonator data as a function of another variable
    Typical applications are power scans, magnetic field scans etc.
    '''
    
    def __init__(self,porttype):
        '''
        porttype = 'notch', 'direct', 'transm'
        results is an array of dictionaries containing the fitresults
        '''
        self.porttype = porttype
        self.results = []
    
    def autofit(self,cal_dataslice = 0):
        '''
        fits all data
        cal_dataslice: choose scatteringdata which should be used for calibration
        of the amplitude and phase, default = 0 (first)
        '''
        pass
    
class coupled_resonators(batch_processing):
    '''
    A class for fitting a resonator coupled to a second one
    '''
    
    def __init__(self,porttype):
        self.porttype = porttype
        self.results = []
    