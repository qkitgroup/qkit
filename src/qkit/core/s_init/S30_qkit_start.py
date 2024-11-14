# brings QKIT around 
# HR@KIT/2017 based on work by R. Heeres/2008
# YS@KIT/2018: Further emancipated from qtlab
from __future__ import print_function

import qkit
import logging

from qkit.core.lib import temp

temp.File.set_temp_dir(qkit.cfg['tempdir'])

#
# assign instruments
#
from qkit.core.instrument_tools import Insttools

qkit.instruments = Insttools()

#
# assign flow
#
import qkit.core.flow as flow

qkit.flow = flow.FlowControl()
qkit.flow.sleep = qkit.flow.measurement_idle
qkit.flow.start = qkit.flow.measurement_start
qkit.flow.end = qkit.flow.measurement_end

if qkit.cfg.get("qt_compatible", False):
    raise ValueError("We do no longer provide legacy qtlab support. Please set qkit.cfg['qt_compatible']=False and clean up your code.")

# Other functions should be registered using qt.flow.register_exit_handler
from qkit.core.lib.misc import register_exit

register_exit(flow.qtlab_exit)
