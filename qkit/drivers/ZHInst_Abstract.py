from abc import ABC, abstractmethod
from typing import Union
from typing_extensions import Self
import black
from matplotlib.pyplot import isinteractive

import numpy as np

from zhinst.toolkit.control.node_tree import NodeList
from qkit.core.instrument_base import Instrument
SETTING_TAG = 'setting'

class ZHInst_Abstract(ABC, Instrument):

    def __init__(self, name, **kwargs) -> None:
        super().__init__(name, **kwargs)
        if not hasattr(self, "blacklist"):
            self.blacklist = []
        self.add_tag(SETTING_TAG)

    def mount_api(self, file_name: str, node_tree):
        with open(file_name, "w", encoding="utf-8") as f:
            visitor = self.NodeTreeVisitor(f, self, self.blacklist)
            visitor.visit_node([node_tree])

    class NodeTreeVisitor:

        def __init__(self, doc_file, target, blacklist) -> None:
            self.doc_file = doc_file
            self.target = target
            self.blacklist = blacklist


        def visit_parameter(self, parameters: list, path=[]):
            prefix, func_name = self._derive_channel_affix(path)
            if any(map(lambda it: func_name.startswith(it), self.blacklist)):
                return
            parameters = list(parameters)
            access = parameters[0]._properties # A set of strings describing access: Read, Write, Setting
            if 'Setting' in access:
                tags = [SETTING_TAG] 
            else:
                tags = []

            def get_call(zhinst_getters=parameters, channel=0): # We need the kv-arg to capture the value.
                return zhinst_getters[channel]()

            try:
                get_call()
            except Exception as e:
                print(f"Can't access {func_name}.")
                print(e)
                return

            setattr(self.target, f"_do_get_{func_name}", get_call)
            if 'Write' in access:
                def set_call(value, zhinst_setters=parameters, channel=0):
                    zhinst_setters[channel](value)
                setattr(self.target, f"_do_set_{func_name}", set_call)
                access = Instrument.FLAG_GETSET
            else:
                access = Instrument.FLAG_GET
            property_type = parameters[0]._type

            if property_type == 'Double':
                property_type = float
            elif property_type == 'Integer' or property_type == 'Integer (enumerated)' or property_type == 'Integer (64 bit)':
                property_type = int
            elif property_type == 'String':
                property_type = str
            elif property_type == 'ZIVectorData':
                property_type = np.ndarray
            else:
                import sys
                print(f"Type '{property_type}' of '{func_name}' is not supported!", file=sys.stderr)
                return

            unit = getattr(parameters[0], "_unit", None)
            
            if len(parameters) > 1:
                self.target.add_parameter(func_name, channel_prefix = prefix, type = property_type, flags = access, units = unit, doc = parameters.__repr__(), tags = tags, channels = (0, len(parameters) - 1))
            else:
                self.target.add_parameter(func_name, type = property_type, flags = access, units = unit, doc = parameters.__repr__(), tags = tags)
            # Lastly, for user reference, we print a file containing all mappings.
            # This will later be a reference manual, so that we can use meta-programming
            # to create all hooks, adapt to future updates, and let the user know what to call.
            print(f"get/set_{func_name}:", file=self.doc_file)
            print(parameters[0].__repr__(), file=self.doc_file)

        def visit_node(self, nodes: list, path=[]):
            if self._check_all_have_non_deviating(nodes, lambda node: hasattr(node, "parameters")):
                for param_name in nodes[0].parameters:
                    self.visit_parameter(self._map_to_list(lambda node: getattr(node, param_name), nodes), path = path + [param_name])
            
            if self._check_all_have_non_deviating(nodes, lambda node: hasattr(node, "nodes")):
                for node_name in nodes[0].nodes:
                    if node_name == "_parent":
                        continue
                    self.visit_node(self._map_to_list(lambda node: getattr(node, node_name), nodes), path = path + [node_name])
            
            if self._check_all_have_non_deviating(nodes, lambda node: isinstance(node, NodeList)):
                if len(nodes) == 1: # We have not yet hit such a split -> Channel Marker
                    marker = self.ChannelNodeMarker(0, len(nodes[0]))
                    self.visit_node([n for n in nodes[0]], path = path + [marker])
                else: # Go down recursively, each iteration the next index
                    for i in range(len(nodes[0])):
                        self.visit_node(self._map_to_list(lambda node: node[i], nodes), path = path + [str(i)])

        
        def _derive_channel_affix(self, path):
            splits = [i for i, x in enumerate(path) if isinstance(x, self.ChannelNodeMarker)]
            if len(splits) > 0:
                split_index = splits[0]
                prefix = path[split_index - 1] + "_%s_"
                name = self._derive_channel_name(path[:split_index] + path[split_index + 1:])
                return  prefix, name
            else:
                return "", self._derive_channel_name(path)

        @staticmethod
        def _map_to_list(expr, l):
            return list(map(expr, l))

        @staticmethod
        def _derive_channel_name(path):
            return "_".join(map(lambda it: str(it), path))

        @staticmethod
        def _check_all_have_non_deviating(nodes, expression):
            return all(map(expression, nodes)) and not any(map(lambda node: not expression(node), nodes))
        
        class ChannelNodeMarker:
            
            lower_index_bound: int
            upper_index_bound: int

            def __init__(self, lower_index, upper_index) -> None:
                self.lower_index_bound = lower_index
                self.upper_index_bound = upper_index

            def __repr__(self) -> str:
                return f"{self.lower_index_bound}..{self.upper_index_bound}"

class ZHInst_AWG(ABC):
    """
    This is a mixin for all Zurich Instruments Devices which support an AWG.
    """