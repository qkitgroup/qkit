import numpy as np
from abc import ABC, abstractmethod
import scipy.optimize as spopt
import scipy.ndimage
import logging
from qkit.storage.store import Data as qkitData
from qkit.storage.hdf_dataset import hdf_dataset
from qkit.analysis.circle_fit.circle_fit_2019 import circuit

class ResonatorFitBase(ABC):
    """
    Defines the core functionality any fit function should offer, namely freq, amp & phase in, simulated freq, amp, phase + extracted data out. 
    Contrary to previous version, fit-functionality is completely decoupled from the h5 file format, this should be handled in the respective measurement script instead. 
    Complex IQ data + view should be created in measurement script by default as well. 

    extract_data dict contains information like f_res, Qc, etc. and its (final) keys should be static accessible for each fit function class overriding this base implementation.
    This allows preparing hdf datasets for them without them being calculated yet
    """
    def __init__(self):
        self.freq_fit: np.ndarray[float] = None
        self.amp_fit: np.ndarray[float] = None
        self.pha_fit: np.ndarray[float] = None
        self.extract_data: dict[str, float] = {}
        self.out_nop = 501 # number of points the output fits are plotted with

    @abstractmethod
    def do_fit(self, freq: np.ndarray[float] = [0, 1], amp: np.ndarray[float] = None, pha: np.ndarray[float] = None):
        logging.error("Somehow ran into abstract resonator fit base class fit-function")
        self.freq_fit = np.linspace(np.min(freq), np.max(freq), self.out_nop)
        self.amp_fit = np.ones(self.out_nop)
        self.pha_fit = np.zeros(self.out_nop)
        self.extract_data = {}
        return self


def autofit_file(file: qkitData | str, fit_func: ResonatorFitBase, f_min: float = None, f_max: float = None):
    # ensure file is qkit.storage.store.Data
    if type(file) == str:
        try:
            file = qkitData(file) # assume path
        except:
            logging.error("'{}' is not a valid path".format(file))
            raise AttributeError
    # check if file has freq, amp, phase
    try: 
        freq_data = np.array(file.data.frequency)
        amp_data = np.array(file.data.amplitude)
        pha_data = np.array(file.data.phase)
    except:
        logging.error("Could not access frequency, amplitude and/or phase. Is this really a VNA measurement?")
        raise AttributeError
    # do not allow overriding existing fits
    try: 
        dummy = file.analysis._fit_frequency
        logging.error("File already contains fit data. Please access and store everything manually.")
        raise ValueError
    except:
        pass
    # add frequency coordinate
    f_min = -np.inf if f_min is None else f_min
    f_max = np.inf if f_max is None else f_max
    selly = (freq_data >= f_min) & (freq_data <= f_max)
    file_freq_fit = file.add_coordinate("_fit_frequency", unit="Hz", folder="analysis")
    file_freq_fit.add(np.linspace(np.min(freq_data[selly]), np.max(freq_data[selly]), fit_func.out_nop))
    file_extracts: dict[str, hdf_dataset] = {}

    if len(amp_data.shape) == 1: # 1D measurement
        # add result datastores
        file_amp_fit = file.add_value_vector("_fit_amplitude", x=file_freq_fit, unit="arb. unit", folder="analysis")
        file_pha_fit = file.add_value_vector("_fit_phase", x=file_freq_fit, unit="rad", folder="analysis")
        file_real_fit = file.add_value_vector("_fit_real", x=file_freq_fit, unit="", folder="analysis")
        file_imag_fit = file.add_value_vector("_fit_imag", x=file_freq_fit, unit="", folder="analysis")
        for key in fit_func.extract_data.keys():
            file_extracts[key] = file.add_coordinate("fit_" + key, folder="analysis")
        # actual fitting
        fit_func.do_fit(freq_data[selly], amp_data[selly], pha_data[selly])
        # fill entries
        file_amp_fit.append(fit_func.amp_fit)
        file_pha_fit.append(fit_func.pha_fit)
        file_real_fit.append(fit_func.amp_fit*np.cos(fit_func.pha_fit))
        file_imag_fit.append(fit_func.amp_fit*np.sin(fit_func.pha_fit))
        for key, val in fit_func.extract_data.items():
            file_extracts[key].add(np.array([val]))
    
    elif len(amp_data.shape) == 2: # 2D measurement
        # add result datastores
        file_amp_fit = file.add_value_matrix("_fit_amplitude", x=file.get_dataset(file.data.amplitude.x_ds_url), y=file_freq_fit, unit="arb. unit", folder="analysis")
        file_pha_fit = file.add_value_matrix("_fit_phase", x=file.get_dataset(file.data.amplitude.x_ds_url), y=file_freq_fit, unit="rad", folder="analysis")
        file_real_fit = file.add_value_matrix("_fit_real", x=file.get_dataset(file.data.amplitude.x_ds_url), y=file_freq_fit, unit="", folder="analysis")
        file_imag_fit = file.add_value_matrix("_fit_imag", x=file.get_dataset(file.data.amplitude.x_ds_url), y=file_freq_fit, unit="", folder="analysis")
        buffer_extracts: dict[str, np.ndarray] = {}
        for key in fit_func.extract_data.keys():
            file_extracts[key] = file.add_value_vector("fit_" + key, x=file.get_dataset(file.data.amplitude.x_ds_url), folder="analysis")
            buffer_extracts[key] = np.full(file[file.data.amplitude.x_ds_url].shape[0], np.nan)
        for ix in range(amp_data.shape[0]):
            # actual fitting
            fit_func.do_fit(freq_data[selly], amp_data[ix, selly], pha_data[ix, selly])
            # fill entries
            file_amp_fit.append(fit_func.amp_fit)
            file_pha_fit.append(fit_func.pha_fit)
            file_real_fit.append(fit_func.amp_fit*np.cos(fit_func.pha_fit))
            file_imag_fit.append(fit_func.amp_fit*np.sin(fit_func.pha_fit))
            for key, val in fit_func.extract_data.items():
                buffer_extracts[key][ix] = val
                file_extracts[key].append(buffer_extracts[key], reset=True)

    elif len(amp_data.shape) == 3: # 3D measurement
        # add result datastores
        file_amp_fit = file.add_value_box("_fit_amplitude", x=file.get_dataset(file.data.amplitude.x_ds_url), y=file.get_dataset(file.data.amplitude.y_ds_url), z=file_freq_fit, unit="arb. unit", folder="analysis")
        file_pha_fit = file.add_value_box("_fit_phase", x=file.get_dataset(file.data.amplitude.x_ds_url), y=file.get_dataset(file.data.amplitude.y_ds_url), z=file_freq_fit, unit="rad", folder="analysis")
        file_real_fit = file.add_value_box("_fit_real", x=file.get_dataset(file.data.amplitude.x_ds_url), y=file.get_dataset(file.data.amplitude.y_ds_url), z=file_freq_fit, unit="", folder="analysis")
        file_imag_fit = file.add_value_box("_fit_imag", x=file.get_dataset(file.data.amplitude.x_ds_url), y=file.get_dataset(file.data.amplitude.y_ds_url), z=file_freq_fit, unit="", folder="analysis")
        for key in fit_func.extract_data.keys():
            file_extracts[key] = file.add_value_matrix("fit_" + key, x=file.get_dataset(file.data.amplitude.x_ds_url), y=file.get_dataset(file.data.amplitude.y_ds_url), folder="analysis")
        buffer_extracts: dict[str, np.ndarray] = {}
        import itertools # alternative to nested loops that allows easier breaking when fill is reached
        for ix, iy in itertools.product(range(amp_data.shape[0]), range(amp_data.shape[1])):
            if iy == 0:
                for key in fit_func.extract_data.keys():
                     buffer_extracts[key] = np.full(file[file.data.amplitude.y_ds_url].shape[0], np.nan)
            # actual fitting
            fit_func.do_fit(freq_data[selly], amp_data[ix, iy, selly], pha_data[ix, iy, selly])
            # fill entries
            file_amp_fit.append(fit_func.amp_fit)
            file_pha_fit.append(fit_func.pha_fit)
            file_real_fit.append(fit_func.amp_fit*np.cos(fit_func.pha_fit))
            file_imag_fit.append(fit_func.amp_fit*np.sin(fit_func.pha_fit))
            for key, val in fit_func.extract_data.items():
                buffer_extracts[key][iy] = val
                file_extracts[key].append(buffer_extracts[key], reset=(iy != 0))
            if (ix + 1 == file.data.amplitude.fill[0]) & (iy + 1 == file.data.amplitude.fill[1]):
                # The measurement stopped somewhere in the middle of a xy-sweep, no more data to analyze
                break
            if iy + 1 == amp_data.shape[1]:
                file_amp_fit.next_matrix()
                file_pha_fit.next_matrix()
                file_real_fit.next_matrix()
                file_imag_fit.next_matrix()
    else:
        logging.error("What?")
        raise NotImplementedError()
    
    # add/update views
    file["/entry/views/IQ"].attrs.create("xy_1", "/entry/analysis0/_fit_real:/entry/analysis0/_fit_imag")
    file["/entry/views/IQ"].attrs.create("xy_1_filter", "None")
    file["/entry/views/IQ"].attrs.create("overlays", 1)
    file.add_view("AmplitudeFit", file.data.frequency, file.data.amplitude).add(file_freq_fit, file_amp_fit)
    file.add_view("PhaseFit", file.data.frequency, file.data.phase).add(file_freq_fit, file_pha_fit)


class CircleFit(ResonatorFitBase):
    def __init__(self, n_ports: int, fit_delay_max_iterations: int = 5, fixed_delay: float = None, isolation: int = 15, guesses: list[float] = None):
        super().__init__()
        self.extract_data = {
            'Qc': np.nan, 
            'Qc_max': np.nan, 
            'Qc_min': np.nan, 
            'Qc_no_dia_corr': np.nan, 
            'Qi': np.nan, 
            'Qi_err': np.nan, 
            'Qi_max': np.nan, 
            'Qi_min': np.nan, 
            'Qi_no_dia_corr': np.nan, 
            'Qi_no_dia_corr_err': np.nan, 
            'Ql': np.nan, 
            'Ql_err': np.nan, 
            'a': np.nan, 
            'absQc_err': np.nan, 
            'alpha': np.nan, 
            'chi_square': np.nan, 
            'delay': np.nan, 
            'delay_remaining': np.nan, 
            'fano_b': np.nan, 
            'fr': np.nan, 
            'fr_err': np.nan, 
            'phi': np.nan, 
            'phi_err': np.nan, 
            'theta': np.nan
        }
        # fit parameters
        self.n_ports = n_ports # 1: reflection port, 2: notch port
        self.fit_delay_max_iterations = fit_delay_max_iterations
        self.fixed_delay = fixed_delay
        self.isolation = isolation
        self.guesses = guesses # init guess (f_res, Ql, delay) for phase fit
    
    def do_fit(self, freq: np.ndarray[float], amp: np.ndarray[float], pha: np.ndarray[float]):
        # use external circlefit 
        my_circuit = circuit.reflection_port(freq, amp*np.exp(1j*pha)) if self.n_ports == 1 else circuit.notch_port(freq, amp*np.exp(1j*pha))
        my_circuit.fit_delay_max_iterations = self.fit_delay_max_iterations
        my_circuit.autofit(fixed_delay=self.fixed_delay, isolation=self.isolation)

        # update to be read parameters
        self.extract_data = {
            'Qc': np.nan, 
            'Qc_max': np.nan, 
            'Qc_min': np.nan, 
            'Qc_no_dia_corr': np.nan, 
            'Qi': np.nan, 
            'Qi_err': np.nan, 
            'Qi_max': np.nan, 
            'Qi_min': np.nan, 
            'Qi_no_dia_corr': np.nan, 
            'Qi_no_dia_corr_err': np.nan, 
            'Ql': np.nan, 
            'Ql_err': np.nan, 
            'a': np.nan, 
            'absQc_err': np.nan, 
            'alpha': np.nan, 
            'chi_square': np.nan, 
            'delay': np.nan, 
            'delay_remaining': np.nan, 
            'fano_b': np.nan, 
            'fr': np.nan, 
            'fr_err': np.nan, 
            'phi': np.nan, 
            'phi_err': np.nan, 
            'theta': np.nan
        }
        self.extract_data.update(my_circuit.fitresults)
        self.freq_fit = np.linspace(np.min(freq), np.max(freq), self.out_nop)
        z_sim = my_circuit.Sij(self.freq_fit, my_circuit.fr, my_circuit.Ql, my_circuit.Qc, my_circuit.phi, my_circuit.a, my_circuit.alpha, my_circuit.delay)
        self.amp_fit = np.abs(z_sim)
        self.pha_fit = np.angle(z_sim)

        return self
    

class LorentzianFit(ResonatorFitBase):
    def __init__(self):
        super().__init__()
        self.extract_data = {
            "f_res": None, 
            "f_res_err": None, 
            "Ql": None, 
            "Ql_err": None, 
            # TODO
        }

    def do_fit(self, freq, amp, pha):
        # TODO 
        logging.error("Lorentzian Fit not yet implemented. Feel free to adapt the respective maths yourself based on old resonator class")
        self.extract_data["f_res"] = 1 
        self.extract_data["f_res_err"] = 0.5
        self.extract_data["Ql"] = 1 
        self.extract_data["Ql_err"] = 0.5
        return super().do_fit(freq, amp, pha)


class SkewedLorentzianFit(ResonatorFitBase):
    def __init__(self):
        super().__init__()
        self.extract_data = {
            "f_res": None, 
            "f_res_err": None, 
            "Ql": None, 
            "Ql_err": None, 
            # TODO
        }

    def do_fit(self, freq, amp, pha):
        # TODO 
        logging.error("Lorentzian Fit not yet implemented. Feel free to adapt the respective maths yourself based on old resonator class")
        self.extract_data["f_res"] = 1 
        self.extract_data["f_res_err"] = 0.5
        self.extract_data["Qc"] = 1 
        self.extract_data["Qc_err"] = 0.5
        return super().do_fit(freq, amp, pha)


class FanoFit(ResonatorFitBase):
    def __init__(self):
        super().__init__()
        self.extract_data = {
            "f_res": None, 
            "f_res_err": None, 
            "Qc": None, 
            "Qc_err": None, 
            # TODO
        }

    def do_fit(self, freq, amp, pha):
        # TODO 
        logging.error("Lorentzian Fit not yet implemented. Feel free to adapt the respective maths yourself based on old resonator class")
        self.extract_data["f_res"] = 1 
        self.extract_data["f_res_err"] = 0.5
        self.extract_data["Qc"] = 1 
        self.extract_data["Qc_err"] = 0.5
        return super().do_fit(freq, amp, pha)
    

FitNames: dict[str, ResonatorFitBase] = {
    'lorentzian': LorentzianFit, 
    'skewed_lorentzian': SkewedLorentzianFit, 
    'circle_fit_reflection': CircleFit, 
    'circle_fit_notch': CircleFit,
    'fano': FanoFit, 
}