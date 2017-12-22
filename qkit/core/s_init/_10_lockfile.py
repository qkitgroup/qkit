import qkit
from qkit.core.lib import lockfile

import os
import sys


sys.path.append(qkit.cfg['coredir']) 
_lockname = os.path.join(qkit.cfg['coredir'], 'qkit.lock')
lockfile.set_filename(_lockname)

del _lockname

msg = "QTlab already running, start with '-f' to force start.\n"
msg += "Press s<enter> to start anyway or just <enter> to quit."

print '10_lockfile.py: not creating nor checking lockfile !!!'
#lockfile.check_lockfile(msg)
del msg