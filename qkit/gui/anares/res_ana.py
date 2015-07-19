import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *

import numpy as np
sys.path.append('../../analysis/circle_fit')
import resonator_tools as rt
import resonator_tools_xtras as rtx
import tools as to

def notch(f_data,z_data,progress_bar,var_col=0,f_col=1,z_col=2):
    #progress bar
    progress_bar.setMaximum(5)
    i_progress=0
    progress_bar.setValue(i_progress)
    QApplication.processEvents()
    #calibration
    delay,amp_norm,alpha,fr,Qr,A2,frcal=rtx.do_calibration(f_data,z_data[0],ignoreslope=True)
    i_progress+=1
    progress_bar.setValue(i_progress)
    QApplication.processEvents()
    #normalization
    z_norm = rtx.do_normalization(f_data,z_data,delay,amp_norm,alpha,A2,frcal)
    i_progress+=1
    progress_bar.setValue(i_progress)
    QApplication.processEvents()
    #circlefit
    parameters = map(lambda x: rtx.circlefit(f_data,z_norm[x],calc_errors=True), xrange(len(z_norm)))
    i_progress+=1
    progress_bar.setValue(i_progress)
    QApplication.processEvents()
    #simulation
    z_data_sim = np.array(map(lambda p: to.S21(f_data,fr=p["fr"],Qr=p["Qr"],Qc=p["absQc"],
                                   phi=p["phi0"],a=amp_norm,alpha=alpha,delay=delay), parameters))
    #residual values
    residual_amp = np.absolute(z_norm) - np.absolute(z_data_sim)
    residual_phase = np.angle(z_norm) - np.angle(z_data_sim)
    i_progress+=1
    progress_bar.setValue(i_progress)
    QApplication.processEvents()

    return {"z_sim":z_data_sim,
    "res_amp":residual_amp,
    "res_phase":residual_phase,"parameters":parameters,
    "amp_norm":amp_norm,"alpha":alpha,
    "delay":delay}

def skewed_lorentzian_fit(f_data,z_data,progress_bar,var_col=0,f_col=1,z_col=2):

    progress_bar.setMaximum(4)
    i_progress=1
    progress_bar.setValue(i_progress)
    QApplication.processEvents()

    parameters = map(lambda x: to.fit_skewed_lorentzian_2(f_data,z_data[x]),xrange(len(z_data)))
    i_progress+=1
    progress_bar.setValue(i_progress)
    QApplication.processEvents()

    amp_sim = np.array( map(lambda p: to.skewed_lorentz_function(f_data,*p),parameters))
    i_progress+=1
    progress_bar.setValue(i_progress)
    QApplication.processEvents()

    residual_amp = np.absolute(z_data) - np.absolute(amp_sim)
    i_progress+=1
    progress_bar.setValue(i_progress)
    QApplication.processEvents()

    results={"z_sim":amp_sim,
    "res_amp":residual_amp,"parameters":parameters}

    return results



