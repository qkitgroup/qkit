import numpy as np
from zhinst.toolkit.control.drivers import SHFSG as _SHFSG
from qkit.drivers.ZHInst_Abstractv2 import ZHInst_Abstract


class ZHInst_SHFSGv2(ZHInst_Abstract):
    def __init__(self, name, serialnumber, host="129.13.93.38",  **kwargs):
        super().__init__(name, **kwargs)
        self._shfsg = _SHFSG(name, serialnumber, host=host)
        self._shfsg.setup()
        self._shfsg.connect_device()
        
        # Iterate node tree for readable entries and hook them into QKit
        self.mount_api(self._shfsg.nodetree)
        self.nodetree = self._shfsg.nodetree
        # Register readout methods

    
        
