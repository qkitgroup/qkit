from qkit.drivers.ZHInst_Abstract import ZHInst_Abstract
from zhinst.toolkit.control.drivers import PQSC as _PQSC


class ZHInst_PQSC(ZHInst_Abstract):
    def __init__(self, name, serialnumber, host="129.13.93.38",  **kwargs):
        super().__init__(name, **kwargs)
        self._pqsc = _PQSC(name, serialnumber, host=host)
        self._pqsc.setup()
        self._pqsc.connect_device()
        
        # Iterate node tree for readable entries and hook them into QKit
        self.blacklist = ["system_fwlog", "features_code"]
        self.mount_api("node_dump_shfsg.txt", self._pqsc.nodetree)

        # Register readout methods
