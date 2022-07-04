import numpy as np
import matplotlib.pyplot as plt

from qkit.analysis.semiconductor.main.pre_formatted_figures import SemiFigure
from qkit.analysis.semiconductor.main.saving import create_saving_path
from qkit.analysis.semiconductor.main.find_index_of_value import map_array_to_index

def func_power(x, a, b):
    return b * x ** a
def func_power2(x, *params):
    if len(params) == 2:
        return params[1] * x ** params[0]
    else:
        part1 = params[1] * x[x <= params[3]] ** params[0]
        part2 = params[1]/(params[3] ** (params[2]-params[0])) * x[x > params[3]] ** params[2]
        return np.concatenate((part1, part2))

class PlotterTimetraceSpectralNoiseDensity(SemiFigure):
    """Plots the spectral noise density using the equivalent gate voltage found in fit_params['fit_coef'][0] if provided.
    """
    
    def __init__(self, saving_path, spectrogram, fit = {"popt": [], "fit_range" : []}, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fit_params_plunger = None
        self.fit_vals = None
        self.savename = ""
        self.xlim = None
        self.ylim = None
        self.dotsize = 0.5
        self.fiftyHz = False
        self.alpha = 1.0 # Transparency of plotted line

        
        self.spectrogram = spectrogram
        self.fit = fit
        self.saving_path = saving_path

        self.ax.set_title("Power Spectral Noise Density")
        self.ax.set_xscale("log")
        self.ax.set_yscale("log")
        self.ax.set_xlabel("Frequency (Hz)")
        self.ax.set_ylabel("PSD (V²/Hz)")

    @property
    def spectrogram(self):
        return self._spectrogram
    @spectrogram.setter
    def spectrogram(self, new_spec):
        if len(new_spec) != 2:
            raise TypeError(f"{__name__}: Invalid spectrogram data. Must be of form [freqs, spectrum].")
        if len(new_spec[0]) != len(new_spec[1]):
            raise TypeError(f"{__name__}: Invalid spectrogram data. Freqs and spectrum have to be arrays of same length.")
        self._spectrogram = new_spec

    @property
    def fit(self):
        return self._fit
    @fit.setter
    def fit(self, new_pars):
        if not isinstance(new_pars, dict):
            raise TypeError(f"{__name__}: Invalid fit data. Must be a dictionary containing keys 'popt' and 'fit_range'.")
        if not "popt" in new_pars.keys() or not "fit_range" in new_pars.keys():
            raise TypeError(f"{__name__}: Invalid fit data. Must be a dictionary containing keys 'popt' and 'fit_range'.")
        self._fit = new_pars

    def _plot_50Hz_multiples(self):
        self.savename += "_50Hz"
        freqs = []
        signals = []
        for f in [i*50 for i in range(6)]:
            freqs.extend([f]*1000 )
            signals.extend(np.logspace(-11, -4, 1000))
        self.ax.plot(freqs, signals, "yo", markersize=self.dotsize)

    def _plot_fit(self):
        index_begin = map_array_to_index(self.spectrogram[0], self.fit["fit_range"][0])
        index_end = map_array_to_index(self.spectrogram[0], self.fit["fit_range"][1])
        freqs = self.spectrogram[0][index_begin : index_end]

        SND_1Hz = float(func_power2(np.array([1]), *self.fit["popt"]) / (self.plunger_calib)**2)
        exponent_1Hz = self.fit["popt"][-2]
        text = f"PSD(1Hz) : {1e9 * SND_1Hz:.1f} * e-9 V²/Hz"
        text = text + f"\nexponent(1Hz) : {exponent_1Hz:.3f} "
        fit_spectrum = func_power2(freqs, *self.fit["popt"]) / (self.plunger_calib)**2
        self.ax.plot(freqs, fit_spectrum, label=text, alpha=self.alpha)
        self.ax.legend(loc="lower left")

    def plot(self):
        """Plots the sqrt of a spectrum (data["spectrogram"]). Respecting scaling with the slope of a plunger gate sweep (fit_params_plunger). 
            data: spectral data in dictionary with keys "freq", "times", "spectorgram"
            fit_params_plunger_in: dict including key "fit_coef" 
            fit_vals: dict with keys "popt" and "SND1Hz" that is used to plot a linear fit to the data
            fifyHz: bool that overlays the first 30 50Hz multiples.
        """        
        if self.xlim:
            self.ax.set_xlim(self.xlim)
        if self.ylim:
            self.ax.set_ylim(self.ylim)
        if not self.fit_params_plunger: # for reference measurements without plunger gate sweeps the slope is 1
            fit_params_plunger = {"fit_coef" : [1]}
        else:
            fit_params_plunger = self.fit_params_plunger
        
        self.plunger_calib = fit_params_plunger['fit_coef'][0]

        if not self.savename:
            self.savename = f"PSD_slope_{self.plunger_calib:.3f}"
        if self.fiftyHz: # plotting 50Hz multiples
            self._plot_50Hz_multiples()
        
        self.ax.plot(self.spectrogram[0], self.spectrogram[1] / (self.plunger_calib)**2, "ok", markersize=self.dotsize)

        if self.fit["popt"].any() and self.fit["fit_range"]:
            '''self.fit_vals are the parameters of f(x)=a*x+b to the data_x=log10(freqencies), data_y=log10(PSD)
            so plotting of f_power(x)=b'*x**a' leads to 
            b' = 10^b
            a'= a 
            '''
            self._plot_fit()          

        plt.grid()
        plt.savefig(self.saving_path + ".png", dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show()
        self.close_delete()
