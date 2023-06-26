# R. Heeres 2008
# HR@KIT 2017
import qkit
import os
import logging

if qkit.cfg.get('startdir',False):
    os.chdir(qkit.cfg.get('startdir'))


if qkit.cfg.get('startscript',False):
    _scripts = qkit.cfg.get('startscript')
    if type(_scripts) not in (list, tuple):
        _scripts = [_scripts, ]
    for _s in _scripts:
        if os.path.isfile(_s):
            print('Executing (user startscript): %s' % _s)
            execfile(_s)
        else:
            logging.warning('Did not find startscript "%s", skipping'%_s)


if qkit.cfg.get('exitscript',False):
    _scripts = qkit.cfg.get('exitscript')
    if type(_scripts) not in (list, tuple):
        _scripts = [_scripts, ]
    for _s in _scripts:
        if os.path.isfile(_s):
            qkit.flow.register_exit_script(_s)
        else:
            logging.warning('Did not find exitscript "%s", will not be executed', _s)

# Start IPython command logging if requested
if qkit.cfg.get('ipython_logfile',None):
    from IPython import get_ipython
    _ip = get_ipython()
    _ip.IP.logger.logstart(logfname=qkit.cfg.get('ipython_logfile'), logmode='append')
