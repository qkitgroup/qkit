import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
from qkit.measure.utils.spectroscopy_tools import ModelGuidedExtremumTracker

def test_modelled_resonance_tracker():
    data = [simulate_detection(35, 4) for i in range(1000)]
    plt.hist(data, bins=range(30, 41, 1))
    plt.show()

def simulate_detection(true_peak, guess_deviation):
    frequencies = np.linspace(0, 100, 100)
    noise = np.random.normal(0, 0.3, len(frequencies))
    low_frequency_variations = sp.interpolate.CubicSpline([0, 50, 100], [0, -3, 3])
    peak = 2 * np.exp(- (frequencies - true_peak) ** 2 / (2 * 1 ** 2))
    signal = low_frequency_variations(frequencies) + noise + peak
    tracker = ModelGuidedExtremumTracker(
        lambda: true_peak + guess_deviation, fallback_phrases=['q0'],
        bias_scale=20, filter_scale=10
    )
    return tracker._find_peak(signal, frequencies)