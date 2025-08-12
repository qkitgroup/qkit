import logging
import threading
import time
from dataclasses import dataclass
import numpy as np
from abc import ABC, abstractmethod
from typing import Optional, Callable, Protocol, override, Literal, Iterable
import textwrap
from h5py import Dataset
import json
from tqdm.auto import tqdm

import qkit
from qkit.measure.json_handler import QkitJSONEncoder
from qkit.measure.samples_class import Sample
from qkit.measure.measurement_class import Measurement
import qkit.measure.write_additional_files as waf
from qkit.storage.thin_hdf import HDF5
from qkit.storage.file_path_management import MeasurementFilePath
import qkit.gui.plot.plot as qviewkit  # Who names these things?
from warnings import warn

"""
The unified measurement class infrastructure. Will attempt to unify all kinds of measurements into a common code base.
This needs to do the following:
- Allow for sweeps along various axis
- (Optionally) Log some kind of measurement for each point of this axis
- When at the point of the axis, perform some kind of measurement. This measurement may be 0- or 1-Dimensional
- The points of a sweep may be a subset of the total range, depending on the previous axes.
- Handle the dataset management ourselves, as the wrapped wrapper from store is too complicated.
- Custom Views
- Default Views
- Analysis
- Progress Bars
- Open Qviewkit

Nesting is performed using with-statement to improve readability.

Proposed API:
>>> e = Experiment() # At this point we don't care about the actual type of data.
>>> with e.sweep() as x_sweep:
>>>     x_sweep.measure(MeasureOther()) # Log some value
>>>     with x_sweep.sweep() as y_sweep:
>>>         y_sweep.measure(MeasureWrapper()) # Main measurement
>>>
>>>  e.run()

>>> (Measurement, Sweep).sweep(
>>>     setter: Callable(float),
>>>     full_range: np.ndarray(float, 1D),
>>>     filter: Callable(np.ndarray(float, 1D) -> np.ndarray(bool, 1D))
>>> ) -> Sweep


>>> measure(
>>>     measurement_adapter: MeasurementAdapter
>>> )
"""

warn("The unified measurement class infrastructure is still in development and considered experimental.", DeprecationWarning)
if not qkit.cfg.get("measurement.unified_measurements.enabled", False):
    raise RuntimeError("Experimental feature requires explicit opt-in!")

# The custom format of the progress bar for qkit
def bar_format():
    """
    Build the format string for the progress bar.

    Uses tqdm as a progress bar, extending it with a start time.
    """
    current_time = time.strftime("%H:%M:%S", time.localtime())
    info_line = f"✈ {current_time} " + "🕐 {elapsed} ✚ {remaining} "
    return "{l_bar} " + info_line + '{bar}{n_fmt}/{total_fmt}, {rate_fmt} ➤ {eta}'

@dataclass(frozen=True)
class EnterableWrapper[T]:
    """
    Return this to require the user to use a with-statement.
    """
    value: T

    def __enter__(self):
        return self.value

    def __exit__(self, *args):
        pass

measurement_log = logging.getLogger("Measurement")

class ParentOfSweep(ABC):
    """
    Abstract class handling the relationship to sweeps.

    Has a single child sweep. Can be called upon to perform the sweep.
    """
    _sweep_child: Optional['Sweep']

    def __init__(self) -> None:
        super().__init__()
        self._sweep_child = None

    def sweep(self,
              setter: Callable[[float], None],
              axis: 'Axis',
              axis_filter: Optional[Callable[[np.ndarray], np.ndarray]] = None) -> EnterableWrapper['Sweep']:
        """
        Create a sweep over some axis (optionally filtered), setting the value using the setter.

        It is recommended to add the filter function using the `sweep.filtered()` call for improved readability.

        Used with `with`-statements:
        >>> e = Experiment()
        >>> with e.sweep(lambda val: None, Axis("x", np.linspace(0, 1, 10))) as x_sweep:
        >>>     x_sweep.filtered(lambda r: np.logical_and(r <= 8, r >= 2))
        >>>     pass # Do something, e.g., measure on each position.
        """
        s = Sweep(setter=setter, axis=axis, axis_filter=axis_filter)
        self._sweep_child = s
        return EnterableWrapper(s)

    def _run_child_sweep(self, data_file, index_list: tuple[int, ...]):
        if self._sweep_child is not None:
            self._sweep_child._run_sweep(data_file, index_list)

    @property
    def _child_dimensionality(self):
        if self._sweep_child is not None:
            return self._sweep_child.dimensionality
        else:
            return 0


class ParentOfMeasurements(ABC):
    """
    Abstract class handling the ownership of measurements and running them.

    Can have multiple measurements and manages them (calls them for creation of datasets and running the measurements).
    """

    _measurements: list['MeasurementTypeAdapter']

    def __init__(self) -> None:
        super().__init__()
        self._measurements = []

    def measure(self, measurement_type: 'MeasurementTypeAdapter'):
        """
        Register a measurement type at this stage. Will be executed before any nested sweeps.

        Example:
        >>> e = Experiment()
        >>> with e.sweep(lambda val: None, Axis("x", np.linspace(0, 1, 10))) as x_sweep:
        >>>     x_sweep.measure(ScalarMeasurement('const', lambda: 1.0))
        """
        self._measurements.append(measurement_type)

    @property
    def _largest_measurement_dimension(self):
        """
        Get the largest dimensionality of all measurements.
        """
        if len(self._measurements) == 0:
            return 0
        return max(map(lambda m: len(m.expected_structure), self._measurements))

    def create_datasets(self, data_file: HDF5, swept_axes: list[Dataset]):
        """
        Based on the measurements and parent sweeps, create the datasets.
        """
        for measurement in self._measurements:
            measurement.create_datasets(data_file, swept_axes)

    def run_measurements(self, data_file: HDF5, index_list: tuple[int, ...]):
        """
        Run the measurements and handle the acquired data.
        """
        for measurement_type in self._measurements:
            measurement_type.record(data_file, index_list)


class FilterCallback(Protocol):
    """
    A helper class defining the function signature of a filter callback.
    """
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
    _current_value: Optional[float] = None

    def __init__(self, setter: Callable[[float], None], axis: 'Axis', axis_filter: Optional[FilterCallback]=None) -> None:
        super().__init__()
        super(ParentOfSweep, self).__init__()
        self._setter = setter
        self._axis = axis
        self._filter = axis_filter

    def filtered(self, axis_filter: FilterCallback) -> 'Sweep':
        self._filter = axis_filter
        return self

    def _generate_enumeration(self) -> tuple[Iterable[tuple[int, float]], Optional[int]]:
        """
        Generates the indices and values of the sweep.
        Returns the iterator over indices and values, as well as the expected size (or None if unknown).
        """
        if self._filter is not None:
            # Apply the filter to get the subset we need to sweep over.
            mask = self._filter(self._axis.range)
            filtered_range = self._axis.range[mask]
            filtered_indices = np.where(mask)[0]
        else:
            filtered_range = self._axis.range
            filtered_indices = np.arange(len(filtered_range))
        assert filtered_range is not None, "Initialization of range failed!"
        return zip(filtered_indices, filtered_range), len(filtered_range)

    def _run_sweep(self, data_file: HDF5, index_list: tuple[int, ...]):
        """
        Internal function to run the sweep. You should not call this outside measurement_base.py!

        Perform the sweep, checks for filters, and continue down the chain of sweeps.
        """
        sweep, size = self._generate_enumeration()
        try:
            for index, value in tqdm(sweep, desc=self._axis.name, bar_format=bar_format(), total=size, leave=False):
                try:
                    self._setter(value)
                    self._current_value = value
                except Exception as e:
                    measurement_log.error(f"Error setting {self._axis.name} to {value}.", exc_info=e)
                    raise e

                self.run_measurements(data_file, index_list + (index,))

                # Go down the nested sweeps.
                if self._sweep_child is not None:
                    self._sweep_child._run_sweep(data_file, index_list + (index,))
        finally:
            # Reset the 'current value',
            self._current_value = None

    @override
    def create_datasets(self, data_file: HDF5, swept_axes: list[Dataset]):
        swept_axes.append(self._axis.get_data_axis(data_file))
        super().create_datasets(data_file, swept_axes)
        if self._sweep_child is not None:
            self._sweep_child.create_datasets(data_file, swept_axes)

    def __str__(self):
        setter_name = self._setter.__qualname__
        filter_repr = self._filter.__qualname__ if self._filter is not None else "None"
        self_repr = f"Sweep(setter={setter_name}, range={str(self._axis)}, filter={filter_repr})"
        for measurement in self._measurements:
            self_repr += '\n' + textwrap.indent(str(measurement), '\t')
        if self._sweep_child is not None:
            self_repr += '\n' + textwrap.indent(str(self._sweep_child), '\t')
        return self_repr

    @property
    def dimensionality(self):
        return 1 + max(self._largest_measurement_dimension, self._child_dimensionality)

    @property
    def current_value(self):
        """When called during a sweep, returns the current value of the sweep, None otherwise."""
        return self._current_value


@dataclass(frozen=True)
class Axis:
    """
    An object describing an axis of a measurement. Has a name, unit, and values it can have.
    """
    name: str
    range: np.ndarray
    unit: str = 'a.u.'

    def get_data_axis(self, data_file: HDF5):
        """
        Returns the filled axis data set. Creates it if it doesn't exist yet.
        """
        if data_file.get_dataset(self.name) is None:
            ds = data_file.create_dataset(self.name, (len(self.range),), self.unit)
            ds[:] = self.range
        return data_file.get_dataset(self.name)

    def __str__(self):
        low = np.min(self.range)
        high = np.max(self.range)
        return f"{self.name}=({low} {self.unit} to {high} {self.unit} in {len(self.range)} steps)"


class DataGenerator(ABC):
    """
    A high-level Adapter Interface for everything that generates data.

    Handles storing data into datasets, and provides the structures for describing the data.
    """

    @property
    def dataset_category(self) -> Literal['data', 'analysis']:
        """
        The category into which the returned data should be sorted.
        """
        return 'data'

    def store(self, data_file: HDF5, data: tuple['MeasurementTypeAdapter.GeneratedData', ...], sweep_indices: tuple[int, ...]):
        """
        Store the generated [data] in the [data_file], while selecting based on the current [sweep_indices].
        """
        assert isinstance(data, tuple), "Measurement must return a tuple of MeasurementData!"
        for datum in data:
            assert isinstance(datum, self.GeneratedData), "Measurement must return a tuple of MeasurementData!"
            datum.validate()
            ds = data_file.get_dataset(datum.descriptor.name, category=self.dataset_category)
            assert ds is not None, f"Dataset {datum.descriptor.name} not found!"
            # Based on the sweeps that occurred, get the relevant subset of the Dataset
            assert np.all(np.isnan(ds[*sweep_indices])), \
                "Overwriting data! This indicates a logic error in the sweeps!"
            ds[*sweep_indices] = datum.data
            ds.flush()
        data_file.flush()

    @dataclass(frozen=True)
    class DataDescriptor:
        """
        A dataclass containing a n-Dimensional measurement result with axis data.
        """
        name: str
        axes: tuple[Axis]
        unit: str = 'a.u.'

        def with_data(self, data: np.ndarray | float) -> 'MeasurementTypeAdapter.GeneratedData':
            """
            Create a MeasurementData object from this MeasurementDescriptor and the provided data.
            """
            return MeasurementTypeAdapter.GeneratedData(self, data=np.asarray(data))

    @dataclass(frozen=True)
    class GeneratedData:
        """
        Actual Measurement Data, associating a Descriptor with a nd-array.

        Created by calling MeasurementDescriptor.with_data(data).
        """
        descriptor: 'MeasurementTypeAdapter.DataDescriptor'
        data: np.ndarray

        def validate(self):
            assert len(self.descriptor.axes) == len(self.data.shape), "Axis data incongruent with descriptor"
            for (i, axis) in enumerate(self.descriptor.axes):
                assert self.data.shape[i] == len(axis.range), f"Axis ({axis.name}) length and data length mismatch"


class AnalysisTypeAdapter(DataGenerator, ABC):
    """
    A high-level Adapter Interface to the Analysis-Specific Code.

    Should implement a particular kind of analysis, such as Resonator fitting, numerical derivatives, ...
    """
    def record(self, data_file: HDF5, sweep_indices: tuple[int, ...], measured_data: tuple['MeasurementTypeAdapter.GeneratedData', ...]):
        """
        Perform the analysis and record the results.
        """
        try:
            data = self.perform_analysis(measured_data)
        except Exception as e:
            measurement_log.error(f"Analysis failed for {self}: {e}", exc_info=e)
            raise e
        else:
            self.store(data_file, data, sweep_indices)

    def create_datasets(self, data_file: HDF5, parent_schema: tuple['MeasurementTypeAdapter.DataDescriptor', ...], swept_axes: list[Dataset]):
        """
        Create the datasets as described in the schema provided by the child class with [expected_structure].
        """
        for descriptor in self.expected_structure(parent_schema):
            all_axes = swept_axes + list(map(lambda ax: ax.get_data_axis(data_file), list(descriptor.axes)))
            data_file.create_dataset(descriptor.name,
                                     tuple(map(lambda axis: len(axis), all_axes)),
                                     descriptor.unit,
                                     axes=all_axes,
                                     category='analysis'
                                     )

        for name, view in self.default_views(parent_schema).items():
            data_file.insert_view(name, view)

    @override
    @property
    def dataset_category(self) -> Literal['data', 'analysis']:
        return 'analysis'

    @abstractmethod
    def expected_structure(self, parent_schema: tuple['MeasurementTypeAdapter.DataDescriptor', ...]) -> tuple[
        'MeasurementTypeAdapter.DataDescriptor', ...]:
        """
        The datasets to be created in the analysis section of the file.
        """
        pass

    @abstractmethod
    def default_views(self, parent_schema: tuple['MeasurementTypeAdapter.DataDescriptor', ...]) -> dict[str, HDF5.DataView]:
        """
        A default set of views to be created for this kind of measurement. Can be empty.
        Maps the name to the view, thus a dict.
        """
        return {}

    @abstractmethod
    def perform_analysis(self, data: tuple['MeasurementTypeAdapter.GeneratedData', ...]) -> tuple['MeasurementTypeAdapter.GeneratedData', ...]:
        """
        Perform the Analysis on the data of the measurement.
        """
        pass

class MeasurementTypeAdapter(DataGenerator, ABC):
    """
    A high-level Adapter Interface to the Measurement Type Specific Code.

    Should implement a particular kind of measurement, such as Spectroscopy, IV-Curve, ..., which
    then communicates with the device driver using its own interfaces.
    """

    _analyses: list[AnalysisTypeAdapter]

    def __init__(self):
        super().__init__()
        self._analyses = []

    def create_datasets(self, data_file: HDF5, swept_axes: list[Dataset]):
        """
        Create the datasets for this kind of measurement. Takes into account
        swept axes in the measurement tree.
        """
        for descriptor in self.expected_structure:
            all_axes = swept_axes + list(map(lambda ax: ax.get_data_axis(data_file), list(descriptor.axes)))
            data_file.create_dataset(descriptor.name,
                                     tuple(map(lambda axis: len(axis), all_axes)),
                                     descriptor.unit,
                                     axes=all_axes
                                     )

        for name, view in self.default_views:
            data_file.insert_view(name, view)

        for analysis in self._analyses:
            analysis.create_datasets(data_file, self.expected_structure, swept_axes)

    def record(self, data_file: HDF5, sweep_indices: tuple[int, ...]):
        """
        Perform the measurement and record the results.
        """
        try:
            data = self.perform_measurement()
        except Exception as e:
            measurement_log.error(f"Measurement failed for {self}.", exc_info=e)
            raise e
        else:
            self.store(data_file, data, sweep_indices)
            for analysis in self._analyses:
                analysis.record(data_file, sweep_indices, data)

    def with_analysis(self, analysis: AnalysisTypeAdapter) -> 'MeasurementTypeAdapter':
        """
        Add an Analysis to this measurement.
        """
        self._analyses.append(analysis)
        return self

    @property
    @abstractmethod
    def expected_structure(self) -> tuple['MeasurementTypeAdapter.DataDescriptor', ...]:
        """
        Return a list of MeasurementDescriptors for this kind of measurement.

        This is used to initialize the measurement files.
        """
        pass

    @property
    def default_views(self) -> dict[str, HDF5.DataView]:
        """
        A default set of views to be created for this kind of measurement. Can be empty.
        Maps the name to the view, thus a dict.
        """
        return {}

    @abstractmethod
    def perform_measurement(self) -> tuple['MeasurementTypeAdapter.GeneratedData', ...]:
        """
        Perform the measurement and return a list of MeasurementData.

        The length of this list must be identical to the one returned by expected_structure,
        and all MeasurementDescriptors associated with MeasurementData must be present in expected_structure.
        """
        pass

    def __str__(self):
        return f"Measurement({self.__class__.__name__}, ({self.expected_structure}))"


class ScalarMeasurement(MeasurementTypeAdapter):
    """
    Implements a scalar measurement, the simplest kind. Only has a name, unit and a getter.
    """
    _descriptor: MeasurementTypeAdapter.DataDescriptor
    _getter: Callable[[], float]

    def __init__(self, name: str, getter: Callable[[], float], unit: str = 'a.u.'):
        super().__init__()
        self._descriptor = MeasurementTypeAdapter.DataDescriptor(name, axes=tuple(), unit=unit)
        self._getter = getter

    @property
    def expected_structure(self) -> tuple['MeasurementTypeAdapter.DataDescriptor', ...]:
        return (self._descriptor,)

    def perform_measurement(self) -> tuple['MeasurementTypeAdapter.GeneratedData', ...]:
        return (self._descriptor.with_data(self._getter()),)


class Experiment(ParentOfSweep, ParentOfMeasurements):
    """
    The main experiment class and root of all sweeps and measurements.

    Create and instance and use sweep() and measure() to build up the experiment.

    Note that sweep() is to be used with `with`-statements.

    Example:
    >>> experiment = Experiment("my_experiment", Sample()) # Creates the experiment
    >>> # Use sweep() and measure() to create an experiment
    >>> experiment.run()
    """

    _name: str
    _sample: Sample
    _comment: Optional[str]

    def __init__(self, name: str, sample: Sample) -> None:
        """
        Create an experiment with the given name and sample.
        """
        super().__init__()
        super(ParentOfSweep, self).__init__()
        self._name = name
        self._sample = sample
        self._comment = None

    def with_comment(self, comment: str) -> 'Experiment':
        """
        Attach a comment to the experiment.
        """
        self._comment = comment
        return self

    @property
    def dimensionality(self):
        """
        Recursively calculate the maximum dimensionality of the experiment.
        """
        return max(self._largest_measurement_dimension, self._child_dimensionality)

    @property
    def _filename(self):
        """
        Derive the filename based on the largest dimension and the user provided name.
        """
        return f"{self.dimensionality}D_{self._name}"

    def run(self, open_qviewkit: bool = True, open_datasets: list[HDF5.DataReference] | None = None):
        """
        Perform the configured measurements. Sweep the nested axes and record the results.

        By default opens qviewkit. Using [open_datasets], a set of datasets can be opened on start.
        """

        measurement_file = MeasurementFilePath(measurement_name=self._filename)
        measurement_file.mkdirs()
        # Create an additional log file:
        log_handler = waf.open_log_file(str(measurement_file.into_path()))
        # HDF5 file initialization
        data_file = measurement_file.into_h5_file()
        try:
            # Recurse down the tree to create datasets.
            self.create_datasets(data_file, [])
            if self._sweep_child is not None:
                self._sweep_child.create_datasets(data_file, [])

            # Get Instrument settings, write to a file
            settings = waf.get_instrument_settings(str(measurement_file.into_path()))

            # Also store in hdf5
            settings_str = json.dumps(obj=settings, cls=QkitJSONEncoder, indent=4, sort_keys=True)
            data_file.write_text_record('settings', settings_str, 'Instrument States before measurement started.')

            data_file.hdf.attrs['comment'] = self._comment if self._comment is not None else ''

            # Backwards compatibility, mostly obsolete.
            measurement = Measurement()
            measurement.hdf_relpath = str(measurement_file.rel_path)
            measurement.sample = self._sample
            measurement.uuid = measurement_file.uuid
            measurement.analyzed = False
            measurement.web_visible = True
            measurement.instruments = qkit.instruments.get_instrument_names()
            measurement.save()

            # Write to HDF5
            data_file.write_text_record('measurement', measurement.get_JSON(), 'Measurement description')

            # All records are created, enter swmr mode
            data_file.swmr = True

            # Open Qviewkit, if desired
            if open_qviewkit:
                if open_datasets is None:
                    open_datasets: list[str] = []
                else:
                    open_datasets: list[str] = [ref.to_path(data_file) for ref in open_datasets]

                qviewkit.plot(measurement_file.into_path(), datasets=open_datasets)

            # Everything is prepared. Do the actual measurement.
            self.run_measurements(data_file, ())
            self._run_child_sweep(data_file, ())
        finally:
            # Calling into existing plotting code in the background.
            t = threading.Thread(target=qviewkit.save_plots, args=[measurement_file.into_path(), self._comment])
            t.start()
            waf.close_log_file(log_handler)
            data_file.close()

    def __str__(self):
        return "Experiment:\r\n" + (
            textwrap.indent(str(self._sweep_child), '\t') if self._sweep_child is not None else "No Sweep"
        )
