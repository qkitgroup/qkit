import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *

import numpy as np
import resonator_tools as rt
import resonator_tools_xtras as rtx
import tools as to

def notch(f_data,z_data,progress_bar,var_col=0,f_col=1,z_col=2):
    
    progress_bar.setMaximum(len(f_data)*len(z_data))
    i_progress=0
    delay,amp_norm,alpha,fr,Qr,A2,frcal=rtx.do_calibration(f_data,z_data[0],ignoreslope=True)
    
    z_data_sim=[]
    parameters=[]
    residual_amp=[]
    residual_phase=[]

    for z_data0 in z_data:
    
        z_new=rtx.do_normalization(f_data,z_data0,delay,amp_norm,alpha,A2,frcal)
        p=rtx.circlefit(f_data,z_new,calc_errors=False)
        parameters.append(p)    
    
        z_data_sim_temp=[]
        residual_amp_temp=[]
        residual_phase_temp=[]
    
        for f,z in zip(f_data,z_data0):
            z_temp=np.array(to.S21(f,fr=p["fr"],Qr=p["Qr"],Qc=p["absQc"],
                                   phi=p["phi0"],a=amp_norm,alpha=alpha,delay=delay))
                                   
            z_data_sim_temp.append(z_temp)
            residual_amp_temp.append(np.absolute(z)-np.absolute(z_temp))
            residual_phase_temp.append(np.angle(z)-np.angle(z_temp))
            
            i_progress+=1
            progress_bar.setValue(i_progress)
        
        QApplication.processEvents()
    
        z_data_sim.append(z_data_sim_temp)
        residual_amp.append(residual_amp_temp)
        residual_phase.append(residual_phase_temp)
    
    results={"z_sim":np.array(z_data_sim),
    "res_amp":np.array(residual_amp),
    "res_phase":np.array(residual_phase),"parameters":parameters,
    "amp_norm":amp_norm,"alpha":alpha,
    "delay":delay}
    
    return results
    
def skewed_lorentzian_fit(f_data,z_data,progress_bar,var_col=0,f_col=1,z_col=2):
    
    progress_bar.setMaximum(len(f_data)*len(z_data))
    i_progress=0
    
    amp_sim=[]   
    parameters=[]
    residual_amp=[]
    
    for z0 in z_data:
    
        parameters_temp=to.fit_skewed_lorentzian_2(f_data,z0)
        A1,A2,A3,A4,fr2,Qr2=parameters_temp
        parameters.append(parameters_temp)
    
        amp_sim_temp=[]
        residual_amp_temp=[]
        
        for f,z in zip(f_data,z0):
            x=to.skewed_lorentz_function(f,A1,A2,A3,A4,fr2,Qr2)
            amp_sim_temp.append(x)
            residual_amp_temp.append(np.absolute(z)-x)
            
            i_progress+=1
            progress_bar.setValue(i_progress)
        
        amp_sim.append(amp_sim_temp)
        residual_amp.append(residual_amp_temp)
        
        QApplication.processEvents()
        
    results={"z_sim":np.array(amp_sim),
    "res_amp":np.array(residual_amp),"parameters":parameters}
        
    return results
    
    

