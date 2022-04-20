import numpy as np
import copy
import matplotlib.pyplot as plt
from scipy import signal
from scipy.optimize import curve_fit

from qkit.analysis.semiconductor.basic_functionality import PlotterSemiconInit, convert_conductance, map_array_to_index
from qkit.analysis.semiconductor.basic_functionality import  convert_secs, create_saving_path, make_len_eq


class PlotterDifferenceTimetraceSpectralNoiseDensity(PlotterSemiconInit):
    """Plots the spectral noise density difference of two SNDs using the equivalent gate voltage found in fit_params['fit_coef'][0] if provided.
    """
    number_of_traces = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def plot(self, settings:dict, data_calib:dict, data_no_calib:dict, fit_params_plunger_in=None, fit_vals=None, savename=None, xlim:list=None, ylim:list=None, dotsize=0.5, fiftyHz:bool=False, log=True):
        """Plots the sqrt of a spectrum (data["spectrogram"]). Respecting scaling with the slope of a plunger gate sweep (fit_params_plunger). 
            data: spectral data in dictionary with keys "freq", "times", "spectorgram"
            fit_params_plunger_in: dict including key "fit_coef" 
            fit_vals: dict with keys "popt" and "SND1Hz" that is used to plot a linear fit to the data
            fifyHz: bool that overlays the first 30 50Hz multiples
        """
        self.ax.set_title("Spectral Noise Density")
        if log == True:
            self.ax.set_xscale("log")
            self.ax.set_yscale("log")
        self.ax.set_xlabel("Frequency (Hz)")
        self.ax.set_ylabel("Spectral Density ($V/\sqrt{\mathrm{Hz}}$)")
        if xlim != None:
            self.ax.set_xlim(xlim)
        if ylim != None:
            self.ax.set_ylim(ylim)
        if fit_params_plunger_in is None: # for reference measurements without plunger gate sweeps the slope is 1
            fit_params_plunger = {}
            fit_params_plunger["fit_coef"] = [1]
        else:
            fit_params_plunger = fit_params_plunger_in
        if savename == None:
            savename = f"SND_without_background_slope_{fit_params_plunger['fit_coef'][0]:.3f}"

        if fiftyHz == True: # plotting 50Hz multiples
            savename += "_50Hz"
            freqs = []
            signals = []
            for f in [i*50 for i in range(13)]:
                freqs.extend([f]*1000 )
                signals.extend(np.logspace(-8, -1, 1000))
            self.ax.plot(freqs, signals, "yo", markersize=dotsize)

        if np.array_equal(data_calib["freq"], data_no_calib["freq"]):
            self.spectrum = (data_calib["spectrogram"]  - data_no_calib["spectrogram"] ) / np.abs(fit_params_plunger['fit_coef'][0])
            
            self.ax.plot(data_calib["freq"], np.sqrt(self.spectrum), "ok", markersize=dotsize)

            plt.grid()
            plt.savefig(f"{create_saving_path(settings)}/{savename}.png", dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
            plt.show()
        else:
            print("Error: Frequency arrays of both data inputs not equal!")
        self.close_delete()
