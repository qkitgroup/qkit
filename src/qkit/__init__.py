# root init for QKIT
# these directories are treated as modules
# HR@KIT/2017/2018
__all__ = ['config','gui','measure','tools', 'analysis','core','instruments','services','storage','logs']


"""
Type hint declarations for easier programming.
TYPE_CHECKING is False at runtime, so it isn't breaking qkit, but True when evaluating variable types
for IntelliSense, making programming easier.
"""
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from qkit.core.lib.file_service.file_info_database import fid as fid_class
    from qkit.core.instrument_tools import Insttools
    from qkit.config.config_holder import ConfClass
    from qkit.core.s_init.S16_available_modules import ModuleAvailable
fid: 'fid_class'  # Initilaized in S80_load_file_service
cfg: 'ConfClass'  # Initialized by lazy-loading in __getattr__ (see below)
instruments: 'Insttools'
module_available: 'ModuleAvailable'  # Initialized in S16_available_modules

def __getattr__(name):
    """
    Lazy Loading support for qkit configuration. Based on PEP 562: Module __getattr__ and __dir__
    """
    global cfg
    if name == "cfg":
        print("Lazy-Loading configuration...")
        from qkit.config.config_holder import ConfClass
        cfg = ConfClass()
        return cfg
    raise AttributeError("qkit has no attribute " + name)

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
