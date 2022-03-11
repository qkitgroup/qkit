import sys
import os
import json
import importlib.util

from PyQt5 import uic
from PyQt5.QtWidgets import QTextBrowser, QWidget, QMainWindow, QLineEdit, QApplication, QVBoxLayout, QGridLayout, QLabel, QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT

test_mode = False
if test_mode:
    import numpy as np
    import matplotlib.pyplot as plt
    from itertools import cycle

class Mask:
    def __init__(self, mask):
        self.mask = mask
    def postive_mask(self, obj):
        if obj in self.mask:
            return True
        else:
            return False

    def negative_mask(self, obj):
        if obj in self.mask:
            return False
        else:
            return True

class Settings_tab(QWidget):
    def __init__(self, obj):
        super().__init__()
        self.obj = obj
        self.grid = QGridLayout(self)
        self.masking = Mask([int, float, str])

        for i, (name, value) in enumerate(obj.__dict__.items()):

            if self.masking.postive_mask(type(value)):
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

    def update_canvas(self):
        self.axes.cla()
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

class Model:
    def __init__(self) -> None:
        self.settings = {"files" : [],
        "plotter_path" : "",
        "analyzer_path" : "",
        "loader_path" : ""}

        self.data_raw = {}
        self.data_analyzed = {}

    def save_settings(self):
        with open(os.path.join("main", "configuration.ini"), "w+") as configfile:
            configfile.write(json.dumps(self.settings, indent= 2))

    def load_settings(self):
        try:
            with open(os.path.join("main", "configuration.ini")) as configfile:
                self.settings= json.load(configfile)
        except FileNotFoundError:
            pass

class Controller:
    def __init__(self, model):
        self.model = model
        self.loader = None
        self.analyzer = None
        self.plotter = None
    
    @staticmethod
    def load_module_from_filepath(fname):
        module_name = os.path.splitext(os.path.basename(fname))[0]
        module_spec = importlib.util.spec_from_file_location(module_name, fname)
        module = importlib.util.module_from_spec(module_spec) #type: ignore
        module_spec.loader.exec_module(module) #pyright: reportOptionalMemberAccess=false
        return module
    
    def load_LAP(self):
        self.choose_loader()
        self.choose_analyzer()
        self.choose_plotter()

    def choose_loader(self):
        try:
            module = self.load_module_from_filepath(self.model.settings["loader_path"])
            self.loader = module.Loader()
        except AttributeError:
            self.loader = None

    def choose_analyzer(self):
        try:
            module = self.load_module_from_filepath(self.model.settings["analyzer_path"])
            self.analyzer = module.Analyzer()
        except AttributeError:
            self.analyzer = None

    def choose_plotter(self):
        try:
            module = self.load_module_from_filepath(self.model.settings["plotter_path"])
            self.plotter = module.Plotter()
        except AttributeError:
            self.plotter = None
    
    def load_data(self):
        self.loader.set_filepath(self.model.settings["files"])
        self.model.data_raw = self.loader.load()

    def analyze_data(self):
        self.analyzer.load_data(self.model.data_raw)
        self.analyzer.validate_input()
        self.model.data_analyzed = self.analyzer.analyze()

    def plot_data(self):
        self.plotter.load_data(self.model.data_analyzed)
        self.plotter.validate_input()
        self.plotter.plot()

class View(QMainWindow):
    def __init__(self, controller, model):
        super().__init__()
        self.controller = controller
        self.model = model
        uic.loadUi(os.path.join("main", "ui", "main_window.ui"), self)

        self.button_load.clicked.connect(self.load_data)
        self.button_add_files.clicked.connect(self.add_files)
        self.button_reset_files.clicked.connect(self.reset_files)

        self.button_settings.clicked.connect(self.open_settings_window)
        self.button_plot.clicked.connect(self.open_plot_window)      
        self.button_analyze.clicked.connect(self.analyze_data)
        self.button_replot_reanalyze.clicked.connect(self.update_plot)        
        
        self.action_Save_Settings.triggered.connect(self.save_settings)
        self.action_Load_Settings.triggered.connect(self.load_settings)
        self.action_Choose_Loader.triggered.connect(self.get_loader_file)
        self.action_Choose_Analyzer.triggered.connect(self.get_analyzer_file)
        self.action_Choose_Plotter.triggered.connect(self.get_plotter_file)
        self.action_Reload_Modules.triggered.connect(self.controller.load_LAP)

        self.load_settings()

    def add_to_textbrowser(self, entry):
        self.text_browser_file_display.append(entry)

    def clear_textbrowser(self):
        self.text_browser_file_display.clear()

    def add_files(self):
        fnames, _ = QFileDialog.getOpenFileNames(self, "Choose files to load")
        for name in fnames:
            self.add_to_textbrowser(os.path.basename(name))
        self.model.settings["files"].extend(fnames)

    def reset_files(self):
        self.model.settings["files"] = []
        self.clear_textbrowser()

    def enable_load_button(self):
        allowed = True
        allowed = bool(self.controller.loader) and allowed
        self.button_load.setEnabled(allowed)
    
    def enable_analyze_button(self):
        allowed = True
        allowed = bool(self.controller.analyzer) and allowed
        allowed = bool(self.model.data_raw) and allowed
        self.button_analyze.setEnabled(allowed)        

    def enable_plot_button(self):
        allowed = True
        allowed = bool(self.controller.loader) and allowed
        allowed = bool(self.model.data_analyzed) and allowed
        self.button_plot.setEnabled(allowed)

    def enable_settings_button(self):
        allowed = True
        allowed = bool(self.controller.loader) and allowed
        allowed = bool(self.controller.analyzer) and allowed
        allowed = bool(self.controller.plotter) and allowed
        self.button_settings.setEnabled(allowed)

    def enable_reanalyze_replot_button(self):
        allowed = True
        allowed = bool(self.plot_window) and allowed
        self.button_replot_reanalyze.setEnabled(allowed)

    def get_loader_file(self):
        file = "loader"
        fname, _ = QFileDialog.getOpenFileName(self, f"Choose {file}", os.path.join(f"{file}s"), "Python files(*py)")
        item = QTableWidgetItem(os.path.basename(fname))
        self.Table_LAP.setItem(0, 0, item)
        self.model.settings["loader_path"] = fname
        if self.model.settings["loader_path"]:
            self.controller.choose_loader()
        self.enable_load_button()
        self.enable_settings_button()
    
    def get_analyzer_file(self):
        file = "analyzer"
        fname, _ = QFileDialog.getOpenFileName(self, f"Choose {file}", os.path.join(f"{file}s"), "Python files(*py)")
        item = QTableWidgetItem(os.path.basename(fname))
        self.Table_LAP.setItem(1, 0, item)        
        self.model.settings["analyzer_path"] = fname
        if self.model.settings["analyzer_path"]:
            self.controller.choose_analyzer()
        self.enable_analyze_button()
        self.enable_settings_button()

    def get_plotter_file(self):
        file = "plotter"
        fname, _ = QFileDialog.getOpenFileName(self, f"Choose {file}", os.path.join(f"{file}s"), "Python files(*py)")
        item = QTableWidgetItem(os.path.basename(fname))
        self.Table_LAP.setItem(2, 0, item)
        self.model.settings["plotter_path"] = fname
        if self.model.settings["plotter_path"]:
            self.controller.choose_plotter()
        self.enable_plot_button()
        self.enable_settings_button()

    def save_settings(self):
        self.model.save_settings()

    def closeEvent(self, event):
        event.accept()
        self.save_settings()

    def load_settings(self):
        self.model.load_settings()
        self.controller.load_LAP()
        
        fname = self.model.settings["loader_path"]
        item = QTableWidgetItem(os.path.basename(fname))
        self.Table_LAP.setItem(0, 0, item)
        self.enable_load_button()

        fname = self.model.settings["analyzer_path"]
        item = QTableWidgetItem(os.path.basename(fname))
        self.Table_LAP.setItem(1, 0, item)
        self.enable_analyze_button()

        fname = self.model.settings["plotter_path"]
        item = QTableWidgetItem(os.path.basename(fname))
        self.Table_LAP.setItem(2, 0, item)
        self.enable_plot_button()

        self.enable_settings_button()
        for file in self.model.settings["files"]:
            self.add_to_textbrowser(os.path.basename(file))

    def update_plot(self):
        self.plot_window.plot_widget.canvas.axes.cla()
        self.controller.plot_data()
        self.plot_window.plot_widget.canvas.draw()

    def load_data(self):
        self.controller.load_data()
        if self.model.settings["files"]:
            self.text_browser_file_display.append("---------LOADED---------")
            self.model.settings["files"] = []
            self.enable_analyze_button()

    def analyze_data(self):
        self.controller.analyze_data()
        self.enable_plot_button()

    def re_analyze_re_plot(self):
        self.controller.analyze_data()
        self.update_plot()

    def open_settings_window(self):
        self.settings_window = Settings_window(self.controller.loader, self.controller.analyzer, self.controller.plotter)
        self.controller.plot_data()
        self.settings_window.show()

    def open_plot_window(self):
        self.plot_window = Plot_window(self.controller.plotter)
        self.update_plot()
        self.plot_window.show()
        self.enable_reanalyze_replot_button()

class App(QApplication):
    def __init__(self, sys_argv):
        super().__init__(sys_argv)
        self.model = Model()
        self.main_controller = Controller(self.model)
        self.main_view = View(self.main_controller, self.model)
        self.main_view.show()

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
    app = App(sys.argv)
    sys.exit(app.exec_())
    pass

if __name__ == "__main__":
    main()