import numpy as np

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


