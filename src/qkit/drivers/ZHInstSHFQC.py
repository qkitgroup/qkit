from qkit.core.instrument_base import Instrument
from zhinst.toolkit import Session
import numpy as np
import math

class ZHInstSHFQC(Instrument):

    def __init__(self, name, devID, server='localhost', **kwargs):
        super().__init__(name, **kwargs)
        self._session = Session(server)
        self._device = self._session.connect_device(devID)
        self._sweeper = self._session.modules.create_shfqa_sweeper()
        self._sweeper.device(self._device)
        self._sweeper.use_sequencer = True
        self._synth = [self._device.sgchannels[i].synthesizer() for i in range(6)]

        self.add_parameter('averages',
                           type=int,
                           flags=Instrument.FLAG_GETSET,
                           minval=1,
                           maxval=65536,
                           tags=['sweep'])

        self.add_parameter('Average',
                           type=bool,
                           flags=Instrument.FLAG_GET)

        self.add_parameter('startfreq',
                           type=float,
                           flags=Instrument.FLAG_GET,
                           minval=0,
                           maxval=20e9,
                           units='Hz',
                           tags=['sweep'])

        self.add_parameter('stopfreq',
                           type=float,
                           flags=Instrument.FLAG_GET,
                           minval=0,
                           maxval=20e9,
                           units='Hz',
                           tags=['sweep'])

        self.add_parameter('centerfreq',
                           type=float,
                           flags=Instrument.FLAG_GET,
                           minval=0,
                           maxval=20e9,
                           units='Hz',
                           tags=['sweep'])

        self.add_parameter('span',
                           type=float,
                           flags=Instrument.FLAG_GET,
                           minval=0,
                           maxval=20e9,
                           units='Hz',
                           tags=['sweep'])

        self.add_parameter('nop',
                           type=int,
                           flags=Instrument.FLAG_GETSET,
                           minval=1,
                           maxval=100001,
                           tags=['sweep'])

        self.add_parameter('sweep_type',
                           type=str,
                           flags=Instrument.FLAG_GET,
                           tags=['sweep'])

        self.add_parameter('sweeptime',
                           type=float,
                           flags=Instrument.FLAG_GET,
                           minval=0,
                           maxval=1e3,
                           units='s',
                           tags=['sweep'])
            
        self.add_parameter('sweeptime_averages',
                           type=float,
                           flags=Instrument.FLAG_GET,
                           minval=0,
                           maxval=1e3,
                           units='s',
                           tags=['sweep'])
        
        self.add_parameter('frequency',
                           type=float,
                           flags=Instrument.FLAG_GETSET,
                           minval=0,
                           maxval=9e9,
                           units='Hz',
                           tags=['mw'],
                           channels=(1, 6))
        
        self.add_parameter('power',
                           type=float,
                           flags=Instrument.FLAG_GETSET,
                           minval=-35,
                           maxval=10,
                           units='dBm',
                           tags=['mw'],
                           channels=(1, 6))
        
        self.add_parameter('status',
                           type=bool,
                           flags=Instrument.FLAG_GETSET,
                           tags=['mw'],
                           channels=(1, 6))


        self.add_function(self.set_sweep_range.__name__)
        self.add_function(self.set_sweep_amplitude.__name__)
        self.add_function(self.set_sweep_integration.__name__)
        self.add_function(self.set_rf_in_out.__name__)
        self.add_function(self.in_out_enable.__name__)
        self.add_function(self.start_measurement.__name__)
        self.add_function(self.get_tracedata.__name__)
        self.add_function(self.get_freqpoints.__name__)
        self.add_function(self.avg_clear.__name__)
        self.add_function(self.get_all.__name__)

    def get_all(self):  # Spectroscopy Compatibility
        for param in self._parameters:
            self.get(param)


    def set_sweep_range(self, start_freq, stop_freq):
        assert stop_freq > start_freq
        center = min(int((start_freq + stop_freq) / 2 / 1e8) * 1e8, 8e9) # Can be set with 100Mhz precission
        self._sweeper.rf.center_freq(center)
        self._sweeper.sweep.start_freq(start_freq - center)
        self._sweeper.sweep.stop_freq(stop_freq - center)

    def do_get_Average(self):  # Spectroscopy Compatibility
        return True

    def do_get_sweep_type(self):  # Spectroscopy Compatibility
        return 'LIN' # The device can do non-linear sweeps, but is not implemented here.
    
    def do_get_startfreq(self):  # Spectroscopy Compatibility
        return self._sweeper.sweep.start_freq() + self._sweeper.rf.center_freq()
    
    def do_get_stopfreq(self):  # Spectroscopy Compatibility
        return self._sweeper.sweep.stop_freq() + self._sweeper.rf.center_freq()
    
    def do_get_centerfreq(self):  # Spectroscopy Compatibility
        return (self.get_startfreq() + self.get_stopfreq()) / 2
    
    def do_get_span(self):  # Spectroscopy Compatibility
        return self.get_stopfreq() - self.get_startfreq()

    def do_set_nop(self, nop):  # Spectroscopy Compatibility
        self._sweeper.sweep.num_points(nop)

    def do_get_nop(self):  # Spectroscopy Compatibility
        return self._sweeper.sweep.num_points()

    def set_sweep_amplitude(self, amp): 
        self._sweeper.sweep.oscillator_gain(amp)
    
    def set_sweep_integration(self, delay, int_time, wait_after):
        self._sweeper.average.integration_delay(delay)
        self._sweeper.average.integration_time(int_time)
        self._sweeper.sweep.wait_after_integration(wait_after)
        
        self._sweeper.average.mode('sequential')

    def do_set_averages(self, averages):  # Spectroscopy Compatibility
        self._sweeper.average.num_average(averages)

    def do_get_averages(self):  # Spectroscopy Compatibility
        result = self._sweeper.average.num_average()
        return int(list(result.items())[0][1])
    
    def avg_clear(self):  # Spectroscopy Compatibility
        pass # Per defaul, each measurement is cleared in SHFQC

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

    def start_measurement(self): # Spectrocopy Compatibility
        self._sweeper.run() # Blocking call

    def do_get_sweeptime_averages(self):  # Spectroscopy Compatibility
        return self._sweeper.predicted_cycle_time() * self.get_nop() * self.get_averages()
    
    def do_get_sweeptime(self):  # Spectroscopy Compatibility
        return self._sweeper.predicted_cycle_time() * self.get_nop()

    def get_freqpoints(self):  # Spectroscopy Compatibility
        freqs = np.linspace(self.get_startfreq(), self.get_stopfreq(), self.get_nop())
        return freqs

    def get_tracedata(self, format='AmpPha'): # Spectroscopy Compatibility
        result = self._sweeper.get_result()
        raw = result['vector']
        if format == 'AmpPha':
            return 10*np.log(np.abs(raw)**2 * 1000 / 50), np.angle(raw)
        elif format == 'RealImag':
            return np.real(raw), np.imag(raw)
        
    # MW Source Stuff
    def do_set_frequency(self, frequency, channel):
        synth = self._synth[channel - 1]
        dev_synth = self._device.synthesizers[synth]
        center = (frequency // 200e6) * 200e6
        dev_synth.centerfreq(center)
        
        # Get difference to actually target frequency:
        delta = frequency - dev_synth.centerfreq()
        self._device.sgchannels[channel - 1].oscs[0].freq(delta)
        self._device.sgchannels[channel - 1].awg.modulation.enable(1)
        self._device.sgchannels[channel - 1].sines[0].i.enable(1)
        self._device.sgchannels[channel - 1].sines[0].q.enable(1)
    
    def do_get_frequency(self, channel):
        synth = self._synth[channel - 1]
        dev_synth = self._device.synthesizers[synth]
        center = dev_synth.centerfreq()
        offset = self._device.sgchannels[channel - 1].oscs[0].freq()
        return center + offset
    
    def do_set_power(self, power, channel):
        power_range = math.ceil(power / 5) * 5
        self._device.sgchannels[channel-1].output.range(power_range)
        delta = power - power_range
        self._device.sgchannels[channel-1].awg.outputamplitude(10**(delta/10))
    
    def do_get_power(self, channel):
        power_range = self._device.sgchannels[channel-1].output.range()
        offset = self._device.sgchannels[channel-1].awg.outputamplitude()
        return power_range + 10 * math.log10(offset)
    
    def do_get_status(self, channel):
        return self._device.sgchannels[channel-1].output.on() == 1
    
    def do_set_status(self, enable, channel):
        status = 1 if enable else 0
        self._device.sgchannels[channel-1].output.on(status)
        
