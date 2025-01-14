#%%
import copy
from qkit.analysis.semiconductor.loaders.Loaderh5 import Loaderh5
from qkit.analysis.semiconductor.main.loading import print_nodes
from qkit.analysis.semiconductor.analyzers.AnalyzerPlungerSweep import AnalyzerPlungerSweep
from qkit.analysis.semiconductor.analyzers.AnalyzerTimetraceSpectralNoiseDensity import AnalyzerTimetraceSpectralNoiseDensity
from qkit.analysis.semiconductor.plotters.PlotterTimetraceSpectralNoiseDensity import PlotterTimetraceSpectralNoiseDensity
from qkit.analysis.semiconductor.plotters.PlotterTimetracePeakTrackingSND import PlotterTimetracePeakTrackingSND
from qkit.analysis.semiconductor.plotters.PlotterDifferenceTimetraceSpectralNoiseDensity import PlotterDifferenceTimetraceSpectralNoiseDensity
from qkit.analysis.semiconductor.plotters.PlotterPlungerSweep import PlotterPlungerSweep
from qkit.analysis.semiconductor.plotters.PlotterTimetraceConductance import PlotterTimetraceConductance
from qkit.analysis.semiconductor.plotters.PlotterTimetrace import PlotterTimetrace
from qkit.analysis.semiconductor.plotters.PlotterTimetracePhase import PlotterTimetracePhase
from qkit.analysis.semiconductor.main.rotate_phase import rotate_phase
from qkit.analysis.semiconductor.main.SlicerTimetrace import SlicerTimetrace
from qkit.analysis.semiconductor.loaders.Loader_spectrum_np import Loader_spectrum_np
from qkit.analysis.semiconductor.savers.Saver_spectrum_np import Saver_spectrum_np

loader = Loader_spectrum_np()

#%%
settings_timetrace = {"file_info" : {
                "absolute_path" : "/home/ws/oc0612/SEMICONDUCTOR/analysis/bias-cooling/-0.5V/",
                "filetype" : ".h5",
                "date_stamp" : "20220128",
                "filename" : "175941_1D_measurement_time",
                "savepath" : "analysis/",
                "analysis" : "noise_timetrace"},
            "meas_params" : {
                "measurement_amp" : 200e-6,
                "voltage_divider" : 3,
                "IVgain" : 1e8,
                "in_line_R": 42e3,
                "sampling_rate" : 13732.91015625}
            }


#%%
settings_peak = {"file_info" : {
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

#%%
settings_background = {"file_info" : {
                "absolute_path" : "/home/ws/oc0612/SEMICONDUCTOR/analysis/bias-cooling/background/",
                "filetype" : ".h5",
                "date_stamp" : "20220427",
                "filename" : "143444_1D_measurement_time",
                "savepath" : "analysis/",
                "analysis" : "noise_timetrace"},
            "meas_params" : {
                "measurement_amp" : 200e-6,
                "voltage_divider" : 3,
                "IVgain" : 1e8,
                "in_line_R": 42e3,
                "sampling_rate" : 13732.91015625}
            }

#%%
settings_background_long = {"file_info" : {
                "absolute_path" : "/home/ws/oc0612/SEMICONDUCTOR/analysis/bias-cooling/background/",
                "filetype" : ".h5",
                "date_stamp" : "20220427",
                "filename" : "154538_1D_measurement_time",
                "savepath" : "analysis/",
                "analysis" : "noise_timetrace"},
            "meas_params" : {
                "measurement_amp" : 200e-6,
                "voltage_divider" : 3,
                "IVgain" : 1e8,
                "in_line_R": 42e3,
                "sampling_rate" : 858.306884765625}
            }



#%% Loading timetrace spectrum 
(data_timetrace_Fourier, fit_params_plunger_timetrace, power_fit_params_timetrace_Fourier) = loader.load(settings_timetrace, ending="Fourier")
(data_timetrace_Welch, fit_params_plunger_timetrace, power_fit_params_timetrace_Welch) = loader.load(settings_timetrace, ending="Welch")

#%% Loading peak tracking spectrum 
(data_peak_Fourier, _, _) = loader.load(settings_peak, ending="Fourier")
(data_peak_Welch, _, _) = loader.load(settings_peak, ending="Welch")

#%% Loading background spectrum 
(data_background_Fourier, _, power_fit_params_background_Fourier) = loader.load(settings_background, ending="Fourier")
(data_background_Welch, _, power_fit_params_background_Welch) = loader.load(settings_background, ending="Welch")

#%% Loading long 5h background spectrum 
(data_background_long_Fourier, _, power_fit_params_background_long_Fourier) = loader.load(settings_background_long, ending="Fourier")
(data_background_long_Welch, _, power_fit_params_background_long_Welch) = loader.load(settings_background_long, ending="Welch")





#%% Plotting Timetrace
plotter_SND = PlotterTimetraceSpectralNoiseDensity()
plotter_SND.fit_params_plunger = fit_params_plunger_timetrace
plotter_SND.fit_vals = power_fit_params_timetrace_Fourier
plotter_SND.savename = "SND_fourier"
plotter_SND.plot(settings_timetrace, data_timetrace_Fourier)

plotter_SND = PlotterTimetraceSpectralNoiseDensity()
plotter_SND.fit_params_plunger = fit_params_plunger_timetrace
plotter_SND.fit_vals = power_fit_params_timetrace_Welch
plotter_SND.savename = "SND_welch"
plotter_SND.plot(settings_timetrace, data_timetrace_Welch)



#%% Plotting Peak Tracking
plotter_SND = PlotterTimetraceSpectralNoiseDensity()
plotter_SND.fit_params_plunger = None
plotter_SND.fit_vals = None
plotter_SND.savename = "SND_fourier"
plotter_SND.plot(settings_peak, data_peak_Fourier)

plotter_SND = PlotterTimetraceSpectralNoiseDensity()
plotter_SND.fit_params_plunger = None
plotter_SND.fit_vals = None
plotter_SND.savename = "SND_welch"
plotter_SND.plot(settings_peak, data_peak_Welch)



#%% Plotting Timetrace AND Peak Tracking in one Plot
plotter_SND = PlotterTimetracePeakTrackingSND()
plotter_SND.fit_params_plunger = fit_params_plunger_timetrace
plotter_SND.fit_vals = power_fit_params_timetrace_Fourier
plotter_SND.savename = "SND_combined_fourier"
plotter_SND.plot(settings_peak, data_timetrace_Fourier, data_peak_Fourier)

plotter_SND = PlotterTimetracePeakTrackingSND()
plotter_SND.fit_params_plunger = fit_params_plunger_timetrace
plotter_SND.fit_vals = power_fit_params_timetrace_Welch
plotter_SND.savename = "SND_combined_welch"
plotter_SND.plot(settings_peak, data_timetrace_Welch, data_peak_Welch)



#%% Plotting Background
plotter_SND = PlotterTimetraceSpectralNoiseDensity()
plotter_SND.fit_params_plunger = None
plotter_SND.fit_vals = power_fit_params_background_Fourier
plotter_SND.savename = "SND_fourier"
plotter_SND.fiftyHz = True
plotter_SND.plot(settings_background, data_background_Fourier)

plotter_SND = PlotterTimetraceSpectralNoiseDensity()
plotter_SND.fit_params_plunger = None
plotter_SND.fit_vals = power_fit_params_background_Welch
plotter_SND.savename = "SND_welch"
plotter_SND.fiftyHz = True
plotter_SND.plot(settings_background, data_background_Welch)


#%% Plotting long Background
plotter_SND = PlotterTimetraceSpectralNoiseDensity()
plotter_SND.fit_params_plunger = None
plotter_SND.fit_vals = power_fit_params_background_long_Fourier
plotter_SND.savename = "SND_fourier"
plotter_SND.plot(settings_background_long, data_background_long_Fourier)

plotter_SND = PlotterTimetraceSpectralNoiseDensity()
plotter_SND.fit_params_plunger = None
plotter_SND.fit_vals = power_fit_params_background_long_Welch
plotter_SND.savename = "SND_welch"
plotter_SND.plot(settings_background_long, data_background_long_Welch)



#%% Plotting Background and long Background in one Plot
plotter_SND = PlotterTimetracePeakTrackingSND()
plotter_SND.fit_params_plunger = None
plotter_SND.fit_vals = power_fit_params_background_Fourier
plotter_SND.fiftyHz = True
plotter_SND.savename = "SND_combined_fourier"
plotter_SND.plot(settings_background, data_background_Fourier, data_background_long_Fourier)

plotter_SND = PlotterTimetracePeakTrackingSND()
plotter_SND.fit_params_plunger = None
plotter_SND.fit_vals = power_fit_params_background_Welch
plotter_SND.fiftyHz = True
plotter_SND.savename = "SND_combined_welch"
plotter_SND.plot(settings_background, data_background_Welch, data_background_long_Welch)
