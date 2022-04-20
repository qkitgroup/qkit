import numpy as np
import copy
import matplotlib.pyplot as plt
from scipy import signal
from scipy.optimize import curve_fit

from qkit.analysis.semiconductor.basic_functionality import PlotterSemiconInit, convert_conductance, map_array_to_index
from qkit.analysis.semiconductor.basic_functionality import  convert_secs, create_saving_path, make_len_eq

class AnalyzerPlungerSweep:
    """Fits a tangent to a point in a plunger gate sweep and returns the fit results. 
    Lock-in V used for calculations instead of conductance.
    Slope coef[0] in Volt / Volt.
    """
    number_of_traces = 1
    
    def analyze(self, data, nodes, voltage, intervall):
        """Fits a linear function to values at voltage with intervall around it.
        """
        self.data_x = data[nodes[0]]
        self.data_y = data[nodes[1]]
        index_begin = map_array_to_index(self.data_x, voltage - abs(intervall))
        index_end = map_array_to_index(self.data_x, voltage +  abs(intervall))
        if index_begin > index_end: # array was in descending order
            index_begin, index_end = index_end, index_begin
        self.data_x_cut = self.data_x[index_begin : index_end]
        self.data_y_cut = self.data_y[index_begin : index_end]
        
        coef = np.polyfit(self.data_x_cut, self.data_y_cut, 1)
   
        return {"fit_coef" : coef, "index_begin" : index_begin, "index_end" : index_end}
    