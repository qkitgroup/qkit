"""
sequency_library.py
A. Stehli (04/2018)

This library provides the measurement sequences for standard qubit experiments.
Currently this includes:
    T1 measurments
    Ramsey experiments
    Spin/Hahn echo
"""

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

import pulse_sequence as ps


def compensate():
    # This should be moved to sequence class.
    # Sequence class could have attributes .compensate, .decaytime.
    # If compensate: sequence.__call__ accounts for the decay due to decaytime.
    return

def rabi(sample, pulse_shape = ps.ShapeLib.rect, amplitude = 1, frequency_shift = 0, sample_rate = None):
    """
        Generate sequence object for a rabi experiment (varying drive pulse lengths).

        Input:
            sample          - sample object.
            pulse_shape     - Shape of the pulses (i.e. square, gauss, ...)
            amplitude       - relative ampitude of the sequence.
            frequency_shift - frequency shift of the pulses.

        Output:
            Sequence object for rabi experiment.
    """
    rabi_tone = ps.Pulse(lambda t: t, shape = pulse_shape, name = "rabi-tone", amplitude = amplitude, frequency_shift = frequency_shift)
    sequence = ps.PulseSequence(sample, sample.clock)
    sequence.add(rabi_tone)
    sequence.add_readout()
    return sequence

def t1(sample, pulse_shape = ps.ShapeLib.rect, amplitude = 1, frequency_shift = 0):
    """
        Generate a sequence with one pi pulse followed by a time delay.

        Input:
            sample          - sample object.
            pulse_shape     - Shape of the pulses (i.e. square, gauss, ...)
            amplitude       - relative ampitude of the sequence.
            frequency_shift - frequency shift of the pulses.

        Output:
            Sequence object for T1 measurement.
    """
    pi_pulse = ps.Pulse(sample.tpi, shape = pulse_shape, name = "pi", amplitude = amplitude, frequency_shift = frequency_shift)
    sequence = ps.PulseSequence(sample, sample.clock)
    sequence.add(pi_pulse)
    sequence.add_wait(lambda t: t)
    sequence.add_readout()
    return sequence

def ramsey(sample, pulse_shape = ps.ShapeLib.rect, amplitude = 1, frequency_shift = 0):
    """
    Generate a sequence with two pi/2 pulses seperated by a time delay.

    Input:
        sample          - sample object.
        pulse_shape     - Shape of the pulses (i.e. square, gauss, ...)
        amplitude       - relative ampitude of the sequence.
        frequency_shift - frequency shift of the pulses.

    Output:
        Sequence object for ramsey measurement.
    """
    return spinecho(sample, 0, pulse_shape, amplitude, frequency_shift)

def spinecho(sample, n_pi = 1, pulse_shape = ps.ShapeLib.rect, amplitude = 1, frequency_shift = 0):
    """
    Generate sequence with two pi/2 pulses at the ends and a number n_pi pi pulses inbetween
    pi2 - time/(2*n) - pi - time/n - pi - ... - pi - time/(2*n) - pi2
    

    Input:
        sample          - sample object.
        n_pi            - Number of pi-pulses.
        pulse_shape     - Shape of the pulses (i.e. square, gauss, ...)
        amplitude       - relative ampitude of the sequence.
        frequency_shift - frequency shift of the pulses.

    Output:
        Sequence object for spinecho measurement.
    """
    pi_pulse = ps.Pulse(sample.tpi, shape = pulse_shape, name = "pi", amplitude = amplitude, frequency_shift = frequency_shift)
    pi2_pulse = ps.Pulse(sample.tpi2, shape = pulse_shape, name = "pi/2", amplitude = amplitude, frequency_shift = frequency_shift)
    
    sequence = ps.PulseSequence(sample, sample.clock)
    sequence.add(pi2_pulse)
    if n_pi is 0:
        sequence.add_wait(lambda t: t)
    else:
        sequence.add_wait(lambda t: t/(2*n_pi))
        for i in range(n_pi):
            sequence.add(pi_pulse)
            if i + 1 is not n_pi:
                sequence.add_wait(lambda t: t/n_pi)
        sequence.add_wait(lambda t: t/(2*n_pi))
    sequence.add(pi2_pulse)
    sequence.add_readout()
    return sequence