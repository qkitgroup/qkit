import qkit
import os
import logging
from time import strftime


def cleanup_logfiles():
    '''
    if qkit.cfg['maintain_logiles'] is not False, this script checks the log folder and removes all log files except for the latest 10.
    :return:
    '''
    if qkit.cfg.get('maintain_logfiles',True):
        ld = [filename for filename in os.listdir(qkit.cfg['logdir']) if filename.startswith('qkit') and filename.endswith('.log')]
        ld.sort()
        for f in ld[:-10]:
            try:
                os.remove(os.path.join(qkit.cfg['logdir'], f))
            except:
                pass


def _setup_logging():
    fileLogLevel = getattr(logging, qkit.cfg.get('file_log_level', 'WARNING'))
    stdoutLogLevel = getattr(logging, qkit.cfg.get('stdout_log_level', 'WARNING'))
    
    rootLogger = logging.getLogger()
    
    fileLogger = logging.FileHandler(filename=os.path.join(qkit.cfg['logdir'], strftime('qkit_%Y%m%d_%H%M%S.log')), mode='a+')
    fileLogger.setFormatter(
            logging.Formatter('%(asctime)s %(levelname)-8s: %(message)s (%(filename)s:%(lineno)d)',
                              datefmt='%Y-%m-%d %H:%M:%S'))
    fileLogger.setLevel(fileLogLevel)
    
    jupyterLogger = logging.StreamHandler()
    jupyterLogger.setFormatter(
            logging.Formatter('%(asctime)s [%(levelname)-8s]: %(message)s (%(filename)s:%(lineno)d)',
                              datefmt='%Y-%m-%d %H:%M:%S'))
    jupyterLogger.setLevel(stdoutLogLevel)
    
    rootLogger.addHandler(fileLogger)
    rootLogger.addHandler(jupyterLogger)
    rootLogger.setLevel(min(stdoutLogLevel, fileLogLevel))
    
    logging.info(' ---------- LOGGING STARTED ---------- ')
    
    logging.debug('Set logging level for file to: %s ' % fileLogLevel)
    logging.debug('Set logging level for stdout to: %s ' % stdoutLogLevel)
    
    cleanup_logfiles()

def set_debug(enable):
    logger = logging.getLogger()
    if enable:
        logger.setLevel(logging.DEBUG)
        logging.info('Set logging level to DEBUG')
    else:
        logger.setLevel(logging.INFO)
        logging.info('Set logging level to INFO')


_setup_logging()
