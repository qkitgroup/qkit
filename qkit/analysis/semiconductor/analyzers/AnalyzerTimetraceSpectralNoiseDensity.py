import numpy as np
from scipy import signal
from scipy.optimize import curve_fit

from qkit.analysis.semiconductor.main.find_index_of_value import map_array_to_index

def func_linear(x, a, b):
    return np.multiply(a, x) + b

class AnalyzerTimetraceSpectralNoiseDensity:
   
    def __init__(self):
        self.guess = [-1, 1]
        self.max_iter = 10000000
        self.segment_length = 5e5
        self.fit_func = func_linear

    def analyze(self, sampling_freq, data, nodes):
        """Analyzes a sigle timetrace using consecutive Fourier transforms.
        """
        freqs, times, spectrogram = signal.spectrogram(data[nodes[0]], fs = sampling_freq, nperseg = len(data[nodes[0]]))   
        spectrogram = np.real(spectrogram.flatten().astype(complex)) # yes I know... tell me why data type is object and complex

        return {"freq" : freqs[1:], "times" : times[1:], "spectrogram": spectrogram[1:]} # freqs[0]=0 ; The 0Hz value is cut off:
    

    def analyze_welch(self, sampling_freq, data, nodes):
        """Analyzes a sigle timetrace using Welch's method.
        Welch’s method [1] computes an estimate of the power spectral density by dividing 
        the data into overlapping segments, computing a modified periodogram for each segment
        and averaging the periodograms.
        segment_length is length of a segment.
        """
        freqs, Pxx = signal.welch(data[nodes[0]], fs = sampling_freq, nperseg = self.segment_length)
        spectrogram = np.real(Pxx.flatten().astype(complex)) # yes I know... tell me why data type is object and complex

        return {"freq" : freqs[1:], "spectrogram": spectrogram[1:]} # freqs[0]=0 ; The 0Hz value is cut off:


    def fit(self, spectrum):
        """Fits f(x)= a*x + b to log10(data) AROUND 1Hz. So the spectrum must include 1Hz...
        Return is the parameters of the fit.
        guess is an array or list of starting values for a, b.  
        """
        #make data slice around 1Hz
        index_begin = map_array_to_index(spectrum["freq"], 1e-1)
        index_end = map_array_to_index(spectrum["freq"], 1e1)
        freqs = spectrum["freq"][index_begin : index_end]
        spec = spectrum["spectrogram"][index_begin : index_end]
        self._data_f = freqs

        #fitting of log10(spec)
        popt_raw, cov = curve_fit(self.fit_func, np.log10(freqs), np.log10(spec), p0=self.guess, maxfev=self.max_iter)
        popt = np.array([popt_raw[0], 10**popt_raw[1]])
        return {"popt" : popt, "cov" : cov} # freqs[0]=0 ; The 0Hz value is cut off