import os
import qkit

def create_database():
    qkit.store_db = {}
    for root, dirs, files in os.walk(qkit.cfg['datadir']):
        for f in files:
            if f[-3:] == '.h5':
                uuid = f[:6]
                path = os.path.join(root,f)
                qkit.store_db[uuid] = path