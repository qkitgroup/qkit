import json
from qkit.measure.json_handler import QkitJSONDecoder

class LoaderJSON:
    """Extracts all data from json files and returns it.
    """  
    def load(self, settings):
        path = (f"{settings['file_info']['absolute_path']}"
        f"{settings['file_info']['date_stamp']}/"
        f"{settings['file_info']['folder']}/"
        f"{settings['file_info']['filename']}.json")
        
        with open(path, "r") as file:
            data = json.load(file, cls = QkitJSONDecoder)

        return data