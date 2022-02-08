#%%
from qkit.analysis.semiconductor.basic_functionality import Loaderh5, PlotterAccumulation

settings = {"file_info" : {
                "absolute_path" : "/home/ws/oc0612/SEMICONDUCTOR/analysis/bias-cooling/-3V/cooldown_1/",
                "filetype" : ".h5",
                "date_stamp" : "20220104",
                "filename" : "094628_1D_Accumulate_with_All_Gates",
                "savepath" : "analysis/",
                "analysis" : "accumulation"},
            "meas_params" : {
                "measurement_amp" : 100e-6,
                "voltage_divider" : 3,
                "IVgain" : 1e8,
                "in_line_R": 40e3}
            }



#%% Load Timetrace
loader = Loaderh5()
data = loader.load(settings)
print("\nData nodes:\n" + str([key for key in data.keys()]))

#%% Plot many traces
plotter = PlotterAccumulation()
plotter.add_trace(settings, data, ["gates_4_5_6_7_9_10_11_12_13_14_15_16_17_18_19_20_21_22_23", "demod0.r0"], label_id="left")
plotter.add_trace(settings, data, ["gates_4_5_6_7_9_10_11_12_13_14_15_16_17_18_19_20_21_22_23", "demod4.r4"], label_id="right")
plotter.plot_all(settings, gatename="All gates")


#%% Plot only one trace
plotter = PlotterAccumulation()
plotter.plot_one_trace(settings, data, ["gates_4_5_6_7_9_10_11_12_13_14_15_16_17_18_19_20_21_22_23", "demod4.r4"])
# %%
