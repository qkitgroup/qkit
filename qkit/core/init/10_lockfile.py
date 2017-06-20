from lib import config, lockfile
import os

#qtlab_path = 'C:\\qtlab-15a460b_notebook'
#qtlab_path = 'C:\\qkit\qkit\core' # YS: qtlab ripoff now in qkit/core - should not be hardcoded
print "Execdir: " + config.get_execdir()
_lockname = os.path.join(config.get_execdir(), 'qtlab.lock')
lockfile.set_filename(_lockname)
del _lockname
msg = "QTlab already running, start with '-f' to force start.\n"
msg += "Press s<enter> to start anyway or just <enter> to quit."
print '10_lockfile.py: not creating nor checking lockfile !!!'
#lockfile.check_lockfile(msg)