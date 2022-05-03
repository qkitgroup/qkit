import numpy as np

from qkit.analysis.semiconductor.main.find_index_of_value import map_array_to_index
from qkit.analysis.semiconductor.main.time_conversion import convert_secs_2D

class AnalyzerTimetraceJumps:
   
    def __init__(self):
        self.bin_count = 10
        self.bin_range = None


    def analyze_difference(self, data, nodes:list):
        """Analyzes a timetrace and counts jumps.
        """
        trace = data[nodes[0]]
        difference = np.diff(trace)
        hist = np.histogram(difference, bins=self.bin_count, range=self.bin_range)
        time = convert_secs_2D(data[nodes[1]])[-1] # duration of timetrace in s

        return {"jump_height" : hist[1], "jumps_per_bin" : hist[0], "time_analyzed" : time}

   
