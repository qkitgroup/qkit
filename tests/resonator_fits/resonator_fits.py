import pytest

def test_circlefit():
    from qkit.analysis.resonatorV2 import CircleFit
    from qkit.storage.store import Data # for reading file
    import numpy as np

    datafile = Data("C:/Users/mariu/Desktop/Ordner/Studium/qkit_development/tests/resonator_fits/SVSEWX_VNA_tracedata.h5")
    freq = np.array(datafile.data.frequency)
    amp = np.array(datafile.data.amplitude)
    pha = np.array(datafile.data.phase)

    my_circle_fit = CircleFit(n_ports=2) # notch port
    my_circle_fit.do_fit(freq, amp, pha)

    print(my_circle_fit.extract_data)

    # check reasonable qc and f_res in 2 sigma interval
    assert my_circle_fit.extract_data["Qc"] > 0
    assert (my_circle_fit.extract_data["f_res"] > 5.57019e9*(1 - 2/334)) & (my_circle_fit.extract_data["f_res"] < 5.57019e9*(1 + 2/334))

    if __name__ == "__main__":
        import matplotlib.pyplot as plt

        plt.plot(freq, amp, "ko")
        plt.plot(my_circle_fit.freq_fit, my_circle_fit.amp_fit, "r-")
        plt.title("Amplitude")
        plt.show()

        plt.plot(freq, pha, "ko")
        plt.plot(my_circle_fit.freq_fit, my_circle_fit.pha_fit, "r-")
        plt.title("Phase")
        plt.show()

        plt.plot(amp*np.cos(pha), amp*np.sin(pha), "ko")
        plt.plot(my_circle_fit.amp_fit*np.cos(my_circle_fit.pha_fit), my_circle_fit.amp_fit*np.sin(my_circle_fit.pha_fit), "r-")
        plt.title("IQ Circle")
        plt.show()

if __name__ == "__main__":
    test_circlefit()