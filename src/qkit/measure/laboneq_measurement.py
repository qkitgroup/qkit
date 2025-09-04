from laboneq.simple import *

from qkit.measure.unified_measurements import MeasurementTypeAdapter, Axis


class LabOneQMeasurement(MeasurementTypeAdapter):
    """
    A measurement adapter for LabOneQ experiments.
    Allows adapting all the LabOneQ measurements to Qkit storage and measurement infrastructure.
    """

    _session: Session
    _compiled_experiment: CompiledExperiment
    _structure: tuple['MeasurementTypeAdapter.DataDescriptor', ...]

    def __init__(self, session: Session, experiment: Experiment, unit: str = 'a.u.'):
        super().__init__()
        self._session = session
        self._compiled_experiment = self._session.compile(experiment)
        emulated_session = Session(device_setup=self._compiled_experiment.device_setup)
        emulated_session.connect(do_emulation=True)
        emulated_result = emulated_session.run(self._compiled_experiment)
        self._structure = tuple(
            MeasurementTypeAdapter.DataDescriptor(
                name=name,
                axes=tuple(Axis(name=name, range=values) for (name, values) in zip(entry.axis_name, entry.axis)),
                unit=unit
            ) for (name, entry) in emulated_result.acquired_results
        )

    @property
    def expected_structure(self) -> tuple['MeasurementTypeAdapter.DataDescriptor', ...]:
        return self._structure

    def perform_measurement(self) -> tuple['MeasurementTypeAdapter.GeneratedData', ...]:
        result: Results = self._session.run(self._compiled_experiment)
        return tuple(
            descriptor.with_data(result.acquired_results[descriptor.name].data) for descriptor in self._structure
        )