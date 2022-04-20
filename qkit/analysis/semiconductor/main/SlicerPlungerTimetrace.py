import numpy as np
import copy
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import MaxNLocator
from scipy.optimize import curve_fit

from qkit.analysis.semiconductor.basic_functionality import PlotterSemiconInit, convert_conductance, map_array_to_index
from qkit.analysis.semiconductor.basic_functionality import  convert_secs_2D, create_saving_path, make_len_eq



class SlicerPlungerTimetrace:
    """Slices the nodes which are given in a slice that is given by "begin" and "end" in hours.
    First node needs to be timestamps, second is gate, third and following can be x, y, and/or R.
    """
    def slice(self, data, nodes, beginning, ending): 
        timestamps = convert_secs_2D(data[nodes[0]])
        index_begin = map_array_to_index(timestamps, beginning*3600)
        index_end = map_array_to_index(timestamps, ending*3600)
        data_sliced = {}
        data_sliced[nodes[0]] = copy.deepcopy(data[nodes[0]][index_begin : index_end])
        data_sliced[nodes[1]] = copy.deepcopy(data[nodes[1]])
        for index in np.arange(2, len(nodes)): # could be x, y, R
            data_sliced[nodes[index]] = copy.deepcopy(data[nodes[index]][index_begin : index_end, : ])
     
        return data_sliced