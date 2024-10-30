# root init for QKIT
# these directories are treated as modules
# HR@KIT/2017/2018
__all__ = ['config','gui','measure','tools', 'analysis','core','instruments','services','storage','logs']


from qkit.config.config_holder import LazyConfClass
cfg = LazyConfClass()



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
