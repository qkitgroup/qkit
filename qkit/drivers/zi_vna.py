from qkit.core.instrument_basev2 import ModernInstrument, QkitFunction
from qkit.drivers.zi_shfsg import zi_shfsg
from qkit.drivers.zi_uhfqa import zi_uhfqa
from qkit.core.instrument_base import Instrument
import math
import time

import numpy as np

MAXIMUM_FREQUENCY = 9.1 * 1e9

MINIMUM_UHFQA_FREQUENCY = 1e6


class zi_vna(Instrument):
    """
    A Virtual VNA based on ZurichInstruments devices.
    Uses the SHFSG to generate the RF signal modulated by the IQ mixer connected to the UHFQA.
    """

    def __init__(self, name, uhfqa: zi_uhfqa, shfsg: zi_shfsg, **kwargs):
        super().__init__(name, tags=['virtual'], **kwargs)
        self.uhfqa = uhfqa
        self.shfsg = shfsg
        self._averages = 512
        self.nop = 17
        self._uhfqa_freqs = [70e6, 70.5e6, 71e6, 71.5e6,  72e6, 72.5e6, 73e6, 73.5e6, 74e6, 74.5e6, 75e6, 75.5e6, 76e6, 76.5e6, 77e6, 77.5e6, 78e6]
        self._frequencies = np.ndarray([], dtype=float)
        self._i_q_data = np.ndarray([], dtype=float)
        print("ziVNA created.")
        self._shfsgfreq = zi_shfsg.do_get_ch3_centerfreq(zi_shfsg)
        self.shfsg.do_set_ch8_centerfreq(5.5e9)

        # Implement functions
        self.add_function('get_freqpoints')
        self.add_function('get_tracedata')
        self.add_function('avg_clear')
        #self.add_function('hold')
        self.add_function('get_sweeptime')
        self.add_function('get_sweeptime_averages')
        self.add_function('pre_measurement')
        self.add_function('start_measurement')
        self.add_function('ready')
        self.add_function('post_measurement')


    def get_all(self):
        self.get_nop()
        self.get_power()
        self.get_centerfreq()
        self.get_startfreq()
        self.get_stopfreq()
        self.get_span()
        self.get_averages()
        self.get_freqpoints()
        self.get_sweeptime()
        self.get_sweeptime_averages()



    @QkitFunction
    def configure_frequency_range(self, lower_freq: float, upper_freq: float, steps: int):
        assert 0 < lower_freq < upper_freq < MAXIMUM_FREQUENCY, "Frequency bounds invalid! (Too large? Order?)"
        assert 0 < steps, "Step count must be larger than zero!"
        print(np.floor(10*lower_freq/1e9)/10*1e9-500e6)
        self.shfsg.do_set_ch3_centerfreq(np.floor(10*lower_freq/1e9)/10*1e9-500e6)
        self._frequencies = np.linspace(lower_freq, upper_freq, steps)
        self._uhfqa_freqs = self._frequencies-np.floor(10*lower_freq/1e9)/10*1e9
        if(np.max(self._uhfqa_freqs)>599e6 or np.min(self._uhfqa_freqs)<0e6):
            print("Fatal error, range might be too large. In any case, the UHFQA got invalid frequencies to set.")


    @QkitFunction
    def get_averages(self):
        return self._averages

    @QkitFunction
    def set_averages(self, averages):
        self._averages = averages

    def avg_clear(self):
        return True

    def get_Average(self):
        return True


    @QkitFunction
    def get_startfreq(self):
        return self._shfsgfreq+self._uhfqa_freqs[0]

    @QkitFunction
    def get_stopfreq(self):
        return self._shfsgfreq+self._uhfqa_freqs[-1]

    @QkitFunction
    def get_centerfreq(self):
        return self.get_stopfreq()-self.get_startfreq()



    @QkitFunction
    def set_output_power(self, power):
        self.shfsg.do_set_ch3_range(power)

    @QkitFunction
    def get_freqpoints(self) -> np.ndarray:
        return self._frequencies

    @QkitFunction
    def get_span(self):
        if len(self._uhfqa_freqs)>1:
            return self._uhfqa_freqs[0]-self._uhfqa_freqs[-1]
        else:
            return 0
    @QkitFunction
    def get_nop(self):
        return len(self._uhfqa_freqs)

    @QkitFunction
    def get_power(self):
        return self.shfsg.do_get_ch1_range()



    @QkitFunction
    def get_tracedata(self, RealImag=None) -> tuple((np.ndarray, np.ndarray)):
        if not RealImag:
            return np.abs(self._i_q_data), np.angle(self._i_q_data)
        else:
            return np.real(self._i_q_data), np.imag(self._i_q_data)

    @QkitFunction
    def _get_shfsg_frequencies(self) -> tuple((float, float)):
        """
        Returns (SHF-Upconversion center frequency, Digital Modulation Frequency)
        """
        shfsg_out_freq = self.get_freqpoints()[0] - MINIMUM_UHFQA_FREQUENCY
        base_mod = int(shfsg_out_freq / 0.5e9) * 0.5e9
        return base_mod, shfsg_out_freq - base_mod

    @QkitFunction
    def pre_measurement(self):

        self.uhfqa.do_set_resultsource(7)
        self.uhfqa.set_result(1)

        self.shfsg.do_set_ch1_rerun(0)
        time.sleep(0.5)
        self._i_q_data = np.zeros(shape=(self.get_freqpoints().size, 2), dtype=complex)
        freqqs = self._uhfqa_freqs


        self.uhfqa.do_set_resultlength(len(self._uhfqa_freqs))
        self.uhfqa.do_set_resultaverages(self._averages)


        self.shfsg.setup_triggering(300)
        self.shfsg.twotone_pulse(42e6, 300)
        time.sleep(0.1)


    @QkitFunction
    def start_measurement(self):
        print("Run")
        time.sleep(0.1)
        results = []
        self.uhfqa.do_set_resultlength(self.get_nop())
        self.uhfqa.do_set_resultaverages(self._averages)
        self.uhfqa.do_set_rerun(0)


        for uhfqa_freq in self._uhfqa_freqs:

            self.shfsg.do_set_internaltrigger_on(0)
            self.shfsg.do_set_internaltrigger_repetitions(self._averages)
            self.shfsg.do_set_internaltrigger_holdoff(50e-6)
            self.shfsg.sync()
            self.uhfqa.sync()


            self.uhfqa.set_uhfqa_freq(uhfqa_freq)
            time.sleep(0.4)
            self.shfsg.do_set_internaltrigger_on(1)
            time.sleep(0.1)
            while(self.shfsg.get_internaltrigger_progress()<1):
                time.sleep(0.1)
            self.uhfqa.sync()
            self.shfsg.sync()


            time.sleep(0.3)

            #print(self.uhfqa.get_result())
            #clear_output(wait=True)
            #iqs.append(iq)
            #results.append(self.uhfqa.get_result())

        time.sleep(0.1)
        self._i_q_data = self.uhfqa.get_result()


    @QkitFunction
    def ready(self) -> bool:
        time.sleep(1)
        return self.uhfqa.isReady()

    @QkitFunction
    def post_measurement(self):
        return True

    @QkitFunction
    def get_sweeptime(self, query=True):
        return -1

    @QkitFunction
    def get_sweeptime_averages(self):
        return -1
