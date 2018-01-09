import os
import qkit

class store_db(object):
    def __init__(self):
        self.h5_db    = {}
        self.set_db  = {}
        self.measure_db = {}
        self.create_database()
        
    def __getitem__(self,key):
        return self.h5_db.get(key,None)
    
    def get(self,key,args=None):
        return self.h5_db.get(key,args)

    def update_database(self):        
        for root, dirs, files in os.walk(qkit.cfg['datadir']):
            for f in files:
                if f[-3:] == '.h5':
                    uuid = f[:6]
                    path = os.path.join(root,f)
                    self.h5_db[uuid] = path
                elif f[-3:] == 'set':
                    uuid = f[:6]
                    path = os.path.join(root,f)
                    self.set_db[uuid] = path
                elif f[-3:] == 'ent':
                    uuid = f[:6]
                    path = os.path.join(root,f)
                    self.measure_db[uuid] = path

    def create_database(self):
        self.update_database()