from qkit.analysis.semiconductor.interfaces import AnalyzerInterface

class Analyzer(AnalyzerInterface):
    def load_data(self, data):
        self.data_raw = data

    def validate_input(self):
        if not isinstance(self.data_raw, dict):
            raise TypeError("The loader returned an invalid data type. Type must be dictionary.")

    def analyze(self):
        return self.data_raw