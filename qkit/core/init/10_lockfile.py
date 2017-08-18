from qkit.core.lib import lockfile
from qkit.core.lib.config import create_config
import os
import sys

_config = create_config()

sys.path.append(_config['coredir']) # YS: necessary to make it run without cd into coredir as the driver files import Instrument from instrument.

_lockname = os.path.join(_config['coredir'], 'qtlab.lock')
lockfile.set_filename(_lockname)

del _lockname, _config

msg = "QTlab already running, start with '-f' to force start.\n"
msg += "Press s<enter> to start anyway or just <enter> to quit."

print '10_lockfile.py: not creating nor checking lockfile !!!'
#lockfile.check_lockfile(msg)
del msg