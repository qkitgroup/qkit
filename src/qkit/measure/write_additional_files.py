import logging
import json
import qkit
#from qkit.measure.measurement_class.Measurement import _JSON_instruments_dict
from qkit.measure.json_handler import QkitJSONEncoder, QkitJSONDecoder
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

def get_instrument_settings(path):
    fn, ext = os.path.splitext(path)
    instr_dict = {}
    for ins_name in qkit.instruments.get_instruments():
        ins = qkit.instruments.get(ins_name)
        param_dict = {}
        for (param, popts) in _dict_to_ordered_tuples(ins.get_parameters()):
            param_dict.update({param:ins.get(param, query=False, channels=popts)})
            try:
                if popts.get('offset',False):
                    param_dict.update({param+"_offset": ins._offsets[param]})
            except:
                pass
        instr_dict.update({ins_name:param_dict})
    with open(fn+'.set','w+') as filehandler:
        json.dump(obj=instr_dict, fp=filehandler, cls=QkitJSONEncoder, indent = 4, sort_keys=True)

    return instr_dict
    """
    fn_log = fn + '.set'
    f = open(fn_log, 'w+')
    f.write('Filename: %s\n' % fn)
    settings = ''

    inslist = _dict_to_ordered_tuples(qkit.instruments.get_instruments())
    for (iname, ins) in inslist:
        settings += 'Instrument: %s (%s)\n' % (iname, ins.get_type())
        parlist = _dict_to_ordered_tuples(ins.get_parameters())
        for (param, popts) in parlist:
            settings += '\t%s: %s\n' % (param, ins.get(param, query=False, channels=popts))

    f.write(settings)
    f.close()
    return settings
    """

def _dict_to_ordered_tuples(dic):
    '''Convert a dictionary to a list of tuples, sorted by key.'''
    if dic is None:
        return []
    keys = sorted(dic.keys())
    ret = [(key, dic[key]) for key in keys]
    return ret
