
# written by Sebastian Probst <Sebastian.Probst@kit.edu> (2014)

## load all libraries
import resonator_tools_xtras as rtx
import numpy as np
import matplotlib.pyplot as plt

## Step 0: Load Data
f_data, z_data_raw = rtx.load_data('S21testdata.s2p',3,4)
f_data = f_data*1e9 #because data is in GHz units
print "Step 0: data loaded"

## Automatic calibration (gets all the prefactors of the environment)
#step1#

delay, amp_norm, alpha, fr, Qr, A2, frcal = rtx.do_calibration(f_data,z_data_raw,ignoreslope=True)
print "Step 1: calibration finished"
#----#

##prepare data (remove delay, and normalize)
#step2#
z_data = rtx.do_normalization(f_data,z_data_raw,delay,amp_norm,alpha,A2,frcal)
print "Step 2: normalization finished"
#----#

## optional plotting
#rtx.plot(f_data,z_data,'logamp')
#rtx.plot(f_data,z_data,'phase')
#rtx.plot(f_data,z_data,'circle')

##calculate Q values etc.
#step3#  (function assumes normalized data without cable delay or phase offsets, use step 1 and 2 to remove these)
#results = rtx.circlefit(f_data,z_data,fr,Qr,refine_results=False,calc_errors=True)  # use this for calculation with errors
results = rtx.circlefit(f_data,z_data,fr,Qr,refine_results=False,calc_errors=True)  # calculation without errors (faster)

print "Step 3: circlefit finished"
#----#

#optional data output (more available, see source)
print "Fit results:"
print results

#optional: least square fit of the entire model (slow)
# you have to give start values
#results2 = rtx.fit_S21data(f_data,z_data_raw,amp_norm,alpha,delay,Qr,absQc,phi0,fr,maxiter=0)

#optinal: plot function with fitted parameters
z_data_sim = np.array([A2*(f-frcal)+rtx.S21(f,fr=results["fr"],Qr=results["Qr"],Qc=results["absQc"],phi=results["phi0"],a=amp_norm,alpha=alpha,delay=delay) for f in f_data])

#some plotting
real = z_data_raw.real
imag = z_data_raw.imag
real2 = z_data_sim.real
imag2 = z_data_sim.imag

plt.subplot(221)
plt.plot(real,imag,label='rawdata')
plt.plot(real2,imag2,label='fit')
plt.xlabel('Re(S21)')
plt.ylabel('Im(S21)')
plt.legend()
plt.subplot(222)
plt.plot(f_data*1e-9,np.absolute(z_data_raw),label='rawdata')
plt.plot(f_data*1e-9,np.absolute(z_data_sim),label='fit')
plt.xlabel('f (GHz)')
plt.ylabel('|S21|')
plt.legend()
plt.subplot(223)
plt.plot(f_data*1e-9,np.angle(z_data_raw),label='rawdata')
plt.plot(f_data*1e-9,np.angle(z_data_sim),label='fit')
plt.xlabel('f (GHz)')
plt.ylabel('arg(|S21|)')
plt.legend()
plt.show()


