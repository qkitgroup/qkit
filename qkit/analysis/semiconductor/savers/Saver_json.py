import os
import json
import collections.abc
from qkit.analysis.semiconductor.main.saving import create_saving_path
from qkit.measure.json_handler import QkitJSONEncoder, QkitJSONDecoder

def update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update(d.get(k, {}), v)
        else:
            d[k] = v
    return d

class Saver_json():
    """Saves data in a folder that is set by "save_path". 
    """
    def __init__(self, save_path) -> None:
        self.additional_info = {}
        self.fname = "analyzed_data"
        self.saving_path = save_path
        self.single_file = True
        self.append_to_file = False
    
    def add_info(self, fname, info):
        new_info = {fname : info}
        update(self.additional_info, new_info)
    
    def remove_info(self, fname):
        self.additional_info.pop(fname, None)

    def _overwrite(self, fpath, data):
        #full_path = os.path.join(self.saving_path, fname + ".json")
        with open(fpath, "w") as file: 
            json.dump(data, file, cls = QkitJSONEncoder, indent = 4)
    
    def _append(self, fpath, data):
        #full_path = os.path.join(self.saving_path, fname + ".json")
        with open(fpath, "r") as file:
            data_total= json.load(file, cls = QkitJSONDecoder)
        update(data_total, data)
        with open(fpath, "w") as file:
            json.dump(data_total, file, cls = QkitJSONEncoder, indent = 4)
    
    def _save(self, fname, data):
        full_path = os.path.join(self.saving_path, fname + ".json")
        file_exists = os.path.isfile(full_path)
        file_has_content = False         
        if file_exists:
            file_has_content = os.stat(full_path).st_size != 0

        if file_has_content and self.append_to_file:
            return self._append(full_path, data)
        if not file_exists:
            return self._overwrite(full_path, data)
        if not self.append_to_file:
            return self._overwrite(full_path, data)
        
    def save(self):
        if self.single_file:
            self._save(self.fname, self.additional_info)
        else:
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