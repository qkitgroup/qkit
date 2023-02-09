import copy

    
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