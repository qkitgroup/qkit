# -*- coding: utf-8 -*-
"""
@author: S1@KIT/2020
Before we start, we check whether essential external libraries are available
and check for commonly used libraries.
"""

import qkit
from pkgutil import find_loader


class ModuleAvailable:
    """
    This class hosts and provides information about the installed python modules.
    To check wether a module is available, you can use getitem or the function call
    to the instance.
    Once the availability of a module is checked, the result is stored in a dictionary.
    print(instance) will give you all checked modules
    """
    
    def __init__(self):
        self.available_modules = {}
    
    def module_available(self, module_name):
        if module_name not in self.available_modules:
            self.available_modules[module_name] = bool(find_loader(module_name))
        return self.available_modules[module_name]
    
    def __call__(self, module_name):
        return self.module_available(module_name)
    
    def __getitem__(self, module_name):
        return self.module_available(module_name)
    
    def __repr__(self):
        return repr(self.available_modules)


qkit.module_available = ModuleAvailable()

# In qkit.cfg['blocked_modules'] you can specify modules you do not want to use.
# This can be helpful for programming and debugging but also if a module is not working properly.
for e in qkit.cfg.get('blocked_modules',[]):
    qkit.module_available.available_modules[e] = False


# These modules are essential.
# Qkit does not start if they are not available.
ESSENTIALS = ['numpy', 'h5py', 'zmq']

for e in ESSENTIALS:
    if not qkit.module_available(e):
        raise ImportError(
                "Module '%s' not found. The following modules are essentially needed for basic operation of QKIT:\n - %s" % (e, "\n - ".join(ESSENTIALS)))

# These modules are optional, but very common.
# Typically, they are not used for key functions, so the code should mostly work without them
OPTIONALS = ["IPython", "PyQt4", "PyQt5", "ipywidgets", "matplotlib", "pandas", "peakutils", "pyqtgraph", "scipy"]
for e in OPTIONALS:
    qkit.module_available(e)

