import numpy as np
import matplotlib.pyplot as plt

from qkit.analysis.semiconductor.main.pre_formatted_figures import SemiFigure
from qkit.analysis.semiconductor.main.saving import create_saving_path
from qkit.analysis.semiconductor.main.time_conversion import convert_secs
from qkit.analysis.semiconductor.main.equalize_length import make_len_eq


class PlotterTimetracePhase(SemiFigure):
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