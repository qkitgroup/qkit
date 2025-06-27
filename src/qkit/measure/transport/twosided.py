import numpy as np
from scipy import signal
import logging
import time
import typing

import qkit
import qkit.storage
import qkit.storage.hdf_dataset
import qkit.storage.store
from qkit.gui.notebook.Progress_Bar import Progress_Bar
import qkit.measure
import qkit.measure.samples_class
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
        self._DIVD: qkit.drivers.Douvle_VTE.Double_VTE = DIVD

        self._measurement_object = Measurement()
        self._measurement_object.measurement_type = 'transport'

        self.filename = None
        self.expname = None
        self.comment = None

        # TODO logging

        self._x_coordname = None
        self._x_set_obj = lambda x: None
        self._x_vec = None
        self._x_unit = None
        self._x_dt = None
        
        self._y_coordname = None
        self._y_set_obj = lambda x: None
        self._y_vec = [None]
        self._y_unit = None
        self._y_dt = None

        self._eff_vb_as_coord = None # None or "x" or "y"

        self._sweeps: list[ArbTwosideSweep] = []
        self.eff_va_name = "eff_va"
        self.eff_vb_name = "eff_vb"
        self.eff_ia_name = "eff_ia"
        self.eff_ib_name = "eff_ib"
        self.sweep_dt = None

        self.store_effs = True

        self._derivs: list[tuple[str, str]] = [] # specifiers such as ("Ia", "Vb") for calculating dIa/dVb
        self.deriv_func: typing.Callable[[np.ndarray, np.ndarray], np.ndarray] = self.savgol_deriv 

        self._views: list[tuple[str, str]] = [] # specifiers such as ("Ia", "Vb")

        self._msdim = None # set by resp. measure_ND() call 

    ### Measurement preparation ###
    def set_sample(self, sample: qkit.measure.samples_class):
        self._measurement_object.sample = sample

    def clear_sweeps(self):
        self._sweeps = []
    
    def add_sweep(self, s: ArbTwosideSweep):
        self._sweeps += [s]

    def set_x_parameter(self, name: str = None, set_obj: typing.Callable[[float], None] = lambda x: None, vals: list[float] = [None], unit: str = "A.U.", dt: float = None):
        """
        Empty call to remove x_params
        """
        if self._eff_vb_as_coord == "x":
            self._eff_vb_as_coord = None
        self._x_coordname = name
        self._x_set_obj = set_obj
        self._x_vec = vals
        self._x_unit = unit
        self._x_dt = dt

    def set_x_vb(self, b_vals: list[float], name: str = "eff_v_b", unit: str = "V", dt: float = None):
        [logging.warn("Non-constant v_b in sweeps will be overwritten, please check") for sweep in self.sweeps if not sweep.is_b_const()]
        if self._eff_vb_as_coord == "y":
            logging.warn("Overriding effective Vb as y-coordinate")
            self._y_coordname = None
            self._y_set_obj = lambda x: None
            self._y_vec = [None]
            self._y_unit = None
            self._y_dt = None
        self._eff_vb_as_coord = "x"
        self._x_coordname = name
        self._x_set_obj = self._set_b_for_axis
        self._x_vec = b_vals
        self._x_unit = unit
        self._x_dt = dt

    def set_y_parameter(self, name: str, set_obj: typing.Callable[[float], None], vals: list[float], unit: str = "A.U.", dt: float = 1e-3):
        """
        Empty call to remove x_params
        """
        if self._eff_vb_as_coord == "y":
            self._eff_vb_as_coord = None
        self._y_coordname = name
        self._y_set_obj = set_obj
        self._y_vec = vals
        self._y_unit = unit
        self._y_dt = dt

    def set_y_vb(self, b_vals: list[float], name: str = "eff_v_b", unit: str = "V", dt: float = None):
        [logging.warn("Non-constant v_b in sweeps will be overwritten, please check") for sweep in self.sweeps if not sweep.is_b_const()]
        if self._eff_vb_as_coord == "x":
            logging.warn("Overriding effective Vb as y-coordinate")
            self._x_coordname = None
            self._x_set_obj = lambda x: None
            self._x_vec = [None]
            self._x_unit = None
            self._x_dt = None
        self._eff_vb_as_coord = "y"
        self._y_coordname = name
        self._y_set_obj = self._set_b_for_axis
        self._y_vec = b_vals
        self._y_unit = unit
        self._y_dt = dt

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

    def clear_derivs(self):
        self._derivs = []

    def add_view(self, y: str, x: str):
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
        self._views += [(y, x)]

    def clear_views(self):
        self._views = []

    ### Main measurement routine ### 
    def prepare_measurement_file(self):
        self.the_file = qkit.storage.store.Data(name='_'.join(list(filter(None, ('{:d}D_IV_curve'.format(self._msdim), self.filename, self.expname)))), mode='a')
        # settings
        self.the_file.add_textlist('settings').append(waf.get_instrument_settings(self.the_file.get_filepath()))
        self._measurement_object.uuid = self.the_file._uuid
        self._measurement_object.hdf_relpath = self.the_file._relpath
        self._measurement_object.instruments = qkit.instruments.get_instrument_names()  # qkit.instruments.get_instruments() #
        self._measurement_object.save()
        self.the_file.add_textlist('measurement').append(self._measurement_object.get_JSON())
        # matrices
        mat_dummy_x = self.the_file.add_coordinate("_matrix_x", folder="analysis")
        mat_dummy_x.add([1, 2])
        mat_dummy_y = self.the_file.add_coordinate("_matrix_y", folder="analysis")
        mat_dummy_y.add([1, 2])
        setter_matrix = self.the_file.add_value_matrix("setter_matrix", mat_dummy_x, mat_dummy_y, folder="analysis")
        for sm_elm in self._DIVD._setter_matrix:
            setter_matrix.append(sm_elm)
        getter_matrix = self.the_file.add_value_matrix("getter_matrix", mat_dummy_x, mat_dummy_y, folder="analysis")
        for gm_elm in self._DIVD._getter_matrix:
            getter_matrix.append(gm_elm)
        # coords
        target_eff_va = [self.the_file.add_coordinate("target_" + self.eff_va_name + "_{}".format(i), "V") for i in range(len(self._sweeps))]
        target_eff_vb = [self.the_file.add_coordinate("target_" + self.eff_va_name + "_{}".format(i), "V") for i in range(len(self._sweeps))]
        for i in range(len(self._sweeps)):
            a, b = self._sweeps[i].get()
            target_eff_va[i].add(a)
            target_eff_vb[i].add(b)
        if self._msdim >= 2:
            x_coord = self.the_file.add_coordinate(self._x_coordname, self._x_unit)
            x_coord.add(self._x_vec)
        if self._msdim == 3:
            y_coord = self.the_file.add_coordinate(self._y_coordname, self._y_unit)
            y_coord.add(self._y_vec)
        # data
        def value_dimobj(name, base_coord, unit, folder="data"):
            if self._msdim == 1:
                return self.the_file.add_value_vector(name, base_coord, unit, folder=folder)
            elif self._msdim == 2:
                return self.the_file.add_value_matrix(name, x_coord, base_coord, unit, folder=folder)
            elif self._msdim == 3:
                return self.the_file.add_value_box(name, x_coord, y_coord, base_coord, unit, folder=folder)
        self._v1 = [value_dimobj("v1_{}".format(i), target_eff_va[i], "V") for i in range(len(self._sweeps))]
        self._v2 = [value_dimobj("v2_{}".format(i), target_eff_va[i], "V") for i in range(len(self._sweeps))]
        self._i1 = [value_dimobj("i1_{}".format(i), target_eff_va[i], "A") for i in range(len(self._sweeps))]
        self._i2 = [value_dimobj("i2_{}".format(i), target_eff_va[i], "A") for i in range(len(self._sweeps))]
        
        self._va = [value_dimobj(self.eff_va_name + "_{}".format(i), target_eff_va[i], "V") for i in range(len(self._sweeps))] if self.store_effs else []
        self._vb = [value_dimobj(self.eff_vb_name + "_{}".format(i), target_eff_va[i], "V") for i in range(len(self._sweeps))] if self.store_effs else []
        self._ia = [value_dimobj(self.eff_ia_name + "_{}".format(i), target_eff_va[i], "A") for i in range(len(self._sweeps))] if self.store_effs else []
        self._ib = [value_dimobj(self.eff_ib_name + "_{}".format(i), target_eff_va[i], "A") for i in range(len(self._sweeps))] if self.store_effs else []
        # derivs
        self._deriv_store: list[list[qkit.storage.hdf_dataset.hdf_dataset]] = []
        for dy, dx in self._derivs:
            self._deriv_store += [ [value_dimobj("d{}_d{}_{}".format(dy, dx, i), target_eff_va[i], "V", "analysis") for i in range(len(self._sweeps))] ]
        # views
        for y, x in self._views:
            [self.the_file.add_view(y + "_" + x, eval("self._" + x)[i], eval("self._" + y)[i]) for i in range(len(self._sweeps))]

    def measure_1D(self):
        if len(self._sweeps) == 0:
            logging.error("No sweeps set, cannot measure")
            return
        self._msdim = 1
        self._measure()

    def measure_2D(self):
        if len(self._sweeps) == 0:
            logging.error("No sweeps set, cannot measure")
            return
        if self._x_coordname is None:
            logging.error("x-coordinate not set, cannot measure 2D")
            return
        self._msdim = 2
        self._measure()

    def measure_3D(self):
        if len(self._sweeps) == 0:
            logging.error("No sweeps set, cannot measure")
        if self._x_coordname is None:
            logging.error("x-coordinate not set, cannot measure 3D")
            return
        if self._y_coordname is None:
            logging.error("y-coordinate not set, cannot measure 3D")
            return
        self._msdim = 3
        self._measure()

    def _measure(self):
        self.prepare_measurement_file()
        pb = Progress_Bar((1 if self._msdim < 3 else len(self._y_vec))*(1 if self._msdim < 2 else len(self._x_vec))*len(self._sweeps), self.the_file.get_filepath())
        try:
            for ix, (x, x_func) in enumerate([(None, lambda x: None)] if self._msdim < 2 else [(x, self._x_set_obj) for x in self._x_vec]):
                x_func(x)
                time.sleep(self._x_dt) if (self._msdim >= 2 and not (self._x_dt is None)) else None
                for iy, (y, y_func) in enumerate([(None, lambda y: None)] if self._msdim < 3 else [(y, self._y_set_obj) for y in self._y_vec]):
                    y_func(y)
                    time.sleep(self._y_dt) if (self._msdim == 3 and not (self._y_dt is None)) else None
                    # TODO logging
                    for i in range(len(self._sweeps)):
                        v1, v2, i1, i2 = self._DIVD.get_sweepdata(*self._sweeps[i].get())
                        self._v1[i].append(v1)
                        self._v2[i].append(v2)
                        self._i1[i].append(i1)
                        self._i2[i].append(i2)
                        if self.store_effs:
                            vavb = self._DIVD._setter_matrix @ np.concatenate([v1[None,:], v2[None,:]], axis=0)
                            iaib = self._DIVD._getter_matrix @ np.concatenate([i1[None,:], i2[None,:]], axis=0)
                            self._va[i].append(vavb[0])
                            self._vb[i].append(vavb[1])
                            self._ia[i].append(iaib[0])
                            self._ib[i].append(iaib[1])
                        for j, (dy, dx) in enumerate(self._derivs):
                            self._deriv_store[j][i].append(self.deriv_func(eval("self._" + dy)[i], eval("self._" + dx)[i]))
                        pb.iterate()

                if self._msdim == 3:
                    for df in self._v1 + self._v2 + self._i1 + self._i2 + self._va + self._vb + self._ia + self._ib + sum(self._deriv_store, []):
                        df.next_matrix()
        except:
            self.the_file.close_file()
            print('Measurement complete: {:s}'.format(self.the_file.get_filepath()))


    ### Helper ###
    @staticmethod
    def savgol_deriv(x_vals: np.ndarray, y_vals: np.ndarray, **savgol_args):
        """
        Numerical derivative via savgol filters based qkit transport script
        """
        savgol_args = {'window_length': 10, 'polyorder': 3, 'deriv': 1} | savgol_args
        return signal.savgol_filter(y_vals, **savgol_args)/signal.savgol_filter(x_vals, **savgol_args)
    
    def _set_b_for_axis(self, val: float):
        for sweep in self._sweeps:
            sweep.set_b_const(val)

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
