#%%
from qkit.analysis.semiconductor.loaders import LoaderExcel 
from qkit.analysis.semiconductor.plotters import PlotterBiascoolingAccumulation
from qkit.analysis.semiconductor.plotters.PlotterExcel import PlotterBiascoolingDifferenceBarrierGates, PlotterBiascoolingDifferenceTopgateGates, PlotterBiascoolingMinimalTopgate, PlotterBiascoolingDifferenceTopgateBarriers, PlotterBiascoolingDifferenceTopgateAccumulation 


#%%
path = "/V/GroupWernsdorfer/SEMICONDUCTOR_SYSTEMS/Bias_cooling_Project/Data_overview_P35_B1.xlsx"
ignored_rows = 4
sample_name = "P35_B1"
loader = LoaderExcel()
data = loader.load(path, ignored_rows, sample_name)

room_temp_cooldown = "yes" # decide if all data or only room temp cooldowns with "yes" or "both"

#%%
plotter = PlotterBiascoolingAccumulation()
plotter.plot(data, shape="*", size=300, transparency=0.8)

#%%
plotter = PlotterBiascoolingMinimalTopgate()
plotter.plot(data, shape="*", size=300, transparency=0.8, RT=room_temp_cooldown)


#%%
plotter = PlotterBiascoolingDifferenceTopgateGates()
plotter.plot(data, shape="*", size=300, transparency=0.8, RT=room_temp_cooldown)


#%%
plotter = PlotterBiascoolingDifferenceBarrierGates()
plotter.plot(data, shape="*", size=300, transparency=0.8, RT=room_temp_cooldown)


# %%
plotter = PlotterBiascoolingDifferenceTopgateBarriers()
plotter.plot(data, shape="*", size=300, transparency=0.8, RT=room_temp_cooldown)



# %%
plotter = PlotterBiascoolingDifferenceTopgateAccumulation()
plotter.plot(data, shape="*", size=300, transparency=0.8, RT=room_temp_cooldown)
# %%
