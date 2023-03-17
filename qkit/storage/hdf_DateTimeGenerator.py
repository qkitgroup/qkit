# -*- coding: utf-8 -*-
"""
Created 2015

@author: hrotzing

Modified 2017 by S1
"""
import logging
import os
import time
import qkit

alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


class DateTimeGenerator(object):
    """DateTimeGenerator class to provide a timestamp for each measurement file
    upon creation.
    
    For sorting and unique identification across multiple measurement setups
    we provide a timestamp for each h5 file created with qkit. We use the unix
    timestamp to get time resolution of one second which should be enough for
    our needs. The integer timestamp is then converted either into a HHMMSS
    representation using day and month information to create a folder, or the
    timestamp gets converted using the alphabet to create a 6 digit UUID.
    """
    
    def __init__(self):
        self.returndict = {}
        self.returndict['_unix_timestamp'] = int(time.time())
        self.returndict['_localtime'] = time.localtime(self.returndict['_unix_timestamp'])
        self.returndict['_timestamp'] = time.asctime(self.returndict['_localtime'])
        self.returndict['_timemark'] = time.strftime('%H%M%S', self.returndict['_localtime'])
        self.returndict['_datemark'] = time.strftime('%Y%m%d', self.returndict['_localtime'])
        self.returndict['_uuid'] = encode_uuid(self.returndict['_unix_timestamp'])
    
    # call for h5 filename, qkit config gets checked for encoding procedure.
    def new_filename(self, name=None):
        if qkit.cfg.get('datafolder_structure',1) == 2:
            self.new_filename_v2(name) # 6 digit UUID
        else:
            self.new_filename_v1(name) # HHMMSS representation
        self.returndict['_folder'] = os.path.join(qkit.cfg['datadir'], self.returndict['_relfolder'])
        self.returndict['_relpath'] = os.path.join(self.returndict['_relfolder'],self.returndict['_filename'])
        self.returndict['_filepath'] = os.path.join(self.returndict['_folder'], self.returndict['_filename'])
        
        return self.returndict
    
    def new_filename_v1(self, name):
        filename = str(self.returndict['_timemark'])
        if name != '' and name is not None:
            filename += '_' + str(name)
        self.returndict['_filename'] = filename + '.h5'
        '''Old filename with datadir/YYMMDD/HHMMSS_name/HHMMSS_name.h5'''
        self.returndict['_relfolder'] = os.path.join(
                self.returndict['_datemark'],
                filename
        )
    
    def new_filename_v2(self, name):
        filename = str(self.returndict['_uuid'])
        if name != '' and name is not None:
            filename += '_' + str(name)
        self.returndict['_filename'] = filename + '.h5'
        '''New filename with datadir/run_id/user/uuid_name/uuid_name.h5'''
        
        self.returndict['_relfolder'] = os.path.join(
                qkit.cfg.get('run_id', 'NO_RUN').strip().replace(" ", "_").upper(),
                qkit.cfg.get('user', 'John_Doe').strip().replace(" ", "_"),
                filename
        )


def encode_uuid(value):
    """Encodes the integer unix timestamp into a 6 digit UUID using the alphabet.
    
    Args:
        Integer-cast unix timestamp.
    Return:
        6 digit UUID string.
    """
    # if not value: value = self._unix_timestamp
    output = ''
    la = len(alphabet)
    while value:
        output += alphabet[value % la]
        value = int(value / la)
    return output[::-1]


def decode_uuid(string):
    """Decodes the 6 digit UUID back into integer unix timestamp.
    
    Args:
        6 digit UUID string.        
    Return:
        Integer-cast unix timestamp.
    """
    # if not string: string = self._uuid
    output = 0
    multiplier = 1
    string = string[::-1].upper()
    la = len(alphabet)
    while string != '':
        f = alphabet.find(string[0])
        if f == -1:
            raise ValueError("Can not decode this: {}<--".format(string[::-1]))
        output += f * multiplier
        multiplier *= la
        string = string[1:]
    return output
