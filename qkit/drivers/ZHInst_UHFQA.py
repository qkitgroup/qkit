from qkit.drivers.ZHInst_Common import ZHInst_Device, ZHInst_Path, ZHInst_AWG_Mixin
from typing import Union
import zhinst

class ZHInst_UHFQA(ZHInst_Device, ZHInst_AWG_Mixin):
    """
    This class provides access to a Zurich Instrument UHFQA (Ultra High Frequency Quantum Analyzer).
    This allows users to manage triggers, integrators, upload programs and perform measurements.

    Roughly, this device consists of two main components:
    - The Arbitrary Waveform Generator (AWG) generating signals to affect the Qubits
    - The Qubit Measurement Unit analyzing the Qubits response

    Between them, trigger signals can be exchanged and transceived with the outside world.
    Further, 4 auxiliary outputs (NOT IMPLEMENTED) and 2 auxiliary inputs (NOT IMPLEMENTED) exist exist.
    """

    def __init__(self, name, device_id, server="localhost", port=8004, interface="1GbE"):
        super().__init__(name, device_id, server=server, port=port, interface=interface)

    class QuantumAnalyzerSystem(ZHInst_Path):

        def __init__(self, accessor: Union[zhinst.ziPython.ziDAQServer, 'ZHInst_Path'], qas_index: int):
            super().__init__(accessor, f"QAS/{qas_index}")
