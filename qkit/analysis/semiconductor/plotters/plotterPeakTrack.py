import numpy as np

from qkit.analysis.semiconductor.plotters.pre_formatted_figures import SemiFigure
from qkit.analysis.semiconductor.interfaces import PlotterInterface


class Plotter(PlotterInterface):
    def __init__(self):
        super().__init__()
        self.figure = SemiFigure()
        self.ax = self.figure.ax

    def load_data(self, data_analyzed):
        self.data_analyzed = data_analyzed

    def validate_input(self):
        for file in self.data_analyzed.values():
            keys = file.keys()
            missing_entries = ""
            
            if "demod0&4.r0" not in keys:
                missing_entries += "demod0&4.r0"
            if "demod0&4.r4" not in keys:
                missing_entries += "\ndemod0&4.r4"
            if "demod0&4.x0" not in keys:
                missing_entries += "\ndemod0&4.x0"
            if "demod0&4.x4" not in keys:
                missing_entries += "\ndemod0&4.x4"
            if "demod0&4.y0" not in keys:
                missing_entries += "\ndemod0&4.y0"
            if "demod0&4.y4" not in keys:
                missing_entries += "\ndemod0&4.y4"
            if "demod0&4.timestamp0" not in keys:
                missing_entries += "\ndemod0&4.timestamp0"
            if "demod0&4.timestamp4" not in keys:
                missing_entries += "\ndemod0&4.timestamp4"
            if "peak_positions" not in keys:
                missing_entries += "\npeak_pos"
            if "gates_6_16" not in keys:
                missing_entries += "\ngates_6_16"
            if "number" not in keys:
                missing_entries += "\nnumber"

            if missing_entries:
                raise TypeError(f"{__name__}: Invalid input data. The following nodes are missing: {missing_entries}")

    def plot_measurement(self):
        for file in self.data_analyzed.values():
            (x_len, y_len) = np.shape(file["demod0&4.r0"])
            self.ax.pcolor(file["number"][:x_len], file["gates_6_16"][:y_len], np.transpose(file["demod0&4.r0"]))
            
    
    def plot_peaks(self):
        for file in self.data_analyzed.values():
            self.ax.scatter(file["peak_positions"]["x"], file["peak_positions"]["y"], s = 0.5, c = "r")

    
    def plot(self):
        self.plot_measurement()
        self.plot_peaks()

def main():
    
    arr = [[1,2],[3,4]]
    plotter = Plotter()
    plotter.load_data(arr)
    plotter.plot()

if __name__ == "__main__":
    from analysis_main_nu import main as start_GUI

    #%% start_GUI
    start_GUI()
