import numpy as np


def const(amplitude, length):
    const_wf = amplitude * np.ones(length)
    return const_wf

def const_zeroed(amplitude, zeros_start, zeros_end, length):

    const_zero_padded_wave = amplitude * np.ones(length)
    const_zero_padded_wave[:zeros_start] = 0.0
    const_zero_padded_wave[- zeros_end:] = 0.0

    return const_zero_padded_wave

def gauss(amplitude, delta_t, sigma, length):

    t = np.linspace(-length / 2, length / 2, length)
    gauss_wave = amplitude * np.exp(-((t - delta_t) ** 2) / (2 * sigma ** 2))

    return gauss_wave

def plot_pulses():

    pass



