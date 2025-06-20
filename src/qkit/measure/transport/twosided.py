import numpy as np
import qkit.measure
import qkit.measure.samples_class
from scipy import signal
import logging
import time
import sys
import threading
import typing

import qkit
from qkit.storage import store as hdf
from qkit.gui.plot import plot as qviewkit
from qkit.gui.notebook.Progress_Bar import Progress_Bar
from qkit.measure.measurement_class import Measurement 
import qkit.measure.write_additional_files as waf


class TransportTwoside(object):
    """
    Transport measurement routine for the special cases of applying two different voltages on a sample and measuring the resulting current with trans-impedence amplifiers
    """
    def __init__(self, DIVD):
        """
        DIVD: Double IV-Device. Should provide
            - setter/getter matrixes for converting desired effective values (e.g. voltage/current differences/averages) to respective device-side values 
            - get_sweepdata: effective v_a, v_b arrays in, measured v1, v2, i1, i2 out

        Possible sweep-modes:
            - sweep v_a, v_b constant, arb. x/y-coordinates
            - sweep v_a, v_b as x/y-coordinate, other x/y arb.
            - simultaneous v_a & v_b sweep, arb. x/y-coordinates
        """
        self._DIVD = DIVD

        self._measurement_object = Measurement()
        self._measurement_object.measurement_type = 'transport'

        self.filename = None
        self.expname = None
        self.comment = None

        # TODO logging

        self._x_coordname = None
        self._x_set_obj = None
        self._x_vec = None
        self._x_unit = None
        self._x_dt = 1e-3  # in s
        
        self._y_coordname = None
        self._y_set_obj = None
        self._y_vec = [None]
        self._y_unit = None
        self._y_dt = 1e-3  # in s

        self._eff_vb_as_coord = None # None or "x" or "y"

        self._sweeps: list[TransportTwoside.ArbTwosideSweep] = []
        self.eff_va_name = "eff_va"
        self.eff_vb_name = "eff_vb"
        self.sweep_dt = 0 # in s

        self.store_effs = True

        self._derivs: list[tuple[str, str]] = [] # specifiers such as ("Ia", "Vb") for calculating dIa/dVb
        self.deriv_func: typing.Callable[[np.ndarray, np.ndarray], np.ndarray] = self.savgol_deriv 

    ### Measurement preparation ###
    def set_sample(self, sample: qkit.measure.samples_class):
        self._measurement_object.sample = sample

    def set_x_parameter(self, name: str, set_obj: typing.Callable[[float], None], vals: list[float], unit: str = "A.U.", dt: float = 1e-3):
        if self._eff_vb_as_coord == "x":
            self._eff_vb_as_coord = None
        self._x_coordname = name
        self._x_set_obj = set_obj
        self._x_vec = vals
        self._x_unit = unit
        self._x_dt = dt

    def set_x_vb(self, b_vals: list[float]):
        [logging.warn("Non-constant v_b in sweeps will be overwritten, please check") for sweep in self.sweeps if not sweep.is_b_const()]
        self._eff_vb_as_coord = "x"
        self._x_vec = b_vals

    def set_y_parameter(self, name: str, set_obj: typing.Callable[[float], None], vals: list[float], unit: str = "A.U.", dt: float = 1e-3):
        if self._eff_vb_as_coord == "y":
            self._eff_vb_as_coord = None
        self._y_coordname = name
        self._y_set_obj = set_obj
        self._y_vec = vals
        self._y_unit = unit
        self._y_dt = dt

    def set_y_vb(self, b_vals: list[float]):
        [logging.warn("Non-constant v_b in sweeps will be overwritten, please check") for sweep in self.sweeps if not sweep.is_b_const()]
        self._eff_vb_as_coord = "y"
        self._y_vec = b_vals

    def add_deriv(self, y: str, x: str):
        """
        x/y: should be format "(i/v)(1/2)", e.g. "i2"; or "(i/v)/(1/2/a/b)" if store store_effs enabled. 
             muste be different 
        """
        if len(x) != 2 or len(y) != 2:
            logging.error("x and y identifiers must have length 2")
            return
        x = x.lower()
        y = y.lower()
        if not (x[0] in "iv" and y[0] in "iv" and x[1] in ("12ab" if self.store_effs else "12") and y[1] in ("12ab" if self.store_effs else "12")):
            logging.error("x and y should be format '(i/v)(1/2)', e.g. 'i2'; or '(i/v)/(1/2/a/b)' if store store_effs enabled")
            return
        if x == y:
            logging.error("x and y must be different")
            return
        self._derivs += [(y, x)]

    def clear_deriv(self):
        self._derivs = []

    ### Main measurement routine ### 
    def prepare_measurement_file(self):
        pass

    def measure_1D(self):
        pass

    def measure_2D(self):
        pass

    def measure_3D(self):
        pass

    def _measure(self):
        pass


    ### Helper functions & classes ###
    @staticmethod
    def savgol_deriv(x_vals: np.ndarray, y_vals: np.ndarray, **savgol_args):
        """
        Numerical derivative via savgol filters based qkit transport script
        """
        savgol_args = {'window_length': 10, 'polyorder': 3, 'deriv': 1} | savgol_args
        return signal.savgol_filter(y_vals, **savgol_args)/signal.savgol_filter(x_vals, **savgol_args)
    
    class ArbTwosideSweep(object):
        def __init__(self, a_vals: np.ndarray, b_vals: np.ndarray):
            if len(a_vals.shape) != 1 or len(b_vals.shape) != 1 or a_vals.shape != b_vals.shape:
                logging.error("Sweep arrays must be 1D and of same length")
                return
            self.a_vals = a_vals
            self.b_vals = b_vals
        
        def get(self):
            return self.a_vals, self.b_vals
        
        def is_b_const(self) -> bool:
            return np.all(self.b_vals == self.b_vals[0])
        
        def set_b_const(self, b_val: float):
            self.b_vals = np.linspace(b_val, b_val, self.a_vals.shape[0])

    class LinearTwoside(ArbTwosideSweep):
        def __init__(self, start_a, stop_a, start_b, stop_b, nop):
            super.__init__(np.linspace(start_a, stop_a, nop), np.linspace(start_b, stop_b, nop))


        