import numpy as np
import matplotlib.pyplot as plt

from qkit.analysis.semiconductor.main.pre_formatted_figures import SemiFigure
from qkit.analysis.semiconductor.main.saving import create_saving_path


class PlotterPlungerTraceFit(SemiFigure):
    """Plots a single plunger gate sweep trace and overlays the analyzed fit to see how shitty the fit is. 
    The sechans function uses as x values not voltages but indices of the voltages of the plunger gate array.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.plot_fit = True
        self.savename = "one_plunger_fit"
        self.trace_num = 0

    def plot(self, settings:dict, data:dict, nodes):
        def sech(x, a, b, c, d):
            '''hyperbolic secans function'''
            return a * (1 / np.cosh(b * (x - c))) + d

        self.ax.set_title("One Plunger Sweep")
        self.ax.set_xlabel("Plunger Voltage (V)")
        self.ax.set_ylabel("Lock-in (mV)")

        if self.plot_fit:
            #plotting the fit only in the used intervall 
            fit_peak_index = int(round(data["peaks_fit_popts"][self.trace_num][2])) # value of c in sech(x, *[a, b, c, d]) as an INDEX of the array
            fit_intervall_half_index = data["peaks_fit_intervall_half"]
            fit_x_indices = np.arange(fit_peak_index - fit_intervall_half_index, fit_peak_index + fit_intervall_half_index+1)
            fit_x = data[nodes[0]][fit_x_indices[0] : fit_x_indices[-1]+1]
            fit_y = 1000 * sech(fit_x_indices, *data["peaks_fit_popts"][self.trace_num])
            self.ax.plot(fit_x, fit_y, "r", label="fit")

        self.ax.plot(data[nodes[0]], data[nodes[1]][self.trace_num]*1000)
        plt.legend()
        plt.savefig(create_saving_path(settings, self.savename, self.save_as), dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show()
        self.close_delete()