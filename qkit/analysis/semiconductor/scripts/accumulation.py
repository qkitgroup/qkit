#%%
from qkit.analysis.semiconductor.loaders.Loaderh5 import Loaderh5
from qkit.analysis.semiconductor.plotters.PlotterAccumulation import  PlotterAccumulation
from qkit.analysis.semiconductor.main.loading import print_nodes

settings = {"file_info" : {
                "absolute_path" : "/home/ws/oc0612/SEMICONDUCTOR/analysis/bias-cooling/-3V/cooldown_1/",
                "filetype" : ".h5",
                "date_stamp" : "20220104",
                "filename" : "094628_1D_Accumulate_with_All_Gates",
                "savepath" : "analysis/",
                "analysis" : "accumulation"},
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
node_0_timestamp = "demod0&4.timestamp0"
node_0_x = "demod0.x0"
node_0_y = "demod0.y0"
node_0_r = "demod0.r0"

node_4_timestamp = "demod0&4.timestamp4"
node_4_x = "demod4.x4"
node_4_y = "demod4.y4"
node_4_r = "demod4.r4"

gates = "gates_4_5_6_7_9_10_11_12_13_14_15_16_17_18_19_20_21_22_23"

# Rotate Data??? 

#%% Plot many traces
plotter = PlotterAccumulation()
plotter.marker = "."
plotter.add_trace(settings, data, [gates, node_0_r], label_id="left")
plotter.add_trace(settings, data, [gates, node_4_r], label_id="right")
plotter.gatename = "All gates"
plotter.plot_all(settings)


#%% Plot only one trace
plotter = PlotterAccumulation()
plotter.marker = "."
plotter.plot_one_trace(settings, data, [gates, node_4_r])
# %%
