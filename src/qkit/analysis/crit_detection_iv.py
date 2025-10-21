import itertools
from typing import override, Any, Literal
from enum import Enum
from scipy import signal
import numpy as np

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
        parent_schema = tuple([element.descriptor for element in data])
        output_schema = self.expected_structure(parent_schema)
        out = []
        flipBiasMeas = (parent_schema[0].name == "i_0") ^ (self._onWhat in ["v", "dvdi"])
        if self._onWhat in ["di_dv", "dv_di"]:
            data = self._numderHelper.perform_analysis(data)
        for ((dxdy, dydx), (x, y)) in zip(itertools.batched(output_schema, 2), itertools.batched(data, 2)):
            out.append(dxdy.with_data(signal.savgol_filter(x.data, **self.savgol_kwargs)/signal.savgol_filter(y.data, **self.savgol_kwargs)))
            out.append(dydx.with_data(signal.savgol_filter(y.data, **self.savgol_kwargs)/signal.savgol_filter(x.data, **self.savgol_kwargs)))
        return tuple(out)

    def _crit_find_thresh(x_vals: np.ndarray, y_vals: np.ndarray, thresh: float = 1e-6) -> tuple[np.ndarray]:
        """
        helper function for main threshold detection on y-vals, x-vals needed for sanity checking
        data should be flipped & mirrored to ideally look like 
        ^ x_vals (.), y_vals (x), crits (o)
        |                         .x
        |                      . x 
        |                   .   x
        |                .      
      0 +------oxxxxxxxxxxxxxxxo-----> #idx
        |     x    .
        |    x  .    
        |   x.
        | .x
        v
        """
        # thresh detect
        upper_idxs = np.argmax(np.logical_and(y_vals > thresh, x_vals > 0), axis=-1)
        upper_idxs = np.where(np.any(np.logical_and(y_vals > thresh, x_vals > 0), axis=-1), upper_idxs, x_vals.shape[-1] - 1) # default to max if no tresh found
        lower_idxs = y_vals.shape[-1] - 1 - np.argmax(np.flip(np.logical_and(y_vals > thresh, x_vals < 0), axis=-1), axis=-1) # flip because argmax returns first occurence
        lower_idxs = np.where(np.any(np.logical_and(y_vals > thresh, x_vals < 0), axis=-1), lower_idxs, 0)
        return upper_idxs, lower_idxs


    @override
    def expected_structure(self, parent_schema: tuple['MeasurementTypeAdapter.DataDescriptor', ...]) -> tuple['MeasurementTypeAdapter.DataDescriptor', ...]:
        structure = []
        for i, bias in enumerate(parent_schema[::2]):
            structure += [
                MeasurementTypeAdapter.DataDescriptor(
                    name=f"ic_upper_{i}" if self._onWhat in ["v", "dv_di"] else f"vc_upper_{i}",
                    unit=f"{bias.unit}",
                    axes=bias.axes[:-1], 
                    category="analysis"
                ),
                MeasurementTypeAdapter.DataDescriptor(
                    name=f"ic_lower_{i}" if self._onWhat in ["v", "dv_di"] else f"vc_lower_{i}",
                    unit=f"{bias.unit}",
                    axes=bias.axes[:-1], 
                    category="analysis"
                ),
            ]
        return tuple(structure)

    @override
    def default_views(self, parent_schema: tuple['MeasurementTypeAdapter.DataDescriptor', ...]) -> dict[str, DataView]:
        return ()
