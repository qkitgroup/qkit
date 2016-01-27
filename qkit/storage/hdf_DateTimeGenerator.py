# -*- coding: utf-8 -*-
"""
Created 2015

@author: hrotzing
"""
import time
import os
from qkit.config.environment import cfg

class DateTimeGenerator(object):
    '''
    Class to generate filenames / directories based on the date and time.
    Date (YYYYMMDD) -> Time (HHMMSS) -> data
    '''

    def __init__(self):
        pass

    def create_data_dir(self, datadir, name=None, ts=None, datesubdir=True, timesubdir=True):
        '''
        Create and return a new data directory.

        Input:
            datadir (string): base directory
            name (string): optional name of measurement
            ts (time.localtime()): timestamp which will be used if timesubdir=True
            datesubdir (bool): whether to create a subdirectory for the date
            timesubdir (bool): whether to create a subdirectory for the time

        Output:
            The directory to place the new file in
        '''

        path = datadir
        if ts is None:
            ts = time.localtime()
        if datesubdir:
            path = os.path.join(path, time.strftime('%Y%m%d', ts))
        if timesubdir:
            tsd = time.strftime('%H%M%S', ts)
            if name is not None:
                tsd += '_' + name
            path = os.path.join(path, tsd)

        return path

    def new_filename(self, data_obj):
        '''Return a new filename, based on name and timestamp.'''

        dir = self.create_data_dir(cfg['datadir'], name=data_obj._name,
                ts=data_obj._localtime)
        tstr = time.strftime('%H%M%S', data_obj._localtime)
        filename = '%s_%s.h5' % (tstr, data_obj._name)

        return os.path.join(dir, filename)
