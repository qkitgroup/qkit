from tkinter import *
# import filedialog module
from tkinter import filedialog
  
# Function for opening the file explorer 
def browseFiles():
    filenames = filedialog.askopenfilenames(initialdir = "/",
                                          title = "Select a File",
                                          filetypes = (("Text files","*.txt*"),("all files","*.*")))
    return filenames

browseFiles()

