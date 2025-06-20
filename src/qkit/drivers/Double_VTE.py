from qkit.core.instrument_base import Instrument
import numpy as np
import logging
import typing
import time

class Double_VTE(Instrument):
    def __init__(self, name):
        """
        Double Virtual Tunnel Electronics

        So far only supports voltage bias, measure pseudo current for 2x transimpedance amplifier setup
        """
        super().__init__(name, tags=["virtual"])
        # setter matrix & getter matrix for e.g. sweeping voltage difference at const. total voltage across a sample and measuring current:
        # (VA) = (1   -1) . (V1) 
        # (VB)   (.5  .5)   (V2)
        # (IA) = (.5 -.5) . (I1)
        # (IB)   (1    1)   (I2)
        self._setter_matrix = np.array([[1, 0], [0, 1]])
        self._getter_matrix = np.array([[1, 0], [0, 1]]) # technically not required for sweeping, but handled here alongside setter for consistency

        self.v_div_1 = 1
        self.v_div_2 = 1
        self.dVdA_1 = 1
        self.dVdA_2 = 1

        self.sweep_manually = True
        # for manual sweeps
        self.setter_1: typing.Callable[[float], None] = None
        self.setter_2: typing.Callable[[float], None] = None
        self.getter_1: typing.Callable[[], float] = None
        self.getter_2: typing.Callable[[], float] = None
        self.rdb_set_1: typing.Callable[[], float] = None # optional but recommended to catch e.g. insufficient device resolution
        self.rdb_set_2: typing.Callable[[], float] = None
        self.dt = 0.001 # wait between set & get
        # for automated sweeps: func(to_be_set_v1, to_be_set_v2) -> actual_set_v1*v_div_1, actual_set_v2*v_div_2, measured_i1*dVdA_1, measured_i2*dVdA_2
        self.double_sweeper: typing.Callable[[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = None
    
    def set_setter_matrix(self, mat: np.ndarray):
        if mat.shape != (2, 2):
            logging.error("Setter-matrix shape was {}, but (2, 2) is required".format(str(mat.shape)))
            return
        if np.linalg.det(mat) == 0:
            logging.error("Setter-matrix needs to be invertible")
            return
        self._setter_matrix = mat
    def get_setter_matrix(self):
        return self._setter_matrix
    
    def set_getter_matrix(self, mat: np.ndarray):
        if mat.shape != (2, 2):
            logging.error("Getter-matrix shape was {}, but (2, 2) is required".format(str(mat.shape)))
            return
        if np.linalg.det(mat) == 0:
            logging.error("Getter-matrix needs to be invertible")
            return
        self._getter_matrix = mat
    def get_getter_matrix(self):
        return self._getter_matrix
    
    def show_effective_minmax(self, v1_min: float, v1_max: float, v2_min: float, v2_max: float, fix_a: float | None = None, fix_b: float | None = None, make_plot: bool = True) -> tuple[float]:
        helper = np.array([[v1_min, v1_max, v1_max, v1_min, v1_min], 
                           [v2_min, v2_min, v2_max, v2_max, v2_min]])
        # boundary box trivially as min/max over corners
        a_min = np.min(self._setter_matrix @ helper, axis=-1)[0]
        a_max = np.max(self._setter_matrix @ helper, axis=-1)[0]
        b_min = np.min(self._setter_matrix @ helper, axis=-1)[1]
        b_max = np.max(self._setter_matrix @ helper, axis=-1)[1]

        # if specific fixed point is within boundary, its according range can be found as the innermost intersections between quadrilateral edges and fixed line
        # draw everything in v1, v2 and va, vb space for above comment to make sense
        if fix_a is None:
            eff_b_min = None
            eff_b_max = None
        elif (fix_a < a_min) or (fix_a > a_max):
            eff_b_min = None
            eff_b_max = None
        else:
            eff_cand = []
            for i in range(4):
                try:
                    # https://en.wikipedia.org/wiki/Line%E2%80%93line_intersection P_y formula with p1 = setter@h_i, p2 = setter@h_i+1, p3 = (fix_a, 1), p4 = (fix_a, 0)
                    eff_cand += [(np.linalg.det(self._setter_matrix) * np.linalg.det(helper[:,i:i+2]) + fix_a*(self._setter_matrix @ (helper[:,i] - helper[:,i+1]))[1])/(self._setter_matrix @ (helper[:,i] - helper[:,i+1]))[0]]
                except:
                    pass
            eff_cand = np.array(eff_cand)
            eff_cand = np.unique(eff_cand[(eff_cand >= b_min) & (eff_cand <= b_max)])
            if len(eff_cand) != 2:
                logging.warning("Something went wrong during fix_a calculations")
                eff_b_min = None
                eff_b_max = None
            else:
                eff_b_min = np.min(eff_cand)
                eff_b_max = np.max(eff_cand)
        
        if fix_b is None:
            eff_a_min = None
            eff_a_max = None
        elif (fix_b < b_min) or (fix_b > b_max):
            eff_a_min = None
            eff_a_max = None
        else:
            eff_cand = []
            for i in range(4):
                try:
                    eff_cand += [(-np.linalg.det(self._setter_matrix) * np.linalg.det(helper[:,i:i+2]) + fix_b*(self._setter_matrix @ (helper[:,i] - helper[:,i+1]))[0])/(self._setter_matrix @ (helper[:,i] - helper[:,i+1]))[1]]
                except:
                    pass
            eff_cand = np.array(eff_cand)
            eff_cand = np.unique(eff_cand[(eff_cand >= a_min) & (eff_cand <= a_max)])
            if len(eff_cand) != 2:
                logging.warning("Something went wrong during fix_b calculations")
                eff_a_min = None
                eff_a_max = None
            else:
                eff_a_min = np.min(eff_cand)
                eff_a_max = np.max(eff_cand)

        if make_plot:
            import matplotlib.pyplot as plt
            plt.subplots(figsize=(12,12), dpi=360)
            plt.plot(*(self._setter_matrix @ helper), "k-", zorder=0)
            plt.hlines([b_min, b_max], a_min, a_max, "b", ":", zorder=1)
            plt.vlines([a_min, a_max], b_min, b_max, "b", ":", zorder=1)
            plt.hlines(fix_b, eff_a_min, eff_a_max, "r", "--", zorder=1) if not ((fix_b is None) or (eff_a_min is None) or (eff_a_max is None)) else None
            plt.vlines(fix_a, eff_b_min, eff_b_max, "r", "--", zorder=1) if not ((fix_a is None) or (eff_b_min is None) or (eff_b_max is None)) else None
            plt.scatter(*(self._setter_matrix @ helper[:,:-1]), c=range(1, helper.shape[-1]), marker="o", cmap="gist_rainbow", zorder=2)
            plt.show()

        return a_min, a_max, b_min, b_max, eff_b_min, eff_b_max, eff_a_min, eff_a_max

    def get_sweepdata(self, a_vals: np.ndarray, b_vals: np.ndarray):
        # (nop), (nop)   = *as tuple*:   (2, 2)                                         @          (2, 2)                    @      (2, nop)             //   (1, nop),                         (1, nop)
        sweep_1, sweep_2 = (s for s in np.array([[self.v_div_1, 0], [0, self.v_div_2]]) @ np.linalg.inv(self._setter_matrix) @ np.concatenate([a_vals.reshape((1, len(a_vals))), b_vals.reshape((1, len(b_vals)))], axis=0))
        logging.info("Sweeping Setter_1 within {}V to {}V and Setter_2 within {}V to {}V".format(np.min(sweep_1), np.max(sweep_1), np.min(sweep_2), np.max(sweep_2)))
        if self.sweep_manually:
            v_set_1, v_set_2, v_meas_1, v_meas_2 = ([], [], [], [])
            for i in range(len(a_vals)):
                self.setter_1(sweep_1[i])
                self.setter_2(sweep_2[i])
                time.sleep(self.dt)
                v_set_1 += [self.rdb_set_1() if not (self.rdb_set_1 is None) else sweep_1[i]]
                v_set_2 += [self.rdb_set_2() if not (self.rdb_set_2 is None) else sweep_2[i]]
                v_meas_1 += [self.getter_1()]
                v_meas_2 += [self.getter_2()]
            return np.array(v_set_1)/self.v_div_1, np.array(v_set_2)/self.v_div_2, np.array(v_meas_1)/self.dVdA_1, np.array(v_meas_2)/self.dVdA_2
        else:
            v_set_1, v_set_2, v_meas_1, v_meas_2 = self.double_sweeper(sweep_1, sweep_2)
            return v_set_1/self.v_div_1, v_set_2/self.v_div_2, v_meas_1/self.dVdA_1, v_meas_2/self.dVdA_2
        
    # qkit setting stuffs
    def get_parameters(self):
        return {
            "setter_matrix": None, 
            "getter_matrix": None, 
            "v_div_1": None,
            "v_div_2": None,
            "dVdA_1": None,
            "dVdA_2": None,
        } | ({
            "setter_1": None,
            "setter_2": None,
            "getter_1": None,
            "getter_2": None,
            "rdb_set_1": None,
            "rdb_set_2": None,
            "dt": None
        } if self.sweep_manually else {
            "double_sweeper": None
        })
    
    def get(self, param, **kwargs):
        try:
            return eval("self.get_{}()".format(param)) if "etter_matrix" in param else eval("self.{}".format(param))
        except:
            return None
        

if __name__ == "__main__":
    mydvte = Double_VTE("mydvte")
    mydvte.set_setter_matrix(np.array([[1, -1], [1/3, 2/3]]))
    print(mydvte.show_effective_minmax(0, 4, -4, 0, 2, 0))