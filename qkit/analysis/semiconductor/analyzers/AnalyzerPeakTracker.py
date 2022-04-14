import numpy as np
from qkit.analysis.semiconductor.interfaces import AnalyzerInterface
from scipy import signal
from scipy.optimize import curve_fit

class Analyzer(AnalyzerInterface):
    def __init__(self) -> None:
        self.data = {}
        self.sampling_freq = 10.0e3
        self.segment_length = 10.0e3 

        self.node_to_analyze = "demod0&4.r0"
        self.min_peak_height = 0.01 #in V
        self.min_peak_width = 10 #in samples
        self.trace_no = 0
    
    def load_data(self, data_raw):
        self.data = data_raw

    def validate_input(self):
        for file in self.data.values():
            keys = file.keys()
            missing_entries = ""
            
            if "demod0&4.r0" not in keys:
                missing_entries += "demod0&4.r0"
            if "demod0&4.r4" not in keys:
                missing_entries += "\ndemod0&4.r4"
            if "demod0&4.x0" not in keys:
                missing_entries += "\ndemod0&4.x0"
            if "demod0&4.x4" not in keys:
                missing_entries += "\ndemod0&4.x4"
            if "demod0&4.y0" not in keys:
                missing_entries += "\ndemod0&4.y0"
            if "demod0&4.y4" not in keys:
                missing_entries += "\ndemod0&4.y4"
            if "demod0&4.timestamp0" not in keys:
                missing_entries += "\ndemod0&4.timestamp0"
            if "demod0&4.timestamp4" not in keys:
                missing_entries += "\ndemod0&4.timestamp4"
            if "gates_6_16" not in keys:
                missing_entries += "\ngates_6_16"
            if "number" not in keys:
                missing_entries += "\nnumber"

            if missing_entries:
                raise TypeError(f"{__name__}: Invalid input data. The following nodes are missing: {missing_entries}")
    
    #TODO: Write Something to rotate the phase before analysis

    def analyze(self):
        for file in self.data.values():
            matrix = file[self.node_to_analyze]
            peak_positions = []
            v_offset = file["gates_6_16"][0]
            v_step = file["gates_6_16"][1] - v_offset
            for trace in matrix:
                peak_pos,_ = signal.find_peaks(trace, height = self.min_peak_height, width = self.min_peak_width)
                peak_positions.append(peak_pos * v_step + v_offset)
            file["peak_pos"] = np.array(peak_positions)
            #print(np.shape(file["peak_pos"]))
            #print(file["peak_pos"])
        return self.data

if __name__ == "__main__":
    A = Analyzer()
    data = {"x": 1, "y": 2}
    A.load_data(data)
    A.validate_input()