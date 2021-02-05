"""
sequency_library.py
A. Stehli (05/2018)

This library provides the measurement sequences for standard qubit experiments.
Currently this includes:
    rabi experiment
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

import qkit.measure.timedomain.pulse_sequence as ps

"""
TODO: How to implement the mixer calibration? Should it be stored in the sample object or in an external file where it can be acessed?
"""


def rabi(sample, pulse_shape=ps.ShapeLib.rect, amplitude=1, iq_frequency=None):
    """
        Generate sequence object for a rabi experiment (varying drive pulse lengths).

        Args:
            sample:      sample object
            pulse_shape: shape of the pulses (i.e. square, gauss, ...)
            amplitude:   relative ampitude of the sequence
            iq_frequency: IQ-frequency for heterodyne mixing. If iq_frequency is None, the sample.iq_frequency is used.
                            If iq_frequency is 0 homodyne mixing is employed.

        Returns:
            Sequence object for rabi experiment
    """
    if iq_frequency is None:
        if hasattr(sample, "iq_frequency"):
            iq_frequency = sample.iq_frequency
            print("IQ-frequency set to {:.0f} MHz.".format(iq_frequency / 1e6))
        else:
            iq_frequency = 0
            print(
                "Sample has no attribute iq_frequency.\n IQ-frequency set to 0 for homodyne mixing.")
    rabi_tone = ps.Pulse(lambda t: t, shape=pulse_shape, name="rabi-tone",
                         amplitude=amplitude, iq_frequency=iq_frequency)
    sequence = ps.PulseSequence(sample)
    sequence.add(rabi_tone)
    sequence.add_readout()
    return sequence


def t1(sample, pulse_shape=ps.ShapeLib.rect, amplitude=1, iq_frequency=None):
    """
        Generate a sequence with one pi pulse followed by a time delay.

        Args:
            sample:       sample object
            pulse_shape:  shape of the pulses (i.e. square, gauss, ...)
            amplitude:    relative ampitude of the sequence
            iq_frequency: IQ-frequency for heterodyne mixing. If iq_frequency is None, the sample.iq_frequency is used.
                            If iq_frequency is 0 homodyne mixing is employed.

        Returns:
            Sequence object for T1 measurement
    """
    if iq_frequency is None:
        if hasattr(sample, "iq_frequency"):
            iq_frequency = sample.iq_frequency
            print("IQ-frequency set to {:.0f} MHz.".format(iq_frequency / 1e6))
        else:
            iq_frequency = 0
            print(
                "Sample has no attribute iq_frequency.\n IQ-frequency set to 0 for homodyne mixing.")
    pi_pulse = ps.Pulse(sample.tpi, shape=pulse_shape, name="pi",
                        amplitude=amplitude, iq_frequency=iq_frequency)
    sequence = ps.PulseSequence(sample)
    sequence.add(pi_pulse)
    sequence.add_wait(lambda t: t)
    sequence.add_readout()
    return sequence


def ramsey(sample, pulse_shape=ps.ShapeLib.rect, amplitude=1, iq_frequency=None):
    """
    Generate a sequence with two pi/2 pulses seperated by a time delay.

    Args:
        sample:       sample object
        pulse_shape:  shape of the pulses (i.e. square, gauss, ...)
        amplitude:    relative ampitude of the sequence
        iq_frequency: IQ-frequency for heterodyne mixing. If iq_frequency is None, the sample.iq_frequency is used.
                      If iq_frequency is 0 homodyne mixing is employed.

    Returns:
        Sequence object for ramsey measurement
    """
    return spinecho(sample, 0, pulse_shape, amplitude, iq_frequency)


def spinecho(sample, n_pi=1, pulse_shape=ps.ShapeLib.rect, amplitude=1, iq_frequency=None):
    """
    Generate sequence with two pi/2 pulses at the ends and a number n_pi pi pulses inbetween
    pi2 - time/(2*n) - pi - time/n - pi - ... - pi - time/(2*n) - pi2


    Args:
        sample:       sample object
        n_pi:         number of pi-pulses
        pulse_shape:  shape of the pulses (i.e. square, gauss, ...)
        amplitude:    relative ampitude of the sequence
        iq_frequency: IQ-frequency for heterodyne mixing. If iq_frequency is None, the sample.iq_frequency is used.
                      If iq_frequency is 0 homodyne mixing is employed.

    Returns:
        Sequence object for spinecho measurement
    """
    if iq_frequency is None:
        if hasattr(sample, "iq_frequency"):
            iq_frequency = sample.iq_frequency
            print("IQ-frequency set to {:.0f} MHz.".format(iq_frequency / 1e6))
        else:
            iq_frequency = 0
            print(
                "Sample has no attribute iq_frequency.\n IQ-frequency set to 0 for homodyne mixing.")
    pi_pulse = ps.Pulse(sample.tpi, shape=pulse_shape, name="pi",
                        amplitude=amplitude, iq_frequency=iq_frequency)
    pi2_pulse = ps.Pulse(sample.tpi2, shape=pulse_shape, name="pi/2",
                         amplitude=amplitude, iq_frequency=iq_frequency)

    sequence = ps.PulseSequence(sample)
    sequence.add(pi2_pulse)
    if n_pi == 0:
        sequence.add_wait(lambda t: t)
    else:
        sequence.add_wait(lambda t: t/(2*n_pi))
        for i in range(n_pi):
            sequence.add(pi_pulse)
            if i + 1 != n_pi:
                sequence.add_wait(lambda t: t/n_pi)
        sequence.add_wait(lambda t: t/(2*n_pi))
    sequence.add(pi2_pulse)
    sequence.add_readout()
    return sequence


def spinlocking(sample, pi2sign=1, add_pi=True, wait_time=5e-9, pulse_shape=ps.ShapeLib.rect, amplitude=1, iq_frequency=None):
    """
    Generate sequence with two pi/2 pulses (around y-axis) at the ends and a drive in-between.
    The drive is phase shifted by 90 degrees in respect to the pi/2 pulses (rotates around x-axis).
    Furthermore a pi-pulse (around x-axis) may be added (True by default) before as well as after the drive.
    This reduces the susceptibility to low frequency oscillations.

    Args:
        sample:       sample object
        pi2sign:      sign of the first pi/2 pulse
        add_pi:       if True an additional pi-pulse is added before and after the drive
        wait_time:    wait time between pi/2 or pi-pulse and the drive
        pulse_shape:  shape of the pi and pi/2 pulses (i.e. square, gauss, ...)
        amplitude:    relative ampitude of the sequence
        iq_frequency: IQ-frequency for heterodyne mixing. If iq_frequency is None, the sample.iq_frequency is used.
                        If iq_frequency is 0 homodyne mixing is employed.

    Returns:
        Sequence object for spinecho measurement
    """
    if iq_frequency is None:
        if hasattr(sample, "iq_frequency"):
            iq_frequency = sample.iq_frequency
            print("IQ-frequency set to {:.0f} MHz.".format(iq_frequency / 1e6))
        else:
            iq_frequency = 0
            print(
                "Sample has no attribute iq_frequency.\n IQ-frequency set to 0 for homodyne mixing.")
    # check if pi/2-pulse needs to be flipped
    if pi2sign == -1:
        phase = 270
    else:
        phase = 90

    # define pulses
    pi_pulse = ps.Pulse(sample.tpi, shape=pulse_shape, name="pi",
                        amplitude=amplitude, iq_frequency=iq_frequency)
    pi2_pulse1 = ps.Pulse(sample.tpi2, shape=pulse_shape, name="pi/2",
                          amplitude=amplitude, iq_frequency=iq_frequency, phase=phase)
    pi2_pulse2 = ps.Pulse(sample.tpi2, shape=pulse_shape, name="pi/2(Y)",
                          amplitude=amplitude, iq_frequency=iq_frequency, phase=90)
    locking_tone = ps.Pulse(lambda t: t, shape=ps.ShapeLib.rect,
                            name="locking-drive", amplitude=amplitude, iq_frequency=iq_frequency)

    # add pulses to sequence
    sequence = ps.PulseSequence(sample)
    sequence.add(pi2_pulse1)
    if add_pi:
        sequence.add(pi_pulse)
    sequence.add_wait(wait_time)
    sequence.add(locking_tone)
    sequence.add_wait(wait_time)
    if add_pi:
        sequence.add(pi_pulse)
    sequence.add(pi2_pulse2)
    sequence.add_readout()
    return sequence
