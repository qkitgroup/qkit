import matplotlib.pyplot as plt

from qkit.analysis.semiconductor.main.pre_formatted_figures import SemiFigure
from qkit.analysis.semiconductor.main.saving import create_saving_path
from qkit.analysis.semiconductor.main.time_conversion import convert_secs
from qkit.analysis.semiconductor.main.equalize_length import make_len_eq


class PlotterTimetrace(SemiFigure):
    """Plots a timetrace of the lock-in amplitude over time. 
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.savename = "timetrace"
        self.label = "-"
        self.title = "Timetrace"
        self.jumbo_data = True
                       
    def plot(self, settings, data_in, nodes):
        """nodes are time and x,y,R of lock-in like ["demod0.timestamp0", "demod0.x0"].
        """
        data = make_len_eq(data_in, nodes)
        self.ax.set_title(self.title)
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Lock-in R (mV)")
        self.ax.plot(convert_secs(data[nodes[0]]), data[nodes[1]]*1000, self.label)
        plt.savefig(create_saving_path(settings, self.savename, self.save_as), dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show()
        self.close_delete()