import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from qkit.analysis.semiconductor.main.pre_formatted_figures import SemiFigure

class PlotterBiascoolingAccumulation(SemiFigure):
    """Plots Accumulation voltages over bias cooling voltage.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.savename = "accumulations_biascooling"
        self.shape = "*"
        self.size = 500
        self.transparency = 1

    def plot(self, data):
        self.ax.set_title("Accumulation Voltages depending on Bias Cooling")
        self.ax.set_xlabel("Bias Cooling Voltage (V)")
        self.ax.set_ylabel("Accumulation Voltage (V)")
        for sample in data:
            for cooldown in data[sample]:
                self.ax.scatter(cooldown["bias_V"], cooldown["first_acc_V"], marker=self.shape, s=self.size, alpha=self.transparency)
        plt.grid()
        savepath = self.savename + self.save_as
        plt.savefig(savepath, dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show() 
        self.close_delete()


class PlotterBiascoolingAccumulationColors(SemiFigure):
    """Plots Accumulation voltages over bias cooling voltage.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.savename = "accumulations_biascooling_color"
        self.shape = "*"
        self.size = 500
        self.transparency = 1

    def plot(self, data, savename="accumulations_biascooling"):
        self.ax.set_title("Accumulation Voltages depending on Bias Cooling")
        self.ax.set_xlabel("Bias Cooling Voltage (V)")
        self.ax.set_ylabel("Accumulation Voltage (V)")
        plt.grid()

        color_palette = ["r", "b", "k", "g"]
        i = 0

        for sample in data:
            color_plot = color_palette[i]
            for cooldown in data[sample]:
                if cooldown["RT_cooldown"] == "y" or cooldown["RT_cooldown"] == "new":
                    self.ax.scatter(cooldown["bias_V"], cooldown["first_acc_V"], marker="*", s=self.size, alpha=self.transparency, color=color_plot)
                elif cooldown["RT_cooldown"] == "n":
                    self.ax.scatter(cooldown["bias_V"], cooldown["first_acc_V"], marker="3", s=self.size, alpha=self.transparency, color=color_plot)
                else:
                    self.ax.scatter(cooldown["bias_V"], cooldown["first_acc_V"], marker="s", s=self.size, alpha=self.transparency, color=color_plot)
            i+=1

        red_patch = mpatches.Patch(color='red', label='Sample B1')
        blue_patch = mpatches.Patch(color='blue', label='Sample B4')
        plt.legend(handles=[ red_patch, blue_patch])
        plt.savefig(f"{savename}.png", dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show() 
        self.close_delete()