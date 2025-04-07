import copy

from qkit.analysis.semiconductor.main.find_index_of_value import  map_array_to_index



class SlicerTimetrace:
    """Slices data by beginning and ending values of the time (first node entry) in seconds.
    """
    def __init__(self, begin, end):
        """initialize with beginning and ending.
        """
        self.begin = begin
        self.end = end
        
    def make_slice_timetrace(self, data, nodes, f=1.8*1e9):
        begin_x = data[nodes[0]][0] + self.begin * f
        end_x = data[nodes[0]][0] + self.end * f
        index_begin = map_array_to_index(data[nodes[0]], begin_x)
        index_end = map_array_to_index(data[nodes[0]], end_x)
        data_sliced = {}
        for key in nodes:
            data_sliced[key] = copy.deepcopy(data[key][index_begin : index_end])
        
        return data_sliced
      