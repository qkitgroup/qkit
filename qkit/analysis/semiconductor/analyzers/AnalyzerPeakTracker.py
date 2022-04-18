from typing import Any, Dict

import numpy as np
from numpy.typing import NDArray
from qkit.analysis.semiconductor.interfaces import AnalyzerInterface
from scipy import signal
from scipy.optimize import curve_fit


class Analyzer(AnalyzerInterface):
    def __init__(self) -> None:
        self.data = {}

        self.node_to_analyze = "demod0.r0"
        self.node_timestamps = "demod0.timestamp0"
        self.min_peak_height = 0.01  # in V
        self.min_peak_width = 0.001  # in V

    def load_data(self, data: Dict[str, Dict[str, Any]]) -> None:
        self.data = data

    def validate_input(self):
        for file in self.data.values():
            keys = file.keys()
            missing_entries = ""

            if self.node_to_analyze not in keys:
                missing_entries += self.node_to_analyze
            if self.node_timestamps not in keys:
                missing_entries += self.node_timestamps
            if "gates_6_16" not in keys:
                missing_entries += "\ngates_6_16"
            if "number" not in keys:
                missing_entries += "\nnumber"

            if missing_entries:
                raise TypeError(
                    f"{__name__}: Invalid input data. The following nodes are missing: {missing_entries}"
                )

    def analyze(self):
        for file in self.data.values():
            file["peak_positions"] = {}
            v_offset = file["gates_6_16"][0]
            v_step = file["gates_6_16"][1] - v_offset

            t_step = 1

            matrix = file[self.node_to_analyze]
            peak_positions_y = []
            peak_positions_x = []
            peak_positions_index = []

            for index, trace in enumerate(matrix):
                peak_pos_y, _ = signal.find_peaks(
                    trace,
                    height=self.min_peak_height,
                    width=self.min_peak_width / v_step,
                )
                peak_pos_x = np.array([index] * len(peak_pos_y))
                peak_positions_y.extend(peak_pos_y * v_step + v_offset)
                peak_positions_x.extend(peak_pos_x * t_step)
                peak_positions_index.extend(peak_pos_y)

            file["peak_positions"]["x"] = np.array(peak_positions_x)
            file["peak_positions"]["y"] = np.array(peak_positions_y)
            file["peak_positions"]["index"] = np.array(peak_positions_index)

        return self.data


if __name__ == "__main__":
    A = Analyzer()
    data = {"x": 1, "y": 2}
    A.load_data(data)
    A.validate_input()
