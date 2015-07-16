def plot_hdf(filepath, datasets=[]):
    append_string = '-f '+filepath + ' '
    if datasets:
        append_string += '-ds '
        for dataset in datasets:
            append_string += str(dataset)+','
    execfile('qkit\gui\qviewkit\main.py %s', append_string[:-1])