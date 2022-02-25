import sys
import os

from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QMainWindow, QLineEdit, QApplication, QVBoxLayout, QGridLayout, QLabel

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

class Mainframe(QMainWindow):
    def __init__(self, *objects):
        super().__init__()
        uic.loadUi(os.path.join("main", "ui", "main_window.ui"), self)
        self.objects = objects
        self.button_settings.clicked.connect(self.open_settings_window)    
    
    def open_settings_window(self):
        self.settings_window = Settings_window(*self.objects)
        self.settings_window.show()

class Test_plotter():
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

def main():
    plottr = Test_plotter()

    plottr.Viktor ="kek"
    plottr2 = Test_plotter()
    Test_plotter.class_attr1 = 12
    plottr3 = Test_plotter()
    plottr4 = Test_plotter()
    plottr2.attr1 = 67
    print(plottr.attr1)
    print(plottr2.attr1)
    print(f"plottr1 class_attr1: {plottr.class_attr1}")
    print(f"plottr2 class_attr1: {plottr2.class_attr1}")
    print(f"plottr3 class_attr1: {plottr3.class_attr1}")
    print(f"plottr4 class_attr1: {plottr4.class_attr1}")

    app = QApplication([])
    mainWin = Mainframe(plottr, plottr2)
    mainWin.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()