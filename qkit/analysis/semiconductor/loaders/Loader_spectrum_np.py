import numpy as np
from qkit.analysis.semiconductor.main.saving import create_saving_path

class Loader_spectrum_np():
    """Loads spectrum of folder given in settings. 
    """
    def load(self, settings:dict, ending=""):
        """Return is a touple of the data dict, fit params of the plunger gate sweep potentially used for 
        calibration, and data of the power fit. 
        """
        data = {}
        fit_params_plunger = {}
        power_fit_params = {}

        data["freq"] = np.loadtxt(create_saving_path(settings, "frequency_data"+ending, filetype=".txt"))
        data["spectrogram"] = np.loadtxt(create_saving_path(settings, "spectrum_data"+ending, filetype=".txt"))
        try:
            fit_params_plunger['fit_coef'] = np.loadtxt(create_saving_path(settings, "plunger_fit_data"+ending, filetype=".txt"))
        except FileNotFoundError:
            print("No plunger data found.")    
            fit_params_plunger = None  
        try:
            power_fit_params["popt"] = np.loadtxt(create_saving_path(settings, "power_fit_data"+ending, filetype=".txt"))
        except FileNotFoundError:
            print("No power fit data found.") 
            power_fit_params = None     

        return (data, fit_params_plunger, power_fit_params)
