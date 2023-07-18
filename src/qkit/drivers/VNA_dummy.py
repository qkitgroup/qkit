# VNA dummy driver, M. Wildermuth
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
# along with this program; if not, query to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from qkit.core.instrument_base import Instrument
import numpy as np

def get_resonance_curve(f, f_r, Q_l, Q_c, mode='notch'):
    if mode == 'notch':
        S_21 = 1 - (Q_l / Q_c) / (1 + 2j * Q_l * (f - f_r) / f_r)
    elif mode == 'reflection':
        S_21 = 1 - (2 * Q_l / Q_c) / (1 + 2j * Q_l * (f - f_r) / f_r)
    elif mode == 'inline':
        S_21 = (Q_l / Q_c) / (1 + 2j * Q_l * (f - f_r) / f_r)
    return S_21


class VNA_dummy(Instrument):
    """
    This is the python driver for a dummy Vector Network Analyzer

    Usage:
    Initialise with
    <name> = instruments.create('<name>')

    """

    def __init__(self, name):
        """
        Initializes

        Input:
        """
        self.__name__ = __name__
        Instrument.__init__(self, name, tags=['virtual'])
        self.func = get_resonance_curve
        self.args = ()
        self.kwargs = {'f_r': 5e9, 'Q_l': 9e3, 'Q_c': 1e4}

        # Implement parameters
        self.add_parameter('averages',
                           type=int,
                           flags=Instrument.FLAG_GETSET,
                           minval=1,
                           maxval=65536,
                           tags=['sweep'])

        self.add_parameter('Average',
                           type=bool,
                           flags=Instrument.FLAG_GETSET)

        self.add_parameter('startfreq',
                           type=float,
                           flags=Instrument.FLAG_GETSET,
                           minval=0,
                           maxval=20e9,
                           units='Hz',
                           tags=['sweep'])

        self.add_parameter('stopfreq',
                           type=float,
                           flags=Instrument.FLAG_GETSET,
                           minval=0,
                           maxval=20e9,
                           units='Hz',
                           tags=['sweep'])

        self.add_parameter('centerfreq',
                           type=float,
                           flags=Instrument.FLAG_GETSET,
                           minval=0,
                           maxval=20e9,
                           units='Hz',
                           tags=['sweep'])

        self.add_parameter('span',
                           type=float,
                           flags=Instrument.FLAG_GETSET,
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
                           flags=Instrument.FLAG_GETSET,
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

        # Implement functions
        self.add_function('avg_clear')
        self.add_function('avg_status')
        self.add_function('get_freqpoints')
        self.add_function('get_tracedata')
        self.add_function('pre_measurement')
        self.add_function('start_measurement')
        self.add_function('post_measurement')
        self.add_function('ready')

        self.centerfreq = self.kwargs.get('f_r')
        self.Q_l = self.kwargs.get('Q_l')
        self.Q_c = self.kwargs.get('Q_c')
        self.span = 10e6
        self.nop = 1001
        self.sweep_type = 'LIN'
        self.averages = 1
        self.Average = False
        self.startfreq, self.stopfreq = self.centerfreq + np.array((-1, 1)) * self.span / 2

        self.get_all()
    
    def get_all(self):
        self.get_Average()
        self.get_averages()
        self.get_startfreq()
        self.get_stopfreq()
        self.get_centerfreq()
        self.get_span()
        self.get_nop()
        self.get_freqpoints()
        self.get_sweeptime()
        self.get_sweeptime_averages()


    def avg_clear(self):
        pass

    def avg_status(self):
        return

    def do_set_Average(self, status):
        """
        Set status of Average

        Input:
            status (boolean)

        Output:
            None
        """
        self.Average = status

    def do_get_Average(self):
        """
        Get status of Average

        Input:
            None

        Output:
            Status of Averaging (boolean)
        """
        return self.Average

    def do_set_averages(self, av):
        """
        Set number of averages

        Input:
            av (int) : Number of averages
        Output:
            None
        """
        self.averages = av

    def do_get_averages(self):
        """
        Get number of averages

        Input:
            None
        Output:
            Number of averages
        """
        return self.averages

    def get_freqpoints(self, query=False):
        return np.linspace(self.centerfreq - self.span / 2,
                           self.centerfreq + self.span / 2,
                           self.nop)

    def get_tracedata(self, format='AmpPha'):
        f = self.get_freqpoints()
        S_21 = self.func(f, *self.args, **self.kwargs)
        if format == 'AmpPha':
            return np.abs(S_21), np.angle(S_21)
        elif format == 'RealImag':
            return np.real(S_21), np.imag(S_21)

    def do_set_startfreq(self, val):
        """
        Set Start frequency

        Input:
            span (float) : Frequency in Hz

        Output:
            None
        """
        self.startfreq = val
        
    def do_get_startfreq(self):
        """
        Get Start frequency

        Input:
            None

        Output:
            span (float) : Start Frequency in Hz
        """
        return self.startfreq

    def do_set_stopfreq(self, val):
        """
        Set STop frequency

        Input:
            val (float) : Stop Frequency in Hz

        Output:
            None
        """
        self.stopfreq = val

    def do_get_stopfreq(self):
        """
        Get Stop frequency

        Input:
            None

        Output:
            val (float) : Start Frequency in Hz
        """
        return self.stopfreq

    def do_set_centerfreq(self, cf):
        """
        Set the center frequency

        Input:
            cf (float) :Center Frequency in Hz

        Output:
            None
        """
        self.centerfreq = cf

    def do_get_centerfreq(self):
        """
        Get the center frequency

        Input:
            None

        Output:
            cf (float) :Center Frequency in Hz
        """
        return self.centerfreq

    def do_set_span(self, span):
        """
        Set Span

        Input:
            span (float) : Span in KHz

        Output:
            None
        """
        self.span = span

    def do_get_span(self):
        """
        Get Span

        Input:
            None

        Output:
            span (float) : Span in Hz
        """
        return self.span

    def do_set_nop(self, nop):
        """
        Set Number of Points (nop) for sweep

        Input:
            nop (int) : Number of Points

        Output:
            None
        """
        self.nop = nop

    def do_get_nop(self):
        """
        Get Number of Points (nop) for sweep

        Input:
            None
        Output:
            nop (int)
        """
        return self.nop

    def do_get_sweep_type(self):
        """
        Get the Sweep Type

        Input:
            None

        Output:
            Sweep Type (string). One of
            LIN:    Frequency-based linear sweep
            LOG:    Frequency-based logarithmic sweep
            SEGM:   Segment-based sweep with frequency-based segments
            POW:    Power-based sweep with CW frequency
            CW:     Single frequency mode
        """
        return self.sweep_type

    def do_set_sweep_type(self, swtype):
        """
        Set the Sweep Type
        Input:
            swtype (string):    One of
                LIN:    Frequency-based linear sweep
                LOG:    Frequency-based logarithmic sweep
                SEGM:   Segment-based sweep with frequency-based segments
                POW:    Power-based sweep with CW frequency
                CW:     Time-based sweep with CW frequency

        Output:
            None
        """
        self.sweep_type = swtype

    def do_get_sweeptime_averages(self):
        """
        Get sweeptime

        Input:
            None

        Output:
            sweep time (float) times number of averages: sec
        """
        return 1

    def do_get_sweeptime(self):
        """
        Get sweeptime

        Input:
            None

        Output:
            sweep time (float) : sec
        """
        return 1

    def pre_measurement(self):
        """
        Set everything needed for the measurement
        Averaging has to be enabled.
        Trigger count is set to number of averages
        """
        pass

    def start_measurement(self):
        """
        This function is called at the beginning of each single measurement in the spectroscopy script.
        Here, it starts n sweeps, where n is the active channels trigger count.
        Also, the averages need to be reset.
        """
        pass

    def post_measurement(self):
        """
        Bring the VNA back to a mode where it can be easily used by the operator.
        """
        pass

    def ready(self):
        """
        This is a proxy function, returning True when the VNA is on HOLD after finishing the required number of averages .
        """
        return True

