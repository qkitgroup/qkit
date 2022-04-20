import os
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT

class Mpl_canvas(FigureCanvasQTAgg):
    def __init__(self, figure) -> None:
        self.axes = figure.gca()
        super().__init__(figure)

    def update_canvas(self):
        self.axes.cla()
        self.draw()

class Plot_widget(QWidget):
    def __init__(self, figure):
        super().__init__()
        
        self.canvas = Mpl_canvas(figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        self.vbox = QVBoxLayout(self)
        self.vbox.addWidget(self.toolbar)
        self.vbox.addWidget(self.canvas)

        self.canvas.draw()

class Plot_window(QWidget):
    def __init__(self, main_dir, figure):
        super().__init__()
        uic.loadUi(os.path.join(main_dir, "main", "ui", "plot_window.ui"), self)

        self.plot_widget = Plot_widget(figure)

        self.layout().addWidget(self.plot_widget)