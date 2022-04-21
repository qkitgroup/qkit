import numpy as np
import matplotlib.pyplot as plt


from qkit.analysis.semiconductor.main.pre_formatted_figures import SemiFigure
from qkit.analysis.semiconductor.main.saving import create_saving_path
from qkit.analysis.semiconductor.main.find_index_of_value import map_array_to_index


class PlotterTimetracePeakTrackingSND(SemiFigure):
    """Plots the spectral noise density using the equivalent gate voltage found in fit_params['fit_coef'][0] if provided.
    """
    number_of_traces = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def plot(self, settings:dict, data:dict, data_peak_tracking, fit_params_plunger_in=None, fit_vals=None, savename=None, xlim:list=None, ylim:list=None, dotsize=0.5, fiftyHz:bool=False, legend_loc="lower left"):
        """Plots the sqrt of a spectrum (data["spectrogram"]). Respecting scaling with the slope of a plunger gate sweep (fit_params_plunger). 
            data: spectral data in dictionary with keys "freq", "times", "spectorgram"
            data_peak_tracking: spectral data of a peak tracking that won't need division by equivalent gate voltage
            fit_params_plunger_in: dict including key "fit_coef" 
            fit_vals: dict with keys "popt" and "SND1Hz" that is used to plot a linear fit to the data
            fifyHz: bool that overlays the first 30 50Hz multiples
        """
        self.ax.set_title("Spectral Noise Density")
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
            savename = f"SND_slope_{fit_params_plunger['fit_coef'][0]:.3f}"

        if fiftyHz == True: # plotting 50Hz multiples
            savename += "_50Hz"
            freqs = []
            signals = []
            for f in [i*50 for i in range(31)]:
                freqs.extend([f]*1000 )
                signals.extend(np.logspace(-8, -1, 1000))
            self.ax.plot(freqs, signals, "yo", markersize=dotsize)

        self.ax.plot(data_peak_tracking["freq"], np.sqrt(data_peak_tracking["spectrogram"]), "or", markersize=dotsize, label="peak tracking", markerscale=3)
        self.ax.plot(data["freq"], np.sqrt(data["spectrogram"] / fit_params_plunger['fit_coef'][0]), "ok", markersize=dotsize, label="timetrace", markerscale=3)

        if fit_vals is not None:
            def func(x, a, b):
                return a * np.power(x, b) 
            index_begin = map_array_to_index(data["freq"], 1e-1)
            index_end = map_array_to_index(data["freq"], 1e1)
            freqs = data["freq"][index_begin : index_end]
            text = f"SD(1Hz): {fit_vals['popt'][0]*1e6:.1f} " + "$\mathrm{\mu V}/\sqrt{\mathrm{Hz}}$"
            self.ax.plot(freqs, func(freqs, *fit_vals["popt"]), label=text)
            self.ax.legend(loc="lower left")

        plt.grid()
        plt.legend(loc=legend_loc)
        plt.savefig(f"{create_saving_path(settings)}/{savename}.png", dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show()
        self.close_delete()
