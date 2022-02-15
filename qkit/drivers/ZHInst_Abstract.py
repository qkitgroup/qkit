from abc import ABC

from numpy import isin

from zhinst.toolkit.control.node_tree import NodeList
from qkit.core.instrument_base import Instrument
SETTING_TAG = 'setting'

class ZHInst_Abstract(ABC, Instrument):

    def __init__(self, name, **kwargs) -> None:
        super().__init__(name, **kwargs)
        if not hasattr(self, "blacklist"):
            self.blacklist = []
        self.add_tag(SETTING_TAG)

    def _recursive_qkit_hook(self, node, out_file, path = []):
        import textwrap
        if hasattr(node, "parameters"): # Check if this node points to leaf nodes
            for param_name in node.parameters: # And then iterate over them
                # Add the parameter to QKit. Do note, that we ignore privacy and access private members.
                param = getattr(node, param_name) # Obtain the actual node
                
                func_name = '_'.join(path + [param_name])
                        
                if any(map(lambda it: func_name.startswith(it), self.blacklist)):
                    continue
                
                access = param._properties # A set of strings describing access: Read, Write, Setting
                if 'Setting' in access:
                    tags = [SETTING_TAG] 
                else:
                    tags = []

                def get_call(zhinst_getter=param): # We need the kv-arg to capture the value.
                    return zhinst_getter()

                try:
                    get_call()
                except Exception as e:
                    print(f"Can't access {func_name}.")
                    print(e)
                    continue

                setattr(self, f"_do_get_{func_name}", get_call)
                if 'Write' in access:
                    def set_call(value, zhinst_setter=param):
                        zhinst_setter(value)
                    setattr(self, f"_do_set_{func_name}", set_call)
                    access = Instrument.FLAG_GETSET
                else:
                    access = Instrument.FLAG_GET
                property_type = param._type

                if property_type == 'Double':
                    property_type = float
                elif property_type == 'Integer' or property_type == 'Integer (enumerated)' or property_type == 'Integer (64 bit)':
                    property_type = int
                elif property_type == 'String':
                    property_type = str
                else:
                    import sys
                    print(f"Type '{property_type}' of '{func_name}' is not supported!", file=sys.stderr)
                    continue

                unit = getattr(param, "_unit", None)
                
                self.add_parameter(func_name, type = property_type, flags = access, units = unit, doc = param.__repr__(), tags = tags)
                # Lastly, for user reference, we print a file containing all mappings.
                # This will later be a reference manual, so that we can use meta-programming
                # to create all hooks, adapt to future updates, and let the user know what to call.
                print(textwrap.indent(f"get/set_{func_name}:", len(path) * " "), file=out_file)
                print(textwrap.indent(param.__repr__(), len(path) * " "), file=out_file)
        if hasattr(node, "nodes"): # Recursively Enter the hierarchy and register new nodes.
            for node_name in node.nodes:
                if node_name == "_parent":
                    continue
                self._recursive_qkit_hook(getattr(node, node_name), out_file, path = path + [node_name])
        if isinstance(node, NodeList):
            for i in range(len(node)):
                self._recursive_qkit_hook(node[i], out_file, path = path + [str(i)])

class ZHInst_AWG(ABC):
    """
    This is a mixin for all Zurich Instruments Devices which support an AWG.
    """