import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

from qkit.analysis.semiconductor.main.pre_formatted_figures import SemiFigure
from qkit.analysis.semiconductor.main.saving import create_saving_path
from qkit.analysis.semiconductor.main.fit_functions import gauss_function


class PlotterTimetraceJumpsHistogram(SemiFigure):
    """Plots a Histogramm of the amount of Jumps in a Timetrace analyzed with AnalyzerTimetraceJumps. 
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.savename = "Jumps_Histogram"
        self.label = "-"
        self.title = "Jumps Histogram"
        self.marker_size = 5
        self.init_guess_0 = [20, 0, 0.2] # inital guess for a and sigma for a gauss around x=0
        
               
    def plot(self, settings, hist):
        """hist is the output of AnalyzerTimetraceJumps.
        """
        self.title = self.title + f"  ({hist['time_analyzed']/3600:.1f} hours)"
        self.ax.set_title(self.title)
        self.ax.set_xlabel("Jump value (mV)")
        self.ax.set_ylabel("Count")

        data_x = np.array(1e3 * hist["jump_height"][:-1], dtype=np.float32)
        data_y = hist["jumps_per_bin"]

        self.ax.plot(data_x, data_y, "-ok", markersize=self.marker_size)
        
        popt, pcov = curve_fit(gauss_function, data_x, data_y) 
        x_linspace = np.linspace(data_x[0], data_x[-1], num = 1000)
        self.ax.plot(x_linspace, gauss_function(x_linspace, *popt), label=f"Gaussian fit\nsigma : {abs(popt[2]):.3f} mV")
        self.ax.legend()
        self.popt = popt
        plt.savefig(create_saving_path(settings, self.savename, self.save_as), dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show()

        # counting jumps bigger than 3 sigma:
        

        self.close_delete()