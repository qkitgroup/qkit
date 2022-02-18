#%%
import numpy as np
import copy
from qkit.analysis.semiconductor.basic_functionality import Loaderh5
from qkit.analysis.semiconductor.timetrace_functionality import AnalyzerTimetraceSpecralNoiseDensity, PlotterTimetraceSpectralNoiseDensity
from qkit.analysis.semiconductor.plunger_timetrace_functionality import PlotterPlungerTimetrace3D, SlicePlungerTimetrace, AnalyzerPeakTracker, PlotterPlungerTraceFit, PlotterPlungerTraceTimestampsDiff

settings = {"file_info" : {
                "absolute_path" : "/home/ws/oc0612/SEMICONDUCTOR/analysis/bias-cooling/test/",
                "filetype" : ".h5",
                "date_stamp" : "20220214",
                "filename" : "184856_2D_Peak_tracking",
                "savepath" : "analysis/",
                "analysis" : "plunger_sweep_timetrace"},
            "meas_params" : {
                "measurement_amp" : 100e-6,
                "voltage_divider" : 3,
                "IVgain" : 1e8,
                "in_line_R": 40e3}
            }


#settings2 = copy.deepcopy(settings) 
#settings2["file_info"]["filename"] = "152849_2D_Timetrace_PlungerGateSweep"

#%% Load Timetrace
loader = Loaderh5()
data = loader.load(settings)
print("\nData nodes:\n" + str([key for key in data.keys()]))

#%% Plot Data
plotter = PlotterPlungerTimetrace3D()
plotter.plot(settings, data, ["demod0.timestamp0", "gates_6_16", "demod0.r0"], max_cond=10)

#%% Slice Data and Plot
slicer = SlicePlungerTimetrace()
begin, end = 0, 6 # in hours
data_sliced = slicer.slice(data, ["demod0.timestamp0", "gates_6_16", "demod0.r0"], beginning=begin, ending=end)

plotter = PlotterPlungerTimetrace3D()
plotter.plot(settings, data_sliced, ["demod0.timestamp0", "gates_6_16", "demod0.r0"], max_cond=10, savename="plunger_timetrace_sliced")

#%% Analyze  Data
analyzer = AnalyzerPeakTracker()
analyzer.analyze( data_sliced, ["demod0.timestamp0", "gates_6_16", "demod0.r0"], peak_V=0.725, intervall1=0.1, intervall2=0.05)

#%% Plot Analyzed Data
plotter = PlotterPlungerTimetrace3D()
plotter.plot(settings, data_sliced, ["demod0.timestamp0", "gates_6_16", "demod0.r0"], point_size=0.5, marker_shape="or", max_cond=10, savename="plunger_timetrace_sliced_fitted")

#%% Plot time difference between consecutive plunger sweeps 
plotter = PlotterPlungerTraceTimestampsDiff()
plotter.plot(settings, data_sliced)


#%% Plot a single plunger trace
plotter = PlotterPlungerTraceFit()
plotter.plot(settings, data_sliced,  ["gates_6_16", "demod0.r0"],  trace_num=10)


#%% SND
sampling_f = 1/data_sliced["avg_sweep_time"]  
analyzer_SND = AnalyzerTimetraceSpecralNoiseDensity()
spectral_result = analyzer_SND.analyze(sampling_f, data_sliced, ["peaks_plunger_V"]) # classic Fourier
segment_length = 50 # length of each segment for Welch
spectral_result_welch = analyzer_SND.analyze_welch(sampling_f, data_sliced, ["peaks_plunger_V"], segment_length) # Welch's method

#%% 
plotter_SND = PlotterTimetraceSpectralNoiseDensity()
plotter_SND.plot(settings, spectral_result, savename="SND") # classic Fourier

plotter_SND = PlotterTimetraceSpectralNoiseDensity()
plotter_SND.plot(settings, spectral_result_welch, savename="SND_welch") # Welch's method



# %%
