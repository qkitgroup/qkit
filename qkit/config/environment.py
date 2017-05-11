import tempfile

# create universal qkit-config. 
# Every module in qkit can rely on these entries to exist.
# In addition this is independent from qtlab
cfg = {}
cfg['datadir'] = tempfile.gettempdir()
cfg['qtlab'] = False

# plot related config settings
cfg['plot_engine'] = 'qkit.gui.qviewkit.main'
# message handling related port setting defaults
cfg['info_port'] = 5600  # this is the port we can listen on messages (signals) told by qkit 
cfg['ask_port']  = 5700  # this is the port rpc could use

# if qtlab is used (qt_cfg exists and qt_cfg['qtlab']): 
# qkit config entries are overridden by the qtlab ones
try:
    from lib.config import get_config
    qt_cfg = get_config()
    in_qt = qt_cfg.get('qtlab', False)
except ImportError:
    in_qt = False

if in_qt:
    for entry in qt_cfg.get_all():
        if entry in cfg.keys():
            cfg[entry] = qt_cfg[entry]

# there can also be a local config file for qkit (qkit/config/local.py) with variable cfg_local = {...}
try:
    from qkit.config.local import cfg_local
    for entry in cfg_local.iterkeys():
        cfg[entry] = cfg_local[entry]
except ImportError:
    pass
#-----------------------------------------------------------
# beyond this line, there can be system wide constants like 
# cfg['ministry'] = 'silly walks' 
