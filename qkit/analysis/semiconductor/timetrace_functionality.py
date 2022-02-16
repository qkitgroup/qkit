import numpy as np
import copy
import matplotlib.pyplot as plt
from scipy import signal
from scipy.optimize import curve_fit

from qkit.analysis.semiconductor.basic_functionality import PlotterSemiconInit, convert_conductance, map_array_to_index
from qkit.analysis.semiconductor.basic_functionality import  convert_secs, create_saving_path, make_len_eq


class PlotterTimetraceCond(PlotterSemiconInit):
    """Plots a timetrace of the conductance over time. 
    """
    number_of_traces = 1
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
               
    def plot(self, settings, data_in, nodes, savename="timetrace", label="-", title="Timetrace"):
        """nodes are time and x,y,R of lock-in like ["demod0.timestamp0", "demod0.x0"].
        """
        data = make_len_eq(data_in, nodes)
        self.ax.set_title(title)
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Conductance ($\mu$S)")
        self.ax.plot(convert_secs(data[nodes[0]]), convert_conductance(data[nodes[1]], settings, multiplier=1e6), label)
        plt.savefig(f"{create_saving_path(settings)}/{savename}.png", dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show()
        self.close_delete()
        

class PlotterTimetraceR(PlotterSemiconInit):
    """Plots a timetrace of the lock-in amplitude over time. 
    """
    number_of_traces = 1
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
               
    def plot(self, settings, data_in, nodes, savename="timetrace", label="-", title="Timetrace"):
        """nodes are time and x,y,R of lock-in like ["demod0.timestamp0", "demod0.x0"].
        """
        data = make_len_eq(data_in, nodes)
        self.ax.set_title(title)
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Lock-in R (mV)")
        self.ax.plot(convert_secs(data[nodes[0]]), data[nodes[1]]*1000, label)
        plt.savefig(f"{create_saving_path(settings)}/{savename}.png", dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show()
        self.close_delete()
        

class PlotterTimetracePhase(PlotterSemiconInit):
    """Plots the phase of the conductance of a timetrace over time. 
    phi = np.arctan2(data_y, data_x)
    """
    number_of_traces = 1
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
               
    def plot(self, settings, data_in, nodes, savename="timetrace_phase", label="-", x_limits=[], y_limits=[]):
        """nodes are t, x, y of lock-in like ["demod0.timestamp0", "demod0.x0", "demod0.y0"].
        """
        data = make_len_eq(data_in, nodes)
        if len(x_limits) == 2:
            self.ax.set_xlim(x_limits)
        if len(y_limits) == 2:
            self.ax.set_ylim(y_limits)
        self.ax.set_title("Timetrace")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Phase (deg)")
        self.phase = np.arctan2(data[nodes[2]], data[nodes[1]]) * 180 / np.pi
        self.ax.plot(convert_secs(data[nodes[0]]), self.phase, label)
        plt.savefig(f"{create_saving_path(settings)}/{savename}.png", dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show()
        self.close_delete()


class SliceTimetrace:
    """Slices data by beginning and ending values of the time (first node entry) in seconds.
    """
    def __init__(self, begin, end):
        """initialize with beginning and ending.
        """
        self.begin = begin
        self.end = end
        
    def make_slice_timetrace(self, data, nodes, f=1.8*1e9):
        begin_x = data[nodes[0]][0] + self.begin * f
        end_x = data[nodes[0]][0] + self.end * f
        index_begin = map_array_to_index(data[nodes[0]], begin_x)
        index_end = map_array_to_index(data[nodes[0]], end_x)
        data_sliced = {}
        for key in nodes:
            data_sliced[key] = copy.deepcopy(data[key][index_begin : index_end])
        
        return data_sliced
      

    
class AnalyzerPlungerSweep:
    """Fits a tangent to a point in a plunger gate sweep and returns the fit results. 
    Lock-in V used for calculations instead of conductance.
    Slope coef[0] in Volt / Volt.
    """
    number_of_traces = 1
    
    def analyze(self, data, nodes, voltage, intervall):
        """Fits a linear function to values at voltage with intervall around it.
        """
        self.data_x = data[nodes[0]]
        self.data_y = data[nodes[1]]
        index_begin = map_array_to_index(self.data_x, voltage - abs(intervall))
        index_end = map_array_to_index(self.data_x, voltage +  abs(intervall))
        self.data_x_cut = self.data_x[index_begin : index_end]
        self.data_y_cut = self.data_y[index_begin : index_end]
        
        coef = np.polyfit(self.data_x_cut, self.data_y_cut, 1)
   
        return {"fit_coef" : coef, "index_begin" : index_begin, "index_end" : index_end}
    

class PlotterPlungerSweep(PlotterSemiconInit):
    """Plots plunger gate sweeps and (if given) overlays tangent.
    """
    number_of_traces = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def plot(self, settings, settings_plunger, data_in, nodes, fit_params=None, savename="plunger_sweep", color="r", x_limits=[]):
        data = make_len_eq(data_in, nodes)
        y_axis_factor = 1000  #scales y axis to mV
        self.ax.set_title("Plunger Gate Sweep")
        self.ax.set_xlabel("Voltage (V)")
        self.ax.set_ylabel("Lock-in Voltage (mV)")
        self.data_x = data[nodes[0]]
        self.data_y = data[nodes[1]]*y_axis_factor
        if len(x_limits) == 2:
            self.ax.set_xlim(x_limits)
        self.ax.plot(self.data_x, self.data_y)
        if fit_params != None:
            poly1d_fn = np.poly1d(fit_params["fit_coef"])
            self.data_x_fit = self.data_x[fit_params["index_begin"] : fit_params["index_end"]]
            self.ax.plot(self.data_x_fit, poly1d_fn(self.data_x_fit)*y_axis_factor, color, 
            label=f"slope: {fit_params['fit_coef'][0]*y_axis_factor:.0f} mV/V")
            self.ax.legend()
        plt.savefig(f"{create_saving_path(settings_plunger)}/{savename}.png", dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.savefig(f"{create_saving_path(settings)}/{savename}.png", dpi=self.set_dpi, bbox_inches=self.set_bbox_inches) 
        plt.show() 
        self.close_delete()





class AnalyzerTimetraceSpecralNoiseDensity:
    number_of_traces = 1
    
    def analyze(self, sampling_freq, data, nodes, fit_params=None):
        """Analyzes a sigle timetrace using the equivalent gate voltage found in fit_params['fit_coef'][0] if provided.
        """
        if fit_params is None: # for reference measurements without plunger gate sweeps
            fit_params = {}
            fit_params["fit_coef"] = [1]
        freqs, times, spectrogram = signal.spectrogram(data[nodes[0]] / fit_params['fit_coef'][0], fs = sampling_freq, nperseg = len(data[nodes[0]]))   
        spectrogram = np.real(spectrogram.flatten().astype(complex)) # yes I know... tell me why data type is object and complex

        return {"freq" : freqs[1:], "times" : times[1:], "spectrogram": spectrogram[1:]} # freqs[0]=0 ; The 0Hz value is cut off:
    
    def fit(self, spectrum, guess=None, max_iter=10000000):
        """Fits f(x)= a*x^b to data. Return is the parameters of the fit around 1Hz.
        guess is an array or list of starting values for a, b.  
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



class PlotterTimetraceSpectralNoiseDensity(PlotterSemiconInit):
    """Plots the spectral noise density.
    """
    number_of_traces = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def plot(self, settings, data, fit_params_plunger_in=None, fit_vals=None, savename=None, xlim:list=None, ylim:list=None, dotsize=0.5, fiftyHz:bool=False):
        """Plots the sqrt of a spectrum (data). Respecting scaling with the slope of a plunger gate sweep (fit_params_plunger). 
            data: spectral data in dictionary with keys "freq", "times", "spectorgram"
            fit_params_plunger: dict including key "fit_coef" that is only used in the savename of the file
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

        if fiftyHz == True: #plotting 50Hz multiples
            savename += "_50Hz"
            freqs = []
            signals = []
            for f in [i*50 for i in range(31)]:
                freqs.extend([f]*1000 )
                signals.extend(np.logspace(-8, -1, 1000))
            self.ax.plot(freqs, signals, "yo", markersize=dotsize)

        self.ax.plot(data["freq"], np.sqrt(data["spectrogram"]), "ok", markersize=dotsize)

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
        plt.savefig(f"{create_saving_path(settings)}/{savename}.png", dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show()
        self.close_delete()
