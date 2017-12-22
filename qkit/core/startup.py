# Script to initialize the startup routine for the Qkit core
# (replacing qtlab_shell)
# YS@KIT/2017
# HR@kit/2017
import qkit
import os
import importlib

def runinit():

    initdir = os.path.join(qkit.cfg.get('coredir'),'s_init')
    filelist = os.listdir(initdir)
    print('Starting the core of the Qkit framework...')
    
    for module in filelist:
        if module == '__init__.py' or module[-3:] != '.py':
            continue
        importlib.import_module("."+module[:-3],package='qkit.core.s_init')
    del module