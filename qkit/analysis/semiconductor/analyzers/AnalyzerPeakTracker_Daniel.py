import numpy as np
from scipy.optimize import curve_fit

from qkit.analysis.semiconductor.main.find_index_of_value import map_array_to_index
from qkit.analysis.semiconductor.main.time_conversion import convert_secs_2D


class AnalyzerPeakTracker:
    """Fits a sechans function to a plunger gate sweep in two iterations.
    """
    def __init__(self) -> None:
        self.init_params=None
        self.intervall1=0.01
        self.intervall2=0.01
        self.max_iter=10000

    def analyze(self, data:dict, nodes, peak_V:float):
        """peak_V is the Voltage of the peak eyeballed.
        width and width2 are the intervalls of idices used to fit the data to.  Better in Volts in future? 
        The sechans fit is NOT using Volt values as x values but instead indices of the array. 
        init_params: first values [a, b, d] of f(x) = a * (1 / np.cosh(b * (x - c))) + d
        peak_V: first value of c 
        """
        def sech(x, a, b, c, d):
            '''hyperbolic secans function'''
            return a * (1 / np.cosh(b * (x - c))) + d # return is scaled in Volts
        
        if self.init_params is None:
            # initial parameters for fit
            a, b, d = 0.01, -0.1, 0.0
        else:
            a, b, d = self.init_params[0], self.init_params[1], self.init_params[2]

        peak_index = map_array_to_index(data[nodes[1]], peak_V)
        intervall1_half_index = map_array_to_index(data[nodes[1]], abs(self.intervall1 / 2) + data[nodes[1]][0])
        intervall2_half_index= map_array_to_index(data[nodes[1]], abs(self.intervall2 / 2) + data[nodes[1]][0])

        p0 = [a, b, peak_index, d]  #initatal guess of a, b, c, d
        timestamps = convert_secs_2D(data[nodes[0]])
        length_sweep = len(timestamps)
        data["timestamps_diff"] = np.diff(timestamps)
        data["avg_sweep_time"] = np.average(np.diff(timestamps)) 
        data["peaks_plunger_V"] =  np.array([None] * length_sweep) # initialize None array for peaks
        data["peaks_value"] =  np.array([None] * length_sweep)
        data["peaks_plunger_V_cov"] =  np.array([None] * length_sweep)
        data["peaks_fit_popts"] =  np.array([None] * length_sweep)
        data["peaks_fit_intervall_half"] = intervall2_half_index # saves the index size of the fit intervall/2

        for trace_num in range(len(timestamps)):
            try:
                # bigger intervall, first fit
                popt, pcov = curve_fit(sech, np.arange(peak_index-intervall1_half_index, peak_index+intervall1_half_index, 1), 
                    data[nodes[2]][trace_num][peak_index-intervall1_half_index : peak_index+intervall1_half_index], p0, maxfev=self.max_iter)
                peak_fitted_index = int(round(popt[2]))

                try:
                    # smaller intervall, second fit around peak of first fit
                    if peak_fitted_index > intervall2_half_index and peak_fitted_index < (length_sweep-intervall2_half_index):
                        p1 = [a, b, peak_fitted_index, d]

                        popt1, pcov1 = curve_fit(sech, np.arange(peak_fitted_index-intervall2_half_index, peak_fitted_index+intervall2_half_index, 1),
                            data[nodes[2]][trace_num][peak_fitted_index-intervall2_half_index : peak_fitted_index+intervall2_half_index], p1, maxfev=self.max_iter)

                        data["peaks_plunger_V"][trace_num] = data[nodes[1]][int(round(popt1[2]))] # plunger gate voltage of peak 
                        data["peaks_value"][trace_num] = sech(popt1[2], *popt1) # lock-in value of fitted peak
                        data["peaks_plunger_V_cov"][trace_num] = pcov1 # covariance on index of peak
                        data["peaks_fit_popts"][trace_num] = popt1 # values of [a, b, c, d]

                        if pcov1[2][2] > 1:
                            print("COV TOO BIG  ", trace_num)  
                            data["peaks_plunger_V"][trace_num] = None 
                            data["peaks_value"][trace_num] = None
                            data["peaks_plunger_V_cov"][trace_num] = None
                            data["peaks_fit_popts"][trace_num] = None
                            
                    else:
                        print("Peak not found in first fit")
                        data["peaks_plunger_V"][trace_num] = None 
                        data["peaks_value"][trace_num] = None
                        data["peaks_plunger_V_cov"][trace_num] = None
                        data["peaks_fit_popts"][trace_num] = None

                      
                except RuntimeError:
                    print("RUNTIME ERROR second ", trace_num)
                    pass

            except RuntimeError:
                print("RUNTIME ERROR first ", trace_num)
                pass
        
