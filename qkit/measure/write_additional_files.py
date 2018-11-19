import logging
import qkit
import os
import re
import inspect
try:
    import dill
    dill_found = True
except ImportError:
    dill_found = False


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


def write_vawg_channels_sequence_dict(path):
    for vawg in qkit.instruments.get_instruments_by_type('VirtualAWG'):
        name = vawg.get_name()
        fn, ext = os.path.splitext(path)
        if dill_found:
            vawg.save_channels(fn + '_' + name + '.dil')
        sequence_dicts = vawg.get_sequence_dicts()
        channels = _sort_vawg_sequence_dicts(sequence_dicts)
        with open(fn + '_' + name+ ' .chn', 'w+') as outfile:
            outfile.write(channels)


def _dict_to_ordered_tuples(dic):
    '''Convert a dictionary to a list of tuples, sorted by key.'''
    if dic is None:
        return []
    keys = dic.keys()
    keys.sort()
    ret = [(key, dic[key]) for key in keys]
    return ret


def _sort_vawg_sequence_dicts(sequence_dicts):
    channels = ''
    for i, chan in enumerate(sequence_dicts):
        channels += ('chan_{}:\n'.format(i))
        sequences = dict((key, val) for key, val in chan.iteritems() if str(key)[:8] == 'sequence')
        for key, values in sequences.iteritems():
            channels += '\t{}:\n'.format(key)
            for j, pulse in enumerate(values):
                channels += '\t\tobject_{}:\n'.format(j)
                for k, v in pulse.iteritems():
                    if callable(v):
                        v = inspect.getsource(v)[:-1]
                        if 'def' in v:
                            channels += '\t\t\t{}:{}\n'.format(k, v)
                        elif k in v:
                            start_index = v.find(k) + len(k + ' = ')
                            end_index = v.find(',', start_index)
                            channels += '\t\t\t{}:{}\n'.format(k, v[start_index:end_index])
                        elif re.split(' |\(', v).count('lambda') == 1:
                            start_index = v.find('lambda')
                            end_index = v.find(',', start_index)  # if there is no , end_index = -1, which works well as
                            channels += '\t\t\t{}:{}\n'.format(k, v[start_index:end_index])  # lambda function will be before a ')'
                        else:
                            channels += '\t\t\t{}:{}\n'.format(k, v)  # Better save everything than to miss an option
                    else:
                        channels += '\t\t\t{}:{}\n'.format(k, v)
        channels += '\tinterleave: {}\n'.format(chan['interleave'])
        params = dict((key, val) for key, val in chan.iteritems() if str(key)[:3] == 'par')
        for k, v in params.iteritems():
            channels += '\t{}:\n'.format(k)
            channels += '\t\t' + ''.join('{}, '.format(l) + '\n\t\t' * ((n + 1) % 5 == 0) for n, l in enumerate(v))
            if channels[-2:] == '\t\t':  # removing unwanted tabs at the end
                channels = channels[:-2]
    return channels
