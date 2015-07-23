
#resonator_tools_xtras.py (extension to resonator_tools.py)
#several useful functions for analyzing resonator data
#by Sebastian Probst  <sebastian.probst@kit.edu>
#last update: 04/06/2015

import matplotlib.pyplot as plt
import resonator_tools as rt
import numpy as np
import random
import time


def init_random():
    random.seed(time.time())

def load_data(filename,y1_col,y2_col,sformat='realimag',phase_conversion = 1,ampformat='lin',fdata_unit=1.,delimiter=None):
    '''
    sformat = 'realimag' or 'ampphase'
    ampformat = 'lin' or 'log'
    '''
    f = open(filename)
    lines = f.readlines()
    f.close()
    z_data = []
    f_data = []

    if sformat=='realimag':
        for line in lines:
            if ((line!="\n") and (line[0]!="#") and (line[0]!="!")) :
                lineinfo = line.split(delimiter)
                f_data.append(float(lineinfo[0])*fdata_unit)
                z_data.append(np.complex(float(lineinfo[y1_col]),float(lineinfo[y2_col])))
    elif sformat=='ampphase' and ampformat=='lin':
        for line in lines:
            if ((line!="\n") and (line[0]!="#") and (line[0]!="!") and (line[0]!="M") and (line[0]!="P")):
                lineinfo = line.split(delimiter)
                f_data.append(float(lineinfo[0])*fdata_unit)
                z_data.append(float(lineinfo[y1_col])*np.exp( np.complex(0.,phase_conversion*float(lineinfo[y2_col]))))
    elif sformat=='ampphase' and ampformat=='log':
        for line in lines:
            if ((line!="\n") and (line[0]!="#") and (line[0]!="!") and (line[0]!="M") and (line[0]!="P")):
                lineinfo = line.split(delimiter)
                f_data.append(float(lineinfo[0])*fdata_unit)
                linamp = 10**(float(lineinfo[y1_col])/20.)
                z_data.append(linamp*np.exp( np.complex(0.,phase_conversion*float(lineinfo[y2_col]))))
    else:
        print "ERROR"
    return np.array(f_data), np.array(z_data)

def cut_data(f_data,z_data,f1,f2):
    def findpos(f_data,val):
        pos = 0
        for i in range(len(f_data)):
            if f_data[i]<val: pos=i
        return pos
    pos1 = findpos(f_data,f1)
    pos2 = findpos(f_data,f2)
    f_data = f_data[pos1:pos2]
    z_data = z_data[pos1,pos2]
    return f_data, z_data

def add_noise_notch(z_data,Qr,Qc,SNR):
    '''
    adds noise to the radius of each point on the resonance circle
    SNR is the desired signal to noise ration, see also "SNR"-function
    only for simulated data in canonical position
    '''
    r0 = 0.5*Qr/Qc
    xc = 1.-r0
    for i in range(len(z_data)):
        #translate to origin
        ri = np.absolute(z_data[i]-xc)
        pi = np.angle(z_data[i]-xc)
        #add noise on radius
        ri_noise = random.gauss(ri,r0/float(SNR))  #def.: SNR = signalamp/sigma
        #shift everything back
        z_data[i] = (ri_noise*np.exp(np.complex(0,pi)))+xc
    return z_data

def shiftandrotate(f_data,z_data,a,alpha,delay):
    '''
    deforms the resonance circle
    '''
    z_data = [z_data[i]*a*np.exp(np.complex(0,-2.*np.pi*delay*f_data[i]+alpha)) for i in range(len(f_data))]
    return z_data

def S21(f,fr=10e9,Qr=900,Qc=1000.,phi=0.,a=1.,alpha=0.,delay=.0):
    '''
    old relict, does the the as "S21_notch"
    '''
    return a*np.exp(np.complex(0,alpha))*np.exp(np.complex(0,-2.*np.pi*f*delay))*(1.-Qr/Qc*np.exp(np.complex(0,phi))/np.complex(1,2*Qr*(f-fr)/fr))

def S21_notch(f,fr=10e9,Qr=900,Qc=1000.,phi=0.,a=1.,alpha=0.,delay=.0):
    '''
    full model for notch type resonances
    '''
    return a*np.exp(np.complex(0,alpha))*np.exp(np.complex(0,-2.*np.pi*f*delay))*(1.-Qr/Qc*np.exp(np.complex(0,phi))/np.complex(1,2*Qr*(f-fr)/fr))

def S21_transm(f,fr=10e9,Qr=900,Qc=1000.,phi=0.,a=1.,alpha=0.,delay=.0):
    '''
    full model for transmission line resonators
    '''
    return a*np.exp(np.complex(0,alpha))*np.exp(np.complex(0,-2.*np.pi*f*delay))*(Qr/Qc*np.exp(np.complex(0,phi))/np.complex(1,2*Qr*(f-fr)/fr))

def SNR(z_data,x_c,y_c,r):
    '''
    calculates the signal to noise ration,
    which is defined by the radius of the resonance circle divided by its standard deviation
    '''
    N = len(z_data)
    sum = 0.
    for i in range(N):
        z = z_data[i]
        di = np.sqrt((z.real-x_c)**2+(z.imag-y_c)**2)
        sum += (di-r)**2
    return r/(np.sqrt(1/float(N-1)*sum))


def get_delay(f_data,z_data,delay=None,ignoreslope=True,guess=True):
    '''
    retrieves the cable delay assuming the ideal resonance has a circular shape
    modifies the cable delay until the shape Im(S21) vs Re(S21) is circular
    see "do_calibration"
    '''
    maxval = np.max(np.absolute(z_data))
    z_data = z_data/maxval
    A1, A2, A3, A4, fr, Qr = rt.fit_skewed_lorentzian(f_data,z_data)
    if ignoreslope==True:
        A2 = 0
    else:
        z_data = (np.absolute(z_data)-A2*(f_data-fr)) * np.exp(np.angle(z_data)*1j)  #usually not necessary
    if delay==None:
        if guess==True:
            delay = rt.guess_delay(f_data,z_data)
        else:
            delay=0.
        delay = rt.fit_delay(f_data,z_data,delay,maxiter=200)
    params = [A1, A2, A3, A4, fr, Qr]
    return delay, params

def do_calibration(f_data,z_data,ignoreslope=True,guessdelay=True):
    '''
    performs an automated calibration and tries to determine the prefactors a, alpha, delay
    fr, Qr, and a possible slope are extra information, which can be used as start parameters for subsequent fits
    see also "do_normalization"
    the calibration procedure works for transmission line resonators as well
    '''
    delay, params = get_delay(f_data,z_data,ignoreslope=ignoreslope,guess=guessdelay)
    z_data = (z_data-params[1]*(f_data-params[4]))*np.exp(2.*1j*np.pi*delay*f_data)
    xc, yc, r0 = rt.fit_circle(z_data)
    zc = np.complex(xc,yc)
    fitparams = rt.phase_fit(f_data,rt.center(z_data,zc),0.,np.absolute(params[5]),params[4])
    theta, Qr, fr = fitparams
    beta = rt.periodic_boundary(theta+np.pi,np.pi)
    offrespoint = np.complex((xc+r0*np.cos(beta)),(yc+r0*np.sin(beta)))
    alpha = np.angle(offrespoint)
    a = np.absolute(offrespoint)
    return delay, a, alpha, fr, Qr, params[1], params[4]

def do_normalization(f_data,z_data,delay,amp_norm,alpha,A2,frcal):
    '''
    removes the prefactors a, alpha, delay and returns the calibrated data, see also "do_calibration"
    works also for transmission line resonators
    '''
    return (z_data-A2*(f_data-frcal))/amp_norm*np.exp(1j*(-alpha+2.*np.pi*delay*f_data))

def plot(f_data,z_data,plottype='logamp'):
    '''
    plottypes are amp, phase, circle
    '''
    if plottype=='amp':
        amp = [np.absolute(z) for z in z_data]
        plt.plot(f_data,amp)
        plt.show()
    if plottype=='logamp':
        amp = [20*np.log10(np.absolute(z)) for z in z_data]
        plt.plot(f_data,amp)
        plt.show()
    if plottype=='phase':
        phase = [np.angle(z) for z in z_data]
        plt.plot(f_data,phase)
        plt.show()
    if plottype=='circle':
        real = [z.real for z in z_data]
        imag = [z.imag for z in z_data]
        plt.plot(real,imag)
        plt.show()
    return True

def transmissionfit(f_data,z_data,fr,Qr): #not tested
    '''
    phasefit enhanced by circlefit method
    '''
    xc, yc, r0 = rt.fit_circle(z_data)
    zc = np.complex(xc,yc)
    fitparams = rt.phase_fit_nooffset(f_data,rt.center(z_data,zc),Qr,fr)
    Qr, fr = fitparams[0]
    results = {"Qr":Qr,"fr":fr}
    p = fr, Qr
    chi_square, cov = rt.get_cov(rt.residuals_transm_ideal,f_data,z_data,p)
    if cov!=None:
        errors = [np.sqrt(cov[i][i]) for i in range(len(cov))]
        results.update({"fr_err":errors[0],"Qr_err":errors[1],"chi_square":chi_square})
    return results

def circlefit(f_data,z_data,fr=None,Qr=None,refine_results=False,calc_errors=True):
    '''
    performs a circle fit on a frequency vs. complex resonator scattering data set
    Data has to be normalized!!
    INPUT:
    f_data,z_data: input data (frequency, complex S21 data)
    OUTPUT:
    outpus a dictionary {key:value} consisting of the fit values, errors and status information about the fit
    values: {"phi0":phi0, "Qr":Qr, "absolute(Qc)":absQc, "Qi": Qi, "electronic_delay":delay, "complexQc":complQc, "resonance_freq":fr, "prefactor_a":a, "prefactor_alpha":alpha}
    errors: {"phi0_err":phi0_err, "Qr_err":Qr_err, "absolute(Qc)_err":absQc_err, "Qi_err": Qi_err, "electronic_delay_err":delay_err, "resonance_freq_err":fr_err, "prefactor_a_err":a_err, "prefactor_alpha_err":alpha_err}
    for details, see:
        [1] (not diameter corrected) Jiansong Gao, "The Physics of Superconducting Microwave Resonators" (PhD Thesis), Appendix E, California Institute of Technology, (2008)
        [2] (diameter corrected) M. S. Khalil, et. al., J. Appl. Phys. 111, 054510 (2012)
        [3] (fitting techniques) N. CHERNOV AND C. LESORT, "Least Squares Fitting of Circles", Journal of Mathematical Imaging and Vision 23, 239, (2005)
        [4] (further fitting techniques) P. J. Petersan, S. M. Anlage, J. Appl. Phys, 84, 3392 (1998)
    the program fits the circle with the algebraic technique described in [3], the rest of the fitting is done with the scipy.optimize least square fitting toolbox
    also, check out [5] S. Probst et al. "Efficient and reliable analysis of noisy complex scatterung resonator data for superconducting quantum circuits" (in preparation)
    '''

    if fr==None: fr=f_data[np.argmin(np.absolute(z_data))]
    if Qr==None: Qr=1e6
    xc, yc, r0 = rt.fit_circle(z_data,refine_results=refine_results)
    phi0 = -np.arcsin(yc/r0)
    theta0 = rt.periodic_boundary(phi0+np.pi,np.pi)
    z_data_corr = rt.center(z_data,np.complex(xc,yc))
    theta0, Qr, fr = rt.phase_fit(f_data,z_data_corr,theta0,Qr,fr)
    #print "Qr from phasefit is: " + str(Qr)
    absQc = Qr/(2.*r0)
    complQc = absQc*np.exp(1j*((-1.)*phi0))
    Qc = 1./(1./complQc).real   # here, taking the real part of (1/complQc) from diameter correction method
    Qi_dia_corr = 1./(1./Qr-1./Qc)
    Qi_no_corr = 1./(1./Qr-1./absQc)

    results = {"Qi_dia_corr":Qi_dia_corr,"Qi_no_corr":Qi_no_corr,"absQc":absQc,"Qc_dia_corr":Qc,"Qr":Qr,"fr":fr,"theta0":theta0,"phi0":phi0}

    #calculation of the error
    p = [fr,absQc,Qr,phi0]
    #chi_square, errors = rt.get_errors(rt.residuals_notch_ideal,f_data,z_data,p)
    if calc_errors==True:
        chi_square, cov, ret_sucess = rt.get_cov_fast(f_data,z_data,p)
        #chi_square, cov = rt.get_cov(rt.residuals_notch_ideal,f_data,z_data,p)

        if ret_sucess:
            errors = np.sqrt(np.diagonal(cov))
            fr_err,absQc_err,Qr_err,phi0_err = errors
            #calc Qi with error prop (sum the squares of the variances and covariaces)
            dQr = 1./((1./Qr-1./absQc)**2*Qr**2)
            dabsQc = - 1./((1./Qr-1./absQc)**2*absQc**2)
            Qi_no_corr_err = np.sqrt((dQr**2*float(cov[2][2])) + (dabsQc**2*float(cov[1][1]))+(2*dQr*dabsQc*float(cov[2][1])))  #with correlations
            #calc Qi dia corr with error prop
            dQr = 1/((1/Qr-np.cos(phi0)/absQc)**2 *Qr**2)
            dabsQc = -np.cos(phi0)/((1/Qr-np.cos(phi0)/absQc)**2 *absQc**2)
            dphi0 = -np.sin(phi0)/((1/Qr-np.cos(phi0)/absQc)**2 *absQc)
            ##err1 = ( (dQr*cov[2][2])**2 + (dabsQc*cov[1][1])**2 + (dphi0*cov[3][3])**2 )
            err1 = ( (dQr**2*float(cov[2][2])) + (dabsQc**2*float(cov[1][1])) + (dphi0**2*float(cov[3][3])) )
            err2 = ( dQr*dabsQc*float(cov[2][1]) + dQr*dphi0*float(cov[2][3]) + dabsQc*dphi0*float(cov[1][3]) )
            Qi_dia_corr_err =  np.sqrt(err1+2*err2)  # including correlations
            errors = {"phi0_err":phi0_err, "Qr_err":Qr_err, "absQc_err":absQc_err, "fr_err":fr_err,"chi_square":chi_square,"Qi_no_corr_err":Qi_no_corr_err,"Qi_dia_corr_err": Qi_dia_corr_err}
            results.update( errors )
        else:
            print "WARNING: Error calculation failed!"
    else:
        #just calc chisquared:
        fun2 = lambda x: rt.residuals_notch_ideal(x,f_data,z_data)**2
        chi_square = 1./float(len(f_data)-len(p)) * (fun2(p)).sum()
        errors = {"chi_square":chi_square}
        results.update(errors)

    return results

def get_full_errors(f_data,z_data,a,alpha,delay,results):
    '''
    calculates the statistical error for all variables
    "results" is the dictionary returned by the circlefit routine
    returns a dictionary with the errors and None if something went wrong
    '''
    fr,absQc,Qr,phi0 = results["fr"], results["absQc"], results["Qr"], results["phi0"]
    p= fr,absQc,Qr,phi0,delay,a,alpha
    chi_square, cov = rt.get_cov(rt.residuals_notch_full,f_data,z_data,p)
    errors = None
    if cov!=None:
        errors = [np.sqrt(cov[i][i]) for i in range(len(cov))]
        fr_err,absQc_err,Qr_err,phi0_err, delay_err, a_err, alpha_err = errors
        #calc Qi with error prop (sum the squares of the variances and covariaces)
        dQr = 1./((1./Qr-1./absQc)**2*Qr**2)
        dabsQc = - 1./((1./Qr-1./absQc)**2*absQc**2)
        Qi_no_corr_err = np.sqrt((dQr**2*cov[2][2]) + (dabsQc**2*cov[1][1])+(2*dQr*dabsQc*cov[2][1]))
        #calc Qi dia corr with error prop
        dQr = 1/((1/Qr-np.cos(phi0)/absQc)**2 *Qr**2)
        dabsQc = -np.cos(phi0)/((1/Qr-np.cos(phi0)/absQc)**2 *absQc**2)
        dphi0 = -np.sin(phi0)/((1/Qr-np.cos(phi0)/absQc)**2 *absQc)
        err1 = ( (dQr**2*cov[2][2]) + (dabsQc**2*cov[1][1]) + (dphi0**2*cov[3][3]) )
        err2 = ( dQr*dabsQc*cov[2][1] + dQr*dphi0*cov[2][3] + dabsQc*dphi0*cov[1][3] )
        Qi_dia_corr_err = np.sqrt(err1+2*err2)
        errors = {"phi0_err":phi0_err, "Qr_err":Qr_err, "absQc_err":absQc_err, "fr_err":fr_err,"chi_square":chi_square,"Qi_no_corr_err":Qi_no_corr_err,"Qi_dia_corr_err": Qi_dia_corr_err, "a_err":a_err,"alpha_err":alpha_err,"delay_err":delay_err}
    else:
        print "WARNING: Error calculation failed!"
    return errors


def fit_S21data(f_data,z_data,amp_norm,alpha,delay,Qr,absQc,phi0,fr,maxiter=0):
    '''
    performs an iterative non-linear least square fit
    do not use this, since it is very slow - use the circlefit instead
    only use it for comparison with the circle fit method
    '''
    ###here comes the final parameter optimization , show all errors! calc error for Qi
    final_params, params_cov, infodict, mesg, ier = rt.fit_entire_model(f_data,z_data,fr,absQc,Qr,phi0,delay,a=amp_norm,alpha=alpha,maxiter=maxiter)   #output: result, cov_x, infodict, mesg, ier
    if(ier in [1,2,3,4]):
        fit_success = True
    else:
        fit_success = False
    fr,absQc,Qr,phi0,delay,a,alpha = final_params
    fr_err,absQc_err,Qr_err,phi0_err,delay_err,a_err,alpha_err = [np.sqrt(params_cov[i][i]) for i in range(len(final_params))]
    complQc = absQc*np.exp(1j*((-1.)*phi0))
    Qc = 1./(1./complQc).real   # here, taking the real part of (1/complQc) from diameter correction method
    Qi_dia_corr = 1./(1./Qr-1./Qc)          # diameter corrected Qi
    Qi_no_corr = 1./(1./Qr-1./absQc)          # uncorrected Qi
    # error of internal quality factor, calculated with gaussian propagation of error, taking all correlations into account!
    def calc_Qi_dia_corr_error(Qr,absQc,phi0,variance):
        dQr = 1./((1./Qr-np.cos(phi0)/absQc)**2 *Qr**2)
        dabsQc = -np.cos(phi0)/((1/Qr-np.cos(phi0)/absQc)**2 *absQc**2)
        dphi0 = -np.sin(phi0)/((1/Qr-np.cos(phi0)/absQc)**2 *absQc)
        err1 = ( (dQr**2*variance[2][2]) + (dabsQc**2*variance[1][1]) + (dphi0**2*variance[3][3]) )
        err2 = ( dQr*dabsQc*variance[2][1] + dQr*dphi0*variance[2][3] + dabsQc*dphi0*variance[1][3] )
        return np.sqrt(err1+2*err2)
    Qi_dia_corr_err = calc_Qi_dia_corr_error(Qr,absQc,phi0,params_cov)

    results = {}
    # add status info
    stat_info = {"fit_success":fit_success, "status_flag":ier, "status_message":mesg, "infodict":infodict, "covariance_matrix":params_cov}
    results.update( stat_info )
    # add values
    values = {"phi0":phi0, "Qr":Qr, "absQc":absQc, "Qi_dia_corr":Qi_dia_corr,"Qi_no_corr":Qi_no_corr , "delay":delay, "complexQc":complQc, "fr":fr, "prefactor_a":a, "prefactor_alpha":alpha}
    results.update( values )
    # add errors
    errors = {"phi0_err":phi0_err, "Qr_err":Qr_err, "absQc_err":absQc_err, "Qi_dia_corr_err": Qi_dia_corr_err, "delay_err":delay_err, "fr_err":fr_err, "prefactor_a_err":a_err, "prefactor_alpha_err":alpha_err}
    results.update( errors )
    return results




