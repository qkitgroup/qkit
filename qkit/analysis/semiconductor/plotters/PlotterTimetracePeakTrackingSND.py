import numpy as np
import matplotlib.pyplot as plt


from qkit.analysis.semiconductor.main.pre_formatted_figures import SemiFigure
from qkit.analysis.semiconductor.main.saving import create_saving_path
from qkit.analysis.semiconductor.main.find_index_of_value import map_array_to_index


class PlotterTimetracePeakTrackingSND(SemiFigure):
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
        self.legend_loc = "lower left"


    def plot(self, settings:dict, data:dict, data_peak_tracking):
        """Plots the sqrt of a spectrum (data["spectrogram"]). Respecting scaling with the slope of a plunger gate sweep (fit_params_plunger). 
            data: spectral data in dictionary with keys "freq", "times", "spectorgram"
            data_peak_tracking: spectral data of a peak tracking that won't need division by equivalent gate voltage
            fit_params_plunger: dict including key "fit_coef" 
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

        plunger_calib = fit_params_plunger['fit_coef'][0]

        if self.savename == None:
            self.savename = f"SND_slope_{plunger_calib:.3f}"

        if self.fiftyHz == True: # plotting 50Hz multiples
            self.savename += "_50Hz"
            freqs = []
            signals = []
            for f in [i*50 for i in range(31)]:
                freqs.extend([f]*1000 )
                signals.extend(np.logspace(-8, -1, 1000))
            self.ax.plot(freqs, signals, "yo", markersize=self.dotsize)

        

        self.ax.plot(data_peak_tracking["freq"], np.sqrt(data_peak_tracking["spectrogram"]), "or", markersize=self.dotsize, label="peak tracking")
        self.ax.plot(data["freq"], np.sqrt(data["spectrogram"] / plunger_calib), "ok", markersize=self.dotsize, label="timetrace")

        if self.fit_vals is not None:
            def func(x, a, b):
                return a * np.power(x, b) 
            index_begin = map_array_to_index(data["freq"], 1e-1)
            index_end = map_array_to_index(data["freq"], 1e1)
            freqs = data["freq"][index_begin : index_end]
            SND_1Hz = 1e6 * np.sqrt(func(1, *self.fit_vals["popt"])/ np.abs(plunger_calib))
            text = f"SD(1Hz): {SND_1Hz:.0f} " + "$\mathrm{\mu V}/\sqrt{\mathrm{Hz}}$"
            fit_spectrum = np.sqrt(func(freqs, *self.fit_vals["popt"])/ np.abs(plunger_calib))
            self.ax.plot(freqs, fit_spectrum, label=text)
            self.ax.legend(loc="lower left")

        plt.grid()
        plt.legend(loc=self.legend_loc)
        plt.savefig(create_saving_path(settings, self.savename, self.save_as), dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show()
        self.close_delete()
