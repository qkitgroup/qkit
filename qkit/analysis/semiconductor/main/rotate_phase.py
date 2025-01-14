import numpy as np
import copy


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