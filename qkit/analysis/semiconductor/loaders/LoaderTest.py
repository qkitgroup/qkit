from interfaces import LoaderInterface
import numpy as np

class Loader(LoaderInterface):
    def __init__(self):
        self.filepath = ""
        self.number = 12

    def set_filepath(self, path):
        self.filepath = path
        print(self.filepath)
    
    def load(self):
        x = np.arange(-100, 100)
        y = x **3

        return {"x" : x, "y" : y}

if __name__ == "__main__":
    loader = Loader()