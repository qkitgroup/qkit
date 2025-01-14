from typing import Any, Dict, List

import numpy as np
from qkit.analysis.semiconductor.main.fit_functions import sech
from scipy.signal import find_peaks, peak_widths
from scipy.optimize import curve_fit

class ItsAllDanielsFaultError(Exception):
    pass

class Peak_fit:
    """Class for peak fits. Takes a callable argument f and assumes f(x, height, width, position) -> Peak.
    width ist the full-width-half-maximum of Peak."""
    def __init__(self, fit_func):
        self.fit_func = fit_func
        self.min_peak_height = 0.002
        self.min_peak_width = 2
        self.min_peak_distance = 30
        self.fit_interval_peak_relheight = 0.5
        
    @property
    def fit_interval_peak_relheight(self):
        return self._fit_interval_peak_relheight
    @fit_interval_peak_relheight.setter
    def fit_interval_peak_relheight(self, new_height):
        self._fit_interval_peak_relheight = new_height
        if new_height == 0.5: self.find_fit_interval = self._calc_fit_interval_peak_width
        else: self.find_fit_interval = self._calc_fit_interval_rel_height
    
    def construct_guess(self, single_trace):
        self.peak_pos, params = find_peaks(single_trace, height = self.min_peak_height,\
                                           width = self.min_peak_width,\
                                           distance = self.min_peak_distance)
        self.peak_heights = params["peak_heights"]
        self.peak_fwhms = peak_widths(single_trace, self.peak_pos, rel_height = 0.5) [0]
    
    def _calc_fit_interval_rel_height(self, single_trace):
        self.fit_idxs_left, self.fit_idxs_right = np.rint(\
                                                peak_widths(single_trace, self.peak_pos, \
                                                rel_height = self.fit_interval_peak_relheight)\
                                                [2:]).astype(np.int_)
    
    def _calc_fit_interval_peak_width(self, single_trace):
        self.fit_idxs_left = np.rint(self.peak_pos - self.peak_fwhms / 2).astype(np.int_)
        self.fit_idxs_right = np.rint(self.peak_pos + self.peak_fwhms / 2).astype(np.int_)
    
    def fit(self, single_trace):
        self.construct_guess(single_trace)
        self.find_fit_interval(single_trace)
        
        x = range(len(single_trace))
        popts, covs = [], []
        
        for i in range(len(self.peak_pos)):
            guess = (self.peak_heights[i], self.peak_fwhms[i], self.peak_pos[i])
            try:
                popt, cov = curve_fit(self.fit_func, x[self.fit_idxs_left[i] : self.fit_idxs_right[i]],
                                    single_trace[self.fit_idxs_left[i] : self.fit_idxs_right[i]], 
                                    p0 = guess, maxfev = 10000)
            except TypeError:
                raise TypeError(f"{__name__}: Fit interval for peak {i} does not contain enough data points. Reconsider the min_peak_width.")
            popts.append(popt)
            covs.append(cov)
            
        return popts, covs

def sech_fwhm(x, a, b, c):
    return sech(x, a, b /2.634, c)

class Analyzer:
    def __init__(self, matrix_to_analyze, timestamps, gate_axis, peak_function = sech_fwhm) -> None:
        self.pf = Peak_fit(peak_function)

        self.matrix_to_analyze = matrix_to_analyze
        self.timestamps = timestamps
        self.gate_axis = gate_axis

        self.rel_jump_height = 0.2
        self.f_clock = 1.8e9
        self.LR_offset = 0
    
    @property
    def matrix_to_analyze(self):
        return self._matrix_to_analyze
    @matrix_to_analyze.setter
    def matrix_to_analyze(self, new_matrix):
        if not isinstance(new_matrix, np.ndarray):
            raise TypeError(f"{__name__}: Invalid data matrix. Must be a 2D numpy array.")
        if new_matrix.ndim != 2:
            raise ValueError(f"{__name__}: Invalid data matrix. Must be a 2D numpy array.")
        self._matrix_to_analyze = new_matrix

    @property
    def timestamps(self):
        return self._timestamps
    @timestamps.setter
    def timestamps(self, new_stamps):
        if not isinstance(new_stamps, np.ndarray):
            raise TypeError(f"{__name__}: Invalid timestamps. Must be a 2D numpy array.")
        if new_stamps.shape != self.matrix_to_analyze.shape:
            raise ValueError(f"{__name__}: Invalid timestamps. Must have the same shape as matrix_to_analyze.")
        self._timestamps = new_stamps

    @property
    def gate_axis(self):
        return self._gate_axis

    @gate_axis.setter
    def gate_axis(self, new_axis):
        if not isinstance(new_axis, np.ndarray):
            raise TypeError(f"{__name__}: Invalid gate_axis. Must be a numpy array.")
        if len(new_axis) != len(self.matrix_to_analyze[0]):            
            raise ValueError(f"{__name__}: Invalid gate_axis. Must have the same length as a trace from matrix_to_analyze.")
        self._gate_axis = new_axis
    
    def _append_to_nearest(self, tracked_positions, position):
        distances = []
        for last_positions in tracked_positions:
            distances.append(abs(np.average(last_positions[-5:]) - position))

        idx = distances.index(min(distances))     
        tracked_positions[idx].append(position)

    def _append_to_nearest_2(self, tracked_positions, positions):
        forbidden_tracks = []
        for position in positions:
            distances = []
            for last_positions in tracked_positions:
                distances.append(abs(np.average(last_positions[-5:]) - position))
            idx = distances.index(min(distances))
            if idx not in forbidden_tracks:
                tracked_positions[idx].append(position)
            forbidden_tracks.append(idx)
    
    def _find_nth_smallest(self, array, n):
        nth_smallest = np.partition(array, n)[n]
        idx = np.where(array == nth_smallest)[0][0]
        return idx

    def _append_to_nearest_3(self, peak_tracks, positions):
        forbidden_tracks = []
        for peak_track in peak_tracks:
            #Calculate the distance of each newly found peak to the average of the
            #last five positions.
            distances = []
            peak_track_avg = np.average(peak_track[-5:])
            for position in positions:
                distances.append(peak_track_avg - position)

            distances = np.array(distances)
            abs_distances = abs(distances)

            #Append the value to one of the peak_tracks based on conditions:

            #Did the peak position change by more then self.rel_jump_height * 100 percent?
            sub_cond11 = (abs_distances > (peak_track_avg * self.rel_jump_height)).all()
            sub_cond12 = (distances < 0).any()
            sub_cond13 = len(distances) >= 2
            condition1 = sub_cond11 and sub_cond12 and sub_cond13
            if condition1:
                #If this is the case, the jump went up therefore append the closest position
                #above the current one.
                idx = self._find_nth_smallest(abs_distances, 1)
            #elif condition2:
            #   ...
            else:
                idx = abs_distances.argmin()
            
            if idx not in forbidden_tracks:
                peak_track.append(positions[idx])
            forbidden_tracks.append(idx)
    
    def _translate_samples(self, tracked_positions : List[List[float]]) -> List[List[float]]:
        v_offset = self.gate_axis[0]
        v_step = self.gate_axis[1] - v_offset
        translated_tracks = []
        for track in tracked_positions:
            trans_track = v_step * np.array(track) + v_offset
            translated_tracks.append(trans_track)
        return translated_tracks

    def _create_time_axis_avg(self):
        durations = []
        for timestamps in self.timestamps:
            duration_of_trace = timestamps[-1] - timestamps[0]
            durations.append(duration_of_trace)
        translated_durations = np.array(durations)/self.f_clock
        avg_duration = np.average(translated_durations)
        time_axis = np.arange(0, len(translated_durations)) * avg_duration
        return time_axis
        
    def analyze(self) ->  Dict[str, Any]:
        raw = self.matrix_to_analyze

        tracked_positions = []        
        trace = self.matrix_to_analyze[0]
        peak_pars, _ = self.pf.fit(trace)
        for peak_par in peak_pars:
            peak_pos = peak_par[2]
            tracked_positions.append([peak_pos])
        
        for trace in raw[1:]:
            peak_pars, _ = self.pf.fit(trace)
            peak_pos = [peak_par[2] for peak_par in peak_pars]            
            self._append_to_nearest_3(tracked_positions, peak_pos)
        
        peak_pos = self._translate_samples(tracked_positions)
        time_axis = self._create_time_axis_avg()
        return {"tracked_peak_positions" : peak_pos, "time_axis" : time_axis}

def main():
    pass
if __name__ == "__main__":
    main()
# from scipy.signal import find_peaks, peak_widths
# from scipy.optimize import curve_fit
# from random import uniform

# def sech(x, a, b, c):
#     return a / np.cosh((x - c) / b)

# def multi_sech(x, *params):
#     y = np.zeros_like(x)
#     for i in range(0, len(params), 3):
#         a = params[i]
#         b = params[i+1]
#         c = params[i+2]
#         y = y + sech(x, a, b, c)
#     return y

# def create_jitter(amplitude):
#     return uniform(-amplitude, amplitude)

# xdata = np.linspace(-40, 40, 1000) # create x_axis
# x_step = xdata[1] - xdata[0]
# rng = np.random.default_rng()
# y_noise = 0
# y_noise = 0.1 * rng.normal(size=xdata.size) # create some noise

# jitter_ampl = 0
# y = multi_sech(xdata, 1, 1, 30 + create_jitter(jitter_ampl),
#                1, 1, 15 + create_jitter(jitter_ampl),
#                1, 3, -30 + create_jitter(jitter_ampl),
#                1, 1, -15 + create_jitter(jitter_ampl))
# ydata = y + y_noise

# peak_pos, params = find_peaks(ydata, height = 0.5, width = 6)
# results = peak_widths(ydata, peak_pos, rel_height=0.5)
# peak_widths = results[0] * x_step / 2.634
# no_peaks = len(peak_pos)
# print(f"peak_widths: {peak_widths}")
# print(f"peak_pos: {xdata[peak_pos]}")
# lower_bounds = [0, 0, -np.inf] * no_peaks
# upper_bounds = [np.inf, np.inf, np.inf] * no_peaks
# bounds = (lower_bounds, upper_bounds)
# print(bounds)
# guess = []
# for peak, height, width in zip(xdata[peak_pos], params["peak_heights"], peak_widths):
#     guess.extend([height, width, peak])
# print(guess)
# #guess  = [1, 1, 0, 1, 1, 20, 1, 1, -8, 1, 1, -15]
# popt, pcov = curve_fit(multi_sech, xdata, ydata, p0 = guess, bounds = bounds, maxfev = 1000)

# plt.figure()
# plt.plot(np.arange(len(ydata)) * x_step - 40, ydata)
# plt.plot(xdata, multi_sech(xdata, *popt), 'r-')
# for i in range(len(results[1:][0])):
#     y = results[1:][0][i]
#     x_min = results[1:][1][i] * x_step + xdata[0]
#     x_max = results[1:][2][i] * x_step + xdata[0]
#     plt.hlines(y, x_min, x_max, color ="C2")
# print(popt)
