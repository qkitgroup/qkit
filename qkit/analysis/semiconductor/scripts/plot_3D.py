#%%
from qkit.analysis.semiconductor.loaders.Loaderh5 import Loaderh5
from qkit.analysis.semiconductor.plotters.Plotter3D import Plotter3D
from qkit.analysis.semiconductor.main.loading import print_nodes


settings = {"file_info" : {
                "absolute_path" : "/home/ws/oc0612/SEMICONDUCTOR/analysis/bias-cooling/0V/cooldown_1/",
                "filetype" : ".h5",
                "date_stamp" : "20220112",
                "filename" : "223439_2D_2D_Sweeps_both_SETs",
                "savepath" : "analysis/",
                "analysis" : "3D plot"},
            "meas_params" : {
                "measurement_amp" : 200e-6,
                "voltage_divider" : 3,
                "IVgain" : 1e8,
                "in_line_R": 42e3}
            }


#%% Load Timetrace
loader = Loaderh5()
data = loader.load(settings)
print_nodes(data)


#%% Define nodes
node_0_x = "gates_5_15"
node_0_y = "gates_7_17"
node_0_r = "demod0.r0"

node_4_x = "gates_5_15"
node_4_y = "gates_7_17"
node_4_r = "demod4.r4"


#%% Plot 3D data
plotter = Plotter3D()
plotter.colorcode = "seismic" # checkout viridis, seismic, PiYG, plasma, gist_rainbow
plotter.savename = "Plot3D_1"
plotter.conductance = True
plotter.min = 0 
plotter.max = None # standart is None
plotter.plot(settings, data, [node_0_x, node_0_y, node_0_r], axis_labels=["Gate 5", "Gate 15"])


#%%
plotter = Plotter3D()
plotter.colorcode = "viridis"
plotter.savename = "Plot3D_2"
plotter.conductance = True
plotter.min = 0 
plotter.max = None
plotter.plot(settings, data, [node_4_x, node_4_y, node_4_r], axis_labels=["Gate 10", "Gate 11"])
# %%
