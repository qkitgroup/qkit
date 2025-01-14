#%%
from qkit.analysis.semiconductor.loaders.Loaderh5 import H5filemerger
from qkit.analysis.semiconductor.plotters.PlotterAccumulation import PlotterAccumulation
from qkit.analysis.semiconductor.main.equalize_length import make_len_eq

#%%
paths=['/home/ws/zz8772/Daten/20220427/143215_1D_AccumulationwithTopgateonly/143215_1D_AccumulationwithTopgateonly.h5',\
       '/home/ws/zz8772/Daten/20220427/143334_1D_AccumulationwithTopgateonly/143334_1D_AccumulationwithTopgateonly.h5',\
       '/home/ws/zz8772/Daten/20220427/151451_1D_AccumulationwithTopgateonly/151451_1D_AccumulationwithTopgateonly.h5',\
       '/home/ws/zz8772/Daten/20220427/151615_1D_AccumulationwithTopgateonly/151615_1D_AccumulationwithTopgateonly.h5',\
       '/home/ws/zz8772/Daten/20220427/151715_1D_AccumulationwithTopgateonly/151715_1D_AccumulationwithTopgateonly.h5',\
       '/home/ws/zz8772/Daten/20220427/151746_1D_AccumulationwithTopgateonly/151746_1D_AccumulationwithTopgateonly.h5',\
       '/home/ws/zz8772/Daten/20220427/151818_1D_AccumulationwithTopgateonly/151818_1D_AccumulationwithTopgateonly.h5',\
       '/home/ws/zz8772/Daten/20220427/151853_1D_AccumulationwithTopgateonly/151853_1D_AccumulationwithTopgateonly.h5',\
       '/home/ws/zz8772/Daten/20220427/151937_1D_AccumulationwithTopgateonly/151937_1D_AccumulationwithTopgateonly.h5',\
       '/home/ws/zz8772/Daten/20220427/153830_1D_AccumulationwithTopgateonly/153830_1D_AccumulationwithTopgateonly.h5',\
       '/home/ws/zz8772/Daten/20220427/153857_1D_AccumulationwithTopgateonly/153857_1D_AccumulationwithTopgateonly.h5',\
       '/home/ws/zz8772/Daten/20220427/153935_1D_AccumulationwithTopgateonly/153935_1D_AccumulationwithTopgateonly.h5',\
       '/home/ws/zz8772/Daten/20220428/134527_1D_AccumulationwithTopgateonly/134527_1D_AccumulationwithTopgateonly.h5',\
       '/home/ws/zz8772/Daten/20220428/134642_1D_AccumulationwithTopgateonly/134642_1D_AccumulationwithTopgateonly.h5',\
       '/home/ws/zz8772/Daten/20220428/134733_1D_AccumulationwithTopgateonly/134733_1D_AccumulationwithTopgateonly.h5']

settings = {"file_info" : {
                "absolute_path" : "/home/ws/zz8772/Daten/",
                "filetype" : ".h5",
                "date_stamp" : "20220427",
                "filename" : "151451_1D_AccumulationwithTopgateonly",
                "savepath" : "analysis/",
                "analysis" : "accumulation"},
            "meas_params" : {
                "measurement_amp" : 200e-6,
                "voltage_divider" : 3,
                "IVgain" : 1e8,
                "in_line_R": 42e3}
            }

###In settings, you can take the info of any of the files in paths (it should be identical). Remember that the generated 
###.png file of the plot will be saved in the analysis folder within the timestamp folder of the file chosen for 'settings'.
nodes = ['gate_4', 'demod0.r0']

print(H5filemerger.__doc__)
merger = H5filemerger()
merger.add_paths(paths)
data_dict = merger.merge()
data = make_len_eq(data_dict, nodes)

#%% Plot only one trace
plotter = PlotterAccumulation()
plotter.marker = "."
plotter.gatename = "Topgate (V)"
plotter.plot_one_trace(settings, data, nodes)

# %%
