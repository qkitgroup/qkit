import os
import sys
from lib.misc import exit_shell

_remove_lock = True
_filename = None

def set_filename(fn):
    global _filename
    _filename = fn

def get_lockfile():
    global _filename
    return _filename

def remove_lockfile():
    if not _remove_lock:
        return

    if os.path.exists(get_lockfile()):
        os.remove(get_lockfile())

def check_lockfile(msg):
    if os.path.exists(get_lockfile()):
        if '-f' not in sys.argv:
            print msg

            line = sys.stdin.readline().strip()
            if line != 's':
                global _remove_lock
                _remove_lock = False
                exit_shell()

    f = file(get_lockfile(), 'w+')
    f.close()
