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
    pass
# from scipy.signal import find_peaks, peak_widths
# from scipy.optimize import curve_fit
# from random import uniform

# def sech(x, a, b, c):
#     return a / np.cosh((x - c) / b)

# def multi_sech(x, *params):
#     y = np.zeros_like(x)
#     for i in range(0, len(params), 3):
#         a = params[i]
#         b = params[i+1]
#         c = params[i+2]
#         y = y + sech(x, a, b, c)
#     return y

# def create_jitter(amplitude):
#     return uniform(-amplitude, amplitude)

# xdata = np.linspace(-40, 40, 1000) # create x_axis
# x_step = xdata[1] - xdata[0]
# rng = np.random.default_rng()
# y_noise = 0
# y_noise = 0.1 * rng.normal(size=xdata.size) # create some noise

# jitter_ampl = 0
# y = multi_sech(xdata, 1, 1, 30 + create_jitter(jitter_ampl),
#                1, 1, 15 + create_jitter(jitter_ampl),
#                1, 3, -30 + create_jitter(jitter_ampl),
#                1, 1, -15 + create_jitter(jitter_ampl))
# ydata = y + y_noise

# peak_pos, params = find_peaks(ydata, height = 0.5, width = 6)
# results = peak_widths(ydata, peak_pos, rel_height=0.5)
# peak_widths = results[0] * x_step / 2.634
# no_peaks = len(peak_pos)
# print(f"peak_widths: {peak_widths}")
# print(f"peak_pos: {xdata[peak_pos]}")
# lower_bounds = [0, 0, -np.inf] * no_peaks
# upper_bounds = [np.inf, np.inf, np.inf] * no_peaks
# bounds = (lower_bounds, upper_bounds)
# print(bounds)
# guess = []
# for peak, height, width in zip(xdata[peak_pos], params["peak_heights"], peak_widths):
#     guess.extend([height, width, peak])
# print(guess)
# #guess  = [1, 1, 0, 1, 1, 20, 1, 1, -8, 1, 1, -15]
# popt, pcov = curve_fit(multi_sech, xdata, ydata, p0 = guess, bounds = bounds, maxfev = 1000)

# plt.figure()
# plt.plot(np.arange(len(ydata)) * x_step - 40, ydata)
# plt.plot(xdata, multi_sech(xdata, *popt), 'r-')
# for i in range(len(results[1:][0])):
#     y = results[1:][0][i]
#     x_min = results[1:][1][i] * x_step + xdata[0]
#     x_max = results[1:][2][i] * x_step + xdata[0]
#     plt.hlines(y, x_min, x_max, color ="C2")
# print(popt)
