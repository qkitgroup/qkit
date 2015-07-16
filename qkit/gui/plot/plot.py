from subprocess import Popen
def plot_hdf(filepath, datasets=[]):
    append_string = r'-f '+filepath + ' '
    if datasets:
        append_string += '-ds '
        for dataset in datasets:
            append_string += str(dataset)+','
    Popen(r'python C:\qtlab\qkit\qkit\gui\qviewkit\main.py '+append_string[:-1], shell=True)