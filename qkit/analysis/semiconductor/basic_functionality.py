import numpy as np
import h5py
import pathlib
import math
import gc 
import copy
import matplotlib.pyplot as plt
from matplotlib.figure import Figure



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
    time_stamps = timestamps - timestamps[0]
    time_stamps = time_stamps / f 
    
    return time_stamps
    

def convert_secs_2D(timestamps, f=1.8*1e9):
    """Sets the starting point to 0 and adjusts with the clock speed of 1.8 GHz. Not really accurate.
    Converts 2D timestamps in 1D arrays with each point in 1D being the beginning of a 2D array. 
    """
    time_stamps = timestamps[:,0] - timestamps[0,0]
    time_stamps = time_stamps / f 
    
    return time_stamps
    
    
    
def create_saving_path(settings):
    """Creats a folder with the name of settings["file_info"]["savepath"] if it's not existent and returns path to it. 
    """
    path = f"{settings['file_info']['absolute_path']}{settings['file_info']['date_stamp']}/{settings['file_info']['filename']}/{settings['file_info']['savepath']}"
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)
    
    return path + "/"   
    
    
def make_len_eq(data:dict, keys:list):
    """Takes a data dict and looks at two entries. Cuts away the end of data of the longer one to make 
    both equal length.
    """
    len1 = len(data[keys[0]])
    len2 = len(data[keys[1]])
    if len1 != len2:
        if len1 < len2:
            data[keys[1]] = copy.deepcopy(data[keys[1]][:len1])
        else:
            data[keys[0]] = copy.deepcopy(data[keys[0]][:len2])

    return data


def rotate_phase(data, nodes, phase_offset_deg):
    """Gives phase offset to x and y data (given in nodes).
    """
    R = np.sqrt(np.add(np.power(data[nodes[0]], 2), np.power(data[nodes[1]], 2)))
    phi = np.arctan2(data[nodes[1]], data[nodes[0]])
    phi = phi + phase_offset_deg*np.pi/180
    data_rotated = copy.deepcopy(data)
    data_rotated[nodes[0]] = R * np.cos(phi)
    data_rotated[nodes[1]] = R * np.sin(phi)  

    return data_rotated





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
        plt.rcParams['agg.path.chunksize'] = 10000 # makes saving too big data sets possible. 
     
    def close_delete(self):
        """Closes fig and deletes instance to free RAM.
        """
        self.fig.clear()
        plt.close(self.fig)
        del self
        gc.collect()



class PlotterAccumulation(PlotterSemiconInit):
    """Plots Accumulation Traces over gate voltage.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def plot_one_trace(self, settings, data_in, nodes, gatename:str="", savename="accumulation", label="-", title="Accumulation"):
        """Plot only one trace.
        """
        data = make_len_eq(data_in, nodes)
        self.ax.set_title(title)
        if len(gatename) == 0:
            gatename = nodes[0]
        self.ax.set_xlabel(gatename)
        self.ax.set_ylabel("Conductance ($\mu$S)")
        self.ax.plot(data[nodes[0]], convert_conductance(data[nodes[1]], settings, multiplier=1e6), label)
        plt.savefig(f"{create_saving_path(settings)}/{savename}.png", dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show()
        self.close_delete()

    def add_trace(self, settings, data_in, nodes, label_id=""):
        """Adds a trace to the plotter object which can be plotted by plot_all().
        """
        data = make_len_eq(data_in, nodes)
        self.ax.plot(data[nodes[0]], convert_conductance(data[nodes[1]], settings, multiplier=1e6), label=label_id)
    
    def plot_all(self, settings, gatename:str="", savename="accumulation_many", title="Accumulation"):
        """Plots the traces that have been added by add_trace().
        """
        self.ax.set_title(title)
        self.ax.set_xlabel(gatename)
        self.ax.set_ylabel("Conductance ($\mu$S)")
        plt.savefig(f"{create_saving_path(settings)}/{savename}.png", dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.legend()
        plt.show()
        self.close_delete()



class PlotterBiascoolingAccumulation(PlotterSemiconInit):
    """Plots Accumulation voltages over bias cooling voltage.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def plot(self, data, savename="accumulations_biascooling", shape="^", size=100, transparency=1):
        self.ax.set_title("Accumulation Voltages depending on Bias Cooling")
        self.ax.set_xlabel("Bias Cooling Voltage (V)")
        self.ax.set_ylabel("Accumulation Voltage (V)")
        for cooldown in data:
            self.ax.scatter(cooldown["bias_V"], cooldown["first_acc_V"], marker=shape, s=size, alpha=transparency)
        plt.grid()
        plt.savefig(f"{savename}.png", dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show() 
        self.close_delete()
