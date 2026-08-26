from collections import namedtuple
from typing import Callable, Union

from qkit.measure.unified_measurements import AnalysisTypeAdapter, DataGenerator, MeasurementTypeAdapter, DataView
from scipy.optimize import curve_fit

FitParam = namedtuple('FitParam', ['name', 'init_value', 'unit'])

class FitAnalysisAdapter(AnalysisTypeAdapter):

    def __init__(self, fit_function: Callable, dataset_phrase: str,
                 p0: tuple[FitParam, ...],
                 post_hook: Union[Callable, None] = None):
        self.fit_function = fit_function
        self.dataset_phrase = dataset_phrase
        self.p0 = p0
        self.post_hook = post_hook
        self.structure = tuple(
            DataGenerator.DataDescriptor(name=param.name, unit=param.unit, axes=tuple(), category='analysis')
            for param in self.p0
        )

    def expected_structure(self, parent_schema: tuple['MeasurementTypeAdapter.DataDescriptor', ...]) -> tuple[
        'MeasurementTypeAdapter.DataDescriptor', ...]:
        return self.structure

    def perform_analysis(self, data: tuple['MeasurementTypeAdapter.GeneratedData', ...]) -> tuple[
        'MeasurementTypeAdapter.GeneratedData', ...]:
        relevant_data = [datum for datum in data if self.dataset_phrase in datum.descriptor.name][0]
        x = relevant_data.descriptor.axes[0]
        y = relevant_data.data

        popt, pcov = curve_fit(self.fit_function, x, y, p0=(param.init_value for param in self.p0))
        self.post_hook(popt, pcov)
        return tuple(
            desc.with_data(opt_param)
            for desc, opt_param in zip(self.structure, popt)
        )