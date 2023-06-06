
import numpy as np
from scipy import sparse
from scipy.interpolate import interp1d

class calibration(object):
    '''
    some useful tools for manual calibration
    '''
    def normalize_zdata(self,z_data,cal_z_data):
        return z_data/cal_z_data
        
    def normalize_amplitude(self,z_data,cal_ampdata):
        return z_data/cal_ampdata
        
    def normalize_phase(self,z_data,cal_phase):
        return z_data*np.exp(-1j*cal_phase)
        
    def normalize_by_func(self,f_data,z_data,func):
        return z_data/func(f_data)
        
    def _baseline_als(self,y, lam, p, niter=10):
        '''
        see http://zanran_storage.s3.amazonaws.com/www.science.uva.nl/ContentPages/443199618.pdf
        "Asymmetric Least Squares Smoothing" by P. Eilers and H. Boelens in 2005.
        http://stackoverflow.com/questions/29156532/python-baseline-correction-library
        "There are two parameters: p for asymmetry and lambda for smoothness. Both have to be
        tuned to the data at hand. We found that generally 0.001<=p<=0.1 is a good choice
        (for a signal with positive peaks) and 10e2<=lambda<=10e9, but exceptions may occur."
        '''
        L = len(y)
        D = sparse.csc_matrix(np.diff(np.eye(L), 2))
        w = np.ones(L)
        for i in xrange(niter):
            W = sparse.spdiags(w, 0, L, L)
            Z = W + lam * D.dot(D.transpose())
            z = sparse.linalg.spsolve(Z, w*y)
            w = p * (y > z) + (1-p) * (y < z)
        return z
        
    def fit_baseline_amp(self,z_data,lam,p,niter=10):
        '''
        for this to work, you need to analyze a large part of the baseline
        tune lam and p until you get the desired result
        '''
        return self._baseline_als(np.absolute(z_data),lam,p,niter=niter)
    
    def baseline_func_amp(self,z_data,f_data,lam,p,niter=10):
        '''
        for this to work, you need to analyze a large part of the baseline
        tune lam and p until you get the desired result
        returns the baseline as a function
        the points in between the datapoints are computed by cubic interpolation
        '''
        return interp1d(f_data, self._baseline_als(np.absolute(z_data),lam,p,niter=niter), kind='cubic')
        
    def baseline_func_phase(self,z_data,f_data,lam,p,niter=10):
        '''
        for this to work, you need to analyze a large part of the baseline
        tune lam and p until you get the desired result
        returns the baseline as a function
        the points in between the datapoints are computed by cubic interpolation
        '''
        return interp1d(f_data, self._baseline_als(np.angle(z_data),lam,p,niter=niter), kind='cubic')
        
    def fit_baseline_phase(self,z_data,lam,p,niter=10):
        '''
        for this to work, you need to analyze a large part of the baseline
        tune lam and p until you get the desired result
        '''
        return self._baseline_als(np.angle(z_data),lam,p,niter=niter)
