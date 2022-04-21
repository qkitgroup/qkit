import numpy as np


def map_array_to_index(array, value):
    """Takes an array of SORTED values and returns the nearest index where the value is found. 
    """
    if array[0]<array[-1]: # array in ascending order
        idx = np.searchsorted(array, value, side="left")
        #if idx > 0 and (idx == len(array) or math.fabs(value - array[idx-1]) < math.fabs(value - array[idx])):
        #    return idx-1
        #else:
        return idx
    else: # array in descending order
        idx = np.searchsorted(array[::-1], value, side="left")
        #if idx > 0 and (idx == len(array) or math.fabs(value - array[idx-1]) < math.fabs(value - array[idx])):
        #   return len(array) - idx - 1
        #else:
        return len(array) - idx    
    
