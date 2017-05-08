# measurement.py, Measurement class
# Reinier Heeres <reinier@heeres.eu>, 2008
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
import gtk
import gobject

import logging
from lib import calltimer

import qt
from data import Data

class Measurement(gobject.GObject):

    __gsignals__ = {
        'finished': (gobject.SIGNAL_RUN_FIRST,
                    gobject.TYPE_NONE,
                    ([gobject.TYPE_PYOBJECT])),
        'progress': (gobject.SIGNAL_RUN_FIRST,
                    gobject.TYPE_NONE,
                    ([gobject.TYPE_PYOBJECT])),
    }

    _PROGRESS_STEPS = 1

    def __init__(self, name, **kwargs):
        gobject.GObject.__init__(self)

        self._name = name
        self._thread = None
        self._options = kwargs

        self._coords = []
        self._measurements = []

        if name in qt.data:
            self._data = qt.data['name']
        else:
            self._data = Data()

    def get_data(self):
        return self._data

    def _add_coordinate_options(self, coord, **kwargs):
        if 'steps' in kwargs:
            if kwargs['steps'] == 0:
                logging.warning('Unable to add coordinate with 0 steps')
                return False

            coord['steps'] = kwargs['steps']
            coord['stepsize'] = float(coord['end'] - coord['start']) / (kwargs['steps'] - 1.0)
        elif 'stepsize' in kwargs:
            if kwargs['stepsize'] == 0:
                logging.warning('Unable to add coordinate with 0 stepsize')
                return False

            if start < end:
                coord['stepsize'] = kwargs['stepsize']
            else:
                coord['stepsize'] = -kwargs['stepsize']
            coord['steps'] = math.ceil((coord['end'] - coord['start']) / kwargs['stepsize'])
        else:
            logging.warning('_add_coordinate_options requires steps or stepsize argument')

        if 'delay' in kwargs:
            coord['delay'] = kwargs['delay']

        self._coords.append(coord)

    def add_coordinate(self, ins, var, start, end, **kwargs):
        '''
        Add a loop coordinate to the internal list. The first coordinate is
        the outer part of the loop, the last coordinate the inner part. The
        measurement loop will set the value of instrument ins, variable var.

        Input:
            ins (Instrument): the instrument
            var (string): the variable to sweep
            start (float): start value
            end (float): end value
            **kwargs: options:
                steps (int) or stepsize (float). One of these is required.
                delay (float): delay after setting value, in ms

        Output:
            None
        '''

        coord = {'start': float(start), 'end': float(end),
                'ins': ins, 'var': var}

        self._add_coordinate_options(coord, **kwargs)

        kwargs['instrument'] = ins.get_name()
        kwargs['parameter'] = var
        kwargs['size'] = kwargs['steps']
        self._data.add_coordinate(var, **kwargs)

    def add_coordinate_func(self, func, start, end, **kwargs):
        '''
        Add a loop coordinate to the internal list. The first coordinate is
        the outer part of the loop, the last coordinate the inner part. The
        measurement loop will call function func with the variable value.

        Input:
            func (function): the function to call
            start (float): start value
            end (float): end value
            **kwargs: options:
                steps (int) or stepsize (float). One of these is required.
                delay (float): delay after setting value, in ms

        Output:
            None
        '''

        coord = {'start': float(start), 'end': float(end), 'func': func}
        self._add_coordinate_options(coord, **kwargs)
        kwargs['size'] = kwargs['steps']
        self._data.add_coordinate(func, **kwargs)

    def get_ncoordinates(self):
        return len(self._coords)

    def add_measurement(self, ins, var, **kwargs):
        '''
        Add a measurement to the internal list.

        Input:
            ins (Instrument): the instrument to use
            var (string): the variable to measure

        Output:
            None
        '''

        meas = {'ins': ins, 'var': var}
        for key, val in kwargs.iteritems():
            meas[key] = val
        self._measurements.append(meas)

        kwargs['instrument'] = ins
        kwargs['parameter'] = var
        self._data.add_value(var, **kwargs)

    def add_measurement_func(self, func, **kwargs):
        meas = {'func': func}
        for key, val in kwargs.iter_items():
            meas[key] = val
        self._measurements.append(meas)

        kwargs['function'] = func
        self._data.add_value(func, **kwargs)

    def get_nmeasurements(self):
        return len(self._measurements)

    def emit(self, *args):
        gobject.idle_add(gobject.GObject.emit, self, *args)

    def _do_set_values(self, iter):
        '''
        Input:
            iter (int): iteration number, -1 to set starting values

        Output:
            float: extra delay required
        '''

        extra_delay = 0
        index = self.iter_to_index(iter + 1)
        coords = self.index_to_coords(index)
        self._current_coords = coords
        delta = []

        for i in xrange(len(coords)):
            delta.append(index[i] - self._last_index[i])

        if iter != -1:
            set_all = False
        else:
            set_all = True

        self._last_index = index
        self._new_data_block = False

        # Set loop variables
        for i in xrange(len(coords)):
            if delta[i] != 0:

                if i != 0:
                    self._new_data_block = True

                try:
                    val = coords[i]
                    if 'ins' in self._coords[i]:
                        ins = self._coords[i]['ins']
                        ins.set(self._coords[i]['var'], val)
                    elif 'func' in self._coords[i]:
                        func = self._coords[i]['func']
                        func(val)
                except Exception, e:
                    self.stop(str(e))
                    return False

                if 'delay' in self._coords[i]:
                    extra_delay += self._coords[i]['delay'] / 1000.0

        return extra_delay

    def _do_measurements(self):
        data = []
        for m in self._measurements:
            if 'ins' in m:
                ins = m['ins']
                data.append(ins.get(m['var']))
            elif 'func' in m:
                func = m['func']
                data.append(func())
            else:
                logging.warning('Measurement action undefined')

        return data

    def _measure(self, iter):
        '''
        The main measurement function. Convert iter to coordinates and
        set parameters accordingly. Then measure the required variables.

        Input:
            iter (int): the iteration number

        Output:
            float: extra requested timeout in ms
        '''

        gtk.gdk.threads_enter()

        coords = self._current_coords
        data = self._do_measurements()

        if iter != self._ntotal - 1:
            extra_delay = self._do_set_values(iter)
        else:
            extra_delay = 0

        gtk.gdk.threads_leave()

        cols = coords + data
        nb = {'newblock': self._new_data_block}
        self._data.add_data_point(*cols, **nb)

        if (iter % self._PROGRESS_STEPS) == 0:
            self.emit('progress', {
                'current': iter,
                'total': self._ntotal,
                })

        return extra_delay

    def start(self, blocking=False):
        '''
        Start measurement loop.

        Input:
            blocking (boolean): If false (default) do measurement in a thread.

        Output:
            None
        '''

        if len(self._coords) == 0:
            logging.info('Not starting measurement without loop')
            self.emit('finished', 'ok')
            return False

        # determine loop delay
        last_coord = self._coords[len(self._coords) - 1]
        if 'delay' in self._options:
            self._delay = self._options['delay']
        elif 'delay' in last_coord:
            self._delay = last_coord['delay']
        else:
            logging.warning('measurement delay undefined')
            return False

        # determine loop steps
        self._ntotal = 1
        for coord in self._coords:
            self._ntotal *= coord['steps']

        # Create file
        self._data.create_file(self._name)

        # Set starting values and sleep
        self._last_index = [-1 for i in xrange(len(self._coords))]
        self._do_set_values(-1)
        time.sleep(self._delay / 1000.0)

        if not blocking:
            self._thread = calltimer.CallTimerThread(self._measure, self._delay, self._ntotal)
            self._thread.connect('finished', self._finished_cb)
        else:
            self._thread = calltimer.CallTimer(self._measure, self._delay, self._ntotal)

        self._thread.start()

    def stop(self, msg):
        if self._thread is not None:
            self._thread.set_stop_request(msg)

    def _finished_cb(self, sender, msg):
        logging.debug('Measurement finished: %s', msg)
        self._data.close_file()
        self.emit('finished', msg)

    def new_data(self, data):
        self.emit('new-data', data)

    def iter_to_index(self, iter):
        ret = []
        for opts in self._coords:
            v = iter % opts['steps']
            ret.append(v)
            iter = (iter - v) / opts['steps']

        return ret

    def index_to_coords(self, index):
        ret = []
        i = 0
        for opts in self._coords:
            v = opts['start'] + index[i] * opts['stepsize']
            ret.append(v)
            i += 1

        return ret

#FIXME: Change to NamedList
class Measurements(gobject.GObject):

    def __init__(self):
        pass

measurements = None

def measure1d(
        read_ins, read_var,
        sweep_ins, sweep_var, start, end, **kwargs):

    m = Measurement()
    m.add_coordinate(start, end, sweep_ins, sweep_var, **kwargs)
    m.add_measurement(read_ins, read_var)

def measure2d(
        read_ins, read_var,
        xsweep_ins, xsweep_var, xstart, xend,
        ysweep_ins, ysweep_var, ystart, yend,
        delay,
        **kwargs):

    m = Measurement(delay=delay)

    if 'ysteps' in kwargs:
        m.add_coordinate(ysweep_ins, ysweep_var, ystart, yend,
            steps=kwargs['ysteps'])
    elif 'ystepsize' in kwargs:
        m.add_coordinate(ysweep_ins, ysweep_var, xstart, xend,
            stepsize=kwargs['ystepsize'])
    else:
        print 'measure2d() needs ysteps or ystepsize argument'

    if 'xsteps' in kwargs:
        m.add_coordinate(xsweep_ins, xsweep_var, xstart, xend,
            steps=kwargs['xsteps'])
    elif 'xstepsize' in kwargs:
        m.add_coordinate(xsweep_ins, xsweep_var, xstart, xend,
            stepsize=kwargs['xstepsize'])
    else:
        print 'measure2d() needs xsteps or xstepsize argument'

    m.add_measurement(read_ins, read_var)

    m.start()

