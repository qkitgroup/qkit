
#resonator_tools.py (see also resonator_tools_xtras.py for more sophisticated functions)
#several useful functions for analyzing resonator data
#by Sebastian Probst  <sebastian.probst@kit.edu>
#last update: 11/11/2013

import numpy as np
import scipy.optimize as spopt
from scipy import stats
import numdifftools as nd
import warnings

def remove_cable_delay(f_data,z_data, delay):
    return [z_data[i]/np.exp(complex(0,2.*np.pi*f_data[i]*delay)) for i in range(len(f_data))]

def center(z_data,zc):
    return [z-zc for z in z_data]

def dist(x):
    for i in range(len(x)):
        x[i] = np.abs(x[i])
        if x[i]>np.pi:
            x[i] = 2.*np.pi-x[i]
    return x

def periodic_boundary(x,bound):
    return np.fmod(x,bound)-np.trunc(x/bound)*bound


def phase_fit_wslope(f_data,z_data,theta0, Qr, fr, slope):
    phase = [np.angle(z_data[i]) for i in range(0,len(z_data),1)]
    def residuals(p,x,y):
        theta0, Qr, fr, slope = p
        err = dist(y - (theta0+2.*np.arctan(2.*Qr*(1.-x/fr))-slope*x))
        return err
    p0 = [theta0, Qr, fr, slope]
    p_final = spopt.leastsq(residuals,p0,args=(np.array(f_data),np.array(phase)))
    return p_final[0]

def phase_fit(f_data,z_data,theta0, Qr, fr):
    phase = [np.angle(z_data[i]) for i in range(0,len(z_data),1)]
    def residuals_1(p,x,y,Qr):
        theta0, fr = p
        err = dist(y - (theta0+2.*np.arctan(2.*Qr*(1.-x/fr))))
        return err
    def residuals_2(p,x,y,theta0):
        Qr, fr = p
        err = dist(y - (theta0+2.*np.arctan(2.*Qr*(1.-x/fr))))
        return err
    def residuals_3(p,x,y,theta0,Qr):
        fr = p
        err = dist(y - (theta0+2.*np.arctan(2.*Qr*(1.-x/fr))))
        return err
    def residuals_4(p,x,y,theta0,fr):
        Qr = p
        err = dist(y - (theta0+2.*np.arctan(2.*Qr*(1.-x/fr))))
        return err
    def residuals_5(p,x,y):
        theta0, Qr, fr = p
        err = dist(y - (theta0+2.*np.arctan(2.*Qr*(1.-x/fr))))
        return err
    p0 = [theta0, fr]
    p_final = spopt.leastsq(lambda a,b,c: residuals_1(a,b,c,Qr),p0,args=(np.array(f_data),np.array(phase)))#,ftol=1e-12,xtol=1e-12)
    theta0, fr = p_final[0]
    p0 = [Qr, fr]
    p_final = spopt.leastsq(lambda a,b,c: residuals_2(a,b,c,theta0),p0,args=(np.array(f_data),np.array(phase)))#,ftol=1e-12,xtol=1e-12)
    Qr, fr = p_final[0]
    p0 = fr
    p_final = spopt.leastsq(lambda a,b,c: residuals_3(a,b,c,theta0,Qr),p0,args=(np.array(f_data),np.array(phase)))#,ftol=1e-12,xtol=1e-12)
    fr = p_final[0]
    p0 = Qr
    p_final = spopt.leastsq(lambda a,b,c: residuals_4(a,b,c,theta0,fr),p0,args=(np.array(f_data),np.array(phase)))#,ftol=1e-12,xtol=1e-12)
    Qr = p_final[0]
    p0 = [theta0, Qr, fr]
    p_final = spopt.leastsq(residuals_5,p0,args=(np.array(f_data),np.array(phase)))#,ftol=1e-12,xtol=1e-12)
    return p_final[0]

def phase_fit_nooffset(f_data,z_data, Qr, fr):
    def residuals_2(p,x,y,theta):
        Qr, fr = p
        err = dist(y - (theta0+2.*np.arctan(2.*Qr*(1.-x/fr))))
        return err
    p0 = [Qr, fr]
    p_final = spopt.leastsq(lambda a,b,c: residuals_2(a,b,c,0.),p0,args=(np.array(f_data),np.array(phase)))
    return p_final[0]

def fit_skewed_lorentzian(f_data,z_data):
    amplitude = np.absolute(z_data)
    amplitude_sqr = amplitude**2
    A1a = np.min(amplitude_sqr[0],amplitude_sqr[len(amplitude_sqr)-1])
    A3a = -np.max(amplitude_sqr)
    fra = f_data[np.argmin(amplitude_sqr)]
    def residuals(p,x,y):
        A2, A4, Qr = p
        err = y -(A1a+A2*(x-fra)+(A3a+A4*(x-fra))/(1.+4.*Qr**2*((x-fra)/fra)**2))
        return err
    p0 = [0., 0., 1e3]
    p_final = spopt.leastsq(residuals,p0,args=(np.array(f_data),np.array(amplitude_sqr)))
    A2a, A4a, Qra = p_final[0]
    ##A2a, A4a, Qra = [0., 0., 1e3]

    def residuals2(p,x,y):
        A1, A2, A3, A4, fr, Qr = p
        err = y -(A1+A2*(x-fr)+(A3+A4*(x-fr))/(1.+4.*Qr**2*((x-fr)/fr)**2))
        return err
    p0 = [A1a, A2a , A3a, A4a, fra, Qra]
    p_final = spopt.leastsq(residuals2,p0,args=(np.array(f_data),np.array(amplitude_sqr)))
    #A1, A2, A3, A4, fr, Qr = p_final[0]
    #print p_final[0][5]
    return p_final[0]

def fit_circle(z_data, refine_results=False):
    def calc_moments(z_data): #optimization possible since matrix is symmetric!!!
        M = []
        xi = [z_data[i].real for i in range(0,len(z_data),1)]
        yi = [z_data[i].imag for i in range(0,len(z_data),1)]
        wi = [xi[i]*xi[i]+yi[i]*yi[i] for i in range(0,len(z_data),1)]
        ni = [1. for i in range(0,len(z_data),1)]
        coeff = [wi,xi,yi,ni]
        for x in range(0,4,1):
            col = []
            for y in range(0,4,1):
                mxy = 0.0
                for i in range(0,len(z_data),1):
                    mxy = mxy+coeff[x][i]*coeff[y][i]
                col.append(mxy)
            M.append(col)
        return M

    M = calc_moments(z_data)

    a0 = ((M[2][0]*M[3][2]-M[2][2]*M[3][0])*M[1][1]-M[1][2]*M[2][0]*M[3][1]-M[1][0]*M[2][1]*M[3][2]+M[1][0]*M[2][2]*M[3][1]+M[1][2]*M[2][1]*M[3][0])*M[0][3]+(M[0][2]*M[2][3]*M[3][0]-M[0][2]*M[2][0]*M[3][3]+M[0][0]*M[2][2]*M[3][3]-M[0][0]*M[2][3]*M[3][2])*M[1][1]+(M[0][1]*M[1][3]*M[3][0]-M[0][1]*M[1][0]*M[3][3]-M[0][0]*M[1][3]*M[3][1])*M[2][2]+(-M[0][1]*M[1][2]*M[2][3]-M[0][2]*M[1][3]*M[2][1])*M[3][0]+((M[2][3]*M[3][1]-M[2][1]*M[3][3])*M[1][2]+M[2][1]*M[3][2]*M[1][3])*M[0][0]+(M[1][0]*M[2][3]*M[3][2]+M[2][0]*(M[1][2]*M[3][3]-M[1][3]*M[3][2]))*M[0][1]+((M[2][1]*M[3][3]-M[2][3]*M[3][1])*M[1][0]+M[1][3]*M[2][0]*M[3][1])*M[0][2]
    a1 = (((M[3][0]-2.*M[2][2])*M[1][1]-M[1][0]*M[3][1]+M[2][2]*M[3][0]+2.*M[1][2]*M[2][1]-M[2][0]*M[3][2])*M[0][3]+(2.*M[2][0]*M[3][2]-M[0][0]*M[3][3]-2.*M[2][2]*M[3][0]+2.*M[0][2]*M[2][3])*M[1][1]+(-M[0][0]*M[3][3]+2.*M[0][1]*M[1][3]+2.*M[1][0]*M[3][1])*M[2][2]+(-M[0][1]*M[1][3]+2.*M[1][2]*M[2][1]-M[0][2]*M[2][3])*M[3][0]+(M[1][3]*M[3][1]+M[2][3]*M[3][2])*M[0][0]+(M[1][0]*M[3][3]-2.*M[1][2]*M[2][3])*M[0][1]+(M[2][0]*M[3][3]-2.*M[1][3]*M[2][1])*M[0][2]-2.*M[1][2]*M[2][0]*M[3][1]-2.*M[1][0]*M[2][1]*M[3][2])
    a2 = ((2.*M[1][1]-M[3][0]+2.*M[2][2])*M[0][3]+(2.*M[3][0]-4.*M[2][2])*M[1][1]-2.*M[2][0]*M[3][2]+2.*M[2][2]*M[3][0]+M[0][0]*M[3][3]+4.*M[1][2]*M[2][1]-2.*M[0][1]*M[1][3]-2.*M[1][0]*M[3][1]-2.*M[0][2]*M[2][3])
    a3 = (-2.*M[3][0]+4.*M[1][1]+4.*M[2][2]-2.*M[0][3])
    a4 = -4.

    def func(x):
        return a0+a1*x+a2*x*x+a3*x*x*x+a4*x*x*x*x

    def d_func(x):
        return a1+2*a2*x+3*a3*x*x+4*a4*x*x*x

    x0 = spopt.fsolve(func, 0., fprime=d_func)

    def solve_eq_sys(val,M):
        #prepare
        M[3][0] = M[3][0]+2*val
        M[0][3] = M[0][3]+2*val
        M[1][1] = M[1][1]-val
        M[2][2] = M[2][2]-val
        return np.linalg.svd(M)

    U,s,Vt = solve_eq_sys(x0[0],M)

    A_vec = Vt[np.argmin(s),:]

    xc = -A_vec[1]/(2*A_vec[0])
    yc = -A_vec[2]/(2*A_vec[0])
    # the term *sqrt term corrects for the constraint. why? I don't know...
    r0 = 1/(2*abs(A_vec[0]))*np.sqrt(A_vec[1]*A_vec[1]+A_vec[2]*A_vec[2]-4*A_vec[0]*A_vec[3])
    if refine_results:
        print "agebraic r0: " + str(r0)
        xc,yc,r0 = fit_circle_iter(z_data, xc, yc, r0)
        r0 = fit_circle_iter_radialweight(z_data, xc, yc, r0)
        print "iterative r0: " + str(r0)
    return xc, yc, r0

def guess_delay(f_data,z_data):
    def fmod2(a,b,c):
        '''
        periodic boundary conditions in interval b shiftet by c
        example fmod(x,2*pi,-pi) establishes periodic boundary
        conditions in interval [-pi,+pi]
        '''
        return np.fmod(b+np.fmod(a-c,b),b)+c
    phase = [np.angle(z_data[i]) for i in range(0,len(z_data),1)]
    phase2 = np.unwrap(phase)
    gradient, intercept, r_value, p_value, std_err = stats.linregress(np.array(f_data),np.array(phase2))
    return gradient*(-1.)/(np.pi*2.)


def fit_delay(f_data,z_data,delay=0.,maxiter=0):
    def residuals(p,x,y):
        phasedelay = p
        z_data_temp = [y[i]*np.exp(np.complex(0,2.*np.pi*phasedelay*x[i])) for i in range(len(x))]
        xc,yc,r0 = fit_circle(z_data_temp)
        err = [np.sqrt((z.real-xc)**2+(z.imag-yc)**2)-r0 for z in z_data_temp]
        return err
    p_final = spopt.leastsq(residuals,delay,args=(np.array(f_data),np.array(z_data)),maxfev=maxiter,ftol=1e-12,xtol=1e-12)
    return p_final[0][0]

def fit_entire_model(f_data,z_data,fr,absQc,Qr,phi0,delay,a=1.,alpha=0.,maxiter=0):
    '''
    fits the whole model: a*exp(i*alpha)*exp(-2*pi*i*f*delay) * [ 1 - {Qr/Qc*exp(i*phi0)} / {1+2*i*Qr*(f-fr)/fr} ]
    '''
    def funcsqr(p,x):
        fr,absQc,Qr,phi0,delay,a,alpha = p
        return np.array([np.absolute( ( a*np.exp(np.complex(0,alpha))*np.exp(np.complex(0,-2.*np.pi*delay*x[i])) * ( 1 - (Qr/absQc*np.exp(np.complex(0,phi0)))/(np.complex(1,2*Qr*(x[i]-fr)/fr)) )  ) )**2 for i in range(len(x))])
    def residuals(p,x,y):
        fr,absQc,Qr,phi0,delay,a,alpha = p
        err = [np.absolute( y[i] - ( a*np.exp(np.complex(0,alpha))*np.exp(np.complex(0,-2.*np.pi*delay*x[i])) * ( 1 - (Qr/absQc*np.exp(np.complex(0,phi0)))/(np.complex(1,2*Qr*(x[i]-fr)/fr)) )  ) ) for i in range(len(x))]
        return err
    p0 = [fr,absQc,Qr,phi0,delay,a,alpha]
    (popt, params_cov, infodict, errmsg, ier) = spopt.leastsq(residuals,p0,args=(np.array(f_data),np.array(z_data)),full_output=True,maxfev=maxiter)
    len_ydata = len(np.array(f_data))
    if (len_ydata > len(p0)) and params_cov is not None:  #p_final[1] is cov_x data  #this caculation is from scipy curve_fit routine - no idea if this works correctly...
        s_sq = (funcsqr(popt, np.array(f_data))).sum()/(len_ydata-len(p0))
        params_cov = params_cov * s_sq
    else:
        params_cov = inf
    return popt, params_cov, infodict, errmsg, ier  #result, cov_x*s_sq, infodict, mesg, ier

#

def optimizedelay(f_data,z_data,Qr,fr,maxiter=4):
    xc,yc,r0 = fit_circle(z_data)
    z_data = center(z_data,np.complex(xc,yc))
    theta, Qr, fr, slope = phase_fit_wslope(f_data,z_data,0.,Qr,fr,0.)
    delay = 0.
    for i in range(maxiter-1): #interate to get besser phase delay term
        delay = delay - slope/(2.*2.*np.pi)
        z_data_corr = remove_cable_delay(f_data,z_data,delay)
        xc, yc, r0 = fit_circle(z_data_corr)
        z_data_corr2 = center(z_data_corr,complex(xc,yc))
        theta0, Qr, fr, slope = phase_fit_wslope(f_data,z_data_corr2,0.,Qr,fr,0.)
    delay = delay - slope/(2.*2.*np.pi)  #start final interation
    return delay

def fit_circle_iter(z_data, xc, yc, rc):
    '''
    this is the radial weighting procedure
    it improves your fitting value for the radius = Qr/Qc
    use this to improve your fit in presence of heavy noise
    after having used the standard algebraic fir_circle() function
    the weight here is: W=1/sqrt((xc-xi)^2+(yc-yi)^2)
    this works, because the center of the circle is usually much less
    corrupted by noise than the radius
    '''
    xdat = [z.real for z in z_data]
    ydat = [z.imag for z in z_data]
    def fitfunc(x,y,xc,yc):
        return np.sqrt((x-xc)**2+(y-yc)**2)
    def residuals(p,x,y):
        xc,yc,r = p
        temp = []
        for i in range(len(x)):
            temp = (r-fitfunc(x,y,xc,yc))
        return temp
    p0 = [xc,yc,rc]
    p_final = spopt.leastsq(residuals,p0,args=(np.array(xdat),np.array(ydat)))
    xc,yc,rc = p_final[0]
    return xc,yc,rc

def fit_circle_iter_radialweight(z_data, xc, yc, rc):
    '''
    this is the radial weighting procedure
    it improves your fitting value for the radius = Qr/Qc
    use this to improve your fit in presence of heavy noise
    after having used the standard algebraic fir_circle() function
    the weight here is: W=1/sqrt((xc-xi)^2+(yc-yi)^2)
    this works, because the center of the circle is usually much less
    corrupted by noise than the radius
    '''
    xdat = [z.real for z in z_data]
    ydat = [z.imag for z in z_data]
    def fitfunc(x,y):
        return np.sqrt((x-xc)**2+(y-yc)**2)
    def weight(x,y):
        try:
            res = 1/np.sqrt((xc-x)**2+(yc-y)**2)
        except:
            res = 1.
        return res
    def residuals(p,x,y):
        r = p[0]
        temp = []
        for i in range(len(x)):
            temp = (r-fitfunc(x,y))*weight(x,y)
        return temp
    p0 = [rc]
    p_final = spopt.leastsq(residuals,p0,args=(np.array(xdat),np.array(ydat)))
    return p_final[0][0]


def get_cov(residual,xdata,ydata,fitparams):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fun1 = lambda x: np.array([residual(x,xdata[i],ydata[i]) for i in range(len(xdata))])
        fun2 = lambda x: np.array([residual(x,xdata[i],ydata[i])**2 for i in range(len(xdata))])
        Jfun = nd.Jacobian(fun1)
        J = np.array(Jfun(fitparams))
        A = np.dot(np.transpose(J),J)
        chisqr = 1./float(len(xdata)-len(fitparams)) * (fun2(fitparams)).sum()
        try:
            cov = np.linalg.inv(A)*chisqr
        except:
            cov = None
        return chisqr, cov

def get_errors(residual,xdata,ydata,fitparams):
    '''
    wrapper for get_cov, only gives the errors and chisquare
    '''
    chisqr, cov = get_cov(residual,xdata,ydata,fitparams)
    if cov!=None:
        errors = [np.sqrt(cov[i][i]) for i in range(len(cov[0]))]
    else:
        errors = None
    return chisqr, errors

def residuals_notch_full(p,x,y):
    fr,absQc,Qr,phi0,delay,a,alpha = p
    err = np.absolute( y - ( a*np.exp(np.complex(0,alpha))*np.exp(np.complex(0,-2.*np.pi*delay*x)) * ( 1 - (Qr/absQc*np.exp(np.complex(0,phi0)))/(np.complex(1,2*Qr*(x-fr)/float(fr))) )  ) )
    return err

def residuals_notch_ideal(p,x,y):
    fr,absQc,Qr,phi0 = p
    #if fr == 0: print p
    err = np.absolute( y - (  ( 1. - (Qr/float(absQc)*np.exp(np.complex(0,phi0)))/(np.complex(1,2*Qr*(x-fr)/float(fr))) )  ) )
    #if np.isinf((np.complex(1,2*Qr*(x-fr)/float(fr))).imag):
     #   print np.complex(1,2*Qr*(x-fr)/float(fr))
      #  print "x: " + str(x)
       # print "Qr: " +str(Qr)
        #print "fr: " +str(fr)
    return err

def residuals_transm_ideal(p,x,y):
    fr,Qr = p
    err = np.absolute( y -   ( 1./(np.complex(1,2*Qr*(x-fr)/float(fr))) )   )
    return err