import numpy as np
import matplotlib.pyplot as plt

from qkit.analysis.semiconductor.main.pre_formatted_figures import SemiFigure
from qkit.analysis.semiconductor.main.saving import create_saving_path


class PlotterDifferenceTimetraceSpectralNoiseDensity(SemiFigure):
    """Plots the spectral noise density difference of two SNDs using the equivalent gate voltage found in fit_params['fit_coef'][0] if provided.
    """
   
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fit_params_plunger = None,
        self.fit_vals = None
        self.savename = None
        self.xlim = None
        self.ylim = None
        self.dotsize = 0.5
        self.fiftyHz = False


    def plot(self, settings:dict, data_calib:dict, data_no_calib:dict):
        """Plots the sqrt of a spectrum (data["spectrogram"]). Respecting scaling with the slope of a plunger gate sweep (fit_params_plunger). 
            data: spectral data in dictionary with keys "freq", "times", "spectorgram"
            fit_params_plunger_in: dict including key "fit_coef" 
            fit_vals: dict with keys "popt" and "SND1Hz" that is used to plot a linear fit to the data
            fifyHz: bool that overlays the first 30 50Hz multiples
        """
        self.ax.set_title("Spectral Noise Density")
        self.ax.set_xscale("log")
        self.ax.set_yscale("log")
        self.ax.set_xlabel("Frequency (Hz)")
        self.ax.set_ylabel("Spectral Density ($V/\sqrt{\mathrm{Hz}}$)")
        if self.xlim != None:
            self.ax.set_xlim(self.xlim)
        if self.ylim != None:
            self.ax.set_ylim(self.ylim)
        if self.fit_params_plunger is None: # for reference measurements without plunger gate sweeps the slope is 1
            fit_params_plunger = {}
            fit_params_plunger["fit_coef"] = [1]
        else:
            fit_params_plunger = self.fit_params_plunger
        if self.savename == None:
            self.savename = f"SND_without_background_slope_{fit_params_plunger['fit_coef'][0]:.3f}"

        if self.fiftyHz == True: # plotting 50Hz multiples
            self.savename += "_50Hz"
            freqs = []
            signals = []
            for f in [i*50 for i in range(13)]:
                freqs.extend([f]*1000 )
                signals.extend(np.logspace(-8, -1, 1000))
            self.ax.plot(freqs, signals, "yo", markersize=self.dotsize)

        if np.array_equal(data_calib["freq"], data_no_calib["freq"]):
            self.spectrum = (data_calib["spectrogram"]  - data_no_calib["spectrogram"] ) / np.abs(fit_params_plunger['fit_coef'][0])
            
            self.ax.plot(data_calib["freq"], np.sqrt(self.spectrum), "ok", markersize=self.dotsize)

            plt.grid()
            plt.savefig(create_saving_path(settings, self.savename, self.save_as), dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
            plt.show()
        else:
            print("Error: Frequency arrays of both data inputs not equal!")
        self.close_delete()
