# Quantum machines coherence library
# started by M. Spiecker, 06.2020
#
# Quantum machines config class for single qubit experiments
#
# HOW TO USE IT:
# Use this file as a template. Create your own QMQubitConfig class and tailor it for your experiments

import numpy as np
from qm.QuantumMachinesManager import QuantumMachinesManager

from qkit.measure.timedomain.quantum_machine import pulses


class QMQubitConfig:

    def __init__(self):

        self.qmm = QuantumMachinesManager()
        self.qm = None

        self.config = None

        # Qubit
        self.qubit_freq = 1e9
        self.QB_IF_freq = 80.0e6
        self.QB_LO_freq = self.qubit_freq - self.QB_IF_freq  # for the mixer

        self.saturation_pulse_len = 5000
        self.pi_pulse_len = 48
        self.pi_wf = pulses.gauss(0.49, 0.0, 10.0, self.pi_pulse_len)
        self.pi2_wf = self.pi_wf / 2

        self.QB_const_amplitude = 0.49

        # Readout
        self.res_freq = 7e9
        self.RR_IF_freq = 62.5e6
        self.RR_LO_freq = self.res_freq - self.RR_IF_freq

        self.wait_res = 160  #  minimum 32 clock cycles
        self.smearing_res = 0  # multiple period

        self.readout_pulse_len = 512  # multiple of 16
        self.readout_wf = pulses.const(0.49, self.readout_pulse_len)
        self.theta = 0.0  # rotation of IQ plane

        # create config and load it
        self.load_config()

    def set_readout_wf(self, func, args, plot=False):

        self.readout_wf = func(*args, self.readout_pulse_len)
        self.load_config()

        #if plot:
        #    self.ax.plot(self.readout_wf)
        #    plt.show()

    def set_pi_pulse_wf(self, func, args, plot=False):

        self.pi_wf = func(*args, self.pi_pulse_len)
        self.pi2_wf = self.pi_wf / 2
        self.load_config()

        #if plot:
        #    self.ax.plot(self.pi_wf)
        #    self.ax.plot(self.pi2_wf)
        #    plt.show()

    def set_theta(self, theta):

        self.theta = theta
        self.load_config()


    # TODO set dc offset mixers
    def load_config(self):

        opx_one = "con1"

        self.config = {
            'version': 1,
            'controllers': {
                opx_one: {
                    'type': 'Opx',
                    'analog_outputs': {
                        # sweep offset of I,Q to see which combination best suppresses LO leakage
                        1: {'offset': 0},  # I resonator
                        2: {'offset': 0},  # Q resonator
                        3: {'offset': 0},  # I qubit
                        4: {'offset': 0},  # Q qubit
                        9: {'offset': 0},  # test
                        10: {'offset': 0}, # test
                    },
                    'analog_inputs': {
                        1: {'offset': 0},  # I
                        2: {'offset': 0}   # Q
                    },
                    'digital_outputs': {
                        1: {}
                    }
                },
            },
            'elements': {
                'qubit': {
                    "mixInputs": {
                        "I": (opx_one, 4),
                        "Q": (opx_one, 3),
                        "mixer": "mixer_QB",
                        "lo_frequency": self.QB_LO_freq
                    },
                    'intermediate_frequency': self.QB_IF_freq,
                    'operations': {
                        'saturation': 'QB_saturation_pulse',
                        'pi': 'pi_pulse',
                        'pi/2': 'pi/2_pulse',
                    }
                },
                'resonator': {
                    "mixInputs": {
                        "I": (opx_one, 1),
                        "Q": (opx_one, 2),
                        'lo_frequency': self.RR_LO_freq,
                        'mixer': "mixer_RR",
                    },
                    'intermediate_frequency': self.RR_IF_freq,
                    'operations': {
                        'readout': 'readout_pulse',
                    },
                    "outputs": {
                        'out1': (opx_one, 1),
                        'out2': (opx_one, 2),
                    },
                    'time_of_flight': 32 + 4 * self.wait_res,  # multiple of 4, minimum 32 clock cycles, ns
                    'smearing': self.smearing_res,
                },
            },
            "pulses": {
                'QB_saturation_pulse': {
                    'operation': 'control',
                    'length': self.saturation_pulse_len,
                    'waveforms': {
                        'I': 'const_wf',
                        'Q': 'zero_wf',
                    }
                },
                'pi_pulse': {
                    'operation': 'control',
                    'length': self.pi_pulse_len,
                    'waveforms': {
                        'I': 'pi_wf',
                        'Q': 'zero_wf'
                    },
                },
                'pi/2_pulse': {
                    'operation': 'control',
                    'length': self.pi_pulse_len,
                    'waveforms': {
                        'I': 'pi/2_wf',
                        'Q': 'zero_wf'
                    },
                },
                'RR_saturation_pulse': {
                    'operation': 'control',
                    'length': self.saturation_pulse_len,
                    'waveforms': {
                        'I': 'const_wf',
                        'Q': 'zero_wf',
                    },
                },
                'readout_pulse': {
                    'operation': 'measurement',
                    'length': self.readout_pulse_len,
                    'waveforms': {
                        'I': 'readout_wf',
                        'Q': 'zero_wf',
                    },
                    'digital_marker': 'ON',    # TODO brauchen wir den?
                    'integration_weights': {
                        'integ_w1_I': 'integ_w1_I',
                        'integ_w2_I': 'integ_w2_I',
                        'integ_w1_Q': 'integ_w1_Q',
                        'integ_w2_Q': 'integ_w2_Q',
                    },
                },
            },
            'waveforms': {
                'zero_wf': {
                    'type': 'constant',
                    'sample': 0
                },
                'const_wf': {
                    'type': 'constant',
                    'sample': 0.49
                },
                'pi_wf': {
                    'type': 'arbitrary',
                    'samples': self.pi_wf.tolist()
                },
                'pi/2_wf': {
                    'type': 'arbitrary',
                    'samples': self.pi2_wf.tolist()
                },
                'readout_wf': {
                    'type': 'arbitrary',
                    'samples': self.readout_wf.tolist()
                },
            },
            'digital_waveforms': {
                'ON': {
                    'samples': [(1, 0)]
                },
            },
            'integration_weights': {
                'integ_w1_I': {
                    'cosine': [np.cos(self.theta)] * (self.readout_pulse_len // 4 + self.smearing_res),   #1 TODO smearing ??
                    'sine': [np.sin(self.theta)] * (self.readout_pulse_len // 4 + self.smearing_res),     #0
                },
                'integ_w2_I': {
                    'cosine': [-np.sin(self.theta)] * (self.readout_pulse_len // 4 + self.smearing_res),   #0
                    'sine': [np.cos(self.theta)] * (self.readout_pulse_len // 4 + self.smearing_res),     #1
                },
                'integ_w1_Q': {
                    'cosine': [np.sin(self.theta)] * (self.readout_pulse_len // 4 + self.smearing_res),   #0
                    'sine': [-np.cos(self.theta)] * (self.readout_pulse_len // 4 + self.smearing_res),     #-1
                },
                'integ_w2_Q': {
                    'cosine': [np.cos(self.theta)] * (self.readout_pulse_len // 4 + self.smearing_res),   #1
                    'sine': [np.sin(self.theta)] * (self.readout_pulse_len // 4 + self.smearing_res),     #0
                },
            },
            'mixers': {
                'mixer_RR': [
                    {
                        'intermediate_frequency': self.RR_IF_freq,
                        'lo_frequency': self.RR_LO_freq,
                        'correction': [1, 0, 0, 1]

                    }
                ],
                'mixer_QB': [
                    {
                        'intermediate_frequency': self.QB_IF_freq,
                        'lo_frequency': self.QB_LO_freq,
                        'correction': [1, 0, 0, 1]
                    }
                ],
            },
        }

        self.qm = self.qmm.open_qm(self.config)


    # TODO make it nice
    def print_config(self):
        print(self.config)
