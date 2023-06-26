import qkit
#qkit.cfg["run_id"] = "Magpie_2020_05_19"
#qkit.cfg["user"] = "Martin"
qkit.start()

import time
import math
import numpy as np
import matplotlib.pyplot as plt
from ipywidgets import interact, interactive, fixed, interact_manual

from scipy.signal import savgol_filter
from scipy.optimize import curve_fit
from scipy import fftpack

from scipy.optimize import curve_fit

from qkit.measure.timedomain.quantum_machine import qm_qubit_config as qc
from qkit.measure.timedomain.quantum_machine import basic_qubit_experiments as bqe
from qkit.measure.timedomain.quantum_machine import quantum_jump_monitoring as qjm
from qkit.measure.timedomain.quantum_machine import pulses
from qkit.analysis import iq_cloud_analysis

qm_config = qc.QMQubitConfig()
qm_config.wait_sig = 156
qm_config.smearing_sig = 48
qm_config.wait_ref = 62
qm_config.smearing_ref = 0

qm_config.readout_pulse_len = 128
qm_config.set_readout_wf(pulses.const, (0.49,))
qm_config.set_pi_pulse_wf(pulses.gauss, (0.3630, 0.0, 10.0))

qm = bqe.BasicQubitExperiments(qm_config)
qmjm = qjm.QuantumJumpMonitoring(qm_config)

iqcloud = iq_cloud_analysis.IQCloudAnalysis()
iqcloud.set_up_gaussian_mixture_model(2)

##### launch experiment ####

ref_pos = np.array([[0.63315114, 0.75654685], [-0.49696001, 0.78736931]])
var = np.array([0.04187039, 0.04051063])
dist_avg = 0.14078334743527843

ts = time.time()

i = 0

qmjm.dirname = "t_rep_2p0us_sigma_1p0_run_{}".format(i)
qmjm.quantum_jump_hist_stab_avg(25, 10, ref_pos * dist_avg, (np.sqrt(var) * dist_avg) * np.array([1.0, 1.0]),
                            t_stab=242, t_measure=230, avg=10,
                            stab_state=True, start_state=False, plot=True, save=False)

#t_stab = 242, t_measure = 480,
#242, t_measure = 230,

print("Ready")



