import qkit
from qkit.core.lib import lockfile

import os
import sys
import logging

sys.path.append(qkit.cfg['coredir']) 
_lockname = os.path.join(qkit.cfg['coredir'], 'qkit.lock')
lockfile.set_filename(_lockname)

del _lockname

msg = "QTlab already running, start with '-f' to force start.\n"
msg += "Press s<enter> to start anyway or just <enter> to quit."

if qkit.cfg.get('set_lockfile',False):
    lockfile.check_lockfile(msg)
else:
    qkit.cfg['set_lockfile'] = False
    logging.info('S12_lockfile.py: not creating nor checking lockfile !!!')

del msg
