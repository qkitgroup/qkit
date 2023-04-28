# instrument_base.py, base class to implement instrument objects
# Reinier Heeres <reinier@heeres.eu>, 2008
# HR@KIT 2017 (converted to python3)
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from __future__ import print_function

import copy
import inspect
import logging
import time

import numpy as np

import qkit


class Instrument(object):
    """
    Base class for instruments.

    Usage:
    Instrument.get(<variable name or list>)
    Instrument.set(<variable name or list>)

    Implement an instrument:
    In __init__ call self.add_variable(<name>, <option dict>)
    Implement _do_get_<variable> and _do_set_<variable> functions
    """



    FLAG_GET = 0x01             # Parameter is gettable
    FLAG_SET = 0x02             # {arameter is settable
    FLAG_GETSET = 0x03          # Shortcut for GET and SET
    FLAG_GET_AFTER_SET = 0x04   # perform a 'get' after a 'set'
    FLAG_SOFTGET = 0x08         # 'get' operation is simulated in software,
                                # e.g. an internally stored value is returned.
                                # Only use for parameters that cannot be read
                                # back from a device.

    RESERVED_NAMES = ('name', 'type')

    def __init__(self, name, **kwargs):

        self._name = name
        self._initialized = False

        self._options = kwargs
        if 'tags' not in self._options:
            self._options['tags'] = []

        self._parameters = {}
        self._parameter_groups = {}
        self._functions = {}
        self._added_methods = []
        self._probe_ids = []
        self._offsets = {}

    def __str__(self):
        return "Instrument '%s'" % (self.get_name())


    def get_name(self):
        '''
        Returns the name of the instrument as a string

        Input: None
        Output: name of instrument (string)
        '''

        return self._name
    
    def _json(self):
        '''
        This function is called by the QkitJSONEncoder and should return a 
        dictionary that will be saved to the JSON file.
        '''
        return {'dtype' : 'qkitInstrument', 'content': str(self.get_name())}
        
    def get_type(self):
        """Return type of instrument as a string."""
        modname = str(self.__module__)
        return modname

    def get_options(self):
        '''Return instrument options.'''
        return self._options

    def get_tags(self):
        '''
        Returns array of tags

        Input: None
        Output: array of strings
        '''
        return self._options['tags']

    def add_tag(self, tag):
        '''
        Add tag to the tag list

        Input: tag (string)
        Output: None
        '''
        self._options['tags'].append(tag)

    def has_tag(self, tags):
        '''
        Return whether instrument has any tag in 'tags'
        '''

        if type(tags) is list:
            for tag in tags:
                if tag in self._options['tags']:
                    return True
            return False

        else:
            if tags in self._options['tags']:
                return True

        return False

    def initialize(self):
        '''
        Currently unsupported; might be used in the future to perform
        extra initialization in sub-classed Instruments.

        Input: None
        Output: None
        '''
        self._initialized = True

    def remove(self):
        '''
        Notify the instrument collection that this instrument should be
        removed. Override this in a sub-classed Instrument to perform
        cleanup.

        Input: None
        Output: None
        '''

        self._remove_parameters()

    def is_initialized(self):
        '''
        Return whether Instrument is initialized.

        Input: None
        Output: Boolean
        '''
        return self._initialized

    def add_parameter(self, name, **kwargs):
        '''
        Create an instrument 'parameter' that is known by the whole
        environment (gui etc).

        This function creates the 'get_<name>' and 'set_<name>' wrapper
        functions that will perform checks on parameters and finally call
        '_do_get_<name>' and '_do_set_<name>'. The latter functions should
        be implemented in the instrument driver.

        Input:
            name (string): the name of the parameter (string)
            optional keywords:
                type: types.FloatType, types.StringType, etc.
                flags: bitwise or of Instrument.FLAG_ constants.
                    If not set, FLAG_GETSET is default
                channels: tuple. Automagically create channels, e.g.
                    (1, 4) will make channels 1, 2, 3, 4.
                minval, maxval: values for bound checking
                units (string): units for this parameter
                maxstep (float): maximum step size when changing parameter
                stepdelay (float): delay when setting steps (in milliseconds)
                tags (array): tags for this parameter
                doc (string): documentation string to add to get/set functions
                listen_to (list of (ins, param) tuples): list of parameters
                    to watch. If any of them changes, execute a get for this
                    parameter. Useful for a parameter that depends on one
                    (or more) other parameters.

        Output: None
        '''

        if name in self._parameters:
            logging.error('Parameter %s already exists.', name)
            return
        elif name in self.RESERVED_NAMES:
            logging.error("'%s' is a reserved name, not adding parameter",
                    name)
            return

        options = kwargs
        if 'flags' not in options:
            options['flags'] = Instrument.FLAG_GETSET
        if 'type' not in options:
            options['type'] = type(None)
        if 'tags' not in options:
            options['tags'] = []
        if 'offset' not in options:
            options['offset'] = False

        # If defining channels call add_parameter for each channel
        if 'channels' in options:
            if len(options['channels']) == 2 and type(options['channels'][0]) is int:
                minch, maxch = options['channels']
                channels = range(minch, maxch + 1)
            else:
                channels = options['channels']

            for i in channels:
                chopt = copy.copy(options)
                del chopt['channels']
                chopt['channel'] = i
                chopt['base_name'] = name

                if 'channel_prefix' in options:
                    var_name = options['channel_prefix'] % i + name
                else:
                    var_name = '%s%s' % (name, i)

                self.add_parameter(var_name, **chopt)

            return

        self._parameters[name] = options
        self._offsets[name] = None

        if 'channel' in options:
            ch = options['channel']
        else:
            ch = None

        base_name = kwargs.get('base_name', name)

        if options['offset']:
            if options["type"] in (bool,bytes,str):
                raise ValueError("%s.%s: Offset not available for parameter with type %s" % (self._name, name, options["type"].__name__))
            else:
                func = lambda value: self._offsets.update({name:value})
                func.__doc__ = """Set an offset for parameter %s on device %s.
                The offset is added on every get and substracted on every set command.
                Use e.g. set_power_offset(-20) if you add 20dB attenuation at the device."""%(self._name,name)
                setattr(self, 'set_%s_offset' % name, func)
                self._added_methods.append('set_%s_offset' % name)
    
                setattr(self, 'get_%s_offset' % name, lambda : self._offsets[name])
                self._added_methods.append('get_%s_offset' % name)

        if options['flags'] & Instrument.FLAG_GET:
            if ch is not None:
                func = lambda query=True, **lopts: \
                    self.get(name, query=query, channel=ch, **lopts)
            else:
                func = lambda query=True, **lopts: \
                    self.get(name, query=query, **lopts)

            func.__doc__ = 'Get variable %s' % name
            if 'doc' in options:
                func.__doc__ += '\n%s' % options['doc']

            setattr(self, 'get_%s' % name,  func)
            self._added_methods.append('get_%s' % name)

            # Set function to do_get_%s or _do_get_%s, whichever is available
            # (if no function specified)
            if 'get_func' not in options:
                options['get_func'] = getattr(self, 'do_get_%s' % base_name, \
                    getattr(self, '_do_get_%s' % base_name, None))
            if options['get_func'] is not None:
                if options['get_func'].__doc__ is not None:
                    func.__doc__ += '\n%s' % options['get_func'].__doc__
            else:
                options['get_func'] = lambda *a, **kw: \
                    self._get_not_implemented(base_name)
                self._get_not_implemented(base_name)

        if options['flags'] & Instrument.FLAG_SOFTGET:
            if ch is not None:
                func = lambda query=True, **lopts: \
                    self.get(name, query=False, channel=ch, **lopts)
            else:
                func = lambda query=True, **lopts: \
                    self.get(name, query=False, **lopts)

            func.__doc__ = 'Get variable %s (internal stored value)' % name
            setattr(self, 'get_%s' % name,  func)
            self._added_methods.append('get_%s' % name)

        if options['flags'] & Instrument.FLAG_SET:
            if ch is not None:
                func = lambda val, **lopts: self.set(name, val, channel=ch, **lopts)
            else:
                func = lambda val, **lopts: self.set(name, val, **lopts)

            func.__doc__ = 'Set variable %s' % name
            if 'doc' in options:
                func.__doc__ += '\n%s' % options['doc']
            setattr(self, 'set_%s' % name, func)
            self._added_methods.append('set_%s' % name)

            # Set function to do_set_%s or _do_set_%s, whichever is available
            # (if no function specified)
            if 'set_func' not in options:
                options['set_func'] = getattr(self, 'do_set_%s' % base_name, \
                    getattr(self, '_do_set_%s' % base_name, None))
            if options['set_func'] is not None:
                if options['set_func'].__doc__ is not None:
                    func.__doc__ += '\n%s' % options['set_func'].__doc__
            else:
                options['set_func'] = lambda *a, **kw: \
                    self._set_not_implemented(base_name)
                self._set_not_implemented(base_name)

#        setattr(self, name,
#            property(lambda: self.get(name), lambda x: self.set(name, x)))

        if 'listen_to' in options:
            insset = set([])
            inshids = []
            for (ins, param) in options['listen_to']:
                inshids.append(ins.connect('changed', \
                        self._listen_parameter_changed_cb,
                        param, options['get_func']))
            options['listed_hids'] = inshids

        if 'group' in options:
            g = options['group']
            if g not in self._parameter_groups:
                self._parameter_groups[g] = [name]
            else:
                self._parameter_groups[g].append(name)

    def _remove_parameters(self):
        '''
        Remove remaining references to bound methods so that the Instrument
        object can be garbage collected.
        '''

        for name, opts in self._parameters.items():
            for fname in ('get_%s' % name, 'set_%s' % name):
                if hasattr(self, fname):
                    delattr(self, fname)
        self._parameters = {}

    def remove_parameter(self, name):
        if name not in self._parameters:
            return

        for func in ('get_%s' % name, 'set_%s' % name):
            if hasattr(self, func):
                delattr(self, func)

        del self._parameters[name]

    def has_parameter(self, name):
        '''
        Return whether instrument has a parameter called 'name'
        '''
        return (name in self._parameters)

    def get_parameter_options(self, name):
        '''
        Return list of options for paramter.

        Input: name (string)
        Output: dictionary of options
        '''
        if name in self._parameters:
            return self._parameters[name]
        else:
            return None

    def get_shared_parameter_options(self, name):
        '''
        Return list of options for paramter.

        Input: name (string)
        Output: dictionary of options
        '''
        if name in self._parameters:
            options = dict(self._parameters[name])
            for i in ('get_func', 'set_func'):
                if i in options:
                    del options[i]
            if 'type' in options and options['type'] is type(None):
                options['type'] = None
            return options
        else:
            return None

    def set_parameter_options(self, name, **kwargs):
        '''
        Change parameter options.

        Input:  name of parameter (string)
        Ouput:  None
        '''
        if name not in self._parameters:
            print('Parameter %s not defined' % name)
            return None

        for key, val in kwargs.items():
            self._parameters[name][key] = val

    def get_parameter_tags(self, name):
        '''
        Return tags for parameter 'name'.

        Input:  name of parameter (string)
        Ouput:  array of tags
        '''

        if name not in self._parameters:
            return []

        return self._parameters[name]['tags']

    def add_parameter_tag(self, name, tag):
        '''
        Add tag to list of tags for parameter 'name'.

        Input:  (1) name of parameter (string)
                (2) tag (string)
        Ouput:  None
        '''

        if name not in self._parameters:
            return

        self._parameters[name]['tags'].append(tag)

    def set_parameter_bounds(self, name, minval, maxval):
        '''
        Change the bounds for a parameter.

        Input:  (1) name of parameter (string)
                (2) minimum value
                (3) maximum value
        Output: None
        '''
        self.set_parameter_options(name, minval=minval, maxval=maxval)

    def set_channel_bounds(self, name, channel, minval, maxval):
        '''
        Change the bounds for a channel.

        Input:  (1) name of parameter (string)
                (2) channel number (int)
                (3) minimum value
                (4) maximum value
        Output: None
        '''

        opts = self.get_parameter_options(name)
        if 'channel_prefix' in opts:
            var_name = opts['channel_prefix'] % channel + name
        else:
            var_name = '%s%d' % (name, channel)

        self.set_parameter_options(var_name, minval=minval, maxval=maxval)

    def set_parameter_rate(self, name, stepsize, stepdelay):
        '''
        Change the rate properties for a channel.

        Input:
            stepsize (float): the maximum step size
            stepdelay (float): the delay after each step
        Output:
            None
        '''
        self.set_parameter_options(name, maxstep=stepsize, stepdelay=stepdelay)

    def get_parameter_names(self):
        '''
        Returns a list of parameter names.

        Input: None
        Output: all the paramter names (list of strings)
        '''
        return self._parameters.keys()

    def get_parameters(self):
        '''
        Return the parameter dictionary.

        Input: None
        Ouput: Dictionary, keys are parameter names, values are the options.
        '''
        return self._parameters

    def get_shared_parameters(self):
        '''
        Return the parameter dictionary, with non-shareable items stripped.

        Input: None
        Ouput: Dictionary, keys are parameter names, values are the options.
        '''

        params = {}
        for key in self._parameters:
            params[key] = self.get_shared_parameter_options(key)
        return params

    def get_parameter_groups(self):
        '''
        Return a dictionary with parameter group name -> group members.
        '''
        return self._parameter_groups
    
    def _offset(self,name,value,sign):
        if self._offsets[name] is not None:
            return value+sign*self._offsets[name]
        return value

    def _get_value(self, name, query=True, **kwargs):
        '''
        Private wrapper function to get a value.

        Input:  (1) name of parameter (string)
                (2) query the instrument or return stored value (Boolean)
                (3) optional list of extra options
        Output: value of parameter (whatever type the instrument driver returns)
        '''

        try:
            p = self._parameters[name]
        except:
            print('Could not retrieve options for parameter %s' % name)
            return None

        if 'channel' in p and 'channel' not in kwargs:
            kwargs['channel'] = p['channel']

        flags = p['flags']
        if not query or flags & 8: #self.FLAG_SOFTGET:
            if 'value' in p:
                if p['type'] == np.ndarray:
                    return self._offset(name,np.array(p['value']),+1)
                else:
                    return self._offset(name,p['value'],+1)
            elif not query:
                if not flags & 1: #Instrument.FLAG_GET, not gettable
                    return None 
                # if this value is not stored but gettable, don't throw an error but just get it.
                logging.debug("%s.%s value not cached. I try getting it with query=True."%(self._name,name))
                return self._get_value(name,query=True,**kwargs)
            else:
                logging.error('Trying to access cached value %s, but none available'%name)
                return False

        # Check this here; getting of cached values should work
        if not flags & 1: #Instrument.FLAG_GET:
            if query:
                logging.error('Instrument %s does not support getting of %s' %(self._name, name))
            return None

        func = p['get_func']
        value = func(**kwargs)
        if 'type' in p and value is not None:
            try:
                if p['type'] == bytes or p['type'] == type(None):
                    pass
                elif p['type'] == np.ndarray:
                    value = np.array(value)
                else:
                    value = p['type'](value)
            except:
                logging.warning('Unable to cast value "%s" to %s', value, p['type'])

        p['value'] = value
        return self._offset(name,value,+1)

    def get(self, name, query=True, fast=False, **kwargs):
        '''
        Get one or more Instrument parameter values.

        Input:
            name (string or list/tuple of strings): name of parameter(s)
            query (bool): whether to query the instrument or return the
                last stored value
            fast (bool): legacy from qtlab
            kwargs: Optional keyword args that will be passed on.

        Output: Single value, or dictionary of parameter -> values
                Type is whatever the instrument driver returns.
        '''
        if type(name) in (list, tuple):
            result = {}
            for key in name:
                val = self._get_value(key, query, **kwargs)
                if val is not None:
                    result[key] = val
        else:
            result = self._get_value(name, query, **kwargs)
        qkit.flow.sleep()
        return result

    def get_threaded(self, *args, **kwargs):
        logging.error('Using threading functions is not supported. Redirecting to normal get')
        return self.get(*args, **kwargs)

    _CONVERT_MAP = {
            int: int,
            float: float,
            bytes: str,
            str: str,
            bool: bool,
            tuple: tuple,
            list: list,
            np.ndarray: lambda x: x.tolist(),
    }

    def _convert_value(self, value, ttype):
        if type(value) is bool and \
                ttype is not bool:
            raise ValueError('Setting a boolean, but that is not the expected type')

        if ttype not in self._CONVERT_MAP:
            raise ValueError('Unsupported type %s', ttype)

        try:
            func = self._CONVERT_MAP[ttype]
            value = func(value)
        except:
            raise ValueError('Conversion of %r to type %s failed',value, ttype)

        return value

    def _set_value(self, name, value, **kwargs):
        '''
        Private wrapper function to set a value.

        Input:  (1) name of parameter (string)
                (2) value of parameter (whatever type the parameter supports).
                    Type casting is performed if necessary.
                (3) Optional keyword args that will be passed on.
        Output: Value returned by the _do_set_<name> function,
                or result of get in FLAG_GET_AFTER_SET specified.
        '''
        if name in self._parameters:
            p = self._parameters[name]
        else:
            raise ValueError("Parameter %s not known"%name)

        if not p['flags'] & Instrument.FLAG_SET:
            print('Instrument does not support setting of %s' % name)
            return None

        if 'channel' in p and 'channel' not in kwargs:
            kwargs['channel'] = p['channel']

        value = self._offset(name, value, -1)

        if 'type' in p:
            value = self._convert_value(value, p['type'])

        if 'minval' in p and value < p['minval']:
            if self._offsets[name] is not None and self._offsets[name] != 0:
                raise qkit.instruments.InstrumentBoundsError('Cannot set %s.%s to %g: With offset %g, %s at %s would be %g, which is too small (Minimum: '
                                                             '%g)' % (self._name, name, value+self._offsets[name],self._offsets[name],name,self._name,value, p['maxval']))
            raise qkit.instruments.InstrumentBoundsError('Cannot set %s.%s to %s: value too small (Minimum: %g)' % (self._name, name,value, p['minval']))

        if 'maxval' in p and value > p['maxval']:
            if self._offsets[name] is not None and self._offsets[name] != 0:
                raise qkit.instruments.InstrumentBoundsError('Cannot set %s.%s to %g: With offset %g, %s at %s would be %g, which is too large (Maximum: '
                                                             '%g)' % (self._name, name, value+self._offsets[name],self._offsets[name],name,self._name,value, p['maxval']))
            raise qkit.instruments.InstrumentBoundsError('Cannot set %s.%s to %s: value too large (Maximum: %g)' % (self._name, name, value, p['maxval']))

        func = p['set_func']
        if 'maxstep' in p and p['maxstep'] is not None:
            curval = p['value']
            if curval is None:
                logging.warning('Current value not available, ignoring maxstep')
                curval = value + 0.01 * p['maxstep']

            sign = np.sign(value - curval)
            for v in np.arange(curval, value, sign * np.abs(p['maxstep'])):
                func(v, **kwargs)  # execute the set function
                time.sleep(p.get('stepdelay', 50) / 1000.)

        func(value, **kwargs)  # execute the set function to get the final value

        if p['flags'] & self.FLAG_GET_AFTER_SET:
            newvalue = self._offset(name,self._get_value(name, **kwargs),-1)
            if newvalue != value:
                logging.warning("%s.%s: actual value (%s) differs from set value (%s)"%(self._name,name,newvalue,value))
            value = newvalue

        p['value'] = value
        return value

    def set(self, name, value=None, fast=False, **kwargs):
        '''
        Set one or more Instrument parameter values.

        Checks whether the Instrument is locked and checks value bounds,
        if specified by minval / maxval.

        Input:
            name (string or dict): which parameter to set, or dictionary of
                parameter -> value
            value (any): the value to set
            fast (bool): if True perform as fast as possible, e.g. don't
                emit a signal to update the GUI.
            kwargs: Optional keyword args that will be passed on.

        Output: True or False whether the operation succeeded.
                For multiple sets return False if any of the parameters failed.
        '''

        result = True
        changed = {}
        if type(name) == dict:
            for key, val in name.items():
                val = self._set_value(key, val, **kwargs)
                if val is not None:
                    changed[key] = val
                else:
                    result = False

        else:
            val = self._set_value(name, value, **kwargs)
            if val is not None:
                changed[name] = val
            else:
                result = False

        qkit.flow.sleep()
        return result

    def get_argspec_dict(self, a):
        return dict(args=a[0], varargs=a[1], keywords=a[2], defaults=a[3])

    def add_function(self, name, **options):
        '''
        Inform the Instrument wrapper class to expose a function.

        Input:  (1) name of function (string)
                (2) dictionary of extra options
        Output: None
        '''

        if not hasattr(self, name):
            logging.warning('Instrument does not implement function %s', name)

        f = getattr(self, name)
        if hasattr(f, '__doc__'):
            options['doc'] = getattr(f, '__doc__')

        options['argspec'] = self.get_argspec_dict(inspect.getfullargspec(f))

        self._functions[name] = options

    def get_function_options(self, name):
        '''
        Return options for an Instrument function.

        Input:  name of function (string)
        Output: dictionary of options for function 'name'
        '''
        if name in self._functions:
            return self._functions[name]
        else:
            return None

    def get_function_parameters(self, name):
        '''
        Return info about parameters for function.
        '''
        if name in self._functions:
            if 'parameters' in self._functions[name]:
                return self._functions[name]['parameters']
        return None

    def get_function_names(self):
        '''
        Return the list of exposed Instrument function names.

        Input: None
        Output: list of function names (list of strings)
        '''
        return self._functions.keys()

    def get_functions(self):
        '''
        Return the exposed functions dictionary.

        Input: None
        Ouput: Dictionary, keys are function  names, values are the options.
        '''
        return self._functions

    def call(self, funcname, **kwargs):
        '''
        Call the exposed function 'funcname'.

        Input:  (1) function name (string)
                (2) Optional keyword args that will be passed on.
        Output: None
        '''
        f = getattr(self, funcname)
        f(**kwargs)

    def reload(self):
        '''
        Reloads the instrument. Make sure to only use the new instance
        of the instrument, which is returned here!

        Input:
            None
        Output:
            New instance of instrument
        '''
        logging.warning("No warranty on reloads. Make sure to re-assign the instrument as \n %s = %s.reload()"%(self._name,self._name))
        return qkit.instruments.reload(self)

    def _get_not_implemented(self, name):
        logging.warning('Get not implemented for %s.%s' % \
            (Instrument.get_type(self), name))

    def _set_not_implemented(self, name):
        logging.warning('Set not implemented for %s.%s' % \
            (Instrument.get_type(self), name))

    def _listen_parameter_changed_cb(self, sender, changed,listen_param, update_func):
        # ToDo this has to be correctly implemented!
        # Cross-related parameters are probably a good thing to have
        # i.e. one parameter is "getted" if another one is set
        if listen_param not in changed:
            return
        update_func()

class InvalidInstrument(Instrument):
    '''
    Placeholder class for instruments that fail to load, mainly to support
    reloading.
    '''

    def __init__(self, name, instype, **kwargs):
        self._instype = instype
        self._kwargs = kwargs
        Instrument.__init__(self, name)

    def get_type(self):
        return self._instype

    def get_create_kwargs(self):
        return self._kwargs

class GPIBInstrument(Instrument):
    def __init__(self, *args, **kwargs):
        kwargs['lockclass'] = 'GPIB'
        Instrument.__init__(self, *args, **kwargs)
