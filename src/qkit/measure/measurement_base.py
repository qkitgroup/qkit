from dataclasses import dataclass
import numpy as np
from abc import ABC, abstractmethod
from typing import Optional, Callable, Protocol
import textwrap

from qkit.measure.samples_class import Sample


# The unified measurement class infrastructure. Will attempt to unify all kinds of measurements into a common code base.
# This needs to do the following:
# - Allow for sweeps along various axis
# - (Optionally) Log some kind of measurement for each point of this axis
# - When at the point of the axis, perform some kind of measurement. This measurement may be 0- or 1-Dimensional
# - The points of a sweep may be a subset of the total range, depending on the previous axes.
#
# It would be beneficial to have easy to understand syntax for this behaviour. With-Statements could be useful here.
#
# Proposed API:
# measurement = Measurement() # At this point we don't care about the actual type of data.
# with measurement.sweep() as x_sweep:
#   x_sweep.measure(MeasureOther()) # Log some value
#   with x_sweep.sweep() as y_sweep:
#       y_sweep.measure(MeasureWrapper()) # Main measurement
#
# measurement.run()
#
# (Measurement, Sweep).sweep(
#   setter: Callable(float),
#   full_range: np.ndarray(float, 1D),
#   filter: Callable(np.ndarray(float, 1D) -> np.ndarray(bool, 1D))
# ) -> Sweep
#
# 
# measure(
#   measurement_adapter: MeasurementAdapter
# )

@dataclass(frozen=True)
class EnterableWrapper[T]:
    value: T

    def __enter__(self):
        return self.value

    def __exit__(self, *args):
        pass


class ParentOfSweep(ABC):
    """
    Abstract class handling the children relationship of sweeps.
    """
    _sweep_child: Optional['Sweep']

    def __init__(self) -> None:
        super().__init__()
        self._sweep_child = None

    def sweep(self,
              setter: Callable[[float], None],
              axis: 'Axis',
              axis_filter: Optional[Callable[[np.ndarray], np.ndarray]] = None) -> EnterableWrapper['Sweep']:
        s = Sweep(setter=setter, axis=axis, axis_filter=axis_filter)
        self._sweep_child = s
        return EnterableWrapper(s)

    def _run_child_sweep(self, **context: float):
        if self._sweep_child is not None:
            self._sweep_child._run_sweep(**context)


class ParentOfMeasurements(ABC):
    """
    Abstract class handling the ownership of measurements and running them.
    """

    _measurements: list['MeasurementTypeAdapter']

    def __init__(self) -> None:
        super().__init__()
        self._measurements = []

    def measure(self, measurement_type: 'MeasurementTypeAdapter'):
        """
        Register a measurement type at this stage. Will be executed before any nested sweeps.
        """
        self._measurements.append(measurement_type)

    def _run_measurements(self):
        """
        Run the measurements and handle the acquired data.
        """
        for measurement_type in self._measurements:
            measurement_type.perform_measurement()  # TODO handle the returned data


class FilterCallback(Protocol):
    def __call__(self, axis_values: np.ndarray, **kwargs: float) -> np.ndarray:
        pass


class Sweep(ParentOfSweep, ParentOfMeasurements):
    """
    Describes a sweep of some parameter set with the setter over some range.

    Optionally filtered to allow landscape measurements.

    Can have measurements as children. There is no distinction between log functions and measurements.
    """
    _setter: Callable[[float], None]
    _axis: 'Axis'
    _filter: Optional[FilterCallback] = None

    def __init__(self, setter, axis, axis_filter=None) -> None:
        super().__init__()
        super(ParentOfSweep, self).__init__()
        self._setter = setter
        self._axis = axis
        self._filter = axis_filter

    def _run_sweep(self, **context: float):
        """
        Internal function to run the sweep. You should not call this outside of measurement_base.py!

        Performs the sweep, checks for filters, and updates **context before continuing down the chain of sweeps.
        """
        if self._filter is not None:
            mask = self._filter(self._axis.range, **context)
            filtered_range = self._axis.range[mask]
        else:
            filtered_range = self._axis.range
        assert filtered_range is not None, "Initialization of range failed!"

        # Do the sweep!
        for value in filtered_range:
            self._setter(value)

            self._run_measurements()

            # Go down the nested sweeps.
            if self._sweep_child is not None:
                new_context = context.copy()
                new_context[self._axis.name] = value
                self._sweep_child._run_sweep(**new_context)

    def __str__(self):
        setter_name = self._setter.__qualname__
        filter_repr = self._filter.__qualname__ if self._filter is not None else "None"
        self_repr = f"Sweep(setter={setter_name}, range={str(self._axis)}, filter={filter_repr})"
        if self._sweep_child is not None:
            self_repr += ":\r\n"
            self_repr += textwrap.indent(str(self._sweep_child), '\t')
        return self_repr


@dataclass(frozen=True)
class Axis:
    name: str
    range: np.ndarray
    unit: str = 'a.u.'

    def __str__(self):
        low = np.min(self.range)
        high = np.max(self.range)
        return f"{self.name}=({low} {self.unit} to {high} {self.unit} in {len(self.range)} steps)"


class MeasurementTypeAdapter(ABC):
    """
    A high level Adapter Interface to the Measurement Type Specific Code.

    Should implement a particular kind of measurement, such as Spectroscopy, IV-Curve, ..., which
    then communicates with the device driver using its own interfaces.
    """

    @property
    @abstractmethod
    def expected_structure(self) -> list['MeasurementTypeAdapter.MeasurementDescriptor']:
        """
        Return a list of MeasurementDescriptors for this kind of measurement.

        This is used to initialize the measurement files.
        """
        pass

    @abstractmethod
    def perform_measurement(self) -> list['MeasurementTypeAdapter.MeasurementData']:
        """
        Perform the measurement and return a list of MeasurementData.

        The length of this list must be identical to the one returned by expected_structure,
        and all MeasurementDescriptors associated with MeasurementData must be present in expected_structure.
        """
        pass

    @dataclass(frozen=True)
    class MeasurementDescriptor:
        """
        A dataclass containing a n-Dimensional measurement result with axis data.
        """
        name: str
        axes: tuple[Axis]
        unit: str = 'a.u.'

        def with_data(self, data: np.ndarray | float) -> 'MeasurementTypeAdapter.MeasurementData':
            """
            Create a MeasurementData object from this MeasurementDescriptor and the provided data.
            """
            return MeasurementTypeAdapter.MeasurementData(self, data=np.asarray(data))

    @dataclass(frozen=True)
    class MeasurementData:
        """
        Actual Measurement Data, associating a Descriptor with a nd-array.

        Created by calling MeasurementDescriptor.with_data(data).
        """
        descriptor: 'MeasurementTypeAdapter.MeasurementDescriptor'
        data: np.ndarray

        def validate(self):
            assert len(self.descriptor.axes) == len(self.data.shape), "Axis data incongruent with "
            for (i, axis) in enumerate(self.descriptor.axes):
                self.data.shape[i] = len(axis.range)


class Experiment(ParentOfSweep, ParentOfMeasurements):

    _name: str
    _sample: Sample

    def __init__(self, name: str, sample: Sample) -> None:
        super().__init__()
        super(ParentOfSweep, self).__init__()
        self._name = name
        self._sample = sample


    def run(self):
        """
        Perform the configured measurements. Sweep the nested axes and record the results.
        """
        self._run_measurements()
        self._run_child_sweep()
        # TODO: Use the measurement_class stuff to write the instrument state

    def __str__(self):
        return "Experiment:\r\n" + (
            textwrap.indent(str(self._sweep_child), '\t') if self._sweep_child is not None else "No Sweep"
        )
