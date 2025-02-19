from qkit.core.instrument_base import Instrument
from zhinst.toolkit import Session

class ZHInstSHFQC(Instrument):

    def __init__(self, name, devID, server='localhost', **kwargs):
        super().__init__(name, **kwargs)
        self._session = Session(server)
        self._device = self._session.connect_device(devID)
        self._sweeper = self._session.modules.create_shfqa_sweeper()
        self._sweeper.device(self._device)
        self._sweeper.use_sequencer = True

        self.add_function(self.set_sweep_range.__name__)
        self.add_function(self.set_sweep_amplitude.__name__)
        self.add_function(self.set_sweep_integration.__name__)
        self.add_function(self.set_rf_in_out.__name__)
        self.add_function(self.in_out_enable.__name__)
        self.add_function(self.measure.__name__)


    def set_sweep_range(self, start_freq, stop_freq, num_points):
        center = min(int((start_freq + stop_freq) / 2 / 1e8) * 1e8, 8e9) # Can be set with 100Mhz precission
        self._sweeper.rf.center_freq(center)
        self._sweeper.sweep.start_freq(start_freq - center)
        self._sweeper.sweep.stop_freq(stop_freq - center)
        self._sweeper.sweep.num_points(num_points)

    def set_sweep_amplitude(self, amp):
        self._sweeper.sweep.oscillator_gain(amp)
    
    def set_sweep_integration(self, delay, int_time, wait_after, averages):
        self._sweeper.average.integration_delay(delay)
        self._sweeper.average.integration_time(int_time)
        self._sweeper.sweep.wait_after_integration(wait_after)
        self._sweeper.average.num_average(averages)
        self._sweeper.average.mode('sequential')

    def set_rf_in_out(self, dB_in, dB_out):
        self._sweeper.rf.channel(0)
        self._sweeper.rf.input_range(dB_in)
        self._sweeper.rf.output_range(dB_out)
    
    def in_out_enable(self, enable: bool):
        val = 1 if enable else 0
        with self._device.set_transaction():
            self._device.qachannels[0].input.on(val)
            self._device.qachannels[0].output.on(val)
            self._device.qachannels[0].output.rflfinterlock(1)

    def measure(self):
        result = self._sweeper.run()
        return result