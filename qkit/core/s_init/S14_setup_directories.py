# HR@KIT 2017 / R.Heeres 2008
import qkit
import os
import sys
import logging

def _set_insdir():
    instdir = qkit.cfg.get('instruments_dir', None)
    if instdir and os.path.exists(instdir):

        sys.path.append(instdir)
        qkit.cfg['instruments_dir'] = instdir
        logging.info('Set instruments dir to %s'% instdir)
        return instdir
    else:
        qkit.cfg['instruments_dir'] = None
        logging.warning(__name__ + ' : "%s" is not a valid path for instruments_dir, setting to None' % instdir)  
        return None

def _set_user_insdir():
    '''
    Setting directory for user-specific instruments.
    For this config['user_instruments_dir'] needs to be defined.
    '''

    instdir = qkit.cfg.get('user_instruments_dir', None)

    if instdir and os.path.exists(instdir):
        absdir = os.path.abspath(instdir)
        qkit.cfg['user_instruments_dir'] = absdir
        logging.info('Set user instruments dir to %s'% absdir)
    else:
        qkit.cfg['user_instruments_dir'] = None
        logging.info(__name__ + ' : "%s" is not a valid path for user_instruments_dir, setting to None' % instdir)
        return None

    # old code below, may not be needed anymore
    if sys.path.count(absdir) != 0:
        return absdir
    else:
        idx = sys.path.index(_insdir)
        sys.path.insert(idx, absdir)
        return absdir


_insdir = _set_insdir()
_user_insdir = _set_user_insdir()
