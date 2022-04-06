#!/usr/bin/python python
import sys
import os
import traceback
import json
import importlib.util

from PyQt5 import uic
from PyQt5.QtWidgets import QTextBrowser, QWidget, QMainWindow, QLineEdit, QApplication, QVBoxLayout, QGridLayout, QLabel, QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT

from main.windows.settings import Settings_window
from main.windows.plot import Plot_window

test_mode = False
if test_mode:
    import numpy as np
    import matplotlib.pyplot as plt
    from itertools import cycle

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

def do_monitored(func):
        def wrapper(self):
            try:
                func(self)
            except:
                error_msg = traceback.format_exc()
                self.view.show_error_msg(error_msg)            
        return wrapper

class Controller:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.loader = None
        self.analyzer = None
        self.plotter = None

        self.view.button_load.clicked.connect(self.load_data)
        self.view.button_add_files.clicked.connect(self.add_files)
        self.view.button_reset_files.clicked.connect(self.reset_files)

        self.view.button_settings.clicked.connect(self.open_settings)
        self.view.button_plot.clicked.connect(self.open_plot)      
        self.view.button_analyze.clicked.connect(self.analyze_data)
        self.view.button_replot_reanalyze.clicked.connect(self.update_plot)        
        
        self.view.action_Save_Settings.triggered.connect(self.save_settings)
        self.view.action_Load_Settings.triggered.connect(self.load_settings)
        self.view.action_Choose_Loader.triggered.connect(self.choose_loader)
        self.view.action_Choose_Analyzer.triggered.connect(self.get_analyzer_file)
        self.view.action_Choose_Plotter.triggered.connect(self.get_plotter_file)
        self.view.action_Reload_Modules.triggered.connect(self.load_LAP)

        self.load_settings()
    
    @staticmethod
    def load_module_from_filepath(fname):
        module_name = os.path.splitext(os.path.basename(fname))[0]
        module_spec = importlib.util.spec_from_file_location(module_name, fname)
        module = importlib.util.module_from_spec(module_spec) #type: ignore
        module_spec.loader.exec_module(module) #pyright: reportOptionalMemberAccess=false
        return module
    
    @do_monitored
    def choose_loader(self):
        fname = self.view.open_python_file_dialog("loader", "loaders")
        if fname:
            self.model.settings["loader_path"] = fname
            module = self.load_module_from_filepath(fname)
            self.loader = module.Loader()
            self.view.display_loader_name(fname)

    @do_monitored
    def choose_analyzer(self):
        fname = self.view.open_python_file_dialog("analyzer", "analyzers")
        if fname:
            self.model.settings["analyzer_path"] = fname
            module = self.load_module_from_filepath(fname)
            self.analyzer = module.Analyzer()
            self.view.display_analyzer_name(fname)

    @do_monitored
    def choose_plotter(self):
        fname = self.view.open_python_file_dialog("plotter", "plotters")
        if fname:
            self.model.settings["plotter_path"] = fname
            module = self.load_module_from_filepath(fname)
            self.plotter = module.Plotter()
            self.view.display_plotter_name(fname)

    def load_LAP(self):
        self.choose_loader()
        self.choose_analyzer()
        self.choose_plotter()
    
    @do_monitored
    def load_data(self):
        self.loader.set_filepath(self.model.settings["files"])
        self.model.data_raw.update(self.loader.load())
        if self.model.settings["files"]:
            self.view.text_browser_file_display.append("---------LOADED---------")
            self.model.settings["files"] = []
            self.view.enable_analyze_button()

    @do_monitored
    def analyze_data(self):
        self.analyzer.load_data(self.model.data_raw)
        self.analyzer.validate_input()
        self.model.data_analyzed.update(self.analyzer.analyze())
        self.view.enable_plot_button()

    @do_monitored
    def plot_data(self):
        self.plotter.load_data(self.model.data_analyzed)
        self.plotter.validate_input()
        self.plotter.plot()

    def open_plot(self):
        self.plot_data()
        self.view.open_plot_window(self.plotter.figure)
    
    def update_plot(self):
        self.view.clear_plot_axis()
        self.plot_data()
        self.view.draw_additional_plot()

    def open_settings(self):
        self.view.open_settings_window(self.loader, self.analyzer, self.plotter)

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

    def open_python_file_dialog(self, title, *dir):
        fname, _ = QFileDialog.getOpenFileName(self, f"Choose {title}", os.path.join(*dir), "Python files(*py)")
        return fname
    
    def display_loader_name(self, name):
        item = QTableWidgetItem(os.path.basename(name))
        self.Table_LAP.setItem(0, 0, item)
    
    def display_analyzer_name(self, name):
        item = QTableWidgetItem(os.path.basename(name))
        self.Table_LAP.setItem(1, 0, item)
    
    def display_plotter_name(self, name):
        item = QTableWidgetItem(os.path.basename(name))
        self.Table_LAP.setItem(2, 0, item)

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
    
    def show_error_msg(self, msg):
        msgBox = QMessageBox(self)
        msgBox.setIcon(QMessageBox.Critical)
        msgBox.setText(msg)
        msgBox.setWindowTitle("Error")
        msgBox.show()

    def update_plot(self):
        self.plot_window.plot_widget.canvas.axes.cla()
        self.display_errors(self.controller.plot_data)
        self.plot_window.plot_widget.canvas.draw()
    
    def re_analyze_re_plot(self):
        self.display_errors(self.controller.analyze_data)
        self.update_plot()

    def open_settings_window(self, *LAPs):
        self.settings_window = Settings_window(LAPs)
        self.settings_window.show()

    def open_plot_window(self, figure):
        self.plot_window = Plot_window(figure)
        self.plot_window.show()

    def clear_plot_axis(self):
        self.plot_window.plot_widget.canvas.axes.cla()

    def draw_additional_plot(self):
        self.plot_window.plot_widget.canvas.draw()


class App(QApplication):
    def __init__(self, sys_argv):
        super().__init__(sys_argv)
        self.model = Model()
        self.main_controller = Controller(self.model)
        self.main_view = View(self.main_controller, self.model)
        self.main_view.show()

def main():
    app = App(sys.argv)
    sys.exit(app.exec_())
    pass

if __name__ == "__main__":
    main()