from lib.network.object_sharer import helper
import time

from lib import config
config = config.get_config()

class constants():
    FLAG_GET = 0x01
    FLAG_SET = 0x02
    FLAG_GETSET = 0x03
    FLAG_GET_AFTER_SET = 0x04
    FLAG_SOFTGET = 0x08
    FLAG_PERSIST = 0x10

flow = helper.find_object('%s:flow' % config['instance_name'])
for i in range(100):
    status = flow.get_status()
    if not (status is None or status == "starting"):
        break
    print 'Status: %r, waiting...' % status
    time.sleep(2)

instruments = helper.find_object('%s:instruments1' % config['instance_name'])
plots = helper.find_object('%s:namedlist_plot' % config['instance_name'])
data = helper.find_object('%s:namedlist_data' % config['instance_name'])
interpreter = helper.find_object('%s:python_server' % config['instance_name'])
frontpanels = {}
sliders = {}

from lib.gui.qtwindow import QTWindow
windows = QTWindow.get_named_list()

def get_instrument_proxy(name):
    return helper.find_object('%s:instrument_%s' % (config['instance_name'], name))

def get_data_proxy(name):
    return helper.find_object('%s:data_%s' % (config['instance_name'], name))

def get_plot_proxy(name):
    return helper.find_object('%s:plot_%s' % (config['instance_name'], name))

def cmd(cmd, callback=None):
    '''Execute a python command in the server.'''
    return interpreter.cmd(cmd, callback=callback)

def replot_all():
    cmd('qt.replot_all()', callback=lambda x:None)

def format_parameter_value(opt, val):
    if val is None:
        return ''
    try:
        if 'format_map' in opt:
            valstr = opt['format_map'][val]
        else:
            if 'format' in opt:
                format = opt['format']
            else:
                format = '%s'

            if type(val) in (types.ListType, types.TupleType):
                val = tuple(val)

            elif type(val) is types.DictType:
                fmt = ""
                first = True
                for k in val.keys():
                    if first:
                        fmt += '%s: %s' % (k, format)
                        first = False
                    else:
                        fmt += ', %s: %s' % (k, format)
                format = fmt
                val = tuple(val.values())

            elif val is None:
                val = ''

            valstr = format % (val)

    except Exception, e:
        valstr = str(val)

    if 'units' in opt:
        unitstr = ' %s' % opt['units']
    else:
        unitstr = ''

    return '%s%s' % (valstr, unitstr)

