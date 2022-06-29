import numpy as np
import numbers
from scipy import signal
from scipy.optimize import curve_fit

from qkit.analysis.semiconductor.main.find_index_of_value import map_array_to_index

def func_linear(x, a, b):
    return np.multiply(a, x) + b

class AnalyzerTimetraceSpectralNoiseDensity:
   
    def __init__(self, trace_to_analyze, sampling_freq, fit_func = func_linear):         

        self.guess = [1, -1]
        self.max_iter = 10000000
        self.welch_segment_length = 5e5
        self.sampling_freq = sampling_freq
        self.trace_to_analyze = trace_to_analyze

        self.fit_func = fit_func
        self._fit_interval = []
    
    @property
    def trace_to_analyze(self):
        return self._trace_to_analyze
    @trace_to_analyze.setter
    def trace_to_analyze(self, new_trace):
        if not isinstance(new_trace, np.ndarray):
            raise TypeError(f"{__name__}: Invalid data trace. Must be a 1D numpy array.")
        if new_trace.ndim != 1:
            raise ValueError(f"{__name__}: Invalid data trace. Must be a 1D numpy array.")
        self._trace_to_analyze = new_trace

    @property
    def fit_interval(self):
        return self._fit_interval    
    @fit_interval.setter
    def fit_interval(self, new_interval):
        if not isinstance(new_interval, list):
            raise TypeError("Fit interval must be a list")
        if len(new_interval) != 2:
            raise ValueError("Invalid input for fit intervall. Must be a list of length 2.")
        for element in new_interval:
            if not isinstance(element, numbers.Number):
                raise TypeError("Fit interval must be two numbers in ascending order. Duh.")
        if new_interval[0] > new_interval[1]:
            raise ValueError("Fit interval must be two numbers in ascending order. Duh.")
        self._fit_interval = new_interval

    def analyze(self):
        """Analyzes a single timetrace using consecutive Fourier transforms.
        """
        
        freqs, times, spectrogram = signal.spectrogram(self.trace_to_analyze, fs = self.sampling_freq, nperseg = len(self.trace_to_analyze))   
        spectrogram = np.real(spectrogram.flatten().astype(complex)) # yes I know... tell me why data type is object and complex
        self.freqs = freqs[1:]
        self.spectrogram = spectrogram[1:]
        self.times = times[1:]
        
        return {"freq" : self.freqs, "times" : self.times, "spectrogram": self.spectrogram} # freqs[0]=0 ; The 0Hz value is cut off:
    
    def analyze_welch(self):
        """Analyzes a sigle timetrace using Welch's method.
        Welch’s method [1] computes an estimate of the power spectral density by dividing 
        the data into overlapping segments, computing a modified periodogram for each segment
        and averaging the periodograms.
        segment_length is length of a segment.
        """
        freqs, Pxx = signal.welch(self.trace_to_analyze, fs = self.sampling_freq, nperseg = self.welch_segment_length)
        spectrogram = np.real(Pxx.flatten().astype(complex)) # yes I know... tell me why data type is object and complex

        self.freqs = freqs[1:]
        self.spectrogram = spectrogram[1:]
        return {"freq" : self.freqs, "spectrogram": self.spectrogram} # freqs[0]=0 ; The 0Hz value is cut off:

    def fit(self, spectrum = None):
        """Fits f(x)= a*x + b to log10(data) AROUND 1Hz. So the spectrum must include 1Hz...
        Return is the parameters of the fit.
        guess is an array or list of starting values for a, b.  
        """
        assert self.freqs.any(), "No spectrum data, yet. Analyze spectrum first."
        
        freqs = self.freqs
        spectrogram = self.spectrogram

        #slice data around the fit interval
        if self._fit_interval:
            index_begin = map_array_to_index(self.freqs, self.fit_interval[0])
            index_end = map_array_to_index(self.freqs, self.fit_interval[1])
            print(index_begin, index_end)
            freqs = self.freqs[index_begin : index_end]
            spectrogram = self.spectrogram[index_begin : index_end]

        #fitting of log10(spec)
        popt_raw, cov = curve_fit(self.fit_func, np.log10(freqs), np.log10(spectrogram), p0=self.guess, maxfev=self.max_iter)
        popt = np.array([popt_raw[0], 10**popt_raw[1]])
        return {"popt" : popt, "cov" : cov, "fit_range" : [min(freqs), max(freqs)]} # freqs[0]=0 ; The 0Hz value is cut off