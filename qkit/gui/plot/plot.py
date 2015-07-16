## MP 06/16/15:
## not tested, since I could not install h5py

import os
from subprocess import Popen

## the os.path.abspath gives the correct path to main.py, whith the working 
## directory being /qkit (as it is in our case)
qviewkit_main = os.path.join('qkit','gui','qviewkit','main.py')
qviewkit_main_path = os.path.abspath(qviewkit_main)

def plot_hdf(filepath, datasets=[]):
	filepath = os.path.abspath(filepath)
	arguments = ' -f '+filepath+' '
	if datasets:
		arguments += '-ds '
		for dataset in datasets:
			arguments += dataset+','
     	open_main = 'python ' + qviewkit_main_path + arguments

## As far as I understood, the encode('string-escape') does the same as \r 
     	open_main.encode('string-escape')
	Popen(open_main, shell=True)

## "old":
"""
def plot_hdf(filepath, datasets=[]):
    append_string = r'-f '+filepath + ' '
    if datasets:
        append_string += '-ds '
        for dataset in datasets:
            append_string += str(dataset)+','
    Popen(r'python C:\qtlab\qkit\qkit\gui\qviewkit\main.py '+append_string[:-1], shell=True)
"""
