#!/usr/bin/python python
import importlib.util
import json
import os
import sys
import traceback

from PyQt5 import uic
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QTableWidgetItem,
)
from qkit.analysis.semiconductor.main.windows.plot import Plot_window
from qkit.analysis.semiconductor.main.windows.settings import Settings_window

HOMEDIR = os.path.dirname(__file__)


class Model:
    def __init__(self) -> None:
        self.settings = {
            "files": [],
            "plotter_path": "",
            "analyzer_path": "",
            "loader_path": "",
        }

        self.data_raw = {}
        self.data_analyzed = {}

    def save_settings(self):
        with open(
            os.path.join(HOMEDIR, "main", "configuration.ini"), "w+"
        ) as configfile:
            configfile.write(json.dumps(self.settings, indent=2))

    def load_settings(self):
        try:
            with open(os.path.join(HOMEDIR, "main", "configuration.ini")) as configfile:
                self.settings = json.load(configfile)
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


class View(QMainWindow):
    def __init__(self, model):
        super().__init__()
        self.model = model
        path = os.path.join(HOMEDIR, "main", "ui", "main_window.ui")
        uic.loadUi(path, self)

    def add_to_file_browser(self, entry):
        self.text_browser_file_display.append(entry)

    def clear_file_browser(self):
        self.text_browser_file_display.clear()

    def enable_load_button(self, yesno):
        self.button_load.setEnabled(yesno)

    def enable_analyze_button(self, yesno):
        self.button_analyze.setEnabled(yesno)

    def enable_plot_button(self, yesno):
        self.button_plot.setEnabled(yesno)

    def enable_settings_button(self, yesno):
        self.button_settings.setEnabled(yesno)

    def enable_reanalyze_replot_button(self, yesno):
        self.button_replot_reanalyze.setEnabled(yesno)

    def open_files_dialog(self, title="Choose files to load", *dir):
        fnames, _ = QFileDialog.getOpenFileNames(self, title, os.path.join(*dir))
        return fnames

    def open_python_file_dialog(self, title, *dir):
        fname, _ = QFileDialog.getOpenFileName(
            self, f"Choose {title}", os.path.join(*dir), "Python files(*py)"
        )
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

    def closeEvent(self, event):
        event.accept()
        self.model.save_settings()

    def show_error_msg(self, msg):
        msgBox = QMessageBox(self)
        msgBox.setIcon(QMessageBox.Critical)
        msgBox.setText(msg)
        msgBox.setWindowTitle("Error")
        msgBox.show()

    def open_settings_window(self, *LAPs):
        self.settings_window = Settings_window(HOMEDIR, *LAPs)
        self.settings_window.show()

    def open_plot_window(self, figure):
        self.plot_window = Plot_window(HOMEDIR, figure)
        self.plot_window.show()

    def clear_plot_axis(self):
        self.plot_window.plot_widget.canvas.axes.cla()

    def draw_additional_plot(self):
        self.plot_window.plot_widget.canvas.draw()


class Controller:
    def __init__(self, model: Model, view: View):
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
        self.view.button_replot_reanalyze.clicked.connect(self.reanalyze_replot)

        self.view.action_Save_Settings.triggered.connect(self.save_settings)
        self.view.action_Load_Settings.triggered.connect(self.load_settings)
        self.view.action_Choose_Loader.triggered.connect(self.choose_loader)
        self.view.action_Choose_Analyzer.triggered.connect(self.choose_analyzer)
        self.view.action_Choose_Plotter.triggered.connect(self.choose_plotter)
        self.view.action_Reload_Modules.triggered.connect(self.load_LAP)

        self.load_settings()

    @staticmethod
    def load_module_from_filepath(fname):
        module_name = os.path.splitext(os.path.basename(fname))[0]
        module_spec = importlib.util.spec_from_file_location(module_name, fname)
        module = importlib.util.module_from_spec(module_spec)  # type: ignore
        module_spec.loader.exec_module(
            module
        )  # pyright: reportOptionalMemberAccess=false
        return module

    @do_monitored
    def load_loader(self):
        module = self.load_module_from_filepath(self.model.settings["loader_path"])
        self.loader = module.Loader()
        self.view.display_loader_name(self.model.settings["loader_path"])

    def choose_loader(self):
        fname = self.view.open_python_file_dialog(
            "loader", os.path.join(HOMEDIR, "loaders")
        )
        self.model.settings["loader_path"] = fname
        if fname:
            self.load_loader()

    @do_monitored
    def load_analyzer(self):
        module = self.load_module_from_filepath(self.model.settings["analyzer_path"])
        self.analyzer = module.Analyzer()
        self.view.display_analyzer_name(self.model.settings["analyzer_path"])

    def choose_analyzer(self):
        fname = self.view.open_python_file_dialog(
            "analyzer", os.path.join(HOMEDIR, "analyzers")
        )
        self.model.settings["analyzer_path"] = fname
        if fname:
            self.load_analyzer()

    @do_monitored
    def load_plotter(self):
        module = self.load_module_from_filepath(self.model.settings["plotter_path"])
        self.plotter = module.Plotter()
        self.view.display_plotter_name(self.model.settings["plotter_path"])

    def choose_plotter(self):
        fname = self.view.open_python_file_dialog(
            "plotter", os.path.join(HOMEDIR, "plotters")
        )
        self.model.settings["plotter_path"] = fname
        if fname:
            self.load_plotter()

    def load_LAP(self):
        self.load_loader()
        self.load_analyzer()
        self.load_plotter()

    def add_files(self):
        fnames = self.view.open_files_dialog("Choose data to load", "")
        for name in fnames:
            self.view.add_to_file_browser(os.path.basename(name))
        self.model.settings["files"].extend(fnames)

    def reset_files(self):
        self.model.settings["files"] = []
        self.view.clear_file_browser()

    @do_monitored
    def load_data(self):
        self.loader.set_filepath(self.model.settings["files"])
        self.model.data_raw.update(self.loader.load())
        if self.model.settings["files"]:
            self.view.text_browser_file_display.append("---------LOADED---------")
            self.model.settings["files"] = []
            # self.view.enable_analyze_button()

    @do_monitored
    def analyze_data(self):
        self.analyzer.load_data(self.model.data_raw)
        self.analyzer.validate_input()
        self.model.data_analyzed.update(self.analyzer.analyze())
        # self.view.enable_plot_button()

    def plot_data(self):
        self.plotter.load_data(self.model.data_analyzed)
        self.plotter.validate_input()
        self.plotter.plot()

    @do_monitored
    def open_plot(self):
        self.plot_data()
        self.view.open_plot_window(self.plotter.figure)

    @do_monitored
    def reanalyze_replot(self):
        self.analyzer.load_data(self.model.data_raw)
        self.analyzer.validate_input()
        self.model.data_analyzed.update(self.analyzer.analyze())
        self.view.clear_plot_axis()
        self.plot_data()
        self.view.draw_additional_plot()

    @do_monitored
    def open_settings(self):
        self.view.open_settings_window(self.loader, self.analyzer, self.plotter)

    def save_settings(self):
        self.model.save_settings()

    def load_settings(self):
        self.model.load_settings()
        self.load_LAP()

        # self.view.enable_settings_button()
        for file in self.model.settings["files"]:
            self.view.add_to_textbrowser(os.path.basename(file))


class App(QApplication):
    def __init__(self, sys_argv):
        super().__init__(sys_argv)
        self.model = Model()
        self.main_view = View(self.model)
        self.main_controller = Controller(self.model, self.main_view)

        self.main_view.show()


def main():
    app = App(sys.argv)
    sys.exit(app.exec_())
    pass


if __name__ == "__main__":
    main()
