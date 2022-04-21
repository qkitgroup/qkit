
def convert_secs(timestamps, f=1.8*1e9):
    """Sets the starting point to 0 and adjusts with the clock speed of 1.8 GHz. Not really accurate.
    Timestamps need to be numpy arrays.
    """
    time_stamps = timestamps - timestamps[0]
    time_stamps = time_stamps / f 
    
    return time_stamps
    
    


def convert_secs_2D(timestamps, f=1.8*1e9):
    """Sets the starting point to 0 and adjusts with the clock speed of 1.8 GHz. Not really accurate.
    Converts 2D timestamps in 1D arrays with each point in 1D being the beginning of a 2D array. 
    """
    time_stamps = timestamps[:,0] - timestamps[0,0]
    time_stamps = time_stamps / f 
    
    return time_stamps