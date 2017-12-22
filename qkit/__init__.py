# root init for QKIT
# these directories are treated as modules
# HR@KIT/2017
__all__ = ['config','gui','measure','tools', 'analysis','core','instruments','storage','logs']

# load configuration 
from config.environment import cfg

# start initialization (qkit/core/init)
def start():
    print("starting QKIT ...")
    import core.startup
    core.startup.runinit()
    #from core.runinit import *
