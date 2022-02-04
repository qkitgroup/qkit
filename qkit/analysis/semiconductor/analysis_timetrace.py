#%%
import sys
sys.path.insert(0, "/home/ws/oc0612/SEMICONDUCTOR/analysis/bias-cooling/scripts/")
import copy

from main_func import Loaderh5, PlotterPlungerSweep, PlotterTimetraceCond, PlotterTimetraceR, PlotterTimetracePhase, SliceTimetrace
from main_func import AnalyzerPlungerSweep, AnalyzerTimetraceSpecralNoiseDensity, PlotterTimetraceSpectralNoiseDensity 

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
                "in_line_R": 45e3}
            }


settings_plunger = copy.deepcopy(settings) 
#settings_plunger["file_info"]["filename"] = "102149_1D_Plunger_sweep_left"
settings_plunger["file_info"]["filename"] = "102526_1D_Plunger_sweep_left"

#%% Load Timetrace
loader = Loaderh5()
data = loader.load(settings)
print("\nData nodes:\n" + str([key for key in data.keys()]))

#%% Plot Timetrace Lock-in R
plotter_timetrace = PlotterTimetraceR()
plotter_timetrace.plot(settings, data, ["demod0.timestamp0", "demod0.r0"], savename="timetrace_R", title="Timetrace R")

#%% Plot Timetrace Lock-in x
plotter_timetrace = PlotterTimetraceR()
plotter_timetrace.plot(settings, data, ["demod0.timestamp0", "demod0.x0"], savename="timetrace_x", title="Timetrace x")

#%% Plot Timetrace Lock-in y
plotter_timetrace = PlotterTimetraceR()
plotter_timetrace.plot(settings, data, ["demod0.timestamp0", "demod0.y0"], savename="timetrace_y", title="Timetrace y")

#%% Plot Timetrace Cond R
plotter_timetrace = PlotterTimetraceCond()
plotter_timetrace.plot(settings, data, ["demod0.timestamp0", "demod0.r0"], savename="timetraceCond_R", title="Timetrace R")

#%% Plot Timetrace Cond x
plotter_timetrace = PlotterTimetraceCond()
plotter_timetrace.plot(settings, data, ["demod0.timestamp0", "demod0.x0"], savename="timetraceCond_x", title="Timetrace x")

#%% Plot Timetrace Cond y
plotter_timetrace = PlotterTimetraceCond()
plotter_timetrace.plot(settings, data, ["demod0.timestamp0", "demod0.y0"], savename="timetraceCond_y", title="Timetrace y")

#%% Plot Phase of Timetrace
plotter_phase = PlotterTimetracePhase()
plotter_phase.plot(settings, data, ["demod0.timestamp0", "demod0.x0", "demod0.y0"])


#%% Slice Timetrace
begin, end = 0, 1800 #seconds
slicer = SliceTimetrace(begin, end)
data_sliced = slicer.make_slice_timetrace(data, ["demod0.timestamp0", "demod0.r0"])

plotter_timetrace = PlotterTimetraceCond()
plotter_timetrace.plot(settings, data_sliced, ["demod0.timestamp0", "demod0.r0"], savename="timetrace_sliced")


#%% Load Plunger Gate Sweep
loader_plunger = Loaderh5()
data_plunger = loader_plunger.load(settings_plunger)


#%% Plot Plunger Sweep
plotter_plunger = PlotterPlungerSweep()
plotter_plunger.plot(settings, settings_plunger, data_plunger, ["gate_6", "demod0.r0"])


#%% Analyze Equvalent Gate Voltage 
analyzer_plunger = AnalyzerPlungerSweep()
fit_params = analyzer_plunger.analyze(data_plunger, ["gate_6", "demod0.r0"], voltage=-0.8555, intervall=0.001)

plotter_plunger = PlotterPlungerSweep()
plotter_plunger.plot(settings, settings_plunger, data_plunger, ["gate_6", "demod0.r0"], fit_params, savename="plunger_sweep_fit")

#%% Analyze and Plot SND
sampling_f = 13732.91015625   #data["  "]
analyzer_SND = AnalyzerTimetraceSpecralNoiseDensity()
spectral_result = analyzer_SND.analyze(sampling_f, fit_params,  data_sliced, ["demod0.r0"])

plotter_SND = PlotterTimetraceSpectralNoiseDensity()
plotter_SND.plot(settings, spectral_result, fit_params)
# %%
