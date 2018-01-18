import qkit
import os
import logging


def _setup_logging():
    fileLogLevel = getattr(logging, qkit.cfg.get('file_log_level', 'WARNING'))
    stdoutLogLevel = getattr(logging, qkit.cfg.get('stdout_log_level', 'WARNING'))
    
    rootLogger = logging.getLogger()
    
    fileLogger = logging.FileHandler(filename=os.path.join(qkit.cfg['logdir'], 'qkit.log'), mode='a+')
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
    
    logging.debug(' ---------- LOGGING STARTED ---------- ')
    
    logging.info('Set logging level for file to: %s ' % fileLogLevel)
    logging.info('Set logging level for stdout to: %s ' % stdoutLogLevel)


def set_debug(enable):
    logger = logging.getLogger()
    if enable:
        logger.setLevel(logging.DEBUG)
        logging.info('Set logging level to DEBUG')
    else:
        logger.setLevel(logging.INFO)
        logging.info('Set logging level to INFO')


_setup_logging()
