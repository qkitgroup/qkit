import matplotlib.pyplot as plt

from qkit.analysis.semiconductor.main.pre_formatted_figures import SemiFigure
from qkit.analysis.semiconductor.main.saving import create_saving_path
from qkit.analysis.semiconductor.main.conversion_lockin_conductance import convert_conductance
from qkit.analysis.semiconductor.main.equalize_length import make_len_eq


class PlotterAccumulation(SemiFigure):
    """Plots Accumulation Traces over gate voltage.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gatename:str = ""
        self.savename = "accumulation"
        self.title = "Accumulation"

    def plot_one_trace(self, settings, data_in, nodes):
        """Plot only one trace.
        """
        data = make_len_eq(data_in, nodes)
        self.ax.set_title(self.title)
        if len(self.gatename) == 0:
            gatename = nodes[0]
        self.ax.set_xlabel(self.gatename)
        self.ax.set_ylabel("Conductance ($\mu$S)")
        self.ax.plot(data[nodes[0]], convert_conductance(data[nodes[1]], settings, multiplier=1e6))
        plt.savefig(create_saving_path(settings, self.savename, self.save_as), dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show()
        self.close_delete()

    def add_trace(self, settings, data_in, nodes, label_id=""):
        """Adds a trace to the plotter object which can be plotted by plot_all().
        """
        data = make_len_eq(data_in, nodes)
        self.ax.plot(data[nodes[0]], convert_conductance(data[nodes[1]], settings, multiplier=1e6), label=label_id)
    
    def plot_all(self, settings):
        """Plots the traces that have been added by add_trace().
        """
        self.ax.set_title(self.title)
        self.ax.set_xlabel(self.gatename)
        self.ax.set_ylabel("Conductance ($\mu$S)")
        plt.savefig(create_saving_path(settings, self.savename, self.save_as), dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.legend()
        plt.show()
        self.close_delete()
