import itertools
from typing import override, Any

from scipy import signal

from qkit.measure.unified_measurements import AnalysisTypeAdapter, MeasurementTypeAdapter, DataView, DataViewSet, DataReference


class SavgolNumericalDerivative(AnalysisTypeAdapter):
    """
    Apply a numerical derivative to the measurement data.

    Performs pair-wise differentiation of the measurement data.

    Assumes that measurement data comes in (I, V, I, V, ...) format or equivalent.
    Assumes that names are in the form of '[IV]_(?:b_)?_[0-9]'
    """

    savgol_kwargs: dict[str, Any]

    def __init__(self, **savgol_kwargs):
        """
        savgol_kwargs: 
            kwargs to pass to scipy.signal.savgol_filter alongside data, refer to scipy docs for more information
        """
        super().__init__()
        self.savgol_kwargs = {"window_length": 15, "polyorder": 3, "deriv": 1} | savgol_kwargs

    @override
    def perform_analysis(self, data: tuple['MeasurementTypeAdapter.GeneratedData', ...]) -> tuple[
        'MeasurementTypeAdapter.GeneratedData', ...]:
        parent_schema = tuple([element.descriptor for element in data])
        output_schema = self.expected_structure(parent_schema)
        out = []
        for ((dxdy, dydx), (x, y)) in zip(itertools.batched(output_schema, 2), itertools.batched(data, 2)):
            out.append(dxdy.with_data(signal.savgol_filter(x.data, **self.savgol_kwargs)/signal.savgol_filter(y.data, **self.savgol_kwargs)))
            out.append(dydx.with_data(signal.savgol_filter(y.data, **self.savgol_kwargs)/signal.savgol_filter(x.data, **self.savgol_kwargs)))
        return tuple(out)


    @override
    def expected_structure(self, parent_schema: tuple['MeasurementTypeAdapter.DataDescriptor', ...]) -> tuple['MeasurementTypeAdapter.DataDescriptor', ...]:
        structure = []
        for (x, y) in itertools.batched(parent_schema, 2):
            assert x.axes == y.axes
            structure += [
                MeasurementTypeAdapter.DataDescriptor(
                    name=f"d{x.name}_d{y.name}",
                    unit=f"{x.unit}/{y.unit}",
                    axes=x.axes, 
                    category="analysis"
                ),
                MeasurementTypeAdapter.DataDescriptor(
                    name=f"d{y.name}_d{x.name}",
                    unit=f"{y.unit}/{x.unit}",
                    axes=x.axes,
                    category="analysis"
                )
            ]
        return tuple(structure)

    @override
    def default_views(self, parent_schema: tuple['MeasurementTypeAdapter.DataDescriptor', ...]) -> dict[str, DataView]:
        schema = self.expected_structure(parent_schema)
        variable_names = (schema[0].name.split('_')[0], schema[1].name.split('_')[0])
        return { # dx/dy
            f'{variable_names[0]}_{variable_names[1]}': DataView(
                view_params={
                    "labels": (schema[0].axes[0].name, f'{variable_names[0]}_{variable_names[1]}'),
                    'plot_style': 1,
                    'markersize': 5
                },
                view_sets=[
                    DataViewSet(
                        x_path=DataReference(entry.axes[0].name,),
                        y_path=DataReference(entry.name, category='analysis')
                    ) for entry in schema[0::2]
                ]
            ), # dy/dx
            f'{variable_names[1]}_{variable_names[0]}': DataView(
                view_params={
                    "labels": (schema[1].axes[0].name, f'{variable_names[1]}_{variable_names[0]}'),
                    'plot_style': 1,
                    'markersize': 5
                },
                view_sets=[
                    DataViewSet(
                        x_path=DataReference(entry.axes[0].name),
                        y_path=DataReference(entry.name, category='analysis')
                    ) for entry in schema[1::2]
                ]
            )
        }