#%%
from qkit.analysis.semiconductor.basic_functionality import PlotterBiascoolingAccumulation
import pandas as pd
import numpy as np


# %%
data = []
path = "/V/GroupWernsdorfer/SEMICONDUCTOR_SYSTEMS/Bias_cooling_Project/test_readout/Data_overview_P35_B1.xlsx"
ignored_rows = 4
df = pd.read_excel(path, skiprows=np.arange(ignored_rows))

#%%
for measurement in range(len(df["Biascooling (V)"].to_numpy())):
    data.append({"bias_V" : df["Biascooling (V)"].to_numpy()[measurement],
                "first_acc_V" : df["Left demod0. gates (V)"].to_numpy()[measurement],
                "date" : "x",
                "sample" : "P35_B1",
                "second_acc_V" : "x",
                "SET" : "x"
                }) 



#%%
plotter = PlotterBiascoolingAccumulation()
plotter.plot(data, shape="*", size=500, transparency=1)

# 