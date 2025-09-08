import logging

from laboneq.simple import *

from qkit.measure.unified_measurements import MeasurementTypeAdapter, Axis

from typing import Optional, List

import numpy as np


class LabOneQMeasurement(MeasurementTypeAdapter):
    """
    A measurement adapter for LabOneQ experiments.
    Allows adapting all the LabOneQ measurements to Qkit storage and measurement infrastructure.
    """

    _session: Session
    _compiled_experiment: CompiledExperiment
    _structure: tuple['MeasurementTypeAdapter.DataDescriptor', ...]

    @staticmethod
    def sanitize_name(internal_name):
        return internal_name.replace('/', '_').replace(' ', '_')

    def __init__(self, session: Session, experiment: Experiment, unit: str = 'a.u.', axis_units: Optional[List[str]] = None):
        super().__init__()
        self._session = session
        self._compiled_experiment = self._session.compile(experiment)
        emulated_session = Session(device_setup=self._compiled_experiment.device_setup, log_level=logging.WARNING)
        emulated_session.connect(do_emulation=True)
        emulated_result = emulated_session.run(self._compiled_experiment)
        self._structure = tuple()
        for (name, entry) in emulated_result.acquired_results.items():
            sanitized = LabOneQMeasurement.sanitize_name(name)
            if axis_units is None:
                axis_units = ("a.u.",) * len(entry.axis_name)
            axes = tuple(Axis(name=name, range=values, unit=unit) for (name, values, unit) in zip(entry.axis_name, entry.axis, axis_units))
            if np.iscomplexobj(entry.data):
                self._structure += (
                    MeasurementTypeAdapter.DataDescriptor(name=sanitized + "_real", axes=axes, unit=unit),
                    MeasurementTypeAdapter.DataDescriptor(name=sanitized + "_imag", axes=axes, unit="i" + unit),
                    MeasurementTypeAdapter.DataDescriptor(name=sanitized + "_mag", axes=axes, unit=unit),
                    MeasurementTypeAdapter.DataDescriptor(name=sanitized + "_phase", axes=axes, unit='rad')
                )
            else:
                self._structure += tuple(
                    MeasurementTypeAdapter.DataDescriptor(name=sanitized, axes=axes, unit=unit)
                )

    @property
    def expected_structure(self) -> tuple['MeasurementTypeAdapter.DataDescriptor', ...]:
        return self._structure

    def perform_measurement(self) -> tuple['MeasurementTypeAdapter.GeneratedData', ...]:
        result: Results = self._session.run(self._compiled_experiment)
        def data_mapper(acquired_results):
            for (name, entry) in acquired_results.items():
                if np.iscomplexobj(entry.data):
                    yield (name + "_real", np.real(entry.data))
                    yield (name + "_imag", np.imag(entry.data))
                    yield (name + "_mag", np.abs(entry.data))
                    yield (name + "_phase", np.angle(entry.data))
                else:
                    yield (name, entry.data)
        return tuple(
            descriptor.with_data(datum) for descriptor, (_, datum) in zip(self._structure, data_mapper(result.acquired_results))
        )