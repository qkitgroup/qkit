# root init for QKIT
# these directories are treated as modules
# HR@KIT/2017/2018
__all__ = ['config','gui','measure','tools', 'analysis','core','instruments','services','storage','logs']


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
