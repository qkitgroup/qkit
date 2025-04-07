from typing import Any, Dict

import numpy as np
from qkit.analysis.semiconductor.main.interfaces import PlotterInterface
from qkit.analysis.semiconductor.main.pre_formatted_figures import SemiFigure


class Plotter(PlotterInterface):
    def __init__(self):
        super().__init__()
        self.figure = SemiFigure()
        self.ax = self.figure.ax
        self.plot_index = 0
        self.data_analyzed = {}
        self.node_to_plot = "demod0.r0"

    def load_data(self, data: Dict[str, Any]):
        self.data_analyzed = data

    def validate_input(self):
        for file in self.data_analyzed.values():
            keys = file.keys()
            missing_entries = ""

            if self.node_to_plot not in keys:
                missing_entries += self.node_to_plot
            if "peak_positions" not in keys:
                missing_entries += "\npeak_pos"
            if "gates_6_16" not in keys:
                missing_entries += "\ngates_6_16"
            if "number" not in keys:
                missing_entries += "\nnumber"

            if missing_entries:
                raise TypeError(
                    f"{__name__}: Invalid input data. The following nodes are missing: {missing_entries}"
                )

    def plot_measurement(self):
        for file in self.data_analyzed.values():
            (x_len, y_len) = np.shape(file[self.node_to_plot])
            self.ax.pcolor(
                file["number"][:x_len],
                file["gates_6_16"][:y_len],
                np.transpose(file[self.node_to_plot]),
            )

    def plot_peaks(self):
        for file in self.data_analyzed.values():
            self.ax.scatter(
                file["peak_positions"]["x"], file["peak_positions"]["y"], s=0.5, c="r"
            )

    def plot_peak_1D(self):
        for file in self.data_analyzed.values():
            self.ax.plot(file["gates_6_16"], file[self.node_to_plot][self.plot_index])
            self.ax.scatter(
                file["peak_positions"]["y"][self.plot_index],
                file[self.node_to_plot][self.plot_index][
                    file["peak_positions"]["index"][self.plot_index]
                ],
            )

    def plot(self):
        self.plot_measurement()
        self.plot_peaks()
        # self.plot_peak_1D()


def main():    
    plotter = Plotter()
    plotter.plot()


if __name__ == "__main__":
    pass
