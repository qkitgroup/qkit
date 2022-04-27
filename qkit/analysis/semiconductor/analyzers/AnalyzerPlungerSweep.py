import numpy as np

from qkit.analysis.semiconductor.main.find_index_of_value import map_array_to_index


class AnalyzerPlungerSweep:
    """Fits a tangent to a point in a plunger gate sweep and returns the fit results. 
    Lock-in V used for calculations instead of conductance.
    Slope coef[0] in Volt / Volt.
    """
    def __init__(self):
        self.voltage_fit = 0
        self.intervall_fit = 0 
    
    def analyze(self, data, nodes):
        """Fits a linear function to values at voltage with intervall around it.
        """
        self.data_x = data[nodes[0]]
        self.data_y = data[nodes[1]]
        index_begin = map_array_to_index(self.data_x, self.voltage_fit - abs(self.intervall_fit))
        index_end = map_array_to_index(self.data_x, self.voltage_fit +  abs(self.intervall_fit))
        if index_begin > index_end: # array was in descending order
            index_begin, index_end = index_end, index_begin
        self.data_x_cut = self.data_x[index_begin : index_end]
        self.data_y_cut = self.data_y[index_begin : index_end]
        
        coef = np.polyfit(self.data_x_cut, self.data_y_cut, 1)
   
        return {"fit_coef" : coef, "index_begin" : index_begin, "index_end" : index_end}
    