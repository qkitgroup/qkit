import numpy as np
from scipy.optimize import curve_fit
from qkit.analysis.semiconductor.main.fit_functions import gauss_function

class Analyzer:
    def __init__(self, trace, time_axis):
        self.trace = trace
        self.time_axis = time_axis
        self.bin_count = 50
        self.bin_range = None
        self.big_jump_minimum_height = 2e-3
        self.hist = np.array([])
        self.guess = None
       
    def analyze(self):
        """Analyzes a timetrace and counts jumps.
        """
        difference = np.diff(self.trace)
        (self.hist, self.bin_edges) = np.histogram(difference, bins=self.bin_count, range=self.bin_range)
        
        jumps = difference[abs(difference) >= self.big_jump_minimum_height]
        jumps_idx = np.flatnonzero(abs(difference) >= self.big_jump_minimum_height) + 1
        jumps_time = self.time_axis[jumps_idx]
        jumps_t_difference = np.diff(jumps_time)

        return {"jump_height" : self.bin_edges[:-1], "jumps_per_bin" : self.hist}, \
        {"number_of_big_jumps" : len(jumps), "height_of_big_jumps" : jumps, 
        "time_between_big_jumps" : jumps_t_difference, "time_of_big_jumps" : jumps_time}
   
    def fit(self):
        assert self.hist.any(), f"{__name__}: Analyze trace first. No histogram available."
        popt, _ = curve_fit(gauss_function, self.bin_edges[:-1], self.hist, self.guess)

        return popt

