from _typeshed import Self
from qkit.drivers.ZHInst_Common import ZHInst_Device, ZHInst_Path, ZHInst_AWG_Mixin
from typing import Union, List
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

    outputs: List(Self.Output)
    inputs: List(Self.Inputs)
    awg: Self.AWG

    def __init__(self, name, device_id, server="localhost", port=8004, interface="1GbE"):
        super().__init__(name, device_id, server=server, port=port, interface=interface)

        self.outputs = [Self.Output(self, i) for i in range(1)] # We have two outputs, indecies 0, 1
        self.inputs = [Self.Input(self, i) for i in range(1)] # We have two inputs aswell.
        self.awg = Self.AWG(self, 0) # In principle, there is support for multiple AWGs. We only use 1?
        

    class Output(ZHInst_Path):

        def __init__(self, accessor: Union[zhinst.ziPython.ziDAQServer, 'ZHInst_Path'], output_id: int):
            super().__init__(accessor, f"sigouts/{output_id}")

        def set_enabled(self, enabled: bool):
            self.setBool("on", enabled)

        def get_enabled(self):
            return self.getBool("on")

    class Input(ZHInst_Path):

        def __init__(self, accessor: Union[zhinst.ziPython.ziDAQServer, 'ZHInst_Path'], input_id: int):
            super().__init__(accessor, f"sigins/{input_id}")

        # TODO: Create accessors. Whenever they are needed.

    class AWG(ZHInst_Path):

        def __init__(self, accessor: Union[zhinst.ziPython.ziDAQServer, 'ZHInst_Path'], awg_id: int):
            super().__init__(accessor, f"awgs/{awg_id}")
            # TODO: Auxtriggers? Triggers?, 

        def set_enabled(self, enabled: bool):
            self.setBool("enable", enabled)

        def get_enabled(self) -> bool:
            return self.getBool("enable")

        def set_user_register(self, register: int, value: int):
            self.setInt(f"userregs/{register}", value)

        def get_user_register(self, register: int) -> int:
            return self.getInt(f"userregs/{register}")

        def set_time(self, exponent: int):
            """
            Sets the sampling rate. [exponent] must be in the interval 0..=13.
            The formula for the sampling rate then is:
            f = 1.8GHz / (2^exponent)
            """
            assert 0 <= exponent <= 13, "Exponent out of range!"
            self.setInt("time", exponent)

        def get_time(self) -> int:
            return self.getInt("time")

        def set_single_shot(self, single_shot: bool):
            self.setBool("single", single_shot)

        def is_ready(self) -> bool:
            return self.getBool("ready")

        class Output(ZHInst_Path):

            def __init__(self, accessor: Union[zhinst.ziPython.ziDAQServer, 'ZHInst_Path'], output_id):
                super().__init__(accessor, f"outputs/{output_id}")

            def set_amplitude(self, amplitude: float):
                self.setDouble("amplitude", amplitude)

            def get_am