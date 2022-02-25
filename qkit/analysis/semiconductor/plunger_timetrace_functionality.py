import numpy as np
import copy
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import MaxNLocator
from scipy.optimize import curve_fit

from qkit.analysis.semiconductor.basic_functionality import PlotterSemiconInit, convert_conductance, map_array_to_index
from qkit.analysis.semiconductor.basic_functionality import  convert_secs_2D, create_saving_path, make_len_eq



class SlicePlungerTimetrace:
    """Slices the nodes which are given in a slice that is given by "begin" and "end" in hours.
    First node needs to be timestamps, second is gate, third and following can be x, y, and/or R.
    """
    def slice(self, data, nodes, beginning, ending): 
        timestamps = convert_secs_2D(data[nodes[0]])
        index_begin = map_array_to_index(timestamps, beginning*3600)
        index_end = map_array_to_index(timestamps, ending*3600)
        data_sliced = {}
        data_sliced[nodes[0]] = copy.deepcopy(data[nodes[0]][index_begin : index_end])
        data_sliced[nodes[1]] = copy.deepcopy(data[nodes[1]])
        for index in np.arange(2, len(nodes)): # could be x, y, R
            data_sliced[nodes[index]] = copy.deepcopy(data[nodes[index]][index_begin : index_end, : ])
     
        return data_sliced



       
class PlotterPlungerTimetrace3D(PlotterSemiconInit):
    """Plots 3D data of plunger gate sweeps.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def plot(self, settings:dict, data:dict, nodes, colorcode="viridis", savename="plunger_timetrace", min_cond=None, max_cond=None, point_size=3, marker_shape="ro"):
        """Nodes in format [timestamps, plunger_gate, R].
        good color codes might be viridis, PiYG, plasma, gist_rainbow...
        """
        data_z = np.transpose(convert_conductance(data[nodes[2]], settings, 1e6))
        data_time = convert_secs_2D(data[nodes[0]])/3600
        plt.xlabel("Time (h)", fontsize=12)
        plt.ylabel("Voltage plunger gate (V)", fontsize=12)
        if min_cond is None:
            min = data_z.min()
        else: 
            min = min_cond
        if max_cond is None:
            max = data_z.max()
        else: 
            max = max_cond 
        levels = MaxNLocator(nbins=100).tick_values(min, max)
        cmap = plt.get_cmap(colorcode)
        norm = BoundaryNorm(levels, ncolors=cmap.N, clip=True)
        plt.pcolormesh(data_time, data[nodes[1]], data_z, cmap=cmap, norm=norm)
        plt.colorbar(label='Conductance ($\mu$S)')

        if "peaks_plunger_V" in data:  # plotting fit
            plt.plot(data_time, data["peaks_plunger_V"], marker_shape, markersize=point_size)

        plt.savefig(f"{create_saving_path(settings)}/{savename}.png", bbox_inches='tight', dpi=400)
        plt.show()
        self.close_delete()
 



class AnalyzerPeakTracker:
    """Fits a sechans function to a plunger gate sweep in two iterations.
    """
    def analyze(self, data:dict, nodes, peak_V:float, intervall1=0.01, intervall2=0.01, max_iter=10000):
        """peak_V is the Voltage of the peak eyeballed.
        width and width2 are the intervalls of idices used to fit the data to.  Better in Volts in future? 
        The sechans fit is NOT using Volt values as x values but instead indices of the array. 
        """
        def sech(x, a, b, c, d):
            '''hyperbolic secans function'''
            return a * (1 / np.cosh(b * (x - c))) + d # return is scaled in Volts
        
        # initial parameters for fit
        a, b, d = 0.08, -0.1, 0.0

        peak_index = map_array_to_index(data[nodes[1]], peak_V)
        intervall1_half_index = map_array_to_index(data[nodes[1]], abs(intervall1 / 2) + data[nodes[1]][0])
        intervall2_half_index= map_array_to_index(data[nodes[1]], abs(intervall2 / 2) + data[nodes[1]][0])

        p0 = [a, b, peak_index, d]  #initatal guess of a, b, c, d
        timestamps = convert_secs_2D(data[nodes[0]])
        length_sweep = len(timestamps)
        data["timestamps_diff"] = np.diff(timestamps)
        data["avg_sweep_time"] = np.average(np.diff(timestamps)) 
        data["peaks_plunger_V"] =  np.array([None] * length_sweep) # initialize None array for peaks
        data["peaks_value"] =  np.array([None] * length_sweep)
        data["peaks_plunger_V_cov"] =  np.array([None] * length_sweep)
        data["peaks_fit_popts"] =  np.array([None] * length_sweep)
        data["peaks_fit_intervall_half"] = intervall2_half_index # saves the index size of the fit intervall/2

        for trace_num in range(len(timestamps)):
            try:
                # bigger intervall, first fit
                popt, pcov = curve_fit(sech, np.arange(peak_index-intervall1_half_index, peak_index+intervall1_half_index, 1), 
                    data[nodes[2]][trace_num][peak_index-intervall1_half_index : peak_index+intervall1_half_index], p0, maxfev=max_iter)
                peak_fitted_index = int(round(popt[2]))

                try:
                    # smaller intervall, second fit around peak of first fit
                    if peak_fitted_index > intervall2_half_index and peak_fitted_index < (length_sweep-intervall2_half_index):
                        p1 = [a, b, peak_fitted_index, d]

                        popt1, pcov1 = curve_fit(sech, np.arange(peak_fitted_index-intervall2_half_index, peak_fitted_index+intervall2_half_index, 1),
                            data[nodes[2]][trace_num][peak_fitted_index-intervall2_half_index : peak_fitted_index+intervall2_half_index], p1, maxfev=max_iter)

                        data["peaks_plunger_V"][trace_num] = data[nodes[1]][int(round(popt1[2]))] # plunger gate voltage of peak 
                        data["peaks_value"][trace_num] = sech(popt1[2], *popt1) # lock-in value of fitted peak
                        data["peaks_plunger_V_cov"][trace_num] = pcov1 # covariance on index of peak
                        data["peaks_fit_popts"][trace_num] = popt1 # values of [a, b, c, d]

                        if pcov1[2][2] > 1:
                            print("COV TOO BIG  ", trace_num)  
                            data["peaks_plunger_V"][trace_num] = None 
                            data["peaks_value"][trace_num] = None
                            data["peaks_plunger_V_cov"][trace_num] = None
                            data["peaks_fit_popts"][trace_num] = None
                            
                    else:
                        print("Peak not found in first fit")
                        data["peaks_plunger_V"][trace_num] = None 
                        data["peaks_value"][trace_num] = None
                        data["peaks_plunger_V_cov"][trace_num] = None
                        data["peaks_fit_popts"][trace_num] = None

                      
                except RuntimeError:
                    print("RUNTIME ERROR second ", trace_num)
                    pass

            except RuntimeError:
                print("RUNTIME ERROR first ", trace_num)
                pass
        

        

class PlotterPlungerTraceTimestampsDiff(PlotterSemiconInit):
    """Plots the time difference between consecutive plunger traces.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def plot(self, settings, data, savename="timestamps_diff" ):
        self.ax.set_title("Length of Plunger Sweeps")
        self.ax.set_xlabel("Sweep Number")
        self.ax.set_ylabel("Difference between Sweeps (s)")
        x_vals = np.arange(1, len(data["timestamps_diff"])+1)
        self.ax.plot(x_vals, data["timestamps_diff"])
        self.ax.plot(x_vals, [data["avg_sweep_time"]]*len(x_vals), "-r", label="average")
        plt.legend()
        plt.savefig(f"{create_saving_path(settings)}/{savename}.png", dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show()
        self.close_delete()





class PlotterPlungerTraceFit(PlotterSemiconInit):
    """Plots a single plunger gate sweep trace and overlays the analyzed fit to see how shitty the fit is. 
    The sechans function uses as x values not voltages but indices of the voltages of the plunger gate array.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def plot(self, settings:dict, data:dict, nodes, trace_num, savename="one_plunger_fit"):
        def sech(x, a, b, c, d):
            '''hyperbolic secans function'''
            return a * (1 / np.cosh(b * (x - c))) + d

        self.ax.set_title("One Plunger Sweep")
        self.ax.set_xlabel("Plunger Voltage (V)")
        self.ax.set_ylabel("Lock-in (mV)")

        #plotting the fit only in the used intervall 
        fit_peak_index = int(round(data["peaks_fit_popts"][trace_num][2])) # value of c in sech(x, *[a, b, c, d]) as an INDEX of the array
        fit_intervall_half_index = data["peaks_fit_intervall_half"]
        fit_x_indices = np.arange(fit_peak_index - fit_intervall_half_index, fit_peak_index + fit_intervall_half_index+1)
        fit_x = data[nodes[0]][fit_x_indices[0] : fit_x_indices[-1]+1]
        fit_y = 1000 * sech(fit_x_indices, *data["peaks_fit_popts"][trace_num])
        self.ax.plot(fit_x, fit_y, "r", label="fit")

        self.ax.plot(data[nodes[0]], data[nodes[1]][trace_num]*1000)
        plt.legend()
        plt.savefig(f"{create_saving_path(settings)}/{savename}.png", dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show()
        self.close_delete()