import numpy as np
from qkit.analysis.semiconductor.main.saving import create_saving_path

class Saver_spectrum_np():
    """Saves data in a folder that is set by "settings". 
    """
    def save(self, settings:dict, data:dict, fit_params_plunger=None, power_fit_params=None, ending=""):
        np.savetxt(create_saving_path(settings, "frequency_data"+ending, filetype=".txt"), data["freq"])
        np.savetxt(create_saving_path(settings, "spectrum_data"+ending, filetype=".txt"), data["spectrogram"])
        if fit_params_plunger != None:
            np.savetxt(create_saving_path(settings, "plunger_fit_data"+ending, filetype=".txt"), fit_params_plunger['fit_coef'])
        if power_fit_params != None:
            np.savetxt(create_saving_path(settings, "power_fit_data"+ending, filetype=".txt"), power_fit_params['popt'])
     
