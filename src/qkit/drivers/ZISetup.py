import logging
from types import NoneType

from laboneq.dsl.device import DeviceSetup
from laboneq.dsl.quantum import QPU, QuantumParameters
from laboneq.dsl.quantum.quantum_element import AttrDict, QuantumElement
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
        parameters: QuantumParameters = self._qubits[0].parameters
        attributes = [entry for entry in dir(parameters) if not entry.startswith('_') and not callable(getattr(parameters, entry))]
        for key in attributes:
            inferred_type = type(getattr(parameters, key))
            if inferred_type is AttrDict:
                inferred_type = dict
            elif inferred_type is NoneType:
                inferred_type = float
            self.add_parameter(key, channels=(0, len(self._qubits)-1), type=inferred_type, flags=Instrument.FLAG_GETSET,
                               get_func=lambda channel, _key=key: getattr(self.get_qubit(channel).parameters, _key),
                               set_func=lambda value, channel, _key=key: setattr(self.get_qubit(channel).parameters, _key, value))

    def get_qpu(self) -> QPU:
        return self._qpu

    def get_qubit(self, index: int) -> QuantumElement:
        return self._qubits[index]

    def get_session(self):
        return self._session