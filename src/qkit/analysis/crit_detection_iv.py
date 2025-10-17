import itertools
from typing import override, Any, Literal
from enum import Enum
from scipy import signal

from qkit.measure.unified_measurements import AnalysisTypeAdapter, MeasurementTypeAdapter, DataView, DataViewSet, DataReference
from qkit.analysis.numerical_derivative import SavgolNumericalDerivative

class CritDetectionIV(AnalysisTypeAdapter):
    """
    Analyzes critical points of IV/VI curves

    Analysis results are '(i/v)c_lower_j' and '(i/v)c_upper_j', with dimension lowered by 1 compared to i_j, v_j
    Example: Getting Ic and Irt from a current bias 4 point measurement
    -> set onWhat = "v", critVal = 5e-6 (whatever value properly cuts off random noise)
    
    """

    _onWhat: Literal["i", "v", "di_dv", "dv_di"]
    _critVal: float
    _numderHelper: SavgolNumericalDerivative | None

    def __init__(self, onWhat: Literal["i", "v", "di_dv", "dv_di"], critVal: float, numderHelper: SavgolNumericalDerivative | None = None):
        super().__init__()
        self._onWhat = onWhat
        self._critVal = critVal
        self._numderHelper = numderHelper
        if onWhat in ["di_dv", "dv_di"]:
            assert isinstance(numderHelper, SavgolNumericalDerivative), "When using crit detection on derivative of data, SavgolNumericalDerivative needs to be passed aswell"

    @override
    def perform_analysis(self, data: tuple['MeasurementTypeAdapter.GeneratedData', ...]) -> tuple['MeasurementTypeAdapter.GeneratedData', ...]:
        data[0].descriptor.axes[:-1]
        data[0].descriptor.name
        return ()

    @override
    def expected_structure(self, parent_schema: tuple['MeasurementTypeAdapter.DataDescriptor', ...]) -> tuple['MeasurementTypeAdapter.DataDescriptor', ...]:
        return ()

    @override
    def default_views(self, parent_schema: tuple['MeasurementTypeAdapter.DataDescriptor', ...]) -> dict[str, DataView]:
        return ()
    
    """
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
    """

