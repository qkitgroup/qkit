#%%
from qkit.analysis.semiconductor.basic_functionality import PlotterSemiconInit
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
import numpy as np


# %%
data = []
path = "/V/GroupWernsdorfer/SEMICONDUCTOR_SYSTEMS/Bias_cooling_Project/Data_overview_P35_B1.xlsx"
ignored_rows = 4
df = pd.read_excel(path, skiprows=np.arange(ignored_rows))

#%%
for measurement in range(len(df["Biascooling (V)"].to_numpy())):
    data.append({"bias_V" : df["Biascooling (V)"].to_numpy()[measurement],
                "first_acc_V" : df["Left demod0. gates (V)"].to_numpy()[measurement],
                "date" : "x",
                "RT cooldown" : df["RT cooldown"].to_numpy()[measurement],
                "sample" : "P35_B1",
                "second_acc_V" : "x",
                "SET" : "x"
                }) 


#%%
class PlotterBiascoolingAccumulation(PlotterSemiconInit):
    """Plots Accumulation voltages over bias cooling voltage.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def plot(self, data, savename="accumulations_biascooling", shape="^", size=100, transparency=1):
        self.ax.set_title("Accumulation Voltages depending on Bias Cooling")
        self.ax.set_xlabel("Bias Cooling Voltage (V)")
        self.ax.set_ylabel("Accumulation Voltage (V)")
        for cooldown in data:
            if cooldown["RT cooldown"] == "y":
                self.ax.scatter(cooldown["bias_V"], cooldown["first_acc_V"], marker=shape, s=size, alpha=transparency, color="r")
            elif cooldown["RT cooldown"] == "n":
                self.ax.scatter(cooldown["bias_V"], cooldown["first_acc_V"], marker=shape, s=size, alpha=transparency, color="b")
            else:
                self.ax.scatter(cooldown["bias_V"], cooldown["first_acc_V"], marker=shape, s=size, alpha=transparency, color="c")
        plt.grid()
        red_patch = mpatches.Patch(color='red', label='Cooldown from room temperature')
        blue_patch = mpatches.Patch(color='blue', label='Cooldown from unknown temperature')
        plt.legend(handles=[blue_patch, red_patch])
        plt.savefig(f"{savename}.png", dpi=self.set_dpi, bbox_inches=self.set_bbox_inches)
        plt.show() 
        self.close_delete()


#%%
plotter = PlotterBiascoolingAccumulation()
plotter.plot(data, shape="*", size=300, transparency=1)

# 
# %%
