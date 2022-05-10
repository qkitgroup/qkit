#%%
from qkit.analysis.semiconductor.loaders.Loaderh5 import Loaderh5
from qkit.analysis.semiconductor.main.loading import print_nodes
from qkit.analysis.semiconductor.analyzers.AnalyzerTimetraceSpectralNoiseDensity import AnalyzerTimetraceSpectralNoiseDensity
from qkit.analysis.semiconductor.plotters.PlotterTimetraceSpectralNoiseDensity import PlotterTimetraceSpectralNoiseDensity
from qkit.analysis.semiconductor.analyzers.AnalyzerPeakTracker_Daniel import AnalyzerPeakTracker
from qkit.analysis.semiconductor.analyzers.AnalyzerTimetraceJumps import AnalyzerTimetraceJumps
from qkit.analysis.semiconductor.plotters.PlotterPlungerTimetrace3D import PlotterPlungerTimetrace3D
from qkit.analysis.semiconductor.plotters.PlotterPlungerTraceFit import PlotterPlungerTraceFit
from qkit.analysis.semiconductor.plotters.PlotterPlungerTraceTimestampsDifference import PlotterPlungerTraceTimestampsDifference
from qkit.analysis.semiconductor.plotters.PlotterTimetraceJumpsHistogram import PlotterTimetraceJumpsHistogram
from qkit.analysis.semiconductor.main.SlicerPlungerTimetrace import SlicerPlungerTimetrace
from qkit.analysis.semiconductor.loaders.Loader_spectrum_np import Loader_spectrum_np
from qkit.analysis.semiconductor.savers.Saver_spectrum_np import Saver_spectrum_np

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
print_nodes(data)

#%% Define nodes
node_timestamp = "demod0.timestamp0"
node_x = "demod0.x0"
node_y = "demod0.y0"
node_r = "demod0.r0"

gates = "gates_6_16"


#%% Plot Data
plotter = PlotterPlungerTimetrace3D()
plotter.max_cond = 10
plotter.plot(settings, data, [node_timestamp, gates , node_r])

#%% Slice Data and Plot
slicer = SlicerPlungerTimetrace()
slicer.beginning, slicer.ending = 0, 6 # in hours
data_sliced = slicer.slice(data, [node_timestamp, gates , node_r])

plotter = PlotterPlungerTimetrace3D()
plotter.max_cond = 10
plotter.savename = "plunger_timetrace_sliced"
plotter.plot(settings, data_sliced, [node_timestamp, gates , node_r])

#%% Analyze  Data
analyzer = AnalyzerPeakTracker()
analyzer.intervall1 = 0.1
analyzer.intervall2 = 0.05
analyzer.peak_voltage = 0.725
analyzer.analyze( data_sliced, [node_timestamp, gates , node_r])

#%% Plot Analyzed Data
plotter = PlotterPlungerTimetrace3D()
plotter.point_size = 0.5
plotter.marker_shape = "or"
plotter.max_cond = 10
plotter.savename = "plunger_timetrace_sliced_fitted"
plotter.plot(settings, data_sliced, [node_timestamp, gates , node_r])

#%% Plot time difference between consecutive plunger sweeps 
plotter = PlotterPlungerTraceTimestampsDifference()
plotter.plot(settings, data_sliced)


#%% Plot a single plunger trace
plotter = PlotterPlungerTraceFit()
plotter.trace_num = 10
plotter.plot(settings, data_sliced,  [gates , node_r])



#%% Analyze Jumps of Timetrace
analyzer_jumps = AnalyzerTimetraceJumps()
analyzer_jumps.bin_count = 50
jumps_hist = analyzer_jumps.analyze_difference(data_sliced, ["peaks_value", node_timestamp])

plotter_hist = PlotterTimetraceJumpsHistogram()
plotter_hist.marker_size = 8
plotter_hist.plot(settings, jumps_hist)



#%% SND
sampling_f = 1/data_sliced["avg_sweep_time"]  
analyzer_SND = AnalyzerTimetraceSpectralNoiseDensity()
spectral_result = analyzer_SND.analyze(sampling_f, data_sliced, ["peaks_plunger_V"]) # classic Fourier

saver = Saver_spectrum_np() # Saving Data
saver.save(settings, spectral_result, ending="Fourier")

analyzer_SND.segment_length = 50 # length of each segment for Welch
spectral_result_welch = analyzer_SND.analyze_welch(sampling_f, data_sliced, ["peaks_plunger_V"]) # Welch's method

saver = Saver_spectrum_np() # Saving Data
saver.save(settings, spectral_result_welch, ending="Welch")

#%% 
plotter_SND = PlotterTimetraceSpectralNoiseDensity()
plotter.savename = "SND"
plotter_SND.plot(settings, spectral_result) # classic Fourier

plotter_SND = PlotterTimetraceSpectralNoiseDensity()
plotter.savename = "SND_welch"
plotter_SND.plot(settings, spectral_result_welch) # Welch's method



