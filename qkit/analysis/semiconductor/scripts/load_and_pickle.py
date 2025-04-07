#%%
import copy
from qkit.analysis.semiconductor.loaders.Loaderh5 import Loaderh5
from qkit.analysis.semiconductor.savers.SaverPickle import SaverPickle

settings_list = []

settings_basic = {"file_info" : {
                "absolute_path" : "/home/ws/oc0612/SEMICONDUCTOR/analysis/bias-cooling/P35_B3/",
                "filetype" : ".h5",
                "date_stamp" : "",
                "filename" : "",
                "savepath" : "analysis/",
                "analysis" : "noise_timetrace"},
            "meas_params" : {
                "measurement_amp" : 200e-6,
                "voltage_divider" : 3,
                "IVgain" : 1e8,
                "in_line_R": 42e3,
                "sampling_rate" : 13732.91015625}
            }



#%% 1
settings = copy.deepcopy(settings_basic) 
settings["file_info"]["date_stamp"] = "20220516"
settings["file_info"]["filename"] = "112714_1D_measurement_time"
settings_list.append(settings)

#%% 2
settings = copy.deepcopy(settings_basic) 
settings["file_info"]["date_stamp"] = "20220517"
settings["file_info"]["filename"] = "183049_1D_measurement_time"
settings_list.append(settings)

#%% 3
settings = copy.deepcopy(settings_basic) 
settings["file_info"]["date_stamp"] = "20220518"
settings["file_info"]["filename"] = "211429_1D_measurement_time"
settings_list.append(settings)

#%% 4
settings = copy.deepcopy(settings_basic) 
settings["file_info"]["date_stamp"] = "20220528"
settings["file_info"]["filename"] = "121949_1D_measurement_time"
settings_list.append(settings)

#%% 5
settings = copy.deepcopy(settings_basic) 
settings["file_info"]["date_stamp"] = "20220528"
settings["file_info"]["filename"] = "194601_1D_measurement_time"
settings_list.append(settings)


#%% 6
settings = copy.deepcopy(settings_basic) 
settings["file_info"]["date_stamp"] = "20220528"
settings["file_info"]["filename"] = "210639_1D_measurement_time"
settings_list.append(settings)


#%% 7
settings = copy.deepcopy(settings_basic) 
settings["file_info"]["date_stamp"] = "20220529"
settings["file_info"]["filename"] = "104210_1D_measurement_time"
settings_list.append(settings)

#%% 8
settings = copy.deepcopy(settings_basic) 
settings["file_info"]["date_stamp"] = "20220529"
settings["file_info"]["filename"] = "185805_1D_measurement_time"
settings_list.append(settings)


#%% Load Timetraces
loader = Loaderh5()
saver = SaverPickle()

for setting in settings_list:
    try:
        data = loader.load(setting)
        saver.save(setting, data)
        print("File saved : ", setting["file_info"]["filename"])
    except:
        print("Failure at ", setting["file_info"]["filename"])


# %%
