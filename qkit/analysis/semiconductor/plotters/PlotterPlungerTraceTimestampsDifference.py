import numpy as np
import matplotlib.pyplot as plt


from qkit.analysis.semiconductor.main.pre_formatted_figures import SemiFigure
from qkit.analysis.semiconductor.main.saving import create_saving_path


class PlotterPlungerTraceTimestampsDifference(SemiFigure):
    """Plots the time difference between consecutive plunger traces.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def plot(self, settings, data, savename="timestamps_diff" ):
        self.ax.set_title("Length of Plunger Sweeps")
        self.ax.set_xlabel("Sweep Number")
        self.ax.set_ylabel("Difference between Sweeps (s)")
        x_vals = np.arange(1, len(data["timestamps_diff"])+1)
        self.ax.plot(x_vals, data["timestamps_diff"])
        self.ax.plot(x_vals, [data["avg_sweep_time"]]*len(x_vals), "-r", label="average")
        plt.legend()
        plt.savefig(f"{create_saving_path(settings)}/{savename}.png", dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show()
        self.close_delete()