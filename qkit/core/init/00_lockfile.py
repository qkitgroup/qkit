from lib import config, lockfile
import os

qtlab_path = 'C:\\qtlab-15a460b_notebook'
print config.get_execdir()
_lockname = os.path.join(qtlab_path, 'qtlab.lock')
lockfile.set_filename(_lockname)
del _lockname

msg = "QTlab already running, start with '-f' to force start.\n"
msg += "Press s<enter> to start anyway or just <enter> to quit."
print '00_lockfile.py: not checking lockfile !!!'
#lockfile.check_lockfile(msg)
