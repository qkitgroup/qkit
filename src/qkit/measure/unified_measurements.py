import logging
import threading
import time
from dataclasses import dataclass, field
from os import PathLike

import numpy as np
from abc import ABC, abstractmethod
from typing import Optional, Callable, Protocol, Literal, Iterable, Any, Union

try:
    from typing import override
except ImportError:
    # This feature got added in 3.12. In older versions, do nothing
    def override(func):
        return func

import textwrap
import json

from tqdm.auto import tqdm

import qkit

from qkit.storage import store as hdf  # Entrypoint for existing hdf infrastructure in qkit
from qkit.storage.hdf_dataset import hdf_dataset  # Existing Dataset representation in qkit

from qkit.measure.json_handler import QkitJSONEncoder
from qkit.measure.samples_class import Sample
from qkit.measure.measurement_class import Measurement
import qkit.measure.write_additional_files as waf

import qkit.gui.plot.plot as qviewkit  # Who names these things?

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

measurement_log = logging.getLogger(__name__)

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
class EnterableWrapper:
    """
    Return this to require the user to use a with-statement.
    """
    value: Any

    def __enter__(self):
        return self.value

    def __exit__(self, *args):
        pass

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
              axis_filter: Optional[Callable[[np.ndarray], np.ndarray]] = None) -> EnterableWrapper:
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
        assert isinstance(measurement_type, MeasurementTypeAdapter), "Measurement type must be an instance of MeasurementTypeAdapter!"
        self._measurements.append(measurement_type)

    @property
    def _largest_measurement_dimension(self):
        """
        Get the largest dimensionality of all measurements.
        """
        if len(self._measurements) == 0:
            return 0
        return max(map(lambda m: len(m.expected_structure), self._measurements))

    def create_datasets(self, data_file: hdf.Data, swept_axes: list[hdf_dataset]):
        """
        Based on the measurements and parent sweeps, create the datasets.
        """
        for measurement in self._measurements:
            measurement_log.debug(f"Creating dataset for {measurement.__str__()}")
            measurement.create_datasets(data_file, swept_axes)

    def run_measurements(self, data_file: hdf.Data, index_list: tuple[int, ...]):
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
        assert callable(setter)
        assert isinstance(axis, Axis)
        assert axis_filter is None or callable(axis_filter)
        self._setter = setter
        self._axis = axis
        self._filter = axis_filter

    def filtered(self, axis_filter: FilterCallback) -> 'Sweep':
        self._filter = axis_filter
        return self

    def _generate_enumeration(self, data_file: hdf.Data) -> tuple[Iterable[tuple[int, float]], Optional[int]]:
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

    def _run_sweep(self, data_file: hdf.Data, index_list: tuple[int, ...]):
        """
        Internal function to run the sweep. You should not call this outside measurement_base.py!

        Perform the sweep, checks for filters, and continue down the chain of sweeps.
        """
        sweep, size = self._generate_enumeration(data_file)
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
    def create_datasets(self, data_file: hdf.Data, swept_axes: list[hdf_dataset]):
        measurement_log.debug(f"Dataset creation passing sweep of {self._axis.name}")
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

class ContinuousTimeSeriesSweep(Sweep):

    _stop_after: Optional[float]

    def __init__(self, stop_after = None):
        """
        Create a continuous time series sweep. There only may be one, since only one time axis makes sense.
        """
        super().__init__(lambda v: None, Axis(name="timestamp", unit="s", range=None))
        self._stop_after = stop_after

    @override
    def _generate_enumeration(self, data_file: hdf.Data) -> tuple[Iterable[tuple[int, float]], Optional[int]]:
        def sweep_generator():
            counter = 0
            while True:
                new_time = time.time()
                if new_time > self._stop_after:
                    return
                ds: hdf_dataset = self._axis.get_data_axis(data_file)
                ds.append(new_time)
                yield counter, new_time
                counter += 1
        return sweep_generator(), None




@dataclass(frozen=True)
class Axis:
    """
    An object describing an axis of a measurement. Has a name, unit, and values it can have.
    """
    name: str
    range: Optional[np.ndarray]
    unit: str = 'a.u.'

    def __post_init__(self):
        assert isinstance(self.name, str), "Axis name must be a string!"
        assert self.range is None or isinstance(self.range, np.ndarray), "Axis range must be a numpy array!"
        assert isinstance(self.unit, str), "Axis unit must be a string!"
        # In the future, maybe consider enforcing the range to be strictly monotonic.

    def get_data_axis(self, data_file: hdf.Data) -> hdf_dataset:
        """
        Returns the filled axis data set. Creates it if it doesn't exist yet.
        """
        try:
            return data_file.get_dataset(self.ds_url)
        except KeyError: # Does not exist yet.
            ds = data_file.add_coordinate(name=self.name, unit=self.unit)
            if self.range is not None:  # We have a known range
                ds.add(self.range)
            return ds

    def __str__(self):
        if self.range is not None:
            low = np.min(self.range)
            high = np.max(self.range)
            return f"{self.name}=({low} {self.unit} to {high} {self.unit} in {len(self.range)} steps)"
        else:
            return f"{self.name}=open ended"

    @property
    def ds_url(self):
        return f"/entry/data0/{self.name}"


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

    def store(self, data_file: hdf.Data, data: tuple['MeasurementTypeAdapter.GeneratedData', ...], sweep_indices: tuple[int, ...]):
        """
        Store the generated [data] in the [data_file], while selecting based on the current [sweep_indices].

        This handles the nuances of qkit store api.
        """
        measurement_log.debug(f"Storing data for {type(self).__name__}")
        assert isinstance(data, tuple), "Measurement must return a tuple of MeasurementData!"
        for datum in data:
            assert isinstance(datum, self.GeneratedData), "Measurement must return a tuple of MeasurementData!"
            # The data is validated on wrapper creation, see GeneratedData.__post_init__
            datum.write_data(data_file, sweep_indices)
        data_file.flush()

    @dataclass(frozen=True)
    class DataDescriptor:
        """
        A dataclass containing a n-Dimensional measurement result with axis data.
        """
        name: str
        axes: tuple[Axis, ...]
        unit: str = 'a.u.'

        def __post_init__(self):
            assert isinstance(self.name, str), "Name must be a string!"
            assert isinstance(self.axes, tuple), "Axes must be a tuple!"
            for axis in self.axes:
                assert isinstance(axis, Axis), "Axes must be a tuple of Axis objects!"
            assert isinstance(self.unit, str), "Unit must be a string!"

        def with_data(self, data: Union[np.ndarray, float]) -> 'MeasurementTypeAdapter.GeneratedData':
            """
            Create a MeasurementData object from this MeasurementDescriptor and the provided data.
            """
            return MeasurementTypeAdapter.GeneratedData(self, data=np.asarray(data))

        def create_dataset(self, file: hdf.Data, axes: list[hdf_dataset]) -> hdf_dataset:
            """
            Use qkit facility to write to file.
            Axes contains a list of a swept axis.

            This is the central method for wrapping the discrepancies in the qkit API.
            """
            all_axes: list[hdf_dataset] = axes + list(map(lambda ax: ax.get_data_axis(file), list(self.axes)))
            measurement_log.debug(f"Creating dataset {self.name} with axes {all_axes}")
            # The API has different methods, depending on dimensionality, which it then unifies again to a generic case.
            # For political reasons, we have to live with this.
            if len(all_axes) == 0:
                return file.add_coordinate(name=self.name, unit=self.unit)
            elif len(all_axes) == 1:
                return file.add_value_vector(name=self.name,x = all_axes[0], unit=self.unit)
            elif len(all_axes) == 2:
                return file.add_value_matrix(name=self.name, x = all_axes[0], y = all_axes[1], unit=self.unit)
            elif len(all_axes) == 3:
                return file.add_value_box(name=self.name, x = all_axes[0], y = all_axes[1], z = all_axes[2], unit=self.unit)
            else:
                raise NotImplementedError("Qkit Store does not support more than 3 dimensions!")

        @property
        def ds_url(self):
            return f"/entry/data0/{self.name}"

    @dataclass(frozen=True)
    class GeneratedData:
        """
        Actual Measurement Data, associating a Descriptor with a nd-array.

        Created by calling MeasurementDescriptor.with_data(data).
        """
        descriptor: 'MeasurementTypeAdapter.DataDescriptor'
        data: np.ndarray

        def __post_init__(self):
            assert isinstance(self.descriptor, MeasurementTypeAdapter.DataDescriptor), "MeasurementData must be created from a MeasurementDescriptor!"
            assert isinstance(self.data, np.ndarray), "MeasurementData must be an ndarray!"
            assert len(self.descriptor.axes) == len(self.data.shape), f"Data shape (d={len(self.data.shape)}) incongruent with descriptor (d={len(self.descriptor.axes)})"
            for (i, axis) in enumerate(self.descriptor.axes):
                assert self.data.shape[i] == len(axis.range), f"Axis ({axis.name}) length and data length mismatch"

        def write_data(self, file: hdf.Data, sweep_indices: tuple[int, ...]):
            """
            Use qkit store api to actually store the data.
            """
            ds: hdf_dataset = file.get_dataset(self.descriptor.ds_url)
            assert ds is not None, f"Dataset {self.descriptor.name} not found!"

            # Integrates into existing storage infrastructure. Should be better, but may not touch append.
            if len(self.data.shape) == 0: # We save a scalar
                if len(sweep_indices) == 0: # Single data point.
                    ds.append(self.data, reset=True) # We won't get here again.
                    return
                elif len(sweep_indices) == 1: # Into a vector, e.g x
                    # This is not supported by qkit hdf_file natively.
                    # QKit expects a 1D array with a single point. We need to hack it a bit.
                    ds.append(np.asarray([self.data]))
                    return
                elif len(sweep_indices) == 2: # Into a matrix, e.g. x,y
                    # QKit expects a 1D array with a single point. We need to hack it a bit.
                    # Explicitly tell it, that it is pointwise.
                    ds.append(np.asarray([self.data]), pointwise=True)
                    # If we reached the end of the inner iteration, go to next
                    if sweep_indices[-1] + 1 == ds.ds.shape[1]:
                        ds.next_matrix()
                    return
                elif len(sweep_indices) == 3: # Into a box
                    raise NotImplementedError("QKit does not support 3D data consisting out of single points!")
            elif len(self.data.shape) == 1: # We save a vector
                ds.append(self.data)
                if len(sweep_indices) == 2: # We fill a box with vectors
                    # In case we just hit end of the last iteration, we need to wrap over.
                    if sweep_indices[-1] + 1 == ds.ds.shape[1]:
                        ds.next_matrix()
                elif len(sweep_indices) >= 3:
                    raise NotImplementedError("QKit does not higher than 3 dimensions!")
                return
            else:
                raise NotImplementedError("QKit does not support higher than 1 dimension of recorded data at once!")
            raise NotImplementedError(f"Uncovered State sweep:{len(sweep_indices)}, data:{len(self.data.shape)}!")

class AnalysisTypeAdapter(DataGenerator, ABC):
    """
    A high-level Adapter Interface to the Analysis-Specific Code.

    Should implement a particular kind of analysis, such as Resonator fitting, numerical derivatives, ...
    """
    def record(self, data_file: hdf.Data, sweep_indices: tuple[int, ...], measured_data: tuple['MeasurementTypeAdapter.GeneratedData', ...]):
        """
        Perform the analysis and record the results.
        """
        try:
            # Validity of data is asserted in self.store in the else branch.
            data = self.perform_analysis(measured_data)
        except Exception as e:
            measurement_log.error(f"Analysis failed for {self}: {e}", exc_info=e)
            raise e
        else:
            self.store(data_file, data, sweep_indices)

    def create_datasets(self, data_file: hdf.Data, parent_schema: tuple['MeasurementTypeAdapter.DataDescriptor', ...], swept_axes: list[hdf_dataset]):
        """
        Create the datasets as described in the schema provided by the child class with [expected_structure].
        """
        descriptors = self.expected_structure(parent_schema)
        assert isinstance(descriptors, tuple), "Expected structure must be a tuple of DataDescriptors!"
        for descriptor in descriptors:
            assert isinstance(descriptor, self.DataDescriptor), "Each descriptor must be of type DataDescriptors!"
            measurement_log.debug(f"Creating dataset for Analysis from descriptor for {descriptor.name} with axes {swept_axes}")
            descriptor.create_dataset(data_file, axes=swept_axes)

        views = self.default_views(parent_schema)
        assert isinstance(views, dict), "Default views must be a dict of str to DataViews!"
        for name, view in views.items():
            assert isinstance(name, str), "Name of view must be a string!"
            assert isinstance(view, DataView), "Each view must be of type DataView!"
            measurement_log.debug(f"Creating View {name} for Analysis.")
            view.write(data_file, name)

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
    def default_views(self, parent_schema: tuple['MeasurementTypeAdapter.DataDescriptor', ...]) -> dict[str, "DataView"]:
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

    def create_datasets(self, data_file: hdf.Data, swept_axes: list[hdf_dataset]):
        """
        Create the datasets for this kind of measurement. Takes into account
        swept axes in the measurement tree.
        """
        measurement_log.debug(f"Creating datasets for {type(self).__name__} with swept axes {swept_axes}.")
        exp_structure = self.expected_structure
        assert isinstance(exp_structure, tuple), "Expected structure must be a tuple of DataDescriptors!"
        for descriptor in exp_structure:
            assert isinstance(descriptor, self.DataDescriptor), "Each descriptor must be of type DataDescriptors!"
            measurement_log.debug(f"Creating dataset from descriptor for {descriptor.name} with axes {swept_axes}")
            descriptor.create_dataset(data_file, axes=swept_axes)

        views = self.default_views
        assert isinstance(views, dict), "Default views must be a dict of str to DataViews!"
        for name, view in views:
            assert isinstance(name, str), "Name of view must be a string!"
            assert isinstance(view, DataView), "Each view must be of type DataView!"
            measurement_log.debug(f"Creating view {name}.")
            view.write(data_file, name)

        for analysis in self._analyses:
            measurement_log.debug(f"Creating analysis datasets for {analysis}.")
            analysis.create_datasets(data_file, self.expected_structure, swept_axes)

    def record(self, data_file: hdf.Data, sweep_indices: tuple[int, ...]):
        """
        Perform the measurement and record the results.
        """
        try:
            data = self.perform_measurement()
        except Exception as e:
            measurement_log.error(f"Measurement failed for {type(self).__name__}.", exc_info=e)
            raise e
        else:
            self.store(data_file, data, sweep_indices)
            for analysis in self._analyses:
                analysis.record(data_file, sweep_indices, data)

    def with_analysis(self, analysis: AnalysisTypeAdapter) -> 'MeasurementTypeAdapter':
        """
        Add an Analysis to this measurement.
        """
        assert isinstance(analysis, AnalysisTypeAdapter), "Analysis must be of type AnalysisTypeAdapter!"
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
    def default_views(self) -> dict[str, 'DataView']:
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

    def timeseries(self, stop_after = None) -> EnterableWrapper:
        """
        Creates an endless timeseries. Only supported as the root of sweeps.
        """
        self._sweep_child = ContinuousTimeSeriesSweep(stop_after=stop_after)
        return EnterableWrapper(self._sweep_child)

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

    def run(self, open_qviewkit: bool = True, open_datasets: Optional[list["DataReference"]] = None) -> PathLike:
        """
        Perform the configured measurements. Sweep the nested axes and record the results.

        By default opens qviewkit. Using [open_datasets], a set of datasets can be opened on start.
        """
        measurement_log.info(f"Starting measurement {self._filename} with {self._sample.name}")
        # HDF5 file initialization
        measurement_log.debug(f"Creating HDF5 file {self._filename}")
        data_file = hdf.Data(name=self._filename, mode='a')
        # Create an additional log file:
        measurement_log.debug(f"Creating log file {self._filename}.log")
        log_handler = waf.open_log_file(data_file.get_filepath())
        try:
            # Recurse down the tree to create datasets.
            measurement_log.debug(f"Creating measurement datasets for {self._name}.")
            self.create_datasets(data_file, [])
            if self._sweep_child is not None:
                self._sweep_child.create_datasets(data_file, [])

            # Get Instrument settings, write to a file
            measurement_log.debug("Writing instrument settings to file...")
            settings = waf.get_instrument_settings(data_file.get_filepath())

            # Also store in hdf5
            settings_str = json.dumps(obj=settings, cls=QkitJSONEncoder, indent=4, sort_keys=True)
            settings_record = data_file.add_textlist(name='settings', comment='Instrument States before measurement started.')
            settings_record.append(settings_str)

            data_file.hf.hf.attrs['comment'] = self._comment if self._comment is not None else ''

            # Backwards compatibility, mostly obsolete.
            measurement_log.debug("Writing Measurement metadata")
            measurement = Measurement()
            measurement.hdf_relpath = str(data_file._relpath)  # Access to DateTimeGenerator internals.
            measurement.sample = self._sample
            measurement.uuid = data_file._uuid
            measurement.analyzed = False
            measurement.web_visible = True
            measurement.instruments = qkit.instruments.get_instrument_names()
            measurement.save()

            # Write to HDF5
            measurement_record = data_file.add_textlist(name='measurement', comment='Measurement description')
            measurement_record.append(measurement.get_JSON())

            # All records are created, enter swmr mode
            measurement_log.debug("Entering SWMR mode")
            data_file.swmr = True

            # Open Qviewkit, if desired
            if open_qviewkit:
                measurement_log.info("Opening Qviewkit")
                if open_datasets is None:
                    open_datasets: list[str] = []
                else:
                    open_datasets: list[str] = [ref.to_path(data_file) for ref in open_datasets]

                qviewkit.plot(data_file.get_filepath(), datasets=open_datasets)

            # Everything is prepared. Do the actual measurement.
            measurement_log.info("Starting measurement")
            self.run_measurements(data_file, ())
            self._run_child_sweep(data_file, ())
        finally:
            # Calling into existing plotting code in the background.
            measurement_log.info("Creating plots...")
            t = threading.Thread(target=qviewkit.save_plots, args=[data_file.get_filepath(), self._comment])
            t.start()
            waf.close_log_file(log_handler)
            data_file.close()
            measurement_log.info("Measurement finalized")
            return data_file.get_filepath()

    def __str__(self):
        return "Experiment:\r\n" + (
            textwrap.indent(str(self._sweep_child), '\t') if self._sweep_child is not None else "No Sweep"
        )

@dataclass(frozen=True)
class DataView:
    """
    Describes the data required for a view, and allows for writing this in the format required by QViewKit.

    The view type defines the type of plot, e.g. line, color, etc. The view parameters allow for default plotting
    options, such as marker size.

    The view sets contain references to data in the hdf5 file to be plotted.
    """
    view_params: dict[str, Any] = field(default_factory=dict)
    view_sets: list['DataViewSet'] = field(default_factory=list)

    def __post_init__(self):
        assert isinstance(self.view_params, dict), "View parameters must be a dict."
        assert isinstance(self.view_sets, list), "View sets must be a list."
        for view_set in self.view_sets:
            assert isinstance(view_set, DataViewSet), "View sets must be a list of DataViewSet."

    def write(self, file: hdf.Data, name: str):
        """
        Write the view metadata to the dataset, followed by the view sets.
        """
        dv = file.add_view(name, view_params=self.view_params, x=self.view_sets[0].x_path, y=self.view_sets[0].y_path)
        for i, view in enumerate(self.view_sets[1:]):
            dv.add(view.x_path, view.y_path, view.error, view.filter)

@dataclass(frozen=True)
class DataReference:
    """
    A reference to a dataset in the hdf5 file. Consists out of its name and the category it belongs to.
    """
    name: str
    category: Literal['data', 'analysis'] = 'data'

    def __post_init__(self):
        assert self.category in ['data', 'analysis'], "Category must be either 'data' or 'analysis'."
        assert isinstance(self.name, str), "Name must be a string."

    def get_dataset(self, file: hdf.Data) -> hdf_dataset:
        """
        Get a handle to the dataset.
        """
        return file.get_dataset(self.ds_url)

    def to_path(self, file: hdf.Data) -> str:
        """
        Get the path of the dataset in the hdf5 file, if it exists.
        """
        ds = self.get_dataset(file)
        if ds is None:
            raise ValueError(f"Dataset '{self.name}' not found.")
        return ds.name

    @property
    def ds_url(self):
        return f"/entry/{self.category}0/{self.name}"

@dataclass(frozen=True)
class DataViewSet:
    """
    A view set for a view, consisting of the x and y datasets, and optional error dataset and filter methods.
    """
    x_path: 'DataReference'
    y_path: 'DataReference'
    filter: Optional[str] = None
    error: Optional[str] = None

    def __post_init__(self):
        assert isinstance(self.x_path, DataReference), "X-Axis must be a DataReference."
        assert isinstance(self.y_path, DataReference), "Y-Axis must be a DataReference."
        assert self.filter is None or isinstance(self.filter, str), "Filter must be a string or None."
        assert self.error is None or isinstance(self.error, str), "Error must be a string or None."