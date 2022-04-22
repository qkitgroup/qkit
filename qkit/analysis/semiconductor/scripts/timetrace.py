#%%
import copy

from qkit.analysis.semiconductor.loaders import Loaderh5
from qkit.analysis.semiconductor.analyzers import AnalyzerPlungerSweep, AnalyzerTimetraceSpectralNoiseDensity
from qkit.analysis.semiconductor.plotters import  PlotterTimetraceSpectralNoiseDensity, PlotterPlungerSweep, PlotterTimetraceConductance, PlotterTimetrace, PlotterTimetracePhase
from qkit.analysis.semiconductor.main import rotate_phase, SlicerTimetrace


settings = {"file_info" : {
                "absolute_path" : "/home/ws/oc0612/SEMICONDUCTOR/analysis/bias-cooling/-3V/cooldown_1/",
                "filetype" : ".h5",
                "date_stamp" : "20220105",
                "filename" : "103542_1D_measurement_time",
                "savepath" : "analysis/",
                "analysis" : "noise_timetrace"},
            "meas_params" : {
                "measurement_amp" : 100e-6,
                "voltage_divider" : 3,
                "IVgain" : 1e8,
                "in_line_R": 40e3}
            }


settings_plunger = copy.deepcopy(settings) 
settings_plunger["file_info"]["filename"] = "102526_1D_Plunger_sweep_left"

#%% Load Timetrace
loader = Loaderh5()
data = loader.load(settings)
print("\nData nodes:\n" + str([key for key in data.keys()]))

#%% Plot Timetrace Lock-in R
plotter_timetrace = PlotterTimetrace()
plotter_timetrace.savename = "timetrace_R"
plotter_timetrace.title = "Timetrace R"
plotter_timetrace.plot(settings, data, ["demod0.timestamp0", "demod0.r0"])

#%% Plot Timetrace Lock-in x
plotter_timetrace = PlotterTimetrace()
plotter_timetrace.savename = "timetrace_x"
plotter_timetrace.title = "Timetrace x"
plotter_timetrace.plot(settings, data, ["demod0.timestamp0", "demod0.x0"])

#%% Plot Timetrace Lock-in y
plotter_timetrace = PlotterTimetrace()
plotter_timetrace.savename = "timetrace_y"
plotter_timetrace.title = "Timetrace y"
plotter_timetrace.plot(settings, data, ["demod0.timestamp0", "demod0.y0"])


#%% Plot Timetrace Cond R
plotter_timetrace = PlotterTimetraceConductance()
plotter_timetrace.savename = "timetraceCond_R"
plotter_timetrace.title = "Timetrace R"
plotter_timetrace.plot(settings, data, ["demod0.timestamp0", "demod0.r0"])


#%% Plot Timetrace Cond x
plotter_timetrace = PlotterTimetraceConductance()
plotter_timetrace.savename = "timetraceCond_x"
plotter_timetrace.title = "Timetrace x"
plotter_timetrace.plot(settings, data, ["demod0.timestamp0", "demod0.x0"])

#%% Plot Timetrace Cond y
plotter_timetrace = PlotterTimetraceConductance()
plotter_timetrace.savename = "timetraceCond_y"
plotter_timetrace.title = "Timetrace y"
plotter_timetrace.plot(settings, data, ["demod0.timestamp0", "demod0.y0"])

#%% Plot Phase of Timetrace
plotter_phase = PlotterTimetracePhase()
plotter_phase.plot(settings, data, ["demod0.timestamp0", "demod0.x0", "demod0.y0"])


#%% Slice Timetrace
begin, end = 0, 100 #seconds
slicer = SlicerTimetrace(begin, end)
data_sliced = slicer.make_slice_timetrace(data, ["demod0.timestamp0", "demod0.r0", "demod0.x0", "demod0.y0"])


plotter_timetrace = PlotterTimetrace()
plotter_timetrace.savename = "timetrace_sliced_R"
plotter_timetrace.title = "Timetrace R"
plotter_timetrace.plot(settings, data_sliced, ["demod0.timestamp0", "demod0.r0"])

plotter_timetrace = PlotterTimetrace()
plotter_timetrace.savename = "timetrace_sliced_x"
plotter_timetrace.title = "Timetrace x"
plotter_timetrace.plot(settings, data_sliced, ["demod0.timestamp0", "demod0.x0"])

plotter_timetrace = PlotterTimetrace()
plotter_timetrace.savename = "timetrace_sliced_y"
plotter_timetrace.title = "Timetrace y"
plotter_timetrace.plot(settings, data_sliced, ["demod0.timestamp0", "demod0.y0"])

plotter_timetrace = PlotterTimetraceConductance()
plotter_timetrace.savename = "timetrace_sliced_R_Cond"
plotter_timetrace.plot(settings, data_sliced, ["demod0.timestamp0", "demod0.r0"])

plotter_phase = PlotterTimetracePhase()
plotter_phase.savename="timetrace_sliced_phase"
plotter_phase.plot(settings, data_sliced, ["demod0.timestamp0", "demod0.x0", "demod0.y0"])

#%% Rotate Data
phase_correction = +75
data_sliced_rotated = rotate_phase(data_sliced, ["demod0.x0", "demod0.y0"], phase_correction)

plotter_timetrace = PlotterTimetrace()
plotter_timetrace.savename = "timetrace_sliced_rotated_x"
title = "Timetrace x"
plotter_timetrace.plot(settings, data_sliced_rotated, ["demod0.timestamp0", "demod0.x0"])

plotter_timetrace = PlotterTimetrace()
plotter_timetrace.savename = "timetrace_sliced_rotated_y"
title = "Timetrace y"
plotter_timetrace.plot(settings, data_sliced_rotated, ["demod0.timestamp0", "demod0.y0"])

plotter_phase = PlotterTimetracePhase()
plotter_phase.savename = "timetrace_sliced_rotated_phase"
plotter_phase.plot(settings, data_sliced_rotated, ["demod0.timestamp0", "demod0.x0", "demod0.y0"])





####################################
### Load Plunger Data and Fit it ###
####################################

#%% Load Plunger Gate Sweep
loader = Loaderh5()
data_plunger = loader.load(settings_plunger)
data_plunger_rotated = rotate_phase(data_plunger, ["demod0.x0", "demod0.y0"], phase_correction)

#%% Plot Plunger Sweep
plotter_plunger = PlotterPlungerSweep()
plotter_plunger.savename = "plunger_sweep_x"
plotter_plunger.plot(settings, settings_plunger, data_plunger_rotated, ["gate_6", "demod0.x0"])


#%% Analyze Equvalent Gate Voltage 
analyzer_plunger = AnalyzerPlungerSweep()
plunger_fit_params = analyzer_plunger.analyze(data_plunger_rotated, ["gate_6", "demod0.x0"], voltage=-0.8555, intervall=0.002)

plotter_plunger = PlotterPlungerSweep()
plotter_plunger.fit_params = plunger_fit_params
plotter_plunger.savename = "plunger_sweep_fit_x"
plotter_plunger.plot(settings, settings_plunger, data_plunger_rotated, ["gate_6", "demod0.x0"])


#%% Analyze and Plot SND with classic Fourier Trafo
sampling_f = 13732.91015625   #data["  "]
analyzer_SND = AnalyzerTimetraceSpectralNoiseDensity()
spectral_result = analyzer_SND.analyze(sampling_f,  data_sliced_rotated, ["demod0.x0"])
analyzer_SND.guess = [1e-5, -1]
power_fit_params = analyzer_SND.fit(spectral_result)
plotter_SND = PlotterTimetraceSpectralNoiseDensity()
plotter_SND.plunger_fit_params_in = plunger_fit_params
plotter_SND.fit_vals = power_fit_params
plotter_SND.savename = "SND_fourier"
plotter_SND.plot(settings, spectral_result)


#%% Analyze and Plot SND with Welch's method
sampling_f = 13732.91015625   #data["  "]
segment_length = 1e5 # length of each segment that is used for Welch
analyzer_SND = AnalyzerTimetraceSpectralNoiseDensity()
spectral_result_welch = analyzer_SND.analyze_welch(sampling_f,  data_sliced_rotated, ["demod0.x0"], segment_length)
power_fit_params_welch = analyzer_SND.fit(spectral_result_welch, guess=[1e-5, -1])
plotter_SND = PlotterTimetraceSpectralNoiseDensity()
plotter_SND.plunger_fit_params_in = plunger_fit_params
plotter_SND.fit_vals = power_fit_params_welch
plotter_SND.savename = "SND_welch"
plotter_SND.plot(settings, spectral_result_welch)


#%% Zoom in higher freqs
plotter_SND = PlotterTimetraceSpectralNoiseDensity()
plotter_SND.plunger_fit_params_in = plunger_fit_params
plotter_SND.fit_vals = power_fit_params
plotter_SND.savename = f"SND_slope_{plunger_fit_params['fit_coef'][0]:.3f}_zoom"
plotter_SND.fiftyHz = True
plotter_SND.xlim = [10,8e3]
plotter_SND.ylim = [1e-8,5e-3]
plotter_SND.plot(settings, spectral_result)

