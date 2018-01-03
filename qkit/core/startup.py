# This file brings QKIT around: init 
# YS@KIT/2017
# HR@kit/2017
import qkit
import os
import importlib

def start():
    #print('Starting the core of the Qkit framework...')
    initdir_name = 's_init'
    initdir = os.path.join(qkit.cfg.get('coredir'),initdir_name)
    filelist = os.listdir(initdir)
    filelist.sort()
    
    # load all modules starting with a 'S' character
    for module in filelist:
        if not module.startswith('S') or module[-3:] != '.py':
            continue
        print("Loading module ... "+module)
        importlib.import_module("."+module[:-3],package='qkit.core.'+initdir_name)
    del module        