from abc import ABC, abstractmethod
from importlib.resources import path
from typing import Union, Any, Callable
from matplotlib.pyplot import isinteractive
import inspect

import numpy as np
import logging

from zhinst.toolkit.control.node_tree import NodeList, Parameter
from zhinst.toolkit.interface import LoggerModule
from qkit.core.instrument_basev2 import ModernInstrument, QkitProperty, ObjectTreeVisistor, PropertyMetadata, CachePolicy
SETTING_TAG = 'setting'

class ZHInstQkitProperty(QkitProperty):

    def __init__(self, param: Parameter, name):
        self.cache_policy = CachePolicy.NONE
        self.get_after_set = False
        self._param = param

        def getter(instance, param=param):
            return param()

        self.fget = getter

        try:
            test = self.fget(param)
        except LoggerModule.ToolkitConnectionError as tce:
            raise TypeError("Get not supported. Skip.", tce)
                
        access = param._properties # A set of strings describing access: Read, Write, Setting
        if 'Setting' in access:
            tags = [SETTING_TAG] 
        else:
            tags = []

        if 'Write' in access:
            def setter(instance, value, param=param):
                return param(value)
            self.fset = setter

        property_type = param._type

        if property_type == 'Double' and type(test) == np.float64:
            property_type = float
        elif (property_type == 'Integer' or property_type == 'Integer (enumerated)' or property_type == 'Integer (64 bit)') and type(test) == np.int64:
            property_type = int
        elif property_type == 'String' and type(test) == str:
            property_type = str
        elif property_type == 'ZIVectorData':
            if type(test) == np.ndarray:
                property_type = np.ndarray
            elif type(test) == str:
                property_type = str
            else:
                raise TypeError(f"Unsupported ZIVetorData type {type(test)} of {param._path}")
        else:
            raise TypeError(f"Documented type '{property_type}' of '{param._path}' with returned type {type(test)} is not supported!")

        unit = getattr(param, "_unit", param)
        
        self.metadata = PropertyMetadata(type = property_type, tags=tags, units=unit)
        self.metadata.name = name
        self.metadata.documentation = param._description

    def __call__(self, *args, **kwargs):
        """
        Overwrites the calls to the zhinst-driver to pass through qkit in order to allow caching
        and logging.
        """
        if len(args) == 0:
            return self.__get__(self._param)
        else:
            return self.__set__(self._param, args[0])


class ZHInstNodeVisitor(ObjectTreeVisistor):
    def visit_instance(self, obj, path=[]):
        if hasattr(obj, "parameters"):
            for param_name in obj.parameters:
                try:
                    self.visit_property(obj, param_name, getattr(obj, param_name), path = path)
                except TypeError as e:
                    logging.warn(f"Caught exception processing {param_name} at {path}: {e}")
                    continue
        
        if hasattr(obj, "nodes"):
            for node_name in obj.nodes:
                if node_name == "_parent":
                    continue
                self.visit_instance(getattr(obj, node_name), path = path + [node_name])
        
        if isinstance(obj, NodeList):
            for i, child in enumerate(obj):
                self.visit_instance(child, path = path + [i])


    def wrap_property(self, obj: Any, name: str, prop: Parameter) -> ModernInstrument.WrappedProperty:
        prop = ZHInstQkitProperty(prop, name)
        obj.__dict__[name] = prop
        return ModernInstrument.WrappedProperty.from_qkit_property(obj, prop)

    def wrap_function(self, obj: Any, name: str, func: Callable) -> ModernInstrument.WrappedFunction:
        raise TypeError(f"Unsupported property type '{type(func)}'! Override 'wrap_function' missing!")

    @staticmethod
    def _derive_channel_name(path):
        return "_".join(map(lambda it: str(it), path))

class ZHInst_Abstract(ABC, ModernInstrument):

    def __init__(self, name, **kwargs) -> None:
        super().__init__(name, **kwargs)
        if not hasattr(self, "blacklist"):
            self.blacklist = []
        self.add_tag(SETTING_TAG)

    def mount_api(self, node_tree):
        visitor = ZHInstNodeVisitor(self)
        visitor.visit_instance (node_tree)
