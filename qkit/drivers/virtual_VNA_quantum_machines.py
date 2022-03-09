# Quantum machines driver, M. Spiecker 2019
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import time
import numpy as np
from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from qkit.core.instrument_base import Instrument




class VirtualVNAQuantumMachines(Instrument):
    """
    Class to use the quantum machines card as a VNA in the spectroscopy script.
    For the readout a interferrometric setup is assmued.
    Feel free to extend the functionality # TODO
    """
    def __init__(self, name):
        Instrument.__init__(self, name, tags=['virtual'])
        self.nop = 1001
        self.startfreq = 4e9
        self.stopfreq = 5e9
        self.sweeptime_averages = 1
        self.span = self.stopfreq - self.startfreq
        self.centerfreq = (self.startfreq + self.stopfreq) / 2
        self._ready = False
        self.add_function('get_freqpoints')
        self.add_function('get_tracedata')
        self.add_function('get_sweeptime_averages')
        self.add_function('pre_measurement')
        self.add_function('start_measurement')
        self.add_function('ready')
        self.add_function('post_measurement')

        self.qmm = QuantumMachinesManager()

        config = self.config()
        self.qm = self.qmm.open_qm(config)

        self.load_card()

    def config(self):

        opx_one = "Opx"
        readout_pulse_len = 200  # attenuation 10 dB #good: 200

        QB_IF_freq = 80.1e6 + 0.08315e6
        QB_LO_freq = 5e9  # for the mixer
        RR_IF_freq = 62.5e6
        theta = 18
        wait_sig = 118
        wait_ref = 52

        config = {
            'version': 1,
            'controllers': {
                opx_one: {
                    'type': 'Opx',
                    'analog_outputs': {
                        # sweep offset of I,Q to see which combination best suppresses LO leakage
                        1: {'offset': -0.01},  # I qubit
                        2: {'offset': -0.006},  # Q qubit
                    },
                    'analog_inputs': {
                        1: {'offset': 0.2},  # Reference
                        2: {'offset': 0}  # Signal
                    },
                    'digital_outputs': {
                        1: {}
                    }
                },
            },

            'elements': {

                'test': {
                    "mixInputs": {
                        "I": (opx_one, 5),
                        "Q": (opx_one, 6),
                        "mixer": "mixer_QB",
                        "lo_frequency": (QB_LO_freq)
                    },
                    'intermediate_frequency': (QB_IF_freq),
                    'operations': {
                        'test_pulse': 'test_pulse'
                    }

                },

                'test_dc': {
                    "singleInput": {
                        "port": (opx_one, 4),
                    },
                    'intermediate_frequency': (QB_IF_freq),
                    'operations': {
                        'test_dc_pulse': 'test_dc_pulse'
                    }

                },

                'qubit': {
                    "mixInputs": {
                        "I": (opx_one, 1),
                        "Q": (opx_one, 2),
                        "mixer": "mixer_QB",
                        "lo_frequency": (QB_LO_freq)
                    },
                    'intermediate_frequency': (QB_IF_freq),
                    'operations': {
                        'gaussian_pulse': 'gaussian_pulse',
                        'pi_pulse': 'pi_pulse',
                        'pi/2_pulse': 'pi/2_pulse',
                        'const': 'const_pulse',
                        'saturation_pulse': 'saturation_pulse',
                        'saturation_low_pulse': 'saturation_low_pulse'
                    }
                },

                'reference': {
                    "singleInput": {
                        "port": (opx_one, 3),
                    },
                    'intermediate_frequency': RR_IF_freq,
                    'operations': {
                        'readout_ref': 'zero_pulse',
                        'readout_ref_bay': 'zero_pulse_bay'
                    },
                    "outputs": {
                        'out1': (opx_one, 1),
                    },
                    'time_of_flight': 32 + 4 * wait_ref,
                    'smearing': 0
                },

                'signal': {
                    "singleInput": {
                        "port": (opx_one, 3),
                    },
                    'intermediate_frequency': RR_IF_freq,
                    'operations': {
                        'readout_sig': 'readout_pulse',
                        'readout_sig_bay': 'readout_pulse_bay'
                    },
                    "outputs": {
                        'out1': (opx_one, 2),
                    },
                    'time_of_flight': 32 + 4 * wait_sig,
                    'smearing': 0
                },

                'reference_T1': {
                    "singleInput": {
                        "port": (opx_one, 3),
                    },
                    'intermediate_frequency': RR_IF_freq,
                    'operations': {
                        'readout_ref': 'zero_pulse',
                        'readout_ref_bay': 'zero_pulse_bay',
                    },
                    "outputs": {
                        'out1': (opx_one, 1),
                    },
                    'time_of_flight': 32 + 4 * wait_ref,
                    'smearing': 0
                },

                'signal_T1': {
                    "singleInput": {
                        "port": (opx_one, 3),
                    },
                    'intermediate_frequency': RR_IF_freq,
                    'operations': {
                        'readout_sig': 'readout_pulse',
                        'readout_sig_bay': 'readout_pulse_bay',
                    },
                    "outputs": {
                        'out1': (opx_one, 2),
                    },
                    'time_of_flight': 32 + 4 * wait_sig,
                    'smearing': 0
                },
            },

            "pulses": {

                'test_dc_pulse': {
                    'operation': 'control',
                    'length': 100,
                    'waveforms': {
                        'single': 'const_wf',
                    },
                },

                'test_pulse': {
                    'operation': 'control',
                    'length': 100,
                    'waveforms': {
                        'I': 'const_wf',
                        'Q': 'zero_wf'
                    },
                },
                'gaussian_pulse': {
                    'operation': 'control',
                    'length': pi_pulse_len,
                    'waveforms': {
                        'I': 'gaussian_wf',
                        'Q': 'zero_wf'
                    },
                },

                'readout_pulse': {
                    'operation': 'measurement',
                    'length': readout_pulse_len,
                    'waveforms': {
                        'single': 'const_wf',
                    },
                    'digital_marker': 'ON',
                    'integration_weights': {
                        'integW_Is': 'integW_Is',
                        'integW_Qs': 'integW_Qs'
                    },
                },
                'zero_pulse': {
                    'operation': 'measurement',
                    'length': readout_pulse_len,
                    'waveforms': {
                        'single': 'zero_wf',
                    },
                    'digital_marker': 'ON',
                    'integration_weights': {
                        'integW_Ir': 'integW_Ir',
                        'integW_Qr': 'integW_Qr',
                    }
                },


                'const_pulse': {
                    'operation': 'control',
                    'length': 320,
                    'waveforms': {
                        'I': 'const_wf',
                        'Q': 'zero_wf',
                    }
                },
                'saturation_pulse': {
                    'operation': 'control',
                    'length': saturation_pulse_length,
                    'waveforms': {
                        'I': 'const_wf',
                        'Q': 'zero_wf',
                    }
                },
                'saturation_low_pulse': {
                    'operation': 'control',
                    'length': saturation_pulse_length,
                    'waveforms': {
                        'I': 'const_low_wf',
                        'Q': 'zero_wf',
                    }
                },
            },

            'waveforms': {
                'zero_wf': {
                    'type': 'constant',
                    'sample': 0
                },
                'const_wf': {
                    'type': 'constant',
                    'sample': 0.4
                },

                'gaussian_wf': {
                    'type': 'arbitrary',
                    'samples': gauss(0.45, 0.0, 10.0, pi_pulse_len)
                },
            },
            'digital_waveforms': {
                'ON': {
                    'samples': [(1, 0)]
                },
            },

            'integration_weights': {
                'integW_Ir': {
                    'cosine': [np.cos(theta / 360 * np.pi)] * int(readout_pulse_len / 4),
                    'sine': [np.sin(- theta / 360 * np.pi)] * int(readout_pulse_len / 4),
                },
                'integW_Qr': {
                    'cosine': [np.sin(theta / 360 * np.pi)] * int(readout_pulse_len / 4),
                    'sine': [np.cos(theta / 360 * np.pi)] * int(readout_pulse_len / 4),
                },
                'integW_Is': {
                    'cosine': [np.cos(theta / 360 * np.pi)] * int(readout_pulse_len / 4),
                    'sine': [np.sin(theta / 360 * np.pi)] * int(readout_pulse_len / 4),
                },
                'integW_Qs': {
                    'cosine': [np.sin(- theta / 360 * np.pi)] * int(readout_pulse_len / 4),
                    'sine': [np.cos(theta / 360 * np.pi)] * int(readout_pulse_len / 4),
                },
            },

            'mixers': {
                'mixer_QB': [
                    {
                        'intermediate_frequency': QB_IF_freq,
                        'lo_frequency': QB_LO_freq,
                        'correction': [1, 0, 0, 1]
                    }
                ],
            },
        }

        return config


    def load_card(self):

        with program() as adc:
            # measurement block:
            align("signal", "reference")
            measure("readout_sig", "signal", "adcs")
            measure("readout_ref", "reference", "adcr")

        job = self.qm.execute(adc, duration_limit=0, data_limit=0, flags=['use-optimized-compiler'])
        job.wait_for_all_results()
        res = job.get_results()

    def set_startfreq(self, startfreq):
        self.startfreq = startfreq
        self.span = self.stopfreq - self.startfreq
        self.centerfreq = (self.stopfreq + self.startfreq) / 2

    def get_startfreq(self):
        return self.startfreq

    def set_stopfreq(self, stopfreq):
        self.stopfreq = stopfreq
        self.span = self.stopfreq - self.startfreq
        self.centerfreq = (self.stopfreq + self.startfreq) / 2

    def get_stopfreq(self):
        return self.stopfreq

    def set_centerfreq(self, centerfreq):
        self.centerfreq = centerfreq
        self.startfreq = centerfreq - self.span / 2
        self.stopfreq = centerfreq + self.span / 2

    def get_centerfreq(self):
        return self.centerfreq

    def get_span(self):
        return self.span

    def set_span(self, span):
        self.span = span
        self.startfreq = self.centerfreq - span / 2
        self.stopfreq = self.centerfreq + span / 2

    def get_nop(self):
        return self.nop

    def set_nop(self, nop):
        self.nop = nop

    def get_freqpoints(self):
        return np.linspace(self.startfreq, self.stopfreq, self.nop)

    def get_sweeptime_averages(self,query=True):
        return self.sweeptime_averages

    def get_sweeptime(self,query=True):
        return 1

    def get_averages(self):
        return 1

    def get_Average(self):
        return False

    def get_tracedata(self, RealImag=None):

        def S21_notch(f, fr, Ql, Qc):
            return 1. - Ql / Qc / (1. + 2j * Ql * (f - fr) / fr)

        Qi = np.random.normal(2000, 500)
        Qc = np.random.normal(1500, 500)  # for a nice signal the resonance is overcoupled
        fr = np.random.normal((self.stopfreq + self.startfreq) / 2, self.span / 8)
        Ql = Qi * Qc / (Qi + Qc)
        S21_data = S21_notch(self.get_freqpoints(), fr, Ql, Qi) + np.random.normal(0., 0.01, self.nop)

        if not RealImag:
            amp = np.abs(S21_data)
            pha = np.angle(S21_data)
            return amp, pha
        else:
            I = S21_data.real
            Q = S21_data.imag
            return I, Q

    def get_all(self):
        pass

    def pre_measurement(self):
        pass

    def post_measurement(self):
        pass

    def start_measurement(self):
        pass

    def ready(self):
        self._ready = not self._ready
        return self._ready

    def avg_clear(self):
        pass

    def gauss(amplitude, mu, sigma, length):
        t = np.linspace(-length / 2, length / 2, length)
        gauss_wave = amplitude * np.exp(-((t - mu) ** 2) / (2 * sigma ** 2))
        return [float(x) for x in gauss_wave]

    def IQ_imbalance_corr(g, phi):
        c = np.cos(phi)
        s = np.sin(phi)
        N = 1 / ((1 - g ** 2) * (2 * c ** 2 - 1))
        return [float(N * x) for x in [(1 - g) * c, (1 + g) * s,
                                       (1 - g) * s, (1 + g) * c]]