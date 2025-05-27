from qkit.storage.store import Data
from qkit.storage.hdf_dataset import hdf_dataset
import typing
import numpy as np

class logFunc(object):
    """
    Unified logging class to offer log-functionality at different points of 1D - 3D spectroscopy or transport measurements.

    The to be logged function can either be single-valued or yield a trace of (n) datapoints (independent from set x/y-parameters).

    For 3D measurements the function can be called
    a) once at the beginning [shape (1) or (n)]
    b) at each x-iteration [shape (x) or (x, n)] -> old spectroscopy.set_log_function & spectroscopy.set_log_function_2d
    c) only for the first x-value at each y-iteration [shape (y) or (y, n)]
    d) at each x- & y-iteration [shape (x, y) or (x, y, n)] -> old transport.set_log_function for the single-valued case
    with 2D measurements being naturally limited to cases a), b) and 1D measurements to case a). 

    This behavior can be controlled via handing over x_vec, y_vec or trace_info arguments. While the first two should be the respective h5 dataset, which 
    is already defined in the main measurement, 'trace_vec provides information about the additional coordinate a trace log function may sweep over as 
    (*values_array*, name, unit). The same base coordinate may be chosen for different trace log functions.
    """
    def __init__(self, file_name: str, func: typing.Callable, name: str, unit: str = "", dtype: str = "f", x_ds_url: str = None, y_ds_url: str = None, trace_info: tuple[np.ndarray, str, str] = None):
        self.file = Data(file_name)
        self.func = func
        self.name = name
        self.unit = unit
        self.dtype = dtype
        # print("Logging {} in file {}".format(name, file_name)) # TODO remove 
        self.signature = ""
        self.x_ds_url = x_ds_url
        if not (x_ds_url is None):
            self.signature += "x"
        self.x_len: int = None
        self.y_ds_url = y_ds_url
        if not (y_ds_url is None):
            self.signature += "y"
        self.y_len: int = None
        self.trace_info = trace_info
        if not (trace_info is None):
            self.signature += "n"
        self.buffer1d: np.ndarray = None
        self.log_ds: hdf_dataset = None
    def prepare_file(self):
        # prepare trace base coordinate if necessary
        if "n" in self.signature:
            try: 
                trace_ds = self.file.get_dataset("/entry/data0/{}".format(self.trace_info[1]))
                # base coordinate already exists in file
            except:
                trace_ds = self.file.add_coordinate(self.trace_info[1], self.trace_info[2])
                trace_ds.add(self.trace_info[0])
        # the logic is admittably more complicated here, writing down all 8 possible cases of x,y,n present or not helps
        if len(self.signature) == 0:
            self.log_ds = self.file.add_coordinate(self.name, self.unit) # coordinate dtype hardcoded as float
        elif len(self.signature) == 1:
            self.log_ds = self.file.add_value_vector(self.name, {"x":self.file.get_dataset(self.x_ds_url),"y":self.file.get_dataset(self.y_ds_url),"n":trace_ds}[self.signature], self.unit, dtype=self.dtype)
        elif len(self.signature) == 2:
            self.log_ds = self.file.add_value_matrix(self.name, self.file.get_dataset(self.x_ds_url) if "x" in self.signature else self.file.get_dataset(self.y_ds_url), trace_ds if "n" in self.signature else self.file.get_dataset(self.y_ds_url), self.unit, dtype=self.dtype)
        elif len(self.signature) == 3:
            self.log_ds = self.file.add_value_box(self.name, self.file.get_dataset(self.x_ds_url), self.file.get_dataset(self.y_ds_url), trace_ds, self.unit, dtype=self.dtype)
        
        if "x" in self.signature:
            self.x_len = self.file.get_dataset(self.x_ds_url).ds.shape[0]
        if "y" in self.signature:
            self.y_len = self.file.get_dataset(self.y_ds_url).ds.shape[0]

    def logIfDesired(self, ix=0, iy=0):        
        if (ix == 0 or "x" in self.signature) and (iy == 0 or "y" in self.signature): # log function call desired
            if len(self.signature) == 0: # ""
                # we will only reach here once, no further case-logic required
                self.log_ds.append(np.array([self.func()]), reset=True)
            elif "n" in self.signature: # "n", "xn", "yn", "xyn"
                self.log_ds.append(self.func())
                if len(self.signature) == 3:
                    if iy + 1 == self.y_len:
                        # who doesnt love 4x nested ifs edge cases? 
                        self.log_ds.next_matrix() 
            elif "y" in self.signature: # "y", "xy"
                if iy == 0:
                    self.buffer1d = np.full(self.y_len, np.nan)
                self.buffer1d[iy] = self.func()
                self.log_ds.append(self.buffer1d, reset=(iy != 0))
            else: # "x"
                if ix == 0:
                    self.buffer1d = np.full(self.x_len, np.nan)
                self.buffer1d[ix] = self.func()
                self.log_ds.append(self.buffer1d, reset=(ix != 0))