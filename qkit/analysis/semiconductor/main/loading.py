#%%
from PyQt5.QtWidgets import QFileDialog
import os

def path_gui(dir="", filters=".h5 files"):
    """Select a file or more via a gui dialog. 
    """
    paths = QFileDialog.getOpenFileNames(None, "Select data file...",
        dir, filters)
    return paths[0]


def open_files_dialog(title="Choose files to load", *dir):
    fnames, _ = QFileDialog.getOpenFileNames(None, title, os.path.join("", *dir))
    return fnames

def open_python_file_dialog(title="Choose file to load", *dir):
    fname, _ = QFileDialog.getOpenFileName(None, title, os.path.join("", *dir), "Python files(*py)")
    return fname


if __name__== "__main__":
    open_files_dialog()
# %%
