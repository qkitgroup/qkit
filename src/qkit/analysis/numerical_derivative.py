import itertools
from typing import override

from scipy import signal

from qkit.measure.unified_measurements import AnalysisTypeAdapter, MeasurementTypeAdapter, DataView, DataViewSet, DataReference


class SavgolNumericalDerivative(AnalysisTypeAdapter):
    """
    Apply a numerical derivative to the measurement data.

    Performs pair-wise differentiation of the measurement data.

    Assumes that measurement data comes in (I, V, I, V, ...) format or equivalent.
    Assumes that names are in the form of '[IV]_(?:b_)?_[0-9]'
    """

    _window_length: int
    _polyorder: int
    _derivative: int

    def __init__(self, window_length: int = 15, polyorder: int = 3, derivative: int = 1):
        super().__init__()
        self._window_length = window_length
        self._polyorder = polyorder
        self._derivative = derivative

    @override
    def perform_analysis(self, data: tuple['MeasurementTypeAdapter.GeneratedData', ...]) -> tuple[
        'MeasurementTypeAdapter.GeneratedData', ...]:
        parent_schema = tuple([element.descriptor for element in data])
        output_schema = self.expected_structure(parent_schema)
        out = []
        for ((dxdy, dydx), (x, y)) in zip(itertools.batched(output_schema, 2), itertools.batched(data, 2)):
            out.append(dxdy.with_data(
                signal.savgol_filter(x.data, window_length=self._window_length, polyorder=self._polyorder, deriv=self._derivative)\
                / signal.savgol_filter(y.data, window_length=self._window_length, polyorder=self._polyorder, deriv=self._derivative)
            ))
            out.append(dydx.with_data(
                signal.savgol_filter(y.data, window_length=self._window_length, polyorder=self._polyorder, deriv=self._derivative)\
                / signal.savgol_filter(x.data, window_length=self._window_length, polyorder=self._polyorder, deriv=self._derivative)
            ))
        return tuple(out)


    @override
    def expected_structure(self, parent_schema: tuple['MeasurementTypeAdapter.DataDescriptor', ...]) -> tuple['MeasurementTypeAdapter.DataDescriptor', ...]:
        structure = []
        for (x, y) in itertools.batched(parent_schema, 2):
            assert x.axes == y.axes
            structure += [
                MeasurementTypeAdapter.DataDescriptor(
                    name=f"d{x.name}_d{y.name}",
                    unit=f"{x.unit}_{y.unit}",
                    axes=x.axes
                ),
                MeasurementTypeAdapter.DataDescriptor(
                    name=f"d{y.name}_d{x.name}",
                    unit=f"{y.unit}_{x.unit}",
                    axes=x.axes
                )
            ]
        return tuple(structure)

    @override
    def default_views(self, parent_schema: tuple['MeasurementTypeAdapter.DataDescriptor', ...]) -> dict[str, DataView]:
        schema = self.expected_structure(parent_schema)
        variable_names = (schema[0].name.split('_')[0], schema[1].name.split('_')[0])
        return {
            f'd{variable_names[0]}_d{variable_names[1]}': DataView(
                view_sets=[
                    DataViewSet(
                        x_path=DataReference(entry.axes[0].name,),
                        y_path=DataReference(entry.name, category='analysis')
                    ) for entry in schema[0::2]
                ]
            ),
            f'd{variable_names[1]}_d{variable_names[0]}': DataView(
                view_sets=[
                    DataViewSet(
                        x_path=DataReference(entry.axes[0].name),
                        y_path=DataReference(entry.name, category='analysis')
                    ) for entry in schema[1::2]
                ]
            )
        }