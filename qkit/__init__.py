# root init for QKIT
# these directories are treated as modules
# HR@KIT/2017/2018
__all__ = ['config','gui','measure','tools', 'analysis','core','instruments','services','storage','logs']

import os.path
import logging
class QkitCfgError(Exception):
    '''
    If something with qkit.cfg does not fit to what the user wants to do, this is the error to throw.
    '''
    pass

class ConfClass(dict):
    def __init__(self, *args):
        dict.__init__(self, args)
    def preset_analyse(self,verbose = False):
        """ Sets basic settings, most of the services are not loaded (default)
            The file index service is run and the UUID registry is populated.
        """

        self['load_info_service'] = False
        self['load_ri_service']   = False
        self['load_visa']         = False
        if verbose:
            print ("Not starting the info_service, ri_service and visa.")
    def preset_measure(self,verbose = False):
        """ Setup of the measurement settings, services are loaded or initialized.
        """
        self['load_info_service'] = True
        self['load_ri_service']   = True
        self['load_visa']         = True
        
        if self['datadir'] == os.path.join(self['qkitdir'],'data'):
                print("Please set a valid data directory! (datadir)")
        if verbose:
            print ("Starting the info_service, ri_service and visa.")
cfg = ConfClass()

# load configuration from $QKITDIR/config/*

try:
    from qkit.config.environment import cfg as cfg_local
    cfg.update(cfg_local)
except ImportError:
    pass

# if a local.py file is defined, load cfg dict and overwrite environment entries.
try:
    from qkit.config.local import cfg_local
    cfg.update(cfg_local)
except ImportError:
    pass

try:    
    from qkit.config.local import cfg as cfg_local
    cfg.update(cfg_local)
except ImportError:
    logging.warning("No local config file found. Basic functionality will still work. Please have a look at the qkit/config/local.py_template")


# clean up 
del cfg_local
# init message
print ("QKIT configuration initialized -> available as qkit.cfg[...]")

"""
startup functions
"""
# start initialization (qkit/core/init)
def start():
    print("Starting QKIT framework ... -> qkit.core.startup")
    import qkit.core.startup
    qkit.core.startup.start()


"""
add a few convenience shortcuts 
"""
# remote interface client after qkit.start_ric() -> qkit.ric
from qkit.core.lib.com.ri_client import start_ric