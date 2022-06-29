import numpy as np
class Analyzer:
   
    def __init__(self, trace, time_axis):
        self.trace = trace
        self.time_axis = time_axis
        self.bin_count = 100
        self.bin_range = None
        self.big_jump_minimum_height = 2e-3
       
    def analyze(self):
        """Analyzes a timetrace and counts jumps.
        """
        difference = np.diff(self.trace)
        (hist, bin_edges) = np.histogram(difference, bins=self.bin_count, range=self.bin_range)
        
        jumps = difference[abs(difference) >= self.big_jump_minimum_height]
        jumps_idx = np.flatnonzero(abs(difference) >= self.big_jump_minimum_height) + 1
        jumps_time = self.time_axis[jumps_idx]
        jumps_t_difference = np.diff(jumps_time)
        print(jumps_idx)

        return {"jump_height" : bin_edges, "jumps_per_bin" : hist}, \
        {"number_of_big_jumps" : len(jumps), "height_of_big_jumps" : jumps, 
        "time_between_big_jumps" : jumps_t_difference, "time_of_big_jumps" : jumps_time}

   
    def fit(self):
        pass