# -*- coding: utf-8 -*-
"""
Created 2015

@author: hrotzing

Modified 2017 by S1
"""
import time
import os
from qkit.config.environment import cfg
import logging

class DateTimeGenerator(object):
    '''
    Class to generate filenames / directories based on the date and time.
    Date (YYYYMMDD) -> Time (HHMMSS) -> data
    '''

    def __init__(self):
        pass
        
    def new_filename(self, data_obj):
        if cfg['new_data_structure']: return self.new_filename_v2(data_obj)
        else:  return self.new_filename_v1(data_obj)
        
    def new_filename_v2(self, data_obj):
            '''Return a new filename, based on name and timestamp.'''
            filename = '%s_%s' % (data_obj._uuid, data_obj._name)
            
            if not cfg.has_key('user') or not cfg.has_key('run_id'):
                logging.warning(__name__+": cfg['user'] or cfg['run_id'] is not set. Using defaults. Have fun searching your data.")
            
            return os.path.join(
                        cfg['datadir'],
                        cfg.get('run_id','NO_RUN'),
                        cfg.get('user','John_Doe').strip().replace(" ","_"),
                        filename,
                        filename+'.h5'
                        )

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

    def new_filename_v1(self, data_obj):
        '''Return a new filename, based on name and timestamp.'''

        dir = self.create_data_dir(cfg['datadir'], name=data_obj._name,
                ts=data_obj._localtime)
        tstr = time.strftime('%H%M%S', data_obj._localtime)
        filename = '%s_%s.h5' % (tstr, data_obj._name)

        return os.path.join(dir, filename)
