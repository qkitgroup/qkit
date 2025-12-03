from qkit.measure.measurement_base import MeasureBase
from qkit.drivers.ZHInstSHFQC import ZHInstSHFQC
from laboneq.data.experiment_results import AcquiredResults
import numpy as np

class MeasureTD(MeasureBase):

    def __init__(self, shfqc: ZHInstSHFQC, sample=None):
        super().__init__(sample)
        self._shfqc = shfqc

    def _prepare_measurement_devices(self):
        # When prepared by user by compilation, everything is prepared.
        pass

    def _append(self, zi_result: AcquiredResults):
        for (handle, result) in zi_result.items():
            self._datasets[f"{handle}_real"].append(np.real(result.data))
            self._datasets[f"{handle}_imag"].append(np.imag(result.data))
            self._datasets[f"{handle}_amp"].append(np.abs(result.data))
            self._datasets[f"{handle}_phase"].append(np.angle(result.data))

    def _build_datafile_from_result(self, result: AcquiredResults, device_axis_unit: dict[str, str]):
        """
        Declare the datasets for saving.

        We get the AcquiredResults object. It contains multiple handles (different readout categories.)
        Each handle has an associated AcquiredResult containing:
        - a complex valued ND array of the measurement result
        - N associated axis names which were swept
        - N arrays of values the swept value took.
        """
        coordinates = {} # Lookuptable for reuse
        datasets = [] # Can be an array, less conversions.
        for (handle, datum) in result.items(): # Iterate over measure categories
            # Ensure all axes have been created
            for axis_name, axis_values in zip(datum.axis_name, datum.axis):
                assert axis_name is str, f"Unexpeced axis name type: {axis_name}"
                if axis_name not in coordinates:
                    coordinates[axis_name] = self.Coordinate(
                        name=axis_name,
                        unit=device_axis_unit[axis_name],
                        values=axis_values
                    )
            
            # Create dataset with existing axes
            datasets.append(self.Data(f"{handle}_real", coords=[coordinates[axis_name] for axis_name in datum.axis_name]))
            datasets.append(self.Data(f"{handle}_imag", coords=[coordinates[axis_name] for axis_name in datum.axis_name]))
            datasets.append(self.Data(f"{handle}_amp", coords=[coordinates[axis_name] for axis_name in datum.axis_name]))
            datasets.append(self.Data(f"{handle}_phase", coords=[coordinates[axis_name] for axis_name in datum.axis_name]))
        self._prepare_measurement_file(data=datasets)

    def measure_ND_ZI(self, device_axis_unit: dict[str, str]):
        """
        Take a 1D measurement with the ZHInst device. No external parameters are swept.

        device_axis_unit: A string describing the unit of the ZI sweep axis.
        """
        result = self._shfqc.measure_td()
        self._build_datafile_from_result(result.acquired_results, device_axis_unit)
        self._append(result.acquired_results)
        self._end_measurement()