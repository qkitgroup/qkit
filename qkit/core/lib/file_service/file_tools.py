# -*- coding: utf-8 -*-
"""
Created 2018 

@author: MP, AS, HR@KIT / 2018

@license GPL
"""


import os
import qkit
import threading
import logging
import time

try:
    import h5py
    m_h5py = True
except ImportError as e:
    logging.error("store_db:%s"%e)
    m_h5py = False

class store_db(object):
    def __init__(self):
        self.h5_db = {}
        self.set_db = {}
        self.measure_db = {}
        self.h5_info = {}
        self.lock = threading.Lock()
        self.create_database()
        self.alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.scan_comment = False
        
    def get_uuid(self,time):
        """
        returns a UUID from a given time, e.g. returned by time.time()
        The UUID is returned with a precision of (integer) seconds 
        and has a fixed length of six characters.
        
        Derived from encode_uuid(), orginally located in hdf_DateTimeGenerator.py (AS/MP/HR)
        """
        # if not value: value = self._unix_timestamp
        output = ''
        time = int(time)
        la = len(self.alphabet)
        while time:
            output += self.alphabet[time % la]
            time = time / la
        return output[::-1]


    
    def get_time(self,uuid):
        """
        returns a integer time value from a given UUID timestamp (reverse of get_UUID())
        orginally located in hdf_DateTimeGenerator.py (AS/MP/HR)
        """
        # if not string: string = self._uuid
        output = 0
        multiplier = 1
        uuid = uuid[::-1].upper()
        la = len(self.alphabet)
        while uuid != '':
            f = self.alphabet.find(uuid[0])
            if f == -1:
                raise ValueError("store_db.get_time: Can not decode this: {}<--".format(uuid[::-1]))
            output += f * multiplier
            multiplier *= la
            uuid = uuid[1:]
        return output
        
    def get_date(self,uuid):
        """
        Returns a date string from a given UUID timestamp (reverse of get_uuid())
        """
        return time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(self.get_time(uuid)))
    
    def __getitem__(self, key):
        with self.lock:
            return self.h5_db.get(key, None)
    
    def get(self, key, args=None):
        with self.lock:
            return self.h5_db.get(key, args)

    def _collect_info(self,uuid,path):
            tm = ""
            dt = ""
            comment = ""
            
            try:
                tm = self.get_time(uuid)
                dt = self.get_date(uuid)
            except ValueError as e:
                logging.info(e)
            j_split = (path.replace('/', '\\')).split('\\')
            name = j_split[-1][7:-3]
            user = j_split[-3]
            run = j_split[-4]
            if m_h5py and self.scan_comment:
                try:
                    h5f=h5py.File(path)
                    comment = h5f['/entry/data0'].attrs.get('comment')
                    h5f.close()
                except Exception as e:
                    logging.error("store_db %s:%s"%(path,e))
                
            h5_info = {'time':tm,   'datetime':dt,     'name' : name, 
                       'user':user, 'comment':comment, 'run':run,}
            self.h5_info[uuid] = h5_info

    def _inspect_and_add_Leaf(self,fname,root):
        uuid = fname[:6]
        fqpath = os.path.join(root, fname)
        if fqpath[-3:] == '.h5':            
            self.h5_db[uuid] = fqpath
            self._collect_info(uuid,fqpath)
        elif fqpath[-3:] == 'set':
            self.set_db[uuid] = fqpath
        elif fqpath[-3:] == 'ent':
            self.measure_db[uuid] = fqpath
            
    def update_database(self):
        with self.lock:
            logging.debug("Store_db: Start to update database.")
            for root, dirs, files in os.walk(qkit.cfg['datadir']):
                for f in files:
                    self._inspect_and_add_Leaf(f,root)
            logging.debug("Store_db: Updating database done.")
    
#    def add_f(self,filename):
#        """
#        function to add a file to the store db.
#        filename: the full quaified filename of a hdf datafile.
#        """
        
    def add(self, h5_filename):
        uuid = h5_filename[:6]
        basename = h5_filename[:-2]
        if h5_filename[-3:] != '.h5':
            raise ValueError("Your filename '{:s}' is not a .h5 filename.".format(h5_filename))
        with self.lock:
            if os.path.isfile(basename + 'h5'):
                self.h5_db[uuid] = basename + 'h5'
                logging.debug("Store_db: Adding manually h5: " + basename + 'h5')
            else:
                raise ValueError("File '{:s}' does not exist.".format(basename + 'h5'))
            if os.path.isfile(basename + 'set'):
                self.set_db[uuid] = basename + 'set'
                logging.debug("Store_db: Adding manually set: " + basename + 'set')
            if os.path.isfile(basename + 'measurement'):
                self.h5_db[uuid] = basename + 'measurement'
                logging.debug("Store_db: Adding manually measurement: " + basename + 'measurement')
    
    def create_database(self):
        t = threading.Thread(target=self.update_database)
        t.start()
