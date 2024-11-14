# Quantum machines coherence library
# started by M. Spiecker, 06.2020
#
# Quantum machines config class for single qubit experiments with an interferrometric setup

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

        self.saturation_pulse_len = 50000
        self.pi_pulse_len = 48
        self.pi_wf = pulses.gauss(0.49, 0.0, 10.0, self.pi_pulse_len)
        self.pi2_wf = self.pi_wf / 2

        # Readout
        self.res_freq = 7e9
        self.RR_IF_freq = 62.5e6
        self.RR_LO_up_freq = self.res_freq + self.RR_IF_freq
        self.RR_LO_down_freq = self.res_freq - self.RR_IF_freq

        self.wait_sig = 160  #  minimum 32 clock cycles
        self.smearing_sig = 0  # multiple period
        self.wait_ref = 53  # minimum 32 clock cycles
        self.smearing_ref = 0

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
                        1: {'offset': 0},  # I qubit
                        2: {'offset': 0},  # Q qubit
                        3: {'offset': 0},  # RR
                    },
                    'analog_inputs': {
                        1: {'offset': 0},  # Reference
                        2: {'offset': 0}  # Signal
                    },
                    'digital_outputs': {
                        1: {}
                    }
                },
            },
            'elements': {
                'signal': {
                    "singleInput": {
                        "port": (opx_one, 3),
                    },
                    'intermediate_frequency': self.RR_IF_freq,
                    'operations': {
                        'readout_sig': 'readout_pulse',
                        'saturation_pulse': 'readout_saturation_pulse',
                    },
                    "outputs": {
                        'out1': (opx_one, 1),
                    },
                    'time_of_flight': 4 * self.wait_sig,
                    'smearing': self.smearing_sig
                },
                'reference': {
                    "singleInput": {
                        "port": (opx_one, 3),
                    },
                    'intermediate_frequency': self.RR_IF_freq,
                    'operations': {
                        'readout_ref': 'reference_pulse',
                    },
                    "outputs": {
                        'out1': (opx_one, 2),  # TODO out2?
                    },
                    'time_of_flight': 4 * self.wait_ref,
                    'smearing': self.smearing_ref
                },
                'qubit': {
                    "mixInputs": {
                        "I": (opx_one, 1),
                        "Q": (opx_one, 2),
                        "mixer": "mixer_QB",
                        "lo_frequency": self.QB_LO_freq
                    },
                    'intermediate_frequency': self.QB_IF_freq,
                    'operations': {
                        'saturation_pulse': 'saturation_pulse',
                        'pi_pulse': 'pi_pulse',
                        'pi/2_pulse': 'pi/2_pulse',
                    }
                },
            },

            "pulses": {
                'readout_saturation_pulse': {
                    'operation': 'control',
                    'length': self.saturation_pulse_len,
                    'waveforms': {
                        'single': 'const_wf',
                    },
                },
                'saturation_pulse': {
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
                'readout_pulse': {
                    'operation': 'measurement',
                    'length': self.readout_pulse_len,
                    'waveforms': {
                        'single': 'readout_wf',
                    },
                    'digital_marker': 'ON',
                    'integration_weights': {
                        'integW_Is': 'integW_Is',
                        'integW_Qs': 'integW_Qs'
                    },
                },
                'reference_pulse': {
                    'operation': 'measurement',
                    'length': self.readout_pulse_len,
                    'waveforms': {
                        'single': 'zero_wf',
                    },
                    'digital_marker': 'ON',
                    'integration_weights': {
                        'integW_Ir': 'integW_Ir',
                        'integW_Qr': 'integW_Qr',
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
                    'sample': 0.49
                },
                'readout_wf': {
                    'type': 'arbitrary',
                    'samples': self.readout_wf.tolist()
                },
                'pi_wf': {
                    'type': 'arbitrary',
                    'samples': self.pi_wf.tolist()
                },
                'pi/2_wf': {
                    'type': 'arbitrary',
                    'samples': self.pi2_wf.tolist()
                }
            },
            'digital_waveforms': {
                'ON': {
                    'samples': [(1, 0)]
                },
            },

            'integration_weights': {
                'integW_Is': {
                    'cosine': [np.cos(self.theta / 360 * np.pi)] * int(self.readout_pulse_len / 4 + self.smearing_sig),
                    'sine': [np.sin(self.theta / 360 * np.pi)] * int(self.readout_pulse_len / 4 + self.smearing_sig),
                },
                'integW_Qs': {
                    'cosine': [np.sin(- self.theta / 360 * np.pi)] * int(
                        self.readout_pulse_len / 4 + self.smearing_sig),
                    'sine': [np.cos(self.theta / 360 * np.pi)] * int(self.readout_pulse_len / 4 + self.smearing_sig),
                },
                'integW_Ir': {
                    'cosine': [np.cos(self.theta / 360 * np.pi)] * int(self.readout_pulse_len / 4 + self.smearing_ref),
                    'sine': [np.sin(- self.theta / 360 * np.pi)] * int(self.readout_pulse_len / 4 + self.smearing_ref),
                },
                'integW_Qr': {
                    'cosine': [np.sin(self.theta / 360 * np.pi)] * int(self.readout_pulse_len / 4 + self.smearing_ref),
                    'sine': [np.cos(self.theta / 360 * np.pi)] * int(self.readout_pulse_len / 4 + self.smearing_ref),
                },
            },
            'mixers': {
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
