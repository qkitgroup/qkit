import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import MaxNLocator

from qkit.analysis.semiconductor.main.pre_formatted_figures import SemiFigure
from qkit.analysis.semiconductor.main.saving import create_saving_path
from qkit.analysis.semiconductor.main.conversion_lockin_conductance import convert_conductance
from qkit.analysis.semiconductor.main.time_conversion import convert_secs_2D


class PlotterPlungerTimetrace3D(SemiFigure):
    """Plots 3D data of plunger gate sweeps.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.colorcode = "viridis"
        self.savename = "plunger_timetrace"
        self.min_cond = None
        self.max_cond = None
        self.point_size = 3
        self.marker_shape = "ro"


    def plot(self, settings:dict, data:dict, nodes):
        """Nodes in format [timestamps, plunger_gate, R].
        good color codes might be viridis, PiYG, plasma, gist_rainbow...
        """
        data_z = np.transpose(convert_conductance(data[nodes[2]], settings, 1e6))
        data_time = convert_secs_2D(data[nodes[0]])/3600
        plt.xlabel("Time (h)", fontsize=12)
        plt.ylabel("Voltage plunger gate (V)", fontsize=12)
        if self.min_cond is None:
            min = data_z.min()
        else: 
            min = self.min_cond
        if self.max_cond is None:
            max = data_z.max()
        else: 
            max = self.max_cond 
        levels = MaxNLocator(nbins=100).tick_values(min, max)
        cmap = plt.get_cmap(self.colorcode)
        norm = BoundaryNorm(levels, ncolors=cmap.N, clip=True)
        plt.pcolormesh(data_time, data[nodes[1]], data_z, cmap=cmap, norm=norm)
        plt.colorbar(label='Conductance ($\mu$S)')

        if "peaks_plunger_V" in data:  # plotting fit
            plt.plot(data_time, data["peaks_plunger_V"], self.marker_shape, markersize=self.point_size)

        plt.savefig(create_saving_path(settings, self.savename, self.save_as), dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show()
        self.close_delete()