import matplotlib.pyplot as plt

from itertools import cycle
from qkit.analysis.semiconductor.interfaces import PlotterInterface

class Plotter(PlotterInterface):
    def __init__(self) -> None:
        self.cycler = cycle("rgb")
        self.figure = plt.Figure()
        self.figure.subplots()
        self.ax = self.figure.gca()
        self.mode = 0

    def load_data(self, data):
        self.data_analyzed = data
        print(f"Data is in plotter: {self.data_analyzed['x']}")
        
    def validate_input(self):
        if "x" not in self.data_analyzed.keys():
            raise KeyError
        if "y" not in self.data_analyzed.keys():
            raise KeyError
    
    def plot(self):
        x = self.data_analyzed["x"]
        if self.mode:
            y = self.data_analyzed["x"] **4 
        else:
            y = self.data_analyzed["y"]
        self.ax.plot(x, y, next(self.cycler))