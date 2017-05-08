_cfg = config.create_config('C:\\qtlab-15a460b_notebook\qtlab.cfg')
#_cfg = config.create_config('qtlab.cfg')
_cfg.load_userconfig()
_cfg.setup_tempdir()
print _cfg

def _parse_options():
    import optparse
    parser = optparse.OptionParser(description='QTLab')
    parser.add_option('--nogui', default=False, action='store_true')
    parser.add_option('-p', '--port', type=int, default=0,
        help='Port to listen on for GUI/remote communication')
    parser.add_option('--name', type=str, default='',
        help='Shared instance name')
    parser.add_option('--nolock', default=False, action='store_true')

    args, pargs = parser.parse_args()
    logging.debug('Started with args %r', args)
    if args.nogui:
        _cfg['startgui'] = False
    if args.name:
        _cfg['instance_name'] = args.name
    if args.port:
        _cfg['port'] = args.port
_parse_options()

# Mark that we're in qtlab
_cfg['qtlab'] = True

import types
from instrument import Instrument
from lib.misc import exact_time, get_ipython
from lib import temp
from time import sleep

#set_debug(True)
from lib.network import object_sharer as objsh
objsh.root.set_instance_name(_cfg.get('instance_name', ''))
objsh.start_glibtcp_server(port=_cfg.get('port', objsh.PORT))
for _ipaddr in _cfg['allowed_ips']:
    objsh.SharedObject.server.add_allowed_ip(_ipaddr)
objsh.PythonInterpreter('python_server', globals())
if _cfg['instrument_server']:
    from lib.network import remote_instrument
    remote_instrument.InstrumentServer()

if False:
    import psyco
    psyco.full()
    logging.info('psyco acceleration enabled')
else:
    logging.info('psyco acceleration not enabled')

import qt
from qt import plot, plot3, Plot2D, Plot3D, Data

from numpy import *
import numpy as np
try:
    from scipy import constants as const
except:
    pass

import time
# Auto-start GUI
print qt.config.get('startgui', False)
if qt.config.get('startgui', True):
    qt.flow.start_gui()
    qt.mstart()
    qt.msleep(2)
    qt.mend()
    

temp.File.set_temp_dir(qt.config['tempdir'])

# change startdir if commandline option is given
if __startdir__ is not None:
    qt.config['startdir'] = __startdir__
# FIXME: use of __startdir__ is spread over multiple scripts:
# 1) source/qtlab_client_shell.py
# 2) init/02_qtlab_start.py
# This should be solved differently

# Set exception handler
'''
try:
    import qtflow
    # Note: This does not seem to work for 'KeyboardInterrupt',
    # likely it is already caught by ipython itself.
    get_ipython().set_custom_exc((Exception, ), qtflow.exception_handler)
except Exception, e:
    print 'Error: %s' % str(e)
'''
	
# Other functions should be registered using qt.flow.register_exit_handler
from lib.misc import register_exit
import qtflow
register_exit(qtflow.qtlab_exit)
