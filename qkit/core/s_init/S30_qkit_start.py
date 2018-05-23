# brings QKIT around 
# HR@KIT/2017 based on work by R. Heeres/2008
# YS@KIT/2018: Further emancipated from qtlab
from __future__ import print_function

import qkit
import logging

from qkit.core.lib import temp

temp.File.set_temp_dir(qkit.cfg['tempdir'])

#
# assign Instrument and Instruments 
#
from qkit.core.instrument_base import Instrument
from qkit.core.instrument_tools import Insttools

qkit.instrument = Instrument
qkit.instruments = Insttools()

#
# assign flow
#
import qkit.core.flow as flow

qkit.flow = flow.FlowControl()
qkit.flow.sleep = qkit.flow.measurement_idle
qkit.flow.start = qkit.flow.measurement_start
qkit.flow.end = qkit.flow.measurement_end

#
# legacy support qt
#
if qkit.cfg.get("qt_compatible", False):
    qkit.cfg["qt_compatible"] = True
    logging.info("QKIT start: Enabling depreciated 'qt' module")


    class qt:
        """
        Placeholder for the deprecated qt module, used for legacy support.
        It is used as container for some modules previously imported through qt.
        """
        pass


    qt.config = qkit.cfg

    qt.instrument = qkit.instrument
    qt.instruments = qkit.instruments

    qt.frontpanels = {}
    qt.sliders = {}

    from qkit.core.flow import get_flowcontrol

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
    sys.modules["qt"] = qt

# Other functions should be registered using qt.flow.register_exit_handler
from qkit.core.lib.misc import register_exit

register_exit(flow.qtlab_exit)
