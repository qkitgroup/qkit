# -*- cod   ing: utf-8 -*-
"""
Created 2015

@author: hrotzing

Modified 2017 by S1
"""
import logging
import os
import time

from qkit.config.environment import cfg

alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


class DateTimeGenerator(object):
    """
    Class to generate filenames / directories based on the date and time.
    Date (YYYYMMDD) -> Time (HHMMSS) -> data
    """
    
    def __init__(self):
        self.returndict = {}
        self.returndict['_unix_timestamp'] = int(time.time())
        self.returndict['_localtime'] = time.localtime(self.returndict['_unix_timestamp'])
        self.returndict['_timestamp'] = time.asctime(self.returndict['_localtime'])
        self.returndict['_timemark'] = time.strftime('%H%M%S', self.returndict['_localtime'])
        self.returndict['_datemark'] = time.strftime('%Y%m%d', self.returndict['_localtime'])
        self.returndict['_uuid'] = encode_uuid(self.returndict['_unix_timestamp'])
    
    def new_filename(self, name=None):
        if cfg['new_data_structure']:
            self.new_filename_v2(name)
        else:
            self.new_filename_v1(name)
        self.returndict['_folder'] = os.path.join(cfg['datadir'], self.returndict['_relpath'])
        self.returndict['_filepath'] = os.path.join(self.returndict['_folder'], self.returndict['_filename'])
        
        return self.returndict
    
    def new_filename_v1(self, name):
        filename = '%s' % (self.returndict['_timemark'])
        if name != '' and name is not None:
            filename += '_%s' % (name)
        self.returndict['_filename'] = filename + '.h5'
        '''Old filename with datadir/YYMMDD/HHMMSS_name/HHMMSS_name.h5'''
        self.returndict['_relpath'] = os.path.join(
                self.returndict['_datemark'],
                filename
        )
    
    def new_filename_v2(self, name):
        filename = '%s' % (self.returndict['_uuid'])
        if name != '' and name is not None:
            filename += '_%s' % (name)
        self.returndict['_filename'] = filename + '.h5'
        '''New filename with datadir/run_id/user/uuid_name/uuid_name.h5'''
        if not cfg.has_key('user') or not cfg.has_key('run_id'):
            logging.warning(__name__ + ": cfg['user'] or cfg['run_id'] is not set. Using defaults. Have fun searching your data.")
        
        self.returndict['_relpath'] = os.path.join(
                cfg.get('run_id', 'NO_RUN'),
                cfg.get('user', 'John_Doe').strip().replace(" ", "_"),
                filename
        )


def encode_uuid(value):
    # if not value: value = self._unix_timestamp
    output = ''
    la = len(alphabet)
    while (value):
        output += alphabet[value % la]
        value = value / la
    return output[::-1]


def decode_uuid(string):
    # if not string: string = self._uuid
    output = 0
    multiplier = 1
    string = string[::-1].upper()
    la = len(alphabet)
    while (string != ''):
        f = alphabet.find(string[0])
        if f == -1:
            raise ValueError("Can not decode this: %s<--" % string[::-1])
        output += f * multiplier
        multiplier *= la
        string = string[1:]
    return output
