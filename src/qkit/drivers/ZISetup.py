import logging

from laboneq.dsl.device import DeviceSetup
from laboneq.dsl.quantum import QPU
from laboneq.dsl.session import Session
from laboneq_applications.qpu_types.tunable_transmon import TunableTransmonQubit, TunableTransmonOperations

from qkit.core.instrument_base import Instrument


class ZISetup(Instrument):

    def __init__(self, name: str, address: str, descriptor, **kwargs):
        super().__init__(name, **kwargs)
        self._setup = DeviceSetup.from_descriptor(descriptor, address)
        self._session = Session(self._setup, log_level=logging.WARNING)
        self._session.connect(reset_devices=True)
        self._qubits = TunableTransmonQubit.from_device_setup(self._setup)
        self._qops = TunableTransmonOperations()
        self._qpu = QPU(self._qubits, quantum_operations=self._qops)

        # Register parameters for each qubit.
        parameters = self._qubits[0].parameters
        attributes = [entry for entry in dir(parameters) if not entry.startswith('_') and not callable(getattr(parameters, entry))]
        for key in attributes:
            self.add_parameter(key, channels=(0, len(self._qubits)-1), type=type(getattr(parameters, key)),
                               get_cmd=lambda channel: getattr(self._qubits[channel].parameters, key),
                               set_cmd=lambda value, channel: setattr(self._qubits[channel].parameters, key, value))

    def get_qpu(self):
        return self._qpu

    def get_qubit(self, index: int):
        return self._qubits[index]