import matplotlib.pyplot as plt

from qkit.analysis.semiconductor.main.pre_formatted_figures import SemiFigure
from qkit.analysis.semiconductor.main.saving import create_saving_path
from qkit.analysis.semiconductor.main.conversion_lockin_conductance import convert_conductance
from qkit.analysis.semiconductor.main.equalize_length import make_len_eq
from qkit.analysis.semiconductor.main.time_conversion import convert_secs


class PlotterTimetraceCond(SemiFigure):
    """Plots a timetrace of the conductance over time. 
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.savename = "timetrace"
        self.label = "-"
        self.title = "Timetrace"

    def plot(self, settings, data_in, nodes):
        """nodes are time and x,y,R of lock-in like ["demod0.timestamp0", "demod0.x0"].
        """
        data = make_len_eq(data_in, nodes)
        self.ax.set_title(self.title)
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Conductance ($\mu$S)")
        self.ax.plot(convert_secs(data[nodes[0]]), convert_conductance(data[nodes[1]], settings, multiplier=1e6), self.label)
        plt.savefig(create_saving_path(settings, self.savename, self.save_as), dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show()
        self.close_delete()