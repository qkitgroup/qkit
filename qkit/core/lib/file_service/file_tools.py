import os
import qkit
import threading
import logging


class store_db(object):
    def __init__(self):
        self.h5_db = {}
        self.set_db = {}
        self.measure_db = {}
        self.lock = threading.Lock()
        self.create_database()
    
    def __getitem__(self, key):
        with self.lock:
            return self.h5_db.get(key, None)
    
    def get(self, key, args=None):
        with self.lock:
            return self.h5_db.get(key, args)
    
    def update_database(self):
        with self.lock:
            logging.debug("Store_db: Start to update database.")
            for root, dirs, files in os.walk(qkit.cfg['datadir']):
                for f in files:
                    if f[-3:] == '.h5':
                        uuid = f[:6]
                        path = os.path.join(root, f)
                        self.h5_db[uuid] = path
                    elif f[-3:] == 'set':
                        uuid = f[:6]
                        path = os.path.join(root, f)
                        self.set_db[uuid] = path
                    elif f[-3:] == 'ent':
                        uuid = f[:6]
                        path = os.path.join(root, f)
                        self.measure_db[uuid] = path
            logging.debug("Store_db: Updating database done.")
    
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
