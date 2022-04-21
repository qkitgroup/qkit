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