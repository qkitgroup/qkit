import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import MaxNLocator

from qkit.analysis.semiconductor.main.pre_formatted_figures import SemiFigure
from qkit.analysis.semiconductor.main.saving import create_saving_path
from qkit.analysis.semiconductor.main.conversion_lockin_conductance import convert_conductance


class Plotter3D(SemiFigure):
    """Plots 3D data of 2D sweeps.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.colorcode = "viridis"
        self.savename = "plot3D"
        self.conductance = True
        self.min = None
        self.max = None    



    def plot(self, settings:dict, data:dict, nodes, axis_labels=["x_gate", "y_gate"]):
        """Nodes in format [x, y, R].
        good color codes might be viridis, PiYG, plasma, gist_rainbow...
        """
        data_x = data[nodes[0]]
        data_y = data[nodes[1]]
        if self.conductance == True:
            data_z = np.transpose(convert_conductance(data[nodes[2]], settings, 1e6))
        else: 
            data_z = 1e3 * data[nodes[2]]
        
        plt.xlabel(axis_labels[0] + " (V)")
        plt.ylabel(axis_labels[1] + " (V)")
        
        if self.min is None:
                min = data_z.min()
        else: 
            min = self.min
        if self.max is None:
            max = data_z.max()
        else: 
            max = self.max

        levels = MaxNLocator(nbins=100).tick_values(min, max)
        cmap = plt.get_cmap(self.colorcode)
        norm = BoundaryNorm(levels, ncolors=cmap.N, clip=True)
        plt.pcolormesh(data_x, data_y, data_z, cmap=cmap, norm=norm)
        if self.conductance == True:
            plt.colorbar(label='Conductance ($\mu$S)')
        else: 
            plt.colorbar(label='Lock-in R (mV)')

        plt.savefig(create_saving_path(settings, self.savename, self.save_as), dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show()
        self.close_delete()