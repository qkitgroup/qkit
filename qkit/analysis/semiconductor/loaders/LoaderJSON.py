import json
from qkit.measure.json_handler import QkitJSONDecoder

from pathlib import Path

class LoaderJSON:
    """Extracts all data from json files and returns it.
    """  
    def load(self, path):        
        with Path(path).open() as file:
            data = json.load(file, cls = QkitJSONDecoder)

        return data