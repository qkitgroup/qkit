## MP (early) 07/17/15:
## alpha-tested on erbium pc
## the opened file shows only the axis, not the value matrices
## fixed, the call for the plot was aparently too early. Now it works!!!

import os
from subprocess import Popen
from qkit.gui.qviewkit import main as plot_main

## This is a little hack. The import command is only for orientaion purposes in the file system
## The abspath of an imported module can be called and we can use this information without
## really using the module. Due to name conflicts, the module is renamed.

qviewkit_main_path = os.path.abspath(plot_main.__file__)
qviewkit_main_path=qviewkit_main_path

def plot_hdf(filepath, datasets=[]):
    filepath = os.path.abspath(filepath)
    arguments = ' -f '+filepath+' '
    if datasets:
        arguments += '-ds '
        for dataset in datasets:
            arguments += dataset+','
    open_main = 'python ' + qviewkit_main_path + arguments

## As far as I understood, the encode('string-escape') does the same as r' 
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
