import matplotlib.pyplot as plt

from qkit.analysis.semiconductor.main.pre_formatted_figures import SemiFigure
from qkit.analysis.semiconductor.main.saving import create_saving_path

class PlotterBiascoolingAccumulation(SemiFigure):
    """Plots Accumulation voltages over bias cooling voltage.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.savename="accumulations_biascooling"
        self.shape="^"
        self.size=100
        self.transparency=1

    def plot(self, settings, data):
        self.ax.set_title("Accumulation Voltages depending on Bias Cooling")
        self.ax.set_xlabel("Bias Cooling Voltage (V)")
        self.ax.set_ylabel("Accumulation Voltage (V)")
        for cooldown in data:
            self.ax.scatter(cooldown["bias_V"], cooldown["first_acc_V"], marker=self.shape, s=self.size, alpha=self.transparency)
        plt.grid()
        plt.savefig(create_saving_path(settings, self.savename, self.save_as), dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show() 
        self.close_delete()

