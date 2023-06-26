import numpy as np


def seconds_to_str(secs):
    '''Convert a number of seconds to hh:mm:ss string.'''
    hours = np.floor(secs / 3600)
    secs -= hours * 3600
    mins = np.floor(secs / 60)
    secs = np.floor(secs - mins * 60)
    return '%02d:%02d:%02d' % (hours, mins, secs)

def get_ipython():
    import IPython
    if ipython_is_newer((0, 11)):
        return IPython.get_ipython()
    else:
        return IPython.ipapi.get()

def get_traceback():
    if ipython_is_newer((0, 11)):
        from IPython.core.ultratb import AutoFormattedTB
    else:
        from IPython.ultraTB import AutoFormattedTB
    return AutoFormattedTB

def ipython_is_newer(vin):
    """
    vin is tuple of version (a,b,c) for version "a.b.c"
    result gives True for larger or equal version
    """
    import IPython
    vs = IPython.__version__.split('.')
    for i in range(len(vs)):
        if i > (len(vin)-1):
            return True
        if int(vs[i]) > vin[i]:
            return True
        elif int(vs[i]) < vin[i]:
            return False
    return True

def is_ipython():
    return get_ipython() != None

def register_exit(func):
    if is_ipython():
        ip = get_ipython()
        if ipython_is_newer((8, 0, 0)):
            import atexit
            atexit.register(func)
        elif ipython_is_newer((0, 11)):
            ip.hooks['shutdown_hook'].add(func, 1)
        else:
            ip.IP.hooks.shutdown_hook.add(func, 1)
    else:
        import atexit
        atexit.register(func)

def str3(string,encoding='UTF-8'):
    try:
        return string.decode(encoding)
    except AttributeError:
        return str(string)

def concat(*args):
    """
    Concatenates any number of strings or bytestrings together to a string.
    This function can be helpful for code migration from py2
    """
    s = ""
    for a in args:
        s+=str3(a)
    return s
