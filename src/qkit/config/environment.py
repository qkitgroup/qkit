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
cfg['logdir']  = os.path.join(cfg['qkitdir'],'../../logs')
cfg['execdir'] = cfg['qkitdir']
cfg['rootdir'] = cfg['qkitdir']
cfg['tempdir'] = tempfile.gettempdir()
cfg['datadir'] = os.path.join(cfg['qkitdir'],'data')

cfg['instruments_dir']      = os.path.join(cfg['qkitdir'],'drivers')
cfg['user_instruments_dir'] = None


##
## Save data with the new naming scheme
##
## Which version of datafolder structuring do you want?
##  1 = YYYYMMDD/HHMMSS_NAME
##  2 = RUN_ID/USERNAME/UUID_NAME
cfg['datafolder_structure'] = 2

##
## Create a database of all measurement-.h5 files with entries {uuid:abspath}
##
## load the file info database (fid):
#fid_scan_datadir = True
## check also the content of hdf files (slow) ?
#fid_scan_hdf     = False
## should the viewer object be created on startup (slow, needs pandas) ?
#fid_init_viewer  = True

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
#cfg['info_port'] = 5600  # this is the port we can listen on messages (signals) told by qkit
#cfg['info_host'] = 'localhost'  # this is the host we can listen on messages  

##
## Load QKIT remote interface service (ris), 
## The info service provides zmq based informations on port cfg['info_port'] 
#cfg['load_ri_service'] = False # default: False
#cfg['ris_port']  = 5700  # this is the port rpc could use
#cfg['ris_host']  = 'localhost' # as above

##
## File based QKIT logging for internal messages 
## the log file is located under cfg['logdir']
## stdout log is displayed in jupyter notebooks
## default log level is 'WARNING'
cfg['file_log_level'] =  'INFO' # one of ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
cfg['stdout_log_level'] = 'WARNING'

##
## check via git if updates are available
##
#cfg['check_for_updates'] = False

##
## Select which VISA library to use:
#cfg['visa_backend'] = '@ivi' # Use NI-VISA
#cfg['visa_backend'] = '@py' # Use pyvisa-py
#cfg['visa_backend'] = '' # (default) use NI-VISA if available, otherwise pyvisa-py

##
## Make png files at the end of the measurement
##
#cfg['save_png'] = True

##
## QT related options
## 
# we don't use qtlab anymore
cfg['qtlab'] = False

##
## To avoid huge log files, logfile maintainance is on per default.
## This keeps only the latest 10 logfiles in your logdir.
#cfg['maintain_logiles'] = True

#-----------------------------------------------------------
# below this line, there can be system wide constants like 
# cfg['ministry'] = 'silly walks'


