# brings QKIT around 
# HR@KIT/2017 based on work by R. Heeres/2008
# YS@KIT/2018: Further emancipated from qtlab
from __future__ import print_function

import qkit
import logging

# orphanted code, not used in the moment
def _parse_options():
    import optparse
    parser = optparse.OptionParser(description='QKIT')
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
    qkit.cfg["qt_compatible"] = True
    logging.info("QKIT start: Enabling depreciated 'qt' module")

    class qt:
        """
        Placeholder for the deprecated qt module, used for legacy support.
        It is used as container for some modules previously imported through qt.
        """
        pass

    from qkit.core.flow import get_flowcontrol
    qt.instrument  = qkit.instrument
    qt.instruments = qkit.instruments

    qt.frontpanels = {}
    qt.sliders = {}
    qt.flow = get_flowcontrol()
    qt.msleep = qt.flow.measurement_idle
    qt.mstart = qt.flow.measurement_start
    qt.mend = qt.flow.measurement_end

    # this is a very bad hack to get around scope issues.
    try:
        import __builtin__
        __builtin__.qt = qt
    except ImportError:
        import builtins
        builtins.qt = qt
    # HR: Another hack to maintain compatibility:
    # Lets pretend that the original qt instrument and instruments modules 
    # are loaded. But instead every instrument driver loads tne qkit.core modules
    import sys
    sys.modules["instrument"] = qkit.core.instrument_base
    sys.modules["instruments"] = qkit.core.instrument_tools
    #sys.modules["qt"] = qkit.core.qt_qkit
    sys.modules["qt"] = qt

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
import qkit.core.flow as flow
register_exit(flow.qtlab_exit)
