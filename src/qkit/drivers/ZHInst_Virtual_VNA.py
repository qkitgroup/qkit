from qkit.core.instrument_base import Instrument
from qkit.drivers.AbstractVNA import AbstractVNA
from qkit.drivers.ZHInst_SHFSG import ZHInst_SHFSG
from qkit.drivers.ZHInst_UHFQA import ZHInst_UHFQA

from zhinst.toolkit import TriggerMode, Alignment, SequenceType

import numpy as np

MAXIMUM_FREQUENCY = (8.5 + 0.65)*1e9
MAXIMUM_BANDWIDTH = (0.65)*1e9

MINIMUM_UHFQA_FREQUENCY = 50e6

class ZHInst_Virtual_VNA(Instrument, AbstractVNA):

    """
    A Virtual VNA based on ZurichInstruments devices.
    Uses the SHFSG to generate the RF signal modulated by the IQ mixer connected to the UHFQA.

    We expect port 7 of the SHFSG to provide the RF signal.
    """
    def __init__(self, name, uhfqa: ZHInst_UHFQA, shfsg: ZHInst_SHFSG, **kwargs):
        super().__init__(name, tags=['virtual'], **kwargs)
        self.register_vna_functions()

        self.uhfqa = uhfqa
        self.shfsg = shfsg
        self.period = 10e-6
        self.repetitions = 512
        self.integration_length = 4096

        self._frequencies = np.ndarray([], dtype=float)
        self._i_q_data = np.ndarray([], dtype=float)

    def configure_frequency_range(self, lower_freq: float, upper_freq: float, steps: int):
        assert 0 < lower_freq < upper_freq < MAXIMUM_FREQUENCY, "Frequency bounds invalid! (Too large? Order?)"
        assert 0 < steps, "Step count must be larger than zero!"
        self._frequencies = np.linspace(lower_freq, upper_freq, steps)

    def configure_pulses(self, period = 10e-6, repetitions = 512, integration_length=4096):
        self.period = 10e-6
        self.repetitions = 512
        self.integration_length = 4096

    def get_freqpoints(self) -> np.ndarray:
        return self._frequencies

    def get_tracedata(self, RealImag = None) -> tuple((np.ndarray, np.ndarray)):
        if not RealImag:
            signal = (self._i_q_data[:, 0] + 1.0j * self._i_q_data[:, 1])
            return np.abs(signal), np.angle(signal)
        else:
            return self._i_q_data[:, 0], self._i_q_data[:, 1]

    def _get_shfsg_frequencies(self) -> tuple((float, float)):
        """
        Returns (SHF-Upconversion center frequency, Digital Modulation Frequency)
        """
        shfsg_out_freq = self.get_freqpoints()[0] - MINIMUM_UHFQA_FREQUENCY
        base_mod = int(shfsg_out_freq / 0.5e9) * 0.5e9
        return base_mod, shfsg_out_freq - base_mod

    def pre_measurement(self):
        print("Setup")
        # Configure output
        base, digital = self._get_shfsg_frequencies()
        self.shfsg.set_sgchannels_7_sgchannels_output_range(0)
        self.shfsg.set_synthesizers_3_synthesizers_centerfreq(base)
        self.shfsg.set_sgchannels_7_sgchannels_awg_modulation_enable(1)
        self.shfsg.set_sgchannels_7_sgchannels_oscs_0_freq(digital)

        # Configure upper side band modulation
        self.shfsg.set_sgchannels_7_sgchannels_sine_oscselect(0)
        self.shfsg.set_sgchannels_7_sgchannels_sine_i_enable(1)
        self.shfsg.set_sgchannels_7_sgchannels_sine_i_sin_amplitude(0.0)
        self.shfsg.set_sgchannels_7_sgchannels_sine_i_cos_amplitude(0.9)
        self.shfsg.set_sgchannels_7_sgchannels_sine_q_enable(1)
        self.shfsg.set_sgchannels_7_sgchannels_sine_q_sin_amplitude(0.9)
        self.shfsg.set_sgchannels_7_sgchannels_sine_q_cos_amplitude(0.0)

        self.uhfqa.compile_program(
            sequence_type=SequenceType.PULSED_SPEC,
            period=self.period,
            repetitions=self.repetitions,
            trigger_mode=TriggerMode.NONE,
            alignment=Alignment.START_WITH_TRIGGER
        )
        self.shfsg.set_sgchannels_7_sgchannels_output_on(1)
        self.uhfqa.set_sigouts_0_sigouts_on(1) # Enable the outputs
        self.uhfqa.set_sigouts_1_sigouts_on(1)

        self.uhfqa.set_outputs_1_awg_outputs_amplitude(-1.0)

        self._i_q_data = np.zeros(shape=(len(self.get_freqpoints()), 2), dtype=complex)

    def start_measurement(self):
        print("Run")
        self.uhfqa.arm(length=self.repetitions, averages=1)

        uhfqa_frequencies = self.get_freqpoints() - (self.get_freqpoints()[0] - MINIMUM_UHFQA_FREQUENCY)

        for i, f in enumerate(uhfqa_frequencies):
            self.uhfqa.set_osc_freq(f)                            # set modulation frequency
            self.uhfqa.set_readout_frequency0(f)
            self.uhfqa.set_readout_frequency1(f)
            self.uhfqa.set_qa_integration_length(self.integration_length)
            self.uhfqa.arm()                                      # reset the readout
            self.uhfqa.run()                                    # start readout AWG                            # wait until trigger AWG has finished
            data = self.uhfqa.get_qubit_result()
            i_avg_result = np.mean(data[0]) # average the result vector
            q_avg_result = np.mean(data[1])
            self._i_q_data[i, :] = [i_avg_result, q_avg_result]         # append to results

    def ready(self) -> bool:
        return True

    def post_measurement(self):
        print("Stop")
        self.uhfqa.set_sigouts_0_sigouts_on(0) # Enable the outputs
        self.uhfqa.set_sigouts_1_sigouts_on(0)
        self.shfsg.set_sgchannels_7_sgchannels_output_on(0)

    def get_sweeptime(self, query=True):
        return 90

    def get_sweeptime_averages(self):
        return 90
        