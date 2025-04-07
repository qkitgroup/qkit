import pickle
import os
import urllib
from smb.SMBHandler import SMBHandler


class LoaderPickle:
    """Extracts all data from pickle files and returns it.
    """  
    def load(self, settings):
        
        if isinstance(settings, str):
            path = settings
        else:
            try: #Are we in the new data format?
                path = settings["file_info"]["filepath"]
                
                if not os.path.isfile(path):
                    mod_path = path.replace("smb://nanospin@phi-ndus", "smb://nanospin:Hadamard_gate@phi-ndus")
                    opener = urllib.request.build_opener(SMBHandler)
                    fh = opener.open(mod_path)
                    data = pickle.load(fh)["entry"]["data0"]
                    return
            except KeyError: #Or in the old?
                    path = (f"{settings['file_info']['absolute_path']}"
                    f"{settings['file_info']['date_stamp']}/"
                    f"{settings['file_info']['filename']}/"
                    f"{settings['file_info']['filename']}.p")
                
                    if not os.path.isfile(path):
                        path = (f"{settings['file_info']['absolute_path']}"
                        f"{settings['file_info']['date_stamp']}/"
                        f"{settings['file_info']['filename']}/"
                        "data_pickle")

        with open(path, "rb") as file:
            data = pickle.load(file)

        return data
