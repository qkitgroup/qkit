import logging
import qt
import os

def open_log_file(path,log_level=logging.INFO):
    fn, ext = os.path.splitext(path)
    fn = fn + '.log'
    if len(logging.getLogger().handlers) > 0:
      formatter = logging.getLogger().handlers[0].formatter
    else:
      formatter = None

    log_file_handler = logging.FileHandler(fn)
    log_file_handler.setLevel(log_level)
    log_file_handler.setFormatter(formatter)
    logging.getLogger().addHandler(log_file_handler)
    logging.debug('Added log_file_handler. path="%s", formatter="%s"' % (fn, str(formatter)))
    return log_file_handler

def close_log_file(log_file_handler):
    if log_file_handler is not None:
        logging.getLogger().removeHandler(log_file_handler)
        log_file_handler.close()
        log_file_handler = None

def write_settings_file(self, path):
    fn, ext = os.path.splitext(path)
    fn_log = fn + '.set'
    f = open(fn_log, 'w+')
    f.write('Filename: %s\n' % fn)

    inslist = _dict_to_ordered_tuples(qt.instruments.get_instruments())
    for (iname, ins) in inslist:
        f.write('Instrument: %s\n' % iname)
        parlist = _dict_to_ordered_tuples(ins.get_parameters())
        for (param, popts) in parlist:
            f.write('\t%s: %s\n' % (param, ins.get(param, query=False)))

    f.close()

def _dict_to_ordered_tuples(dic):
    '''Convert a dictionary to a list of tuples, sorted by key.'''
    if dic is None:
        return []
    keys = dic.keys()
    keys.sort()
    ret = [(key, dic[key]) for key in keys]
    return ret