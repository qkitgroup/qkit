#%%
from qkit.analysis.semiconductor.loaders.LoaderExcel import LoaderExcel
from qkit.analysis.semiconductor.plotters.PlotterBiascoolingAccumulation import PlotterBiascoolingAccumulation, PlotterBiascoolingAccumulationColors
from qkit.analysis.semiconductor.plotters.PlotterExcel import PlotterBiascoolingDifferenceBarrierGates, PlotterBiascoolingDifferenceTopgateGates, PlotterBiascoolingMinimalTopgate, PlotterBiascoolingDifferenceTopgateBarriers, PlotterBiascoolingDifferenceTopgateAccumulation 


#%%
path = "/V/GroupWernsdorfer/SEMICONDUCTOR_SYSTEMS/Bias_cooling_Project/Data_overview_P35_B1.xlsx"
ignored_rows = 4
sample_name = "P35_B1"
loader = LoaderExcel()
data_B1 = loader.load(path, ignored_rows, sample_name)


#%%
path = "/V/GroupWernsdorfer/SEMICONDUCTOR_SYSTEMS/Bias_cooling_Project/Data_overview_P35_B4.xlsx"
ignored_rows = 4
sample_name = "P35_B4"
loader = LoaderExcel()
data_B4 = loader.load(path, ignored_rows, sample_name)


#%%
path = "/V/GroupWernsdorfer/SEMICONDUCTOR_SYSTEMS/Bias_cooling_Project/Data_overview_P35_B3.xlsx"
ignored_rows = 4
sample_name = "P35_B3"
loader = LoaderExcel()
data_B3 = loader.load(path, ignored_rows, sample_name)




#%%
data = dict(**data_B1, **data_B4, **data_B3)

#plotter = PlotterBiascoolingAccumulation()
plotter = PlotterBiascoolingAccumulationColors()
plotter.cooldown_perfect = True
plotter.shape = "*"
plotter.size = 200
plotter.transparency = 1
plotter.plot(data)











#####################################################

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

# %%
