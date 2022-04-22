#%%
from qkit.analysis.semiconductor.loaders import Loaderh5
from qkit.analysis.semiconductor.analyzers import AnalyzerTimetraceSpectralNoiseDensity, AnalyzerPeakTracker_Daniel
from qkit.analysis.semiconductor.plotters import PlotterTimetraceSpectralNoiseDensity, PlotterPlungerTimetrace3D, PlotterPlungerTraceFit, PlotterPlungerTraceTimestampsDifference
from qkit.analysis.semiconductor.main import SlicerPlungerTimetrace

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



#%% Load Timetrace
loader = Loaderh5()
data = loader.load(settings)
print("\nData nodes:\n" + str([key for key in data.keys()]))

#%% Plot Data
plotter = PlotterPlungerTimetrace3D()
plotter.max_cond = 10
plotter.plot(settings, data, ["demod0.timestamp0", "gates_6_16", "demod0.r0"])

#%% Slice Data and Plot
slicer = SlicerPlungerTimetrace()
slicer.beginning, slicer.ending = 0, 6 # in hours
data_sliced = slicer.slice(data, ["demod0.timestamp0", "gates_6_16", "demod0.r0"])

plotter = PlotterPlungerTimetrace3D()
plotter.max_cond = 10
plotter.savename = "plunger_timetrace_sliced"
plotter.plot(settings, data_sliced, ["demod0.timestamp0", "gates_6_16", "demod0.r0"])

#%% Analyze  Data
analyzer = AnalyzerPeakTracker_Daniel()
analyzer.intervall1 = 0.1
analyzer.intervall2 = 0.05
analyzer.analyze( data_sliced, ["demod0.timestamp0", "gates_6_16", "demod0.r0"], peak_V=0.725)

#%% Plot Analyzed Data
plotter = PlotterPlungerTimetrace3D()
plotter.point_size = 0.5
plotter.marker_shape = "or"
plotter.max_cond = 10
plotter.savename = "plunger_timetrace_sliced_fitted"
plotter.plot(settings, data_sliced, ["demod0.timestamp0", "gates_6_16", "demod0.r0"])

#%% Plot time difference between consecutive plunger sweeps 
plotter = PlotterPlungerTraceTimestampsDifference()
plotter.plot(settings, data_sliced)


#%% Plot a single plunger trace
plotter = PlotterPlungerTraceFit()
plotter.plot(settings, data_sliced,  ["gates_6_16", "demod0.r0"],  trace_num=10)


#%% SND
sampling_f = 1/data_sliced["avg_sweep_time"]  
analyzer_SND = AnalyzerTimetraceSpectralNoiseDensity()
spectral_result = analyzer_SND.analyze(sampling_f, data_sliced, ["peaks_plunger_V"]) # classic Fourier
analyzer_SND.segment_length = 50 # length of each segment for Welch
spectral_result_welch = analyzer_SND.analyze_welch(sampling_f, data_sliced, ["peaks_plunger_V"]) # Welch's method

#%% 
plotter_SND = PlotterTimetraceSpectralNoiseDensity()
plotter.savename = "SND"
plotter_SND.plot(settings, spectral_result) # classic Fourier

plotter_SND = PlotterTimetraceSpectralNoiseDensity()
plotter.savename = "SND_welch"
plotter_SND.plot(settings, spectral_result_welch) # Welch's method



# %%
