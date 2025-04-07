import numpy as np
import matplotlib.pyplot as plt


from qkit.analysis.semiconductor.main.pre_formatted_figures import SemiFigure
from qkit.analysis.semiconductor.main.saving import create_saving_path
from qkit.analysis.semiconductor.main.equalize_length import make_len_eq


class PlotterPlungerSweep(SemiFigure):
    """Plots plunger gate sweeps and (if given) overlays tangent.
    """
   
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fit_params = None
        self.savename = "plunger_sweep"
        self.color = "r"
        self.x_limits = []

    def plot(self, settings, settings_plunger, data_in, nodes):
        data = make_len_eq(data_in, nodes)
        y_axis_factor = 1000  #scales y axis to mV
        self.ax.set_title("Plunger Gate Sweep")
        self.ax.set_xlabel("Voltage (V)")
        self.ax.set_ylabel("Lock-in Voltage (mV)")
        self.data_x = data[nodes[0]]
        self.data_y = data[nodes[1]]*y_axis_factor
        if len(self.x_limits) == 2:
            self.ax.set_xlim(self.x_limits)
        self.ax.plot(self.data_x, self.data_y)
        if self.fit_params != None:
            poly1d_fn = np.poly1d(self.fit_params["fit_coef"])
            self.data_x_fit = self.data_x[self.fit_params["index_begin"] : self.fit_params["index_end"]]
            self.ax.plot(self.data_x_fit, poly1d_fn(self.data_x_fit)*y_axis_factor, self.color, 
            label=f"slope: {self.fit_params['fit_coef'][0]*y_axis_factor:.0f} mV/V")
            self.ax.legend()
        plt.savefig(create_saving_path(settings_plunger, self.savename, self.save_as), dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.savefig(create_saving_path(settings, self.savename, self.save_as), dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show() 
        self.close_delete()