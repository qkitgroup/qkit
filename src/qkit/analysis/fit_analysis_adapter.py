from collections import namedtuple
from typing import Callable, Union

import numpy as np

from qkit.measure.unified_measurements import AnalysisTypeAdapter, DataGenerator, MeasurementTypeAdapter, DataView, \
    DataViewSet, DataReference
from scipy.optimize import curve_fit

FitParam = namedtuple('FitParam', ['name', 'init_value', 'unit'])

class FitAnalysisAdapter(AnalysisTypeAdapter):

    def __init__(self, fit_function: Callable, dataset_phrase: str,
                 p0: Union[tuple[FitParam, ...], Callable[[np.ndarray, np.ndarray], tuple[FitParam, ...]]],
                 post_hook: Union[Callable, None] = None, fit_name: str = 'fit_curve'):
        self.fit_function = fit_function
        self.dataset_phrase = dataset_phrase
        self.p0 = p0
        self.post_hook = post_hook
        self.fit_name = fit_name
        example_p0 = self.p0(np.linspace(0, 100, 100), np.ones(100)) if callable(self.p0) else self.p0
        self.structure = tuple(
            DataGenerator.DataDescriptor(name=param.name, unit=param.unit, axes=tuple(), category='analysis')
            for param in example_p0
        )

    def expected_structure(self, parent_schema: tuple['MeasurementTypeAdapter.DataDescriptor', ...]) -> tuple[
        'MeasurementTypeAdapter.DataDescriptor', ...]:
        relevant_descriptor = [desc for desc in parent_schema if self.dataset_phrase in desc.name][0]
        synth_desc = DataGenerator.DataDescriptor(name=self.fit_name, unit=relevant_descriptor.unit, axes=relevant_descriptor.axes, category='analysis')
        return self.structure + (synth_desc,)

    def default_views(self, parent_schema: tuple['MeasurementTypeAdapter.DataDescriptor', ...]) -> dict[str, "DataView"]:
        relevant_descriptor = [desc for desc in parent_schema if self.dataset_phrase in desc.name][0]
        x_axis = relevant_descriptor.axes[0]
        return {
            'fit': DataView(
                view_params= {
                    "plot_style": 1,
                    "markersize": 5
                },
                view_sets=[
                    DataViewSet(# Real Data
                        x_path=DataReference(x_axis.name),
                        y_path=DataReference(relevant_descriptor.name),
                    ),
                    DataViewSet(# Fit Curve
                        x_path=DataReference(x_axis.name),
                        y_path=DataReference(self.fit_name, 'analysis'),
                    )
                ]
            )
        }

    def perform_analysis(self, data: tuple['MeasurementTypeAdapter.GeneratedData', ...]) -> tuple[
        'MeasurementTypeAdapter.GeneratedData', ...]:
        relevant_data = [datum for datum in data if self.dataset_phrase in datum.descriptor.name][0]
        x = relevant_data.descriptor.axes[0].range
        y = relevant_data.data

        start_params = self.p0(x, y) if callable(self.p0) else self.p0
        popt, pcov = curve_fit(self.fit_function, x, y, p0=tuple(param.init_value for param in start_params))
        self.post_hook(popt, pcov)
        synthetic_data = self.fit_function(x, *popt)
        return tuple(
            desc.with_data(opt_param)
            for (desc, opt_param) in zip(self.structure[:-1], popt)
        ) + (self.structure[-1].with_data(synthetic_data),)