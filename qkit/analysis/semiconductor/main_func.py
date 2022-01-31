import numpy as np
import h5py
import pathlib
import math
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import MaxNLocator
from scipy import signal




def convert_conductance(amplitudes, settings, multiplier):
    """Converts Lock-in amplitude in conductance in Siemens. 
        measurement_amp: amplitude of lock-in signal
        voltage_divider: used before the input of the lock-in
        IVgain: of IV converter
        in_line_R: sum of resistances of the line without QD
        multiplier: multiplies values by factor of e.g. 1e6 to get micro Siemens
    """
    return multiplier / (settings["meas_params"]["measurement_amp"] * settings["meas_params"]["IVgain"] / (settings["meas_params"]["voltage_divider"] 
                         * amplitudes * np.sqrt(2)) - settings["meas_params"]["in_line_R"])




def map_array_to_index(array, value):
    """Takes an array of SORTED values and returns the nearest index where the value is found. 
    """
    idx = np.searchsorted(array, value, side="left")
    if idx > 0 and (idx == len(array) or math.fabs(value - array[idx-1]) < math.fabs(value - array[idx])):
        return idx-1
    else:
        return idx

    
def convert_secs(timestamps, f=1.8*1e9):
    """Sets the starting point to 0 and adjusts with the clock speed of 1.8 GHz. Not really accurate.
    Timestamps need to be numpy arrays.
    """
    timestamps = timestamps - timestamps[0]
    timestamps = timestamps / f 
    
    return timestamps
    

def convert_secs_2D(timestamps, f=1.8*1e9):
    """Sets the starting point to 0 and adjusts with the clock speed of 1.8 GHz. Not really accurate.
    Converts 2D timestamps in 1D arrays with each point in 1D being the beginning of a 2D array. 
    """
    timestamps = timestamps[:,0] - timestamps[0,0]
    timestamps = timestamps / f 
    
    return timestamps
    
    
    
def create_saving_path(settings):
    """Creats a folder with the name of settings["file_info"]["savepath"] if it's not existent and returns path to it. 
    """
    path = f"{settings['file_info']['absolute_path']}{settings['file_info']['date_stamp']}/{settings['file_info']['filename']}/{settings['file_info']['savepath']}"
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)
    
    return path + "/"   
    
    



class Loaderh5:
    """Extracts all data from .h5 files in this folder and returns it as a dict.
    """  
    def load(self, settings):
        """Loads the data of a .h5 file. Analysis and views are not loaded.
        """
        path = f"{settings['file_info']['absolute_path']}{settings['file_info']['date_stamp']}/{settings['file_info']['filename']}/{settings['file_info']['filename']}.h5"
        data = h5py.File(path,'r')["entry"]["data0"]
        self.data_dict = {}
        for key in data.keys():
            self.data_dict[key] = np.array(data.get(u'/entry/data0/' + key)[()])
        return self.data_dict
        

class PlotterSemiconInit(Figure):
    """Standard class for plots.
    """
    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)
        self.fig = plt.figure()
        self.ax = self.fig.subplots()
        self.set_dpi = 400
        self.set_bbox_inches = "tight"

        self.ax.title.set_size(fontsize=14) 
        self.ax.xaxis.label.set_size(fontsize=12)
        self.ax.yaxis.label.set_size(fontsize=12)
     
    def close_fig(self):
        """Frees RAM and closes fig.
        """
        self.fig.clear()
        plt.close(self.fig)



    
    
class PlotterTimetraceCond(PlotterSemiconInit):
    """Plots a timetrace of the conductance over time. 
    """
    number_of_traces = 1
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
               
    def plot(self, settings, data, nodes:list, savename="timetrace", label="-", title="Timetrace"):
        """nodes are time and x,y,R of lock-in like ["demod0.timestamp0", "demod0.x0"].
        """
        self.ax.set_title(title)
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Conductance ($\mu$S)")
        self.ax.plot(convert_secs(data[nodes[0]]), convert_conductance(data[nodes[1]], settings, multiplier=1e6), label)
        plt.savefig(f"{create_saving_path(settings)}/{savename}.png", dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show()
        self.close_fig()


class PlotterTimetraceR(PlotterSemiconInit):
    """Plots a timetrace of the lock-in amplitude over time. 
    """
    number_of_traces = 1
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
               
    def plot(self, settings, data, nodes:list, savename="timetrace", label="-", title="Timetrace"):
        """nodes are time and x,y,R of lock-in like ["demod0.timestamp0", "demod0.x0"].
        """
        self.ax.set_title(title)
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Lock-in R (mV)")
        self.ax.plot(convert_secs(data[nodes[0]]), data[nodes[1]]*1000, label)
        plt.savefig(f"{create_saving_path(settings)}/{savename}.png", dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show()
        self.close_fig()
        

class PlotterTimetracePhase(PlotterSemiconInit):
    """Plots the phase of the conductance of a timetrace over time. 
    phi = np.arctan2(data_y, data_x)
    """
    number_of_traces = 1
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
               
    def plot(self, settings, data, nodes, savename="timetrace_phase", label="-"):
        """nodes are t, x, y of lock-in like ["demod0.timestamp0", "demod0.x0", "demod0.y0"].
        """
        self.ax.set_title("Timetrace")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Phase (deg)")
        self.phase = np.arctan2(data[nodes[2]], data[nodes[1]]) * 180 / np.pi
        self.ax.plot(convert_secs(data[nodes[0]]), self.phase, label)
        plt.savefig(f"{create_saving_path(settings)}/{savename}.png", dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show()
    

class SliceTimetrace:
    """Slices data_x and data_y by beginning and ending values of x in seconds.
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
        sliced_x = data[nodes[0]][index_begin : index_end]
        sliced_y = data[nodes[1]][index_begin : index_end]
        
        return {f"{nodes[0]}" : sliced_x, f"{nodes[1]}" : sliced_y,}
    

class SlicePlungerTimetrace:
    """Slices.
    """
    #def make_slice_plunger_timetrace(self, timestamps,   )    

    
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

    def plot(self, settings, settings_plunger, data, nodes, fit_params=None, savename="plunger_sweep", color="r"):
        y_axis_factor = 1000  #scales y axis to mV
        self.ax.set_title("Plunger Gate Sweep")
        self.ax.set_xlabel("Voltage (V)")
        self.ax.set_ylabel("Lock-in Voltage (mV)")
        self.data_x = data[nodes[0]]
        self.data_y = data[nodes[1]]*y_axis_factor
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






class AnalyzerTimetraceSpecralNoiseDensity:
    """Analyzes a sigle timetrace using the equivalent voltage noise found in fit_params['fit_coef'][0].
    Includes conversion of data into conductance. 
    """
    number_of_traces = 1
    
    def analyze(self, sampling_freq, fit_params, data, nodes):
        freqs, times, spectrogram = signal.spectrogram(data[nodes[0]] / fit_params['fit_coef'][0], fs = sampling_freq, nperseg = len(data)) 
       
        return {"freq" : freqs, "times" : times, "spectrogram": spectrogram}
    

class PlotterTimetraceSpectralNoiseDensity(PlotterSemiconInit):
    """Plots the spectral noise density.
    """
    number_of_traces = 1

    def plot(self, settings, data, fit_params, savename=None, xlim:list=None, ylim:list=None, dotsize=0.5):
        self.ax.set_title("Spectral noise density")
        self.ax.set_xscale("log")
        self.ax.set_yscale("log")
        self.ax.set_xlabel("Frequency (Hz)")
        self.ax.set_ylabel("Spectral Density ($V/\sqrt{\mathrm{Hz}}$)")
        if xlim != None:
            self.ax.set_xlim(xlim)
        if ylim != None:
            self.ax.set_ylim(ylim)
        self.ax.plot(data["freq"], np.sqrt(data["spectrogram"]), "ok", markersize=dotsize)
#        freq_line = np.arange(1e-4, 1e4, 1)
#        plt.plot(freq_line, 2*1e-8 * freq_line**(-1), color="orange", label="$1 / f$" )
#        plt.tight_layout()
#        plt.legend()
        if savename == None:
            savename = f"SND_slope_{fit_params['fit_coef'][0]:.0f}"
        plt.savefig(f"{create_saving_path(settings)}/{savename}.png", dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show()


##############################################################
#2D Data Plunger Timetrace
   
class PlotterPlungerTimetrace3D:
    """Plots 3D data.
    """
    def plot(self, settings, data_x, data_y, data_z, colorcode="viridis", savename="Plunger_timetrace"):
        """good color codes might be viridis, PiYG, plasma, gist_rainbow...
        """
        data_z = np.transpose(convert_conductance(data_z, settings, 1e6))
        plt.xlabel("Time (h)", fontsize=12)
        plt.ylabel("Voltage plunger gate", fontsize=12)
        levels = MaxNLocator(nbins=100).tick_values(data_z.min(), data_z.max())
        cmap = plt.get_cmap(colorcode)
        norm = BoundaryNorm(levels, ncolors=cmap.N, clip=True)
        plt.pcolormesh(convert_secs_2D(data_x)/3600, data_y, data_z, cmap=cmap, norm=norm)
        plt.colorbar(label='Conductance ($\mu$S)')
        plt.savefig(f"{create_saving_path(settings)}/{savename}.png", bbox_inches='tight', dpi=400)
        plt.show()
    
 

class AnalyzerPeakTracker:
    """Fits a sechant function to a plunger gate sweep.
    """
    def analyze(self, settings, data_x, data_y, data_z, colorcode="viridis", name="Plunger_timetrace_tracked"):
        pass
    
    
    
    
#    import os, fnmatch
        
#    def find_pattern(self, pattern, path):
#        """finds files with given pattern in name.
#        """
#        result = []
#        for root, dirs, files in os.walk(path):
#            for name in files:
#                if fnmatch.fnmatch(name, pattern):
#                    result.append(os.path.join(root, name))
#        return result
#        
