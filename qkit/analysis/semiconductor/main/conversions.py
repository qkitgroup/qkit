import numpy as np
import h5py
import pathlib
import math
import gc 
import copy
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

def convert_conductance(amplitudes, settings, multiplier):
    """Converts Lock-in amplitude in conductance in Siemens. 
        measurement_amp: amplitude of lock-in signal
        voltage_divider: used before the input of the lock-in
        IVgain: of IV converter
        in_line_R: sum of resistances of the line without QD
        multiplier: multiplies values by factor of e.g. 1e6 to get micro Siemens
    """
    return multiplier / (settings["meas_params"]["measurement_amp"] * settings["meas_params"]["IVgain"] / (settings["meas_params"]["voltage_divider"] 
                         * amplitudes * np.sqrt(2)) - settings["meas_params"]["in_line_R"])

    
def convert_secs(timestamps, f=1.8*1e9):
    """Sets the starting point to 0 and adjusts with the clock speed of 1.8 GHz. Not really accurate.
    Timestamps need to be numpy arrays.
    """
    time_stamps = timestamps - timestamps[0]
    time_stamps = time_stamps / f 
    
    return time_stamps
    

def convert_secs_2D(timestamps, f=1.8*1e9):
    """Sets the starting point to 0 and adjusts with the clock speed of 1.8 GHz. Not really accurate.
    Converts 2D timestamps in 1D arrays with each point in 1D being the beginning of a 2D array. 
    """
    time_stamps = timestamps[:,0] - timestamps[0,0]
    time_stamps = time_stamps / f 
    
    return time_stamps