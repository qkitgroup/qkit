# root init for QKIT
# these directories are treated as modules
# HR@KIT/2017/2018
__version__ = "0.2.0"
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
            
    def get(self, item,default=None):
        try:
            return self[item]
        except KeyError:
            if default is not None:
                self[item]=default
            return default
cfg = ConfClass()

# load configuration from $QKITDIR/config/*

try:
    from qkit.config.environment import cfg as cfg_local
    cfg.update(cfg_local)
except ImportError:
    pass

# if a local.py file is defined, load cfg dict and overwrite environment entries.
_config_sources = []
try:
    from qkit.config.local import cfg_local
    cfg.update(cfg_local)
    _config_sources += ["[qkit]src/qkit/config/local.py - cfg_local"]
    logging.warning("DEPRECATED: Loaded qkit.config.local.py! This has been deprecated in favour of qkit_local_config.py, see README!")
except ImportError:
    pass

try:    
    from qkit.config.local import cfg as cfg_local
    cfg.update(cfg_local)
    _config_sources += ["[qkit]src/qkit/config/local.py - cfg"]
    logging.warning("DEPRECATED: Loaded qkit.config.local.py! This has been deprecated in favour of qkit_local_config.py, see README!")
except ImportError:
    pass


def _load_user_config():
    """
    Loads user configuration from the file system, determined by known file names or environment variables.

    We usually run in a jupyter notebook. If qkit is installed as a package, a local config is not possible,
    and in the long run we should migrate towards a config not in the qkit directory.
    We will use two strategies here:
    1. Check if the environment variable 'QKIT_LOCAL_CONFIG' is set. Use the file it points to.
    2. Use current working directory:
      a. check if a qkit_conf.py file exists. If it does, use it.
      b. Else go to parrent directory and repeat
    If a file was found by either way, load it.

    We log information to stdout, as logging is not yet available. This code is executed before S10_logging.py,
    and will already have become unavailable once logging is initialized.
    """
    global _config_sources
    import os
    from pathlib import Path
    from itertools import chain

    user_config = None
    environment_variable_name = 'QKIT_LOCAL_CONFIG'
    config_file_names = ['qkit_local_config.py', 'local.py']

    if environment_variable_name in os.environ:
        # Inspect environment variable, should it exist
        print("Found environment variable '%s' for configuration." % environment_variable_name)
        user_config = os.environ[environment_variable_name]
    else:
        current_directory = Path(os.getcwd())
        for dir in chain([current_directory], current_directory.parents):
            for (index, config_file_name) in enumerate(config_file_names):
                test_path = dir / config_file_name
                if test_path.exists():
                    if test_path.is_file():
                        user_config = test_path
                        if index != 0:
                            print("WARNING: Found legacy configuration file name. Consider migrating.")
                        # We are done here
                        break
                    else:
                        print("WARNING: Found correct file system name %s, but was not a file?!" % test_path)

    # Load if found
    if user_config is not None:
        # https://stackoverflow.com/questions/67631/how-can-i-import-a-module-dynamically-given-the-full-path
        import importlib.util
        spec = importlib.util.spec_from_file_location("userconfig", user_config)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cfg.update(module.cfg)
        _config_sources += [user_config]

_load_user_config()
del _load_user_config

if len(_config_sources) > 1:
    logging.warn("Loaded more than one configuration file! This may cause conflicts! Sources:")
    logging.warn(_config_sources)
del _config_sources

# clean up 
del cfg_local
# init message
print ("QKIT configuration initialized -> available as qkit.cfg[...]")

"""
startup functions
"""
# start initialization (qkit/core/init)
def start(silent=False):
    if not silent:
        print("Starting QKIT framework ... -> qkit.core.startup")
    import qkit.core.startup
    qkit.core.startup.start(silent=silent)


"""
add a few convenience shortcuts 
"""
# remote interface client after qkit.start_ric() -> qkit.ric
from qkit.core.lib.com.ri_client import start_ric
