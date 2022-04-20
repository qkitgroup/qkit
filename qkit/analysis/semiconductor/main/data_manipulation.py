import numpy as np
import h5py
import pathlib
import math
import gc 
import copy
import matplotlib.pyplot as plt
from matplotlib.figure import Figure


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
    
    
def create_saving_path(settings):
    """Creats a folder with the name of settings["file_info"]["savepath"] if it's not existent and returns path to it. 
    """
    path = f"{settings['file_info']['absolute_path']}{settings['file_info']['date_stamp']}/{settings['file_info']['filename']}/{settings['file_info']['savepath']}"
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)
    
    return path + "/"   
    
    
def make_len_eq(data:dict, keys:list):
    """Takes a data dict and looks at two entries. Cuts away the end of data of the longer one to make 
    both equal length.
    """
    len1 = len(data[keys[0]])
    len2 = len(data[keys[1]])
    if len1 != len2:
        if len1 < len2:
            data[keys[1]] = copy.deepcopy(data[keys[1]][:len1])
        else:
            data[keys[0]] = copy.deepcopy(data[keys[0]][:len2])

    return data


def rotate_phase(data, nodes, phase_offset_deg):
    """Gives phase offset to x and y data (given in nodes).
    """
    R = np.sqrt(np.add(np.power(data[nodes[0]], 2), np.power(data[nodes[1]], 2)))
    phi = np.arctan2(data[nodes[1]], data[nodes[0]])
    phi = phi + phase_offset_deg*np.pi/180
    data_rotated = copy.deepcopy(data)
    data_rotated[nodes[0]] = R * np.cos(phi)
    data_rotated[nodes[1]] = R * np.sin(phi)  

    return data_rotated

