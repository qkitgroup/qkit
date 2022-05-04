import os
import json
from qkit.analysis.semiconductor.main.saving import create_saving_path
from qkit.measure.json_handler import QkitJSONEncoder

class Saver_json():
    """Saves data in a folder that is set by "settings". 
    """
    def __init__(self, settings:dict) -> None:
        self.settings = settings
        self.additional_info = {}
        self.saving_path = create_saving_path(settings, "", filetype="")
    
    def add_info(self, fname, info):
        self.additional_info[fname] = info
    
    def remove_info(self, fname):
        self.add_info.pop(fname, None)

    def _save(self, fname, data):
        full_path = os.path.join(self.saving_path, fname + ".json")
        with open(full_path, "w+") as file: 
            json.dump(data, file, cls = QkitJSONEncoder, indent = 4)
    
    def save(self):        
        for fname, info in self.additional_info.items():
            self._save(fname, info)
     
if __name__ == "__main__":
    import numpy as np
    settings = {"file_info" : {
                "absolute_path" : "/home/ws/lr1740/Dokumente/Doktorarbeit/Messungen/SAVERTEST",
                "filetype" : ".h5",
                "date_stamp" : "20220216",
                "filename" : "bananaasd",
                "savepath" : "analysis/",
                "analysis" : "noise_timetrace"},
            "meas_params" : {
                "measurement_amp" : 100e-3,
                "voltage_divider" : 3,
                "IVgain" : 1e8,
                "in_line_R": 42e3}
            }
    a = np.int64(10)
    b = complex(1,2)
    #

    print(type(b))
    print(b)
    print(type(a))
    if type(a) == np.integer:
        print("Yass")
    data = {"ads" : [12,3], "das" : a}
    plunger = {'fit_coef': np.array([-2.87297491,  2.60734095]), 'index_begin': 158, 'index_end': 204}
    saver = Saver_json(settings)
    saver.add_info("data", data)
    saver.save()