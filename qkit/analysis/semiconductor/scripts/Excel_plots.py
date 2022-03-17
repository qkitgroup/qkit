#%%
from qkit.analysis.semiconductor.excel_basics import LoaderExcel, PlotterBiascoolingAccumulation, PlotterBiascoolingDifferenceBarrierGates, PlotterBiascoolingDifferenceTopgateGates, PlotterBiascoolingMinimalTopgate 


#%%
path = "/V/GroupWernsdorfer/SEMICONDUCTOR_SYSTEMS/Bias_cooling_Project/Data_overview_P35_B1.xlsx"
ignored_rows = 4
loader = LoaderExcel()
data = loader.load(path, ignored_rows)

#%%
plotter = PlotterBiascoolingAccumulation()
plotter.plot(data, shape="*", size=300, transparency=0.8)

#%%
plotter = PlotterBiascoolingMinimalTopgate()
plotter.plot(data, shape="*", size=300, transparency=0.8)


#%%
plotter = PlotterBiascoolingDifferenceTopgateGates()
plotter.plot(data, shape="*", size=300, transparency=0.8)


#%%
plotter = PlotterBiascoolingDifferenceBarrierGates()
plotter.plot(data, shape="*", size=300, transparency=0.8)

