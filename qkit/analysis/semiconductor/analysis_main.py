from importlib.machinery import ModuleSpec
import sys
import os
import importlib.util

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QMainWindow, QLineEdit, QApplication, QVBoxLayout, QGridLayout, QLabel, QPushButton, QFileDialog
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT

test_mode = True
if test_mode:
    import numpy as np
    import matplotlib.pyplot as plt
    from itertools import cycle

class Settings_tab(QWidget):
    def __init__(self, obj):
        super().__init__()
        self.obj = obj
        self.grid = QGridLayout(self)

        for i, (name, value) in enumerate(obj.__dict__.items()):

            label = QLabel(f"{name}:")
            entry = QLineEdit()
            entry.setText(str(value))
            entry.textEdited.connect(self.create_setter(entry, name, value))

            self.grid.addWidget(label, i, 1)
            self.grid.addWidget(entry, i, 2)

    def create_setter(self, entry, name, value):
        def setter():
            newval = entry.text()
            setattr(self.obj, name, type(value)(newval))
        return setter

class Settings_window(QWidget):
    def __init__(self, *objects):
        super().__init__()
        uic.loadUi(os.path.join("main", "ui", "settings_window.ui"), self)

        for obj in objects:
            new_tab = Settings_tab(obj)
            self.tabWidget.addTab(new_tab, type(obj).__name__)

class Mpl_canvas(FigureCanvasQTAgg):
    def __init__(self, plotter) -> None:
        self.plotter = plotter
        figure = self.plotter.fig
        self.axes = figure.gca()
        super().__init__(figure)

    def update_plot(self):
        self.axes.cla()
        self.plotter.validate_input()
        self.plotter.plot()
        self.draw()

class Plot_widget(QWidget):
    def __init__(self, plotter):
        super().__init__()
        
        self.canvas = Mpl_canvas(plotter)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        self.vbox = QVBoxLayout(self)
        self.vbox.addWidget(self.toolbar)
        self.vbox.addWidget(self.canvas)

        self.canvas.draw()

class Plot_window(QWidget):
    def __init__(self, plotter):
        super().__init__()
        uic.loadUi(os.path.join("main", "ui", "plot_window.ui"), self)

        self.plot_widget = Plot_widget(plotter)

        self.layout().addWidget(self.plot_widget)
        self.plot_widget.canvas.update_plot()

class FileDialog_window(QFileDialog):
    def __init__(self):
        super().__init__()
        print(self.getOpenFileName())

class Mainframe(QMainWindow):
    def __init__(self, *objects):
        super().__init__()
        uic.loadUi(os.path.join("main", "ui", "main_window.ui"), self)
        print(self.__dict__)
        self.objects = objects
        self.plotter = objects[-1]

        self.plot_widget = Plot_widget(self.plotter)

        self.button_load.clicked.connect(self.load_data)
        self.button_add_files.clicked.connect(self.add_files)
        self.button_reset_files.clicked.connect(self.reset_files)

        self.button_settings.clicked.connect(self.open_settings_window)
        
        self.button_analyze.clicked.connect(self.analyze_data)
        self.button_plot.clicked.connect(self.open_plot_window)
        
        self.action_Save_Settings.triggered.connect(self.save_settings)
        self.action_Load_Settings.triggered.connect(self.load_settings)
        self.action_Choose_Loader.triggered.connect(self.choose_loader)
        self.action_Choose_Analyzer.triggered.connect(self.choose_analyzer)
        self.action_Choose_Plotter.triggered.connect(self.choose_plotter)

        self.loader = None
        self.analyzer = None
        self.plotter = None

        self.files = []
        self.data_raw = None
        self.data_analyzed = None
    
    @staticmethod
    def load_module_from_filepath(fname):
        module_name = os.path.splitext(os.path.basename(fname))[0]
        module_spec = importlib.util.spec_from_file_location(module_name, fname)
        module = importlib.util.module_from_spec(module_spec) #type: ignore
        module_spec.loader.exec_module(module) #pyright: reportOptionalMemberAccess=false
        return module

    def save_settings(self):
        raise NotImplementedError("Still gotta finish this bad boy. Your princess is in another castle.")
    
    def load_settings(self):
        raise NotImplementedError("Still gotta finish this bad boy. Your princess is in another castle.")

    def choose_loader(self):
        file = "loader"
        fname, _ = QFileDialog.getOpenFileName(self, f"Choose {file}", os.path.join(f"{file}s"), "Python files(*py)")
        if fname:
            module = self.load_module_from_filepath(fname)
            self.loader = module.Loader()

    def choose_analyzer(self):
        file = "analyzer"
        fname, _ = QFileDialog.getOpenFileName(self, f"Choose {file}", os.path.join(f"{file}s"), "Python files(*py)")
        if fname:
            module = self.load_module_from_filepath(fname)
            self.analyzer = module.Analyzer()
    
    def choose_plotter(self):
        file = "plotter"
        fname, _ = QFileDialog.getOpenFileName(self, f"Choose {file}", os.path.join(f"{file}s"), "Python files(*py)")
        if fname:
            module = self.load_module_from_filepath(fname)
            self.plotter = module.Plotter()
    
    def open_settings_window(self):
        self.settings_window = Settings_window(*self.objects)
        self.settings_window.show()

    def add_files(self):
        fnames, _ = QFileDialog.getOpenFileNames(self, "Choose files to load")
        for name in fnames:
            self.text_browser_file_display.append(os.path.basename(name))
        self.files.extend(fnames)

    def reset_files(self):
        self.files = []
        self.text_browser_file_display.clear()

    def load_data(self):
        self.loader.set_filepath(self.files)
        self.data_raw = self.loader.load()    

    def analyze_data(self):
        self.analyzer.load_data(self.data_raw)
        self.analyzer.validate_input()
        self.data_analyzed = self.analyzer.analyze()

    def open_plot_window(self):
        self.plot_window = Plot_window(self.plotter)
        self.plot_window.show()

class Attribute_container():
    class_attr1 = 1
    def __init__(self) -> None:
        self.attr1 = 1
        self.attr2 = 2
        self.Viktor = "kuschelig"
        self.Thomas = "nicer dude"
        self.Daniel = "Heiratsmaterial"
    
    def method1(self):
        self.Viktor = "LoLBrot"
        pass

class Test_plotter:
    def __init__(self) -> None:
        self.cycler = cycle("rgb")
        self.fig = plt.Figure()
        self.fig.subplots()
        self.ax = self.fig.gca()
        self.x = np.linspace(0, 2, 100)
        self.y = self.x**2
        
    def validate_input(self):
        pass
    
    def plot(self):
        self.ax.plot(self.x, self.y, next(self.cycler))

def main():
    obj1 = Attribute_container()
    plottr = Test_plotter()   

    app = QApplication([])
    mainWin = Mainframe(obj1, plottr)
    mainWin.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()