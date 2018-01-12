# file to define the default environment of QKIT
##############################################################################
# Please do not make changes to this file unless you know what you are doing !!!
# If you want to redefine settings, please copy the file 
# local.py_template -> local.py or
# environment.py -> local.py
# and make changes there.
##############################################################################
# create universal qkit-config. 
# Every module in qkit can rely on these entries to exist.
# This file is independent from qtlab
# HR@KIT 2015

import qkit
import os
import tempfile

##
## the configuration dictionary; later available as qkit.cfg[...]
##
cfg = {}

##
## A few path definitions:
##
# set up default path for
cfg['qkitdir'] = os.path.split(qkit.__file__)[0]
cfg['coredir'] = os.path.join(cfg['qkitdir'],'core')
cfg['logdir']  = os.path.join(cfg['qkitdir'],'logs')
cfg['execdir'] = cfg['qkitdir']
cfg['rootdir'] = cfg['qkitdir']
cfg['tempdir'] = tempfile.gettempdir()
cfg['datadir'] = tempfile.gettempdir()

cfg['instruments_dir']      = os.path.join(cfg['qkitdir'],'instruments')
cfg['user_instruments_dir'] = tempfile.gettempdir()


##
## Save data with the new naming scheme
##
cfg['datafolder_structure'] = 1

##
## Create a database of all measurement-.h5 files with entries {uuid:abspath}
##
#cfg['load_file_service'] = True

##
## Load (py) visa (Virtual Instrument Software Architecture) lib 
##
#cfg['load_visa'] = False


##
## set and define the plot engine 
## in the moment only qviewkit is supported
cfg['plot_engine'] = 'qkit.gui.qviewkit.main' # default: qviewkit

##
## Load QKIT info service, 
## The info service provides zmq based informations on port cfg['info_port'] 
#cfg['load_info_service'] = True # default: True
cfg['info_port'] = 5600  # this is the port we can listen on messages (signals) told by qkit
cfg['info_host'] = 'localhost'  # this is the host we can listen on messages  
cfg['ask_port']  = 5700  # this is the port rpc could use
cfg['ask_host']  = 'localhost' # as above

##
## File based QKIT logging for internal messages 
## the log file is located under cfg['logdir']
## default log level is 'WARNING'
cfg['log_level'] =  'DEBUG' # one of ['WARNING', 'DEBUG', 'INFO', 'ERROR', 'CRITICAL']

##
## QT related options
## 
# we don't use qtlab anymore
cfg['qtlab'] = False

##
## Try to be compatible with QT lab 
## (by default we try to be compatible for now)
#cfg['qt_compatible'] = True 

# !!!! depreciated 'qt' module !!!!
# if qtlab is used (qt_cfg exists and qt_cfg['qtlab']): 
# qkit config entries are overridden by the qtlab ones
cfg['use_qtlab_config'] = True

if cfg['use_qtlab_config']:
    try:
        from qkit.core.lib.config import get_config
        qt_cfg = get_config()
        in_qt = qt_cfg.get('qtlab', False)
    except ImportError:
        in_qt = False
    
    if in_qt:
        for entry in qt_cfg.get_all():
            if entry in cfg.keys():
                cfg[entry] = qt_cfg[entry]


# there can also be a local config file for qkit (qkit/config/local.py) with variable cfg = {...}
#try:
#    from qkit.config.local import cfg as cfg_local
#    for entry in cfg_local.iterkeys():
#        cfg[entry] = cfg_local[entry]
#except ImportError:
#    pass
#-----------------------------------------------------------
# below this line, there can be system wide constants like 
# cfg['ministry'] = 'silly walks' 



