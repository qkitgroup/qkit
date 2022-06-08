import numpy as np
import matplotlib.pyplot as plt

from qkit.analysis.semiconductor.main.pre_formatted_figures import SemiFigure
from qkit.analysis.semiconductor.main.saving import create_saving_path
from qkit.analysis.semiconductor.main.find_index_of_value import map_array_to_index


class PlotterTimetraceSpectralNoiseDensity(SemiFigure):
    """Plots the spectral noise density using the equivalent gate voltage found in fit_params['fit_coef'][0] if provided.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fit_params_plunger = None
        self.fit_vals = None
        self.savename = None
        self.xlim = None
        self.ylim = None
        self.dotsize = 0.5
        self.fiftyHz = False


    def plot(self, settings:dict, data:dict):
        """Plots the sqrt of a spectrum (data["spectrogram"]). Respecting scaling with the slope of a plunger gate sweep (fit_params_plunger). 
            data: spectral data in dictionary with keys "freq", "times", "spectorgram"
            fit_params_plunger_in: dict including key "fit_coef" 
            fit_vals: dict with keys "popt" and "SND1Hz" that is used to plot a linear fit to the data
            fifyHz: bool that overlays the first 30 50Hz multiples
        """
        self.ax.set_title("Power Spectral Noise Density")
        self.ax.set_xscale("log")
        self.ax.set_yscale("log")
        self.ax.set_xlabel("Frequency (Hz)")
        self.ax.set_ylabel("PSD (V²/Hz)")
        if self.xlim != None:
            self.ax.set_xlim(self.xlim)
        if self.ylim != None:
            self.ax.set_ylim(self.ylim)
        if self.fit_params_plunger is None: # for reference measurements without plunger gate sweeps the slope is 1
            fit_params_plunger = {}
            fit_params_plunger["fit_coef"] = [1]
        else:
            fit_params_plunger = self.fit_params_plunger
        
        plunger_calib = fit_params_plunger['fit_coef'][0]

        if self.savename == None:
            self.savename = f"PSD_slope_{plunger_calib:.3f}"

        if self.fiftyHz == True: # plotting 50Hz multiples
            self.savename += "_50Hz"
            freqs = []
            signals = []
            for f in [i*50 for i in range(6)]:
                freqs.extend([f]*1000 )
                signals.extend(np.logspace(-11, -4, 1000))
            self.ax.plot(freqs, signals, "yo", markersize=self.dotsize)
        
    
        if self.fit_vals is not None:
            def func(x, a, b):
                return a * np.power(x, b)
            index_begin = map_array_to_index(data["freq"], 1e-1)
            index_end = map_array_to_index(data["freq"], 1e1)
            freqs = data["freq"][index_begin : index_end]
            SND_1Hz = func([1], *self.fit_vals["popt"]) / (plunger_calib)**2
            exponent_1Hz = self.fit_vals["popt"][1] 
            text = f"PSD(1Hz) : {1e9 * SND_1Hz[0]:.1f} * e-9 V²/Hz"
            text = text + f"\nexponent(1Hz) : {exponent_1Hz:.3f} "
            fit_spectrum = func(freqs, *self.fit_vals["popt"]) / (plunger_calib)**2
            self.ax.plot(freqs, fit_spectrum, label=text)
            self.ax.legend(loc="lower left")

        self.ax.plot(data["freq"], data["spectrogram"] / (plunger_calib)**2, "ok", markersize=self.dotsize)

        plt.grid()
        plt.savefig(create_saving_path(settings, self.savename, self.save_as), dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show()
        self.close_delete()
