import numpy as np
from interfaces import AnalyzerInterface
from scipy import signal
from scipy.optimize import curve_fit

class Analyzer(AnalyzerInterface):
    def __init__(self) -> None:
        self.data_raw = {}
        self.sampling_freq = 10.0e3
        self.segment_length = 10.0e3    
    
    def load_data(self, data):
        self.data_raw = data

    def validate_input(self):
        keys = self.data_raw.keys()
        missing_entries = ""
        
        if "x" not in keys:
            missing_entries += "x"
        if "y" not in keys:
            missing_entries += "\ny"

        if missing_entries:
            raise TypeError(f"{__name__}: Invalid input data. The following nodes are missing: {missing_entries}")
    
    #TODO: Write Something to rotate the phase before analysis

    def analyze(self):
        """Analyzes a sigle timetrace using Welch's method.
        Welch’s method [1] computes an estimate of the power spectral density by dividing
        the data into overlapping segments, computing a modified periodogram for each segment
        and averaging the periodograms.
        segment_length is length of a segment.
        """
        freqs, Pxx = signal.welch(self.data_raw["x"], fs = self.sampling_freq, nperseg = self.segment_length)
        spectrogram = np.real(Pxx.flatten().astype(complex)) #yes I know... tell me why data type is object and complex

        return {"f": freqs[1:], "NSD": spectrogram[1:]} #freqs[0]=0 ; The 0Hz value is cut off.

if __name__ == "__main__":
    A = Analyzer()
    data = {"x": 1,
    "y": 2}
    A.load_data(data)
    A.validate_input()