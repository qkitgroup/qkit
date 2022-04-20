import os
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QLineEdit, QGridLayout, QLabel


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
    def __init__(self, main_dir, *objects):
        super().__init__()
        uic.loadUi(os.path.join(main_dir, "main", "ui", "settings_window.ui"), self)

        for obj in objects:
            new_tab = Settings_tab(obj)
            self.tabWidget.addTab(new_tab, type(obj).__name__)