#%%
import copy
from qkit.analysis.semiconductor.loaders.Loaderh5 import Loaderh5
from qkit.analysis.semiconductor.loaders.LoaderPickle import LoaderPickle_samba
from qkit.analysis.semiconductor.savers.SaverPickle import SaverPickle

settings_list = []

settings_basic = {"file_info" : {
                "absolute_path" : "/var/tmp/",
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
settings["file_info"]["date_stamp"] = "20220427"
settings["file_info"]["filename"] = "154538_1D_measurement_time"
settings_list.append(settings)

#%% 2
settings = copy.deepcopy(settings_basic) 
settings["file_info"]["date_stamp"] = "20220128"
settings["file_info"]["filename"] = "175941_1D_measurement_time"
settings_list.append(settings)

#%% 3
settings = copy.deepcopy(settings_basic) 
settings["file_info"]["date_stamp"] = "20220128"
settings["file_info"]["filename"] = "175941_1D_measurement_time"
settings_list.append(settings)

#%% 4
settings = copy.deepcopy(settings_basic) 
settings["file_info"]["date_stamp"] = "20220128"
settings["file_info"]["filename"] = "175941_1D_measurement_time"
settings_list.append(settings)

#%% 5
settings = copy.deepcopy(settings_basic) 
settings["file_info"]["date_stamp"] = "20220128"
settings["file_info"]["filename"] = "175941_1D_measurement_time"
settings_list.append(settings)




#%% Load Timetraces
loader = Loaderh5()
saver = SaverPickle()

for setting in settings_list:
    try:
        data = loader.load(setting)
        saver.save(setting, data)
    except:
        print("Failure at ", setting["file_info"]["filename"])



