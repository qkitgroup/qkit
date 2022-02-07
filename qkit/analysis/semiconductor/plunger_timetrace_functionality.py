import numpy as np
import gc 
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import MaxNLocator

from qkit.analysis.semiconductor.basic_functionality import PlotterSemiconInit, convert_conductance, map_array_to_index
from qkit.analysis.semiconductor.basic_functionality import  convert_secs, create_saving_path, make_len_eq


#EVERYTHING UNDER CONSTRUCTION

class SlicePlungerTimetrace:
    """Slices.
    """
    #def make_slice_plunger_timetrace(self, timestamps,   )  
    

       
class PlotterPlungerTimetrace3D:
    """Plots 3D data.
    """
    def plot(self, settings, data_x, data_y, data_z, colorcode="viridis", savename="Plunger_timetrace", min=None, max=None):
        """good color codes might be viridis, PiYG, plasma, gist_rainbow...
        """
        data_z = np.transpose(convert_conductance(data_z, settings, 1e6))
        plt.xlabel("Time (h)", fontsize=12)
        plt.ylabel("Voltage plunger gate", fontsize=12)
        if min is None:
            min = data_z.min()
        if max is None:
            max = data_z.max()
        levels = MaxNLocator(nbins=100).tick_values(min, max)
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
    

    