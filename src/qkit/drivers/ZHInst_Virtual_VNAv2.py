from qkit.core.instrument_basev2 import ModernInstrument, QkitFunction
from qkit.drivers.AbstractVNA import AbstractVNA
from qkit.drivers.ZHInst_SHFSG import ZHInst_SHFSG
from qkit.drivers.ZHInst_UHFQA import ZHInst_UHFQA

import math

from zhinst.toolkit import TriggerMode, Alignment, SequenceType

import numpy as np

MAXIMUM_FREQUENCY = (8.5 + 0.65)*1e9
MAXIMUM_BANDWIDTH = (0.65)*1e9

MINIMUM_UHFQA_FREQUENCY = 50e6

class ZHInst_Virtual_VNAv2(ModernInstrument, AbstractVNA):

    """
    A Virtual VNA based on ZurichInstruments devices.
    Uses the SHFSG to generate the RF signal modulated by the IQ mixer connected to the UHFQA.

    We expect port 7 of the SHFSG to provide the RF signal.
    """
    def __init__(self, name, uhfqa: ZHInst_UHFQA, shfsg: ZHInst_SHFSG, **kwargs):
        super().__init__(name, tags=['virtual'], **kwargs)
        self.discover_capabilities()

        self.uhfqa = uhfqa
        self.shfsg = shfsg
        self.period = 10e-6
        self.repetitions = 512
        self.integration_length = 4096
        self.output_power = 0
        self.amplitude_factor = 1.0

        self._frequencies = np.ndarray([], dtype=float)
        self._i_q_data = np.ndarray([], dtype=float)

    @QkitFunction
    def configure_frequency_range(self, lower_freq: float, upper_freq: float, steps: int):
        assert 0 < lower_freq < upper_freq < MAXIMUM_FREQUENCY, "Frequency bounds invalid! (Too large? Order?)"
        assert 0 < steps, "Step count must be larger than zero!"
        self._frequencies = np.linspace(lower_freq, upper_freq, steps)

    @QkitFunction
    def configure_pulses(self, period = 10e-6, repetitions = 512, integration_length=4096):
        self.period = 10e-6
        self.repetitions = 512
        self.integration_length = 4096

    @QkitFunction
    def set_output_power(self, power):
        base_power = math.ceil(power / 5.0) * 5
        self.amplitude_factor = 10 ** (-0.5 * (base_power - power))
        self.output_power = base_power
        self.shfsg.nodetree.sgchannels[7].output.range(self.output_power)
        
        expected_voltage = 10**(0.5 * ((power / 10) - 1))
        self.uhfqa.nodetree.sigins[0].range(expected_voltage)
        self.uhfqa.nodetree.sigins[1].range(expected_voltage)

    @QkitFunction
    def get_freqpoints(self) -> np.ndarray:
        return self._frequencies

    @QkitFunction
    def get_tracedata(self, RealImag = None) -> tuple((np.ndarray, np.ndarray)):
        if not RealImag:
            signal = (self._i_q_data[:, 0] + 1.0j * self._i_q_data[:, 1])
            return np.abs(signal), np.angle(signal)
        else:
            return self._i_q_data[:, 0], self._i_q_data[:, 1]

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
        self.uhfqa.nodetree.qa.result.source(2)
        self.uhfqa.nodetree.sigouts[0].on(1)
        self.uhfqa.nodetree.sigouts[1].on(1)

        self.uhfqa.nodetree.awg.outputs[1].amplitude(-1.0)
        self.uhfqa.arm(length=self.repetitions, averages=1)
        # Configure output
        base, digital = self._get_shfsg_frequencies()
        out_channel = self.shfsg.nodetree.sgchannels[7]
        synth = self.shfsg.nodetree.synthesizers[out_channel.synthesizer()]

        out_channel.output.range(self.output_power)
        synth.centerfreq(base)
        out_channel.awg.modulation.enable(1)
        out_channel.oscs[0].freq(digital)

        self.uhfqa.compile_program(
            sequence_type=SequenceType.PULSED_SPEC,
            period=self.period,
            repetitions=self.repetitions,
            trigger_mode=TriggerMode.NONE,
            alignment=Alignment.START_WITH_TRIGGER
        )
        
        self.shfsg.nodetree.sgchannels[7].output.on(1)

        self.uhfqa.nodetree.qa.result.source(2)
        self.uhfqa.nodetree.sigouts[0].on(1)# Enable the outputs
        self.uhfqa.nodetree.sigouts[1].on(1)
        self.uhfqa.nodetree.awg.outputs[1].amplitude(-1.0)

        self._i_q_data = np.zeros(shape=(len(self.get_freqpoints()), 2), dtype=complex)

    @QkitFunction
    def start_measurement(self):
        print("Run")
        # Configure upper side band modulation
        out_channel = self.shfsg.nodetree.sgchannels[7]
        out_channel.sine.oscselect(0)
        out_channel.sine.i.enable(True)
        out_channel.sine.i.sin.amplitude(0.0)
        out_channel.sine.i.cos.amplitude(0.9 * self.amplitude_factor)
        out_channel.sine.q.enable(True)
        out_channel.sine.q.sin.amplitude(0.9 * self.amplitude_factor)
        out_channel.sine.q.cos.amplitude(0.0)
        self.uhfqa.arm(length=self.repetitions, averages=1)

        uhfqa_frequencies = self.get_freqpoints() - (self.get_freqpoints()[0] - MINIMUM_UHFQA_FREQUENCY)

        for i, f in enumerate(uhfqa_frequencies):
            self.uhfqa.nodetree.osc.freq(f)  # set modulation frequency
            for j in (0, 1):
                self.uhfqa.set_readout_frequency(f, j)
            
            self.uhfqa.run()                                    # start readout AWG                            # wait until trigger AWG has finished
            data = self.uhfqa.get_qubit_result()
            i_avg_result = np.mean(data[0]) # average the result vector
            q_avg_result = np.mean(data[1])
            self._i_q_data[i, :] = [i_avg_result, q_avg_result]         # append to results

    @QkitFunction
    def ready(self) -> bool:
        return True

    @QkitFunction
    def post_measurement(self):
        self.uhfqa.nodetree.sigouts[0].on(0)
        self.uhfqa.nodetree.sigouts[1].on(0)
        self.shfsg.nodetree.sgchannels[7].output.on(0)

    @QkitFunction
    def get_sweeptime(self, query=True):
        return 90

    @QkitFunction
    def get_sweeptime_averages(self):
        return 90
        