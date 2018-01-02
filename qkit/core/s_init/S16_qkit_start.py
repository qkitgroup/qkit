# HR@KIT/2017 based on work by R. Heeres/2008

import qkit
import logging

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



from qkit.core.lib import temp
temp.File.set_temp_dir(qkit.cfg['tempdir'])


#
# assign Instrument and Instruments 
#
from qkit.core.instrument_base import Instrument 
from qkit.core.instrument_tools import Insttools
qkit.instrument  = Instrument
qkit.instruments = Insttools()

if qkit.cfg.get("qt_compatible",True):
    qkit.cfg["qt_compatible"]=True
    print("QKIT start: Enabling depreciated 'qt' module")
    import qkit.core.qt as qt
    
    qt.instrument  = qkit.instrument
    qt.instruments = qkit.instruments

    # this is a very bad hack to get around scope issues.
    import __builtin__
    __builtin__.qt = qt
    


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
from qkit.core.lib.misc import register_exit
import qkit.core.qtflow as qtflow
register_exit(qtflow.qtlab_exit)
