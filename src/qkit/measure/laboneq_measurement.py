import logging

from laboneq.simple import *

from qkit.measure.unified_measurements import MeasurementTypeAdapter, Axis

from typing import Optional, List, Generator

import numpy as np

log = logging.getLogger(__name__)

class LabOneQMeasurement(MeasurementTypeAdapter):
    """
    A measurement adapter for LabOneQ experiments.
    Allows adapting all the LabOneQ measurements to Qkit storage and measurement infrastructure.
    """

    _session: Session
    _experiment: Experiment
    _structure: tuple['MeasurementTypeAdapter.DataDescriptor', ...]

    @staticmethod
    def sanitize_name(internal_name):
        return internal_name.replace('/', '_').replace(' ', '_')

    @staticmethod
    def flatten(l: list) -> Generator:
        """
        Takes a list of lists and flattens it into a list. Must handle the case where the root list entries are not lists.
        """
        for element in l:
            if isinstance(element, list):
                yield from LabOneQMeasurement.flatten(element)
            else:
                yield element

    def __init__(self, session: Session, experiment: Experiment, unit: str = 'a.u.', axis_units: Optional[List[str]] = None):
        super().__init__()
        self._session = session
        self._experiment = experiment
        log.debug("Compiling LabOneQ experiment for measurement structure inspection.")
        compiled_experiment = self._session.compile(self._experiment)

        log.debug("Starting emulated session...")
        emulated_session = Session(device_setup=compiled_experiment.device_setup, log_level=logging.WARNING)
        emulated_session.connect(do_emulation=True)
        log.debug("Running emulated experiment...")
        emulated_result = emulated_session.run(compiled_experiment)

        log.debug("Received emulated result. Building measurement structure...")
        self._structure = tuple()
        for (name, entry) in emulated_result.acquired_results.items():
            sanitized = LabOneQMeasurement.sanitize_name(name)
            axis_names = list(LabOneQMeasurement.flatten(entry.axis_name))
            axes = tuple(LabOneQMeasurement.flatten(entry.axis))
            log.debug("Discovered result '%s' with '%d' axes called %s.", sanitized, len(axes), str(axis_names))
            if axis_units is None:
                axis_units = ("a.u.",) * len(axis_names)
            axes = tuple(Axis(name=name, range=values, unit=unit) for (name, values, unit) in zip(axis_names, axes, axis_units))
            if np.iscomplexobj(entry.data):
                self._structure += (
                    MeasurementTypeAdapter.DataDescriptor(name=sanitized + "_real", axes=axes, unit=unit),
                    MeasurementTypeAdapter.DataDescriptor(name=sanitized + "_imag", axes=axes, unit="i" + unit),
                    MeasurementTypeAdapter.DataDescriptor(name=sanitized + "_mag", axes=axes, unit=unit),
                    MeasurementTypeAdapter.DataDescriptor(name=sanitized + "_phase", axes=axes, unit='rad')
                )
            else:
                self._structure += (
                    MeasurementTypeAdapter.DataDescriptor(name=sanitized, axes=axes, unit=unit),
                )
        log.debug("Finished building measurement structure.")
        log.debug(f"Measurement structure: {self._structure}")

    @property
    def expected_structure(self) -> tuple['MeasurementTypeAdapter.DataDescriptor', ...]:
        return self._structure

    def perform_measurement(self) -> tuple['MeasurementTypeAdapter.GeneratedData', ...]:
        compiled_experiment = self._session.compile(self._experiment)
        result: Results = self._session.run(compiled_experiment)
        def data_mapper(acquired_results):
            for (name, entry) in acquired_results.items():
                if np.iscomplexobj(entry.data):
                    yield name + "_real", np.real(entry.data)
                    yield name + "_imag", np.imag(entry.data)
                    yield name + "_mag", np.abs(entry.data)
                    yield name + "_phase", np.angle(entry.data)
                else:
                    yield name, entry.data
        return tuple(
            descriptor.with_data(datum) for descriptor, (_, datum) in zip(self._structure, data_mapper(result.acquired_results))
        )

    @staticmethod
    def calculate_range_and_amplitudes(power: float | np.ndarray) -> tuple[float, np.ndarray]:
        """
        Based on an output power or an array of output powers, calculate the amplitudes and output range for ZI.
        :param power: The output power or array of output powers in dBm
        :return: The output range and the amplitudes
        """
        powers = np.asarray(power)
        maximum_power = np.max(powers)
        # Adjust to steps of 5
        output_range = np.ceil(maximum_power / 5) * 5
        # Calculate amplitudes relative to output range
        amplitudes = np.power(10, (powers - output_range) / 20)
        assert np.all(amplitudes >= 0), "Amplitudes must be positive!"
        assert np.all(amplitudes <= 1), "Amplitudes must be less than or equal to 1!"
        return output_range, amplitudes

    @staticmethod
    def calculate_powers(amplitudes: float | np.ndarray, device_range: float) -> np.ndarray:
        """
        Based on a device input or output range and amplitudes, calculate the corresponding powers in dBm.
        """
        return device_range + 20 * np.log10(amplitudes)