import numpy as np
import copy
import matplotlib.pyplot as plt
from scipy import signal
from scipy.optimize import curve_fit

from qkit.analysis.semiconductor.basic_functionality import PlotterSemiconInit, convert_conductance, map_array_to_index
from qkit.analysis.semiconductor.basic_functionality import  convert_secs, create_saving_path, make_len_eq

class AnalyzerTimetraceSpecralNoiseDensity:
    number_of_traces = 1
    
    def analyze(self, sampling_freq, data, nodes):
        """Analyzes a sigle timetrace using consecutive Fourier transforms.
        """
        freqs, times, spectrogram = signal.spectrogram(data[nodes[0]], fs = sampling_freq, nperseg = len(data[nodes[0]]))   
        spectrogram = np.real(spectrogram.flatten().astype(complex)) # yes I know... tell me why data type is object and complex

        return {"freq" : freqs[1:], "times" : times[1:], "spectrogram": spectrogram[1:]} # freqs[0]=0 ; The 0Hz value is cut off:
    

    def analyze_welch(self, sampling_freq, data, nodes, segment_length):
        """Analyzes a sigle timetrace using Welch's method.
        Welch’s method [1] computes an estimate of the power spectral density by dividing 
        the data into overlapping segments, computing a modified periodogram for each segment
        and averaging the periodograms.
        segment_length is length of a segment.
        """
        freqs, Pxx = signal.welch(data[nodes[0]], fs = sampling_freq, nperseg = segment_length)
        spectrogram = np.real(Pxx.flatten().astype(complex)) # yes I know... tell me why data type is object and complex

        return {"freq" : freqs[1:], "spectrogram": spectrogram[1:]} # freqs[0]=0 ; The 0Hz value is cut off:


    def fit(self, spectrum, guess=None, max_iter=10000000):
        """Fits f(x)= a*x^b to data AROUND 1Hz. So the spectrum must include 1Hz...
        Return is the parameters of the fit.
        guess is an array or list of starting values for a, b of f(x)=a*x**b.  
        """
        #make data slice around 1Hz
        index_begin = map_array_to_index(spectrum["freq"], 1e-1)
        index_end = map_array_to_index(spectrum["freq"], 1e1)
        freqs = spectrum["freq"][index_begin : index_end]
        spec = spectrum["spectrogram"][index_begin : index_end]

        def func(x, a, b):
            return a * np.power(x, b)
        popt, cov = curve_fit(func, freqs, np.sqrt(spec), p0=guess, maxfev=max_iter)
    
        return {"popt" : popt, "cov" : cov, "SND1Hz" : func(1, *popt)}
