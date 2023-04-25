from __future__ import annotations

from abc import ABC, abstractmethod
from functools import wraps
import inspect
from typing import Any, Callable, List
from enum import Enum, unique, auto
import numpy as np

from qkit.core.instrument_base import Instrument
from qkit.drivers.visa_prologix import instrument
import logging

class ModernInstrument(Instrument):
    """
    Base class for instruments.

    Use @QkitProperty() to convert a getter to a property.
    Use @$prop_name$.setter to add a setter to a property.
    Do note, that the function name of the getter and setter must be the same.  
    """
    FLAG_GET = 0x01             # Parameter is gettable
    FLAG_SET = 0x02             # {arameter is settable
    FLAG_GETSET = 0x03          # Shortcut for GET and SET
    FLAG_GET_AFTER_SET = 0x04   # perform a 'get' after a 'set'
    FLAG_SOFTGET = 0x08         # 'get' operation is simulated in software,
                                # e.g. an internally stored value is returned.
                                # Only use for parameters that cannot be read
                                # back from a device.

    class WrappedFunction:

        def __init__(self, func) -> None:
            self.func = func

        def call(self, *args, **kwargs):
            return self.func(*args, **kwargs)

        @classmethod
        def from_qkit_function(cls, target_object: Any, func: function) -> ModernInstrument.WrappedFunction:
            return cls(lambda *args, **kwargs: func(target_object, *args, **kwargs))

    class WrappedProperty:
        """
        A wrapper around QKit-Property with the object information required
        to call the functions on an object.
        Qkit-Property does not belong to an instance, but to an class.
        """

        def __init__(self, getter, setter, metadata: PropertyMetadata) -> None:
            self._getter = getter
            self._setter = setter
            self._metadata = metadata

        def build_options(self) -> dict:
            """
            Backwards compatibility to the old ways of QKit.
            """
            return {
                "set_func": self._setter,
                "get_func": self._getter,
                "flags": Instrument.FLAG_GETSET
            }

        def get(self, query=True, **kwargs):
            """
            Returns the property value.
            """
            return ModernInstrument._convert_value(self._getter(query=query, **kwargs), self._metadata.type)

        def set(self, value):
            """
            Sets the property value.
            """
            self._setter(value)

        def get_metadata(self) -> PropertyMetadata:
            """
            Returns the properties metadata
            """
            return self._metadata

        @classmethod
        def from_qkit_property(cls, target_object: Any, property: QkitProperty) -> ModernInstrument.WrappedProperty:
            """
            Converts a QKitProperty into a Wrapped Property to be handled in a ModernInstrument Instance.
            """
            return cls(lambda **kwargs: property._get_logic(target_object, **kwargs), lambda val: property.__set__(target_object, val), property.metadata)


    def __init__(self, name, **kwargs):
        self._name = name
        self._initialized = False
        self._instrument_options = kwargs
        self._tags = getattr(kwargs, "tags", [])
        self._parameters = {}
        self._parameter_groups = {}
        self._functions = {}
        self._options = {"tags": []}

    def discover_capabilities(self):
        """
        Call this method from init to self-discover QkitNative functions and properties.
        """
        visitor = QkitNativeVisitor(self)
        visitor.visit_instance(self)

    def __str__(self):
        return f"Instrument '{self._name}'"

    def get_name(self):
        "Return the name of the instrument"
        return self._name

    def get_type(self):
        """
        Return the type of the instrument as a string.
        Might behave unexpectedly in case of new drivers.
        """
        return str(self.__module__)

    def _json(self):
        '''
        This function is called by the QkitJSONEncoder and should return a 
        dictionary that will be saved to the JSON file.
        '''
        return {'dtype' : 'qkitInstrumentv2', 'content': str(self.get_name())}

    def get_options(self):
        """
        Return the user provided instrument options.
        """
        return self._instrument_options

    def get_tags(self):
        """
        Return the user provided instrument tags.
        """
        return self._tags

    def has_tag(self, tags):
        if type(tags) is list:
            for tag in tags:
                if tag in self._tags:
                    return True
            return False
        else:
            if tags in self._tags:
                return True

    def initialize(self):
        self._initialized = True

    def remove(self):
        self._remove_parameters()

    def is_initialized(self):
        return self._initialized

    def add_parameter(self, name, **kwargs):
        # FIXME: Reimplement via ObjectTreeVisitor
        raise NotImplementedError("add_parameter no longer supported in ModernInstrument!")
    
    def _remove_parameters(self):
        self._parameters = {}

    def remove_parameter(self, name):
        if name in self._parameters:
            del self._parameters[name]

    def has_parameter(self, name):
        return (name in self._parameters)

    def get_parameter_options(self, name):
        '''
        Return list of options for paramter.

        Input: name (string)
        Output: dictionary of options
        '''
        if name in self._parameters:
            return self._parameters[name].build_options()
        else:
            return None

    def get_shared_parameter_options(self, name):
        '''
        Return list of options for paramter.

        Input: name (string)
        Output: dictionary of options
        '''
        if name in self._parameters:
            options = dict(self._parameters[name].build_options())
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
            logging.warn('Parameter %s not defined' % name)
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

        return self._parameters[name].metadata.tags

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

    _CONVERT_MAP = {
            int: int,
            float: float,
            bytes: str,
            str: str,
            bool: bool,
            tuple: tuple,
            list: list,
            np.ndarray: lambda x: x.tolist(),
            np.int64: int,
            np.float64: float
    }

    @staticmethod
    def _convert_value(value, ttype):
        if type(value) is bool and \
                ttype is not bool:
            raise ValueError('Setting a boolean, but that is not the expected type')

        if ttype not in ModernInstrument._CONVERT_MAP:
            raise ValueError('Unsupported type %s', ttype)

        try:
            func = ModernInstrument._CONVERT_MAP[ttype]
            value = func(value)
        except:
            raise ValueError('Conversion of %r to type %s failed',value, ttype)

        return value

    def get(self, name, query=True, fast=False, **kwargs):
        try:
            return self._parameters[name].get(query=query, **kwargs)
        except (AttributeError, TypeError, NameError, ValueError) as e:
            logging.error(f"Caught error while processing {name}(query={query}): e")
            raise e
    
    def set(self, name, value, **kwargs):
        return self._parameters[name].set(value, **kwargs)

    def call(self, name, *args, **kwargs):
        return self._functions[name].call(*args, **kwargs)

def interval_check(lower, upper):
    """
    Return a callable which returns true if its argument lies between the provided lower and upper bound.
    """
    def checker(arg):
        return lower <= arg <= upper
    checker.lower = lower
    checker.upper = upper
    return checker


def QkitFunction(func):
    """
    A wrapper of functions to facilitate easy self-discovery.
    """
    func._qkit_function = True
    return func

@unique
class CachePolicy(Enum):
    SOFT_GET = auto()
    ALWAYS_REFRESH = auto()
    NONE = auto() # Default value

def caching(cache_policy: CachePolicy, get_after_set = False):
    def decorator(func):
        assert isinstance(func, QkitProperty)
        func.set_caching(cache_policy, get_after_set)
        return func
    return decorator

class QkitProperty:
    """
    A store of metadata for properties, which shall be handled in QKit.
    It does no range checking whatsoever.

    Do note, that this is a member of a class. You will need an object to perform calls.
    For this reason [WrappedProperty] exists.
    """

    QKIT_CACHE_NAME = "_qkit_cache"

    class ValueCache:
        last_value: Any
        dirty: bool

    # no longer implemented: name, channels, doc
    def __init__(self, *args, **kwargs):
        """
        See [QkitProperty.PropertyMetadata] for what the kwargs mean.
        """
        if len(args) != 0:
            raise SyntaxError("Missing Braces on '@QkitProperty()'!")
        self.metadata = PropertyMetadata(**kwargs)
        self.cache_policy = CachePolicy.NONE
        self.get_after_set = False

    def __call__(self, func):
        assert not not func.__doc__, f"Documentation is missing on {func.__name__}!"
        self.__doc__ = func.__doc__
        self.metadata.documentation = func.__doc__
        self.metadata.name = func.__name__
        self.fget = func
        return self

    def __get__(self, obj, objtype=None, query=True):
        """
        Emulate a property-getter. Default call to _get_logic.
        """
        return self._get_logic(obj)

    def _get_logic(self, obj, query=True, **kwargs):
        """
        Gets the value either from the wrapped getter or the cache, depending on [cache_policy]
        Used to access the cache if required. Used for internal calls.

        We ignore all further kwargs, as they may result in incompatibilities.
        """
        if obj is None:
            return 
        
        # We need to determine if we hit the cache or call the actual device.
        hit_cache = False # Per default we can not assume that caching is a good idea. Let's be pessimistic.
        if not query and not self.cache_policy == CachePolicy.ALWAYS_REFRESH: # Automated QKit-Get call. Hit cache if we are not force to always refresh.
            hit_cache = True
        elif query and self.cache_policy == CachePolicy.SOFT_GET: # We have no getter. Always go to cache
            hit_cache = True
        else:
            hit_cache = False

        if hit_cache:
            return self._qkit_cache(obj).last_value
        else: # Default query. Call getter.
            new_value = self.fget(obj)
            self._qkit_cache(obj).last_value = new_value
            return new_value

    def setter(self, fset):
        """
        Decorator to create the 
        """
        sig = inspect.signature(fset)
        assert len(sig.parameters) == 2, "Missing parameters in setter, expected (self, arg) or similar!"
        self.fset = fset
        return self

    def __set__(self, obj, value):
        """
        Wraps the setting of the value.
        """
        if self.fset is None:
            raise AttributeError("Can't set attribute!")
        if inspect.isfunction(value):
            raise ValueError("Likely bug detected: Attempting to set a QkitProperty to a function!")
        assert self.metadata.check_arg(value), "Argument validity check failed!"
        
        retval = self.fset(obj, value)
        # Update cache either with value or __get__
        if self.get_after_set:
            self._get_logic(obj, query=True)
        else:
            self._qkit_cache(obj).last_value = value

        return retval
        

    def set_cache_policy(self, cache_policy: CachePolicy, get_after_set: bool):
        self.cache_policy = cache_policy
        self.get_after_set = get_after_set


    def _qkit_cache(self, obj) -> ValueCache:
        """
        A consistent way to get the [obj]'s qkit value cache and a member of it.
        Creates the cache, should it not already exist.
        Creates a ValueCache instance for this property, should none exist.
        """
        if not hasattr(obj, QkitProperty.QKIT_CACHE_NAME):
            setattr(obj, QkitProperty.QKIT_CACHE_NAME, {})
        cache: dict = getattr(obj, QkitProperty.QKIT_CACHE_NAME)
        name = self.metadata.name
        if not name in cache:
            cache[name] = QkitProperty.ValueCache()
        return cache[name]

    @classmethod
    def from_property(cls, prop: property, metadata: PropertyMetadata) -> QkitProperty:
        """
        Convert a regular python property into a QkitProperty.
        Used to install a shim to notify us if regular calls are made.
        """
        instance = cls()
        instance.fget = prop.fget
        instance.fset = prop.fset
        instance.metadata = metadata
        return instance

    @staticmethod
    def get_metadata(obj, property_name: str) -> PropertyMetadata:
        """
        If the key is a QkitProperty of obj return its Metadata.
        Otherwise return None. 
        """
        try:
            candidate = type(obj).__dict__[property_name]
        except KeyError:
            return None
        if isinstance(candidate, QkitProperty):
            return candidate.metadata
        return None

class ObjectTreeVisistor(ABC):
    """
    A visitor visiting class members to register them as properties and functions of 
    """
    def __init__(self, instrument: ModernInstrument) -> None:
        self.instrument = instrument

    @abstractmethod
    def visit_instance(self, obj, path=[]):
        """
        Visists an object and disects it into usable pieces.
        If some method is intended to be used as a function, call [visit_function]
        If some property is inteded to be used as a property, call [visit_property]
        If some array or iterable and indexable structure is channel-like, call [visit_channel]
        """
        pass
    
    def get_property_metadata(self, obj: Any, name: str, prop: property) -> PropertyMetadata:
        """
        Provides an instance of [PropertyMetadata] for a discovered property if we were
        not able to automatically derive it from [@QkitProperty].
        """
        raise NotImplementedError("Unimplemented 'get_property_metadata'!")

    def wrap_property(self, obj: Any, name: str, prop: property) -> ModernInstrument.WrappedProperty:
        raise TypeError(f"Unsupported property type '{type(prop)}! Override 'wrap_property' missing!'")

    def wrap_function(self, obj: Any, name: str, func: Callable) -> ModernInstrument.WrappedFunction:
        raise TypeError(f"Unsupported property type '{type(func)}'! Override 'wrap_function' missing!")

    @staticmethod
    def derive_name_from_path(path: List(str)) -> str:
        return "_".join(map(lambda it: str(it), path))

    def visit_property(self, obj, name, prop, path=[]):
        """
        Handles a property [prop] of [obj] with the name [name].
        Registers it in discovered properties.
        """
        property_name = self.derive_name_from_path(path + [name])
        if isinstance(prop, QkitProperty):
            wrapped = ModernInstrument.WrappedProperty.from_qkit_property(obj, prop)
        elif isinstance(prop, property):
            wrapped = ModernInstrument.WrappedProperty(
                getter=lambda: property.__get__(obj),
                setter=lambda value: property.__set__(obj, value),
                metadata=self.get_property_metadata(obj, name, prop)
            )
        else:
            wrapped = self.wrap_property(obj, name, prop)
        self.instrument._parameters[property_name] = wrapped
        group = wrapped.get_metadata().group
        if group in self.instrument._parameter_groups:
            self.instrument._parameter_groups[group].append(wrapped)
        else:
            self.instrument._parameter_groups[group] = [wrapped]

    def visit_function(self, obj, name, func, path=[]):
        """
        Handles a function [func] of [obj] with the name [name].
        Registers it in discovered functions.
        """
        property_name = self.derive_name_from_path(path + [name])
        if inspect.isfunction(func) and hasattr(func, "_qkit_function"):
            wrapped = ModernInstrument.WrappedFunction.from_qkit_function(obj, func)
        else:
            wrapped = self.wrap_function(obj, name, func)
        self.instrument._functions[property_name] = wrapped

class QkitNativeVisitor(ObjectTreeVisistor):
    """
    This visitor is good for home-made drivers. It assumes that all properties we want to register
    have been properly marked as QkitProperty. It will not support other properties.

    You can take inspiration from this approach to write your own visitor to shim regular properties
    with [QkitProperty.from_property()] and setting the __dict__ entry.
    """

    def visit_instance(self, obj, path=[]):
        # Check for properties
        setattr(obj, "_qkit_path", path)
        setattr(obj, "_qkit_instrument", self.instrument)
        cls_defined = type(obj).__dict__
        for candidate in cls_defined:
            if candidate.startswith("_"):
                continue
            prop = cls_defined[candidate]
            if isinstance(prop, QkitProperty):
                # This is a QkitProperty. We can wrap it like normal.
                self.visit_property(obj, candidate, cls_defined[candidate], path)
            elif inspect.isfunction(prop) and hasattr(prop, "_qkit_function"):
                # This is a QkitFunction. Wrap it like a function.
                self.visit_function(obj, candidate, cls_defined[candidate], path)
        obj_defined = obj.__dict__
        for candidate in obj_defined:
            if candidate.startswith("_"):
                continue
            prop = obj_defined[candidate]
            if hasattr(prop, "__len__") and hasattr(prop, "__getitem__"):
                # This is a list, which might be channel-like
                for i in range(len(prop)):
                    self.visit_instance(prop[i], path = path + [candidate, str(i)])

class PropertyMetadata:
    """
    Stores metadata about a property. Is read out by [ObjectTreeVisistor]
    to create wrapped properties for [ModernInstrument]
    """

    def __init__(self, type=None, arg_checker=None, tags=[], subscribe=[], units=None, group=None) -> None:
        """
        Optional Arguments:
        type: float, int, str, np.ndarray, ...
        arg_checker: Checks argument for validity (minimum, maximum, steps) and returns either True (valid) or False
        tags: Tags associated with the parameter
        subscribe: A set of parameter names whose change triggers an update of this one 
        units: A string describing this properties units
        group: A string name of a group this property belongs to.
        """
        self.type = type
        self.arg_checker = arg_checker
        self.tags = tags
        self.subsriptions = subscribe
        self.units = units
        self.name = None
        self.documentation = None
        self.group = group

    def check_arg(self, arg):
        if self.arg_checker == None:
            return True
        else:
            return self.arg_checker(arg)

    def __repr__(self) -> str:
        import textwrap
        return textwrap.dedent(f"""
        Property {self.name}({self.type} {self.units}): tagged {self.tags} in group {self.group}
        listens to {self.subsriptions}
        argument checked: {not self.arg_checker == None}
        Documentation: """) + textwrap.dedent(self.documentation)
