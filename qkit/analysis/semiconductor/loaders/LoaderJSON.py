import json
from qkit.measure.json_handler import QkitJSONDecoder

class LoaderJSON:
    """Extracts all data from json files and returns it.
    """  
    def load(self, path):        
        with open(path, "r") as file:
            data = json.load(file, cls = QkitJSONDecoder)

        return data