from tkinter import *
# import filedialog module
from tkinter import filedialog
  
# Function for opening the file explorer 
def browseFiles():
    filenames = filedialog.askopenfilenames(initialdir = "/",
                                          title = "Select a File",
                                          filetypes = (("Text files","*.txt*"),("all files","*.*")))
    return filenames



def print_nodes(file):
    print("\nData nodes:\n" + str([key for key in file.keys()]))

def main():
    browseFiles()

if __name__ == "__main__":
    main()