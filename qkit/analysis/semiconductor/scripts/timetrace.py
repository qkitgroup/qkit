#%%
import copy
from qkit.analysis.semiconductor.loaders.Loaderh5 import Loaderh5
from qkit.analysis.semiconductor.main.loading import print_nodes
from qkit.analysis.semiconductor.analyzers.AnalyzerPlungerSweep import AnalyzerPlungerSweep
from qkit.analysis.semiconductor.analyzers.AnalyzerTimetraceSpectralNoiseDensity import AnalyzerTimetraceSpectralNoiseDensity
from qkit.analysis.semiconductor.plotters.PlotterTimetraceSpectralNoiseDensity import PlotterTimetraceSpectralNoiseDensity
from qkit.analysis.semiconductor.plotters.PlotterDifferenceTimetraceSpectralNoiseDensity import PlotterDifferenceTimetraceSpectralNoiseDensity
from qkit.analysis.semiconductor.plotters.PlotterPlungerSweep import PlotterPlungerSweep
from qkit.analysis.semiconductor.plotters.PlotterTimetraceConductance import PlotterTimetraceConductance
from qkit.analysis.semiconductor.plotters.PlotterTimetrace import PlotterTimetrace
from qkit.analysis.semiconductor.plotters.PlotterTimetracePhase import PlotterTimetracePhase
from qkit.analysis.semiconductor.main.rotate_phase import rotate_phase
from qkit.analysis.semiconductor.main.SlicerTimetrace import SlicerTimetrace
from qkit.analysis.semiconductor.loaders.Loader_spectrum_np import Loader_spectrum_np
from qkit.analysis.semiconductor.savers.Saver_spectrum_np import Saver_spectrum_np
from qkit.analysis.semiconductor.loaders.LoaderPickle import LoaderPickle
from qkit.analysis.semiconductor.savers.SaverPickle import SaverPickle


settings = {"file_info" : {
                "absolute_path" : "/home/ws/oc0612/SEMICONDUCTOR/analysis/bias-cooling/P35_B3/",
                "filetype" : ".h5",
                "date_stamp" : "20220501",
                "filename" : "132507_1D_measurement_time",
                "savepath" : "analysis/",
                "analysis" : "noise_timetrace"},
            "meas_params" : {
                "measurement_amp" : 200e-6,
                "voltage_divider" : 3,
                "IVgain" : 1e8,
                "in_line_R": 42e3,
                "sampling_rate" : 13732.91015625}
            }


settings_plunger = copy.deepcopy(settings) 
settings_plunger["file_info"]["filename"] = "131831_1D_Plunger_sweep_both"

#%% Load Timetrace
loader = Loaderh5()
data = loader.load(settings)
print_nodes(data)

#%% save as Pickle
saver = SaverPickle()
saver.save(settings, data)

#%% load from Pickle
loader = LoaderPickle()
data = loader.load(settings)


#%%
side = "l"

#Define nodes
if side == "l":
    node_timestamp = "demod0&4.timestamp0"
    node_x = "demod0&4.x0"
    node_y = "demod0&4.y0"
    node_r = "demod0&4.r0"
elif side == "r":
    node_timestamp = "demod0&4.timestamp4"
    node_x = "demod0&4.x4"
    node_y = "demod0&4.y4"
    node_r = "demod0&4.r4"
else:
    print("Idiot!")

# define plunger notes
if side == "l":
    node_plunger_timestamp = "demod0&4.timestamp0"
    node_plunger_x = "demod0&4.x0"
    node_plunger_y = "demod0&4.y0"
    node_plunger_r = "demod0&4.r0"
elif side == "r":
    node_plunger_timestamp = "demod0&4.timestamp4"
    node_plunger_x = "demod0&4.x4"
    node_plunger_y = "demod0&4.y4"
    node_plunger_r = "demod0&4.r4"
else:
    print("Idiot!")
    
gate_plunger = "gates_6_12"


#%% Plot Timetrace Lock-in R

plotter_timetrace = PlotterTimetrace()
plotter_timetrace.savename = "timetrace_R" + "_" + side
plotter_timetrace.title = "Timetrace R"
plotter_timetrace.plot(settings, data, [node_timestamp, node_x])

#%% Plot Timetrace Lock-in x
plotter_timetrace = PlotterTimetrace()
plotter_timetrace.savename = "timetrace_x" + "_" + side
plotter_timetrace.title = "Timetrace x"
plotter_timetrace.plot(settings, data, [node_timestamp, node_x])

#%% Plot Timetrace Lock-in y
plotter_timetrace = PlotterTimetrace()
plotter_timetrace.savename = "timetrace_y" + "_" + side
plotter_timetrace.title = "Timetrace y"
plotter_timetrace.plot(settings, data, [node_timestamp, node_y])


#%% Plot Timetrace Cond R
plotter_timetrace = PlotterTimetraceConductance()
plotter_timetrace.savename = "timetraceCond_R" + "_" + side
plotter_timetrace.title = "Timetrace R"
plotter_timetrace.plot(settings, data, [node_timestamp, node_r])


#%% Plot Timetrace Cond x
plotter_timetrace = PlotterTimetraceConductance()
plotter_timetrace.savename = "timetraceCond_x" + "_" + side
plotter_timetrace.title = "Timetrace x"
plotter_timetrace.plot(settings, data, [node_timestamp, node_x])

#%% Plot Timetrace Cond y
plotter_timetrace = PlotterTimetraceConductance()
plotter_timetrace.savename = "timetraceCond_y" + "_" + side
plotter_timetrace.title = "Timetrace y"
plotter_timetrace.plot(settings, data, [node_timestamp, node_y])

#%% Plot Phase of Timetrace
plotter_phase = PlotterTimetracePhase()
plotter_phase.savename = "phase" + "_" + side
plotter_phase.plot(settings, data, [node_timestamp, node_x, node_y])


#%% Slice Timetrace
begin, end = 0, 2000 #seconds
slicer = SlicerTimetrace(begin, end)
data_sliced = slicer.make_slice_timetrace(data, [node_timestamp, node_r, node_x, node_y])


plotter_timetrace = PlotterTimetrace()
plotter_timetrace.savename = "timetrace_sliced_R" + "_" + side
plotter_timetrace.title = "Timetrace R"
plotter_timetrace.plot(settings, data_sliced, [node_timestamp, node_r])

plotter_timetrace = PlotterTimetrace()
plotter_timetrace.savename = "timetrace_sliced_x" + "_" + side
plotter_timetrace.title = "Timetrace x"
plotter_timetrace.plot(settings, data_sliced, [node_timestamp, node_x])

plotter_timetrace = PlotterTimetrace()
plotter_timetrace.savename = "timetrace_sliced_y" + "_" + side
plotter_timetrace.title = "Timetrace y"
plotter_timetrace.plot(settings, data_sliced, [node_timestamp, node_y])

plotter_timetrace = PlotterTimetraceConductance()
plotter_timetrace.savename = "timetrace_sliced_R_Cond" + "_" + side
plotter_timetrace.plot(settings, data_sliced, [node_timestamp, node_r])

plotter_phase = PlotterTimetracePhase()
plotter_phase.savename="timetrace_sliced_phase" + "_" + side
plotter_phase.plot(settings, data_sliced, [node_timestamp, node_x, node_y])

#%% Rotate Data
phase_correction = +75
data_sliced_rotated = rotate_phase(data_sliced, [node_x, node_y], phase_correction)

plotter_timetrace = PlotterTimetrace()
plotter_timetrace.savename = "timetrace_sliced_rotated_x" + "_" + side
plotter_timetrace.title = "Timetrace x"
plotter_timetrace.plot(settings, data_sliced_rotated, [node_timestamp, node_x])

plotter_timetrace = PlotterTimetrace()
plotter_timetrace.savename = "timetrace_sliced_rotated_y" + "_" + side
plotter_timetrace.title = "Timetrace y"
plotter_timetrace.plot(settings, data_sliced_rotated, [node_timestamp, node_y])

plotter_phase = PlotterTimetracePhase()
plotter_phase.savename = "timetrace_sliced_rotated_phase" + "_" + side
plotter_phase.plot(settings, data_sliced_rotated, [node_timestamp, node_x, node_y])





####################################
### Load Plunger Data and Fit it ###
####################################

#%% Load Plunger Gate Sweep
loader = Loaderh5()
data_plunger = loader.load(settings_plunger)
print_nodes(data_plunger)


#%% Rotate data
data_plunger_rotated = rotate_phase(data_plunger, [node_plunger_x, node_plunger_y], phase_correction)

#%% Plot Plunger Sweep
plotter_plunger = PlotterPlungerSweep()
plotter_plunger.savename = "plunger_sweep_x" + "_" + side
plotter_plunger.plot(settings, settings_plunger, data_plunger_rotated, [gate_plunger, node_plunger_x])


#%% Analyze Equvalent Gate Voltage 
analyzer_plunger = AnalyzerPlungerSweep()
analyzer_plunger.voltage_fit = 0.5507
analyzer_plunger.intervall_fit = 4e-3
plunger_fit_params = analyzer_plunger.analyze(data_plunger_rotated, [gate_plunger, node_plunger_x])

plotter_plunger = PlotterPlungerSweep()
plotter_plunger.fit_params = plunger_fit_params
plotter_plunger.savename = "plunger_sweep_fit_x" + "_" + side
plotter_plunger.plot(settings, settings_plunger, data_plunger_rotated, [gate_plunger, node_plunger_x])


#%% Analyze and Plot SND with classic Fourier Trafo
sampling_f = settings["meas_params"]["sampling_rate"]   #data["  "]
analyzer_SND = AnalyzerTimetraceSpectralNoiseDensity()
analyzer_SND.guess = [1e-5, -1]
spectral_result = analyzer_SND.analyze(sampling_f,  data_sliced_rotated, [node_x])
power_fit_params = analyzer_SND.fit(spectral_result)

saver = Saver_spectrum_np() # Saving Data
saver.save(settings, spectral_result, plunger_fit_params, power_fit_params, ending=f"Fourier_{side}")

plotter_SND = PlotterTimetraceSpectralNoiseDensity()
plotter_SND.fit_params_plunger = plunger_fit_params
plotter_SND.fit_vals = power_fit_params
plotter_SND.savename = "SND_fourier" + "_" + side
plotter_SND.plot(settings, spectral_result)




#%% Analyze and Plot SND with Welch's method
sampling_f = settings["meas_params"]["sampling_rate"] 
analyzer_SND = AnalyzerTimetraceSpectralNoiseDensity()
analyzer_SND.segment_length = 5e5 # length of each segment that is used for Welch
spectral_result_welch = analyzer_SND.analyze_welch(sampling_f,  data_sliced_rotated, [node_x])
power_fit_params_welch = analyzer_SND.fit(spectral_result_welch)

saver = Saver_spectrum_np() # Saving Data
saver.save(settings, spectral_result_welch, plunger_fit_params, power_fit_params_welch, ending=f"Welch_{side}")

plotter_SND = PlotterTimetraceSpectralNoiseDensity()
plotter_SND.fit_params_plunger = plunger_fit_params
plotter_SND.fit_vals = power_fit_params_welch
plotter_SND.savename = "SND_welch" + "_" + side
plotter_SND.plot(settings, spectral_result_welch)









#%%
################################################
################################################
#Background noise
settings_background = {"file_info" : {
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

#%% Load Timetrace
loader = Loaderh5()
data_background = loader.load(settings_background)
print_nodes(data_background)

#%% Define nodes
node_background_timestamp = "demod0&4.timestamp0"
node_background_x = "demod0&4.x0"
node_background_y = "demod0&4.y0"
node_background_r = "demod0&4.r0"

#%% Slice Timetrace
#begin, end = 0, 100 #seconds
#slicer = SlicerTimetrace(begin, end)
#data_sliced_background = slicer.make_slice_timetrace(data_background, [node_background_timestamp, node_background_r, node_background_x, node_background_y])
data_sliced_background = data_background

#%% Rotate Data
phase_correction_background = +75
data_sliced_rotated_background = rotate_phase(data_sliced_background, [node_background_x, node_background_y], phase_correction_background)

plotter_timetrace = PlotterTimetrace()
plotter_timetrace.jumbo_data = True
print(plotter_timetrace.jumbo_data)
plotter_timetrace.savename = "timetrace_background_sliced_rotated_x"
plotter_timetrace.title = "Timetrace x"
plotter_timetrace.plot(settings_background, data_sliced_rotated_background, [node_background_timestamp, node_background_x])

plotter_timetrace = PlotterTimetrace()
plotter_timetrace.jumbo_data = True
plotter_timetrace.savename = "timetrace_background_sliced_rotated_y"
plotter_timetrace.title = "Timetrace y"
plotter_timetrace.plot(settings_background, data_sliced_rotated_background, [node_background_timestamp, node_background_y])

plotter_phase = PlotterTimetracePhase()
plotter_timetrace.jumbo_data = True
plotter_timetrace.savename = "timetrace_background_sliced_rotated_phase"
plotter_phase.plot(settings_background, data_sliced_rotated_background, [node_background_timestamp, node_background_x, node_background_y])



#%% Analyze Equvalent Gate Voltage 
analyzer_plunger = AnalyzerPlungerSweep()
plunger_fit_params_background = None 

#%% Analyze and Plot SND with classic Fourier Trafo
sampling_f_background = settings_background["meas_params"]["sampling_rate"]  #data["  "]
analyzer_SND = AnalyzerTimetraceSpectralNoiseDensity()
spectral_result_background = analyzer_SND.analyze(sampling_f_background, data_sliced_rotated_background, [node_background_x])
power_fit_params_background = analyzer_SND.fit(spectral_result_background)

saver = Saver_spectrum_np() # Saving Data
saver.save(settings_background, spectral_result_background, plunger_fit_params_background, power_fit_params_background, ending="Fourier")

plotter_SND = PlotterTimetraceSpectralNoiseDensity()
plotter_SND.fit_params_plunger = None
plotter_SND.fit_vals = power_fit_params_background
plotter_SND.savename = "SND_fourier_background"
plotter_SND.plot(settings_background, spectral_result_background)


#%% Analyze and Plot SND with Welch's method
analyzer_SND = AnalyzerTimetraceSpectralNoiseDensity() 
sampling_f_background = settings_background["meas_params"]["sampling_rate"]
analyzer_SND.segment_length = 1e7 # length of each segment that is used for Welch
spectral_result_welch_background = analyzer_SND.analyze_welch(sampling_f_background, data_sliced_rotated_background, [node_background_x])
power_fit_params_welch_background = analyzer_SND.fit(spectral_result_welch_background)

saver = Saver_spectrum_np() # Saving Data
saver.save(settings_background, spectral_result_welch_background, plunger_fit_params_background, power_fit_params_welch_background, ending="Welch")

plotter_SND = PlotterTimetraceSpectralNoiseDensity()
plotter_SND.fit_params_plunger = None
plotter_SND.fit_vals = power_fit_params_welch_background
plotter_SND.savename = "SND_welch_background_8"
plotter_SND.xlim = [5e-5,1e0]
plotter_SND.ylim = [1e-6,1e-1]
plotter_SND.plot(settings_background, spectral_result_welch_background)



#%%
plotter_SND = PlotterDifferenceTimetraceSpectralNoiseDensity()
plotter_SND.savename = "SND_Fourier_NO_background"
plotter_SND.fit_params_plunger = plunger_fit_params
plotter_SND.plot(settings, spectral_result, spectral_result_background)


#%%
plotter_SND = PlotterDifferenceTimetraceSpectralNoiseDensity()
plotter_SND.savename = "SND_Welch_NO_background"
plotter_SND.fit_params_plunger = plunger_fit_params
plotter_SND.plot(settings, spectral_result_welch, spectral_result_welch_background)


# %%