# calltimer.py, class to do a callback several times in a separate thread.
# Reinier Heeres, <reinier@heeres.eu>, 2008
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

import logging
import gobject
#gobject.threads_init()

import gtk
#gtk.gdk.threads_init()

import threading
import time
from misc import exact_time

class ThreadSafeGObject(gobject.GObject):

    def __init__(self, *args, **kwargs):
        gobject.GObject.__init__(self, *args, **kwargs)

    def _idle_emit(self, signal, *args):
        try:
            gobject.GObject.emit(self, signal, *args)
        except Exception, e:
            print 'Error: %s' % e

    def emit(self, signal, *args):
        gobject.idle_add(self._idle_emit, signal, *args)

class GObjectThread(threading.Thread, ThreadSafeGObject):

    def __init__(self, *args, **kwargs):
        gobject.GObject.__init__(self, *args, **kwargs)
        threading.Thread.__init__(self)

        self.stop = ThreadVariable(False)

class TimedLock():
    def __init__(self, delay=1.0):
        self._lock = threading.Lock()
        self._delay = delay

    def acquire(self):
        n = int(self._delay / 0.01)
        for i in range(n):
            if self._lock.acquire(False):
                return True
            time.sleep(0.01)
        return False

    def release(self):
        self._lock.release()

class ThreadVariable():
    def __init__(self, value=None):
        self._value = value
        self._lock = threading.Lock()

    def get(self):
        self._lock.acquire()
        ret = self._value
        self._lock.release()
        return ret

    def set(self, value):
        self._lock.acquire()
        self._value = value
        self._lock.release()

class CallTimerThread(GObjectThread):
    '''
    Class to several times do a callback with a specified delay in a separate
    thread.
    '''

    __gsignals__ = {
        'finished': (gobject.SIGNAL_RUN_FIRST,
                    gobject.TYPE_NONE,
                    ([gobject.TYPE_PYOBJECT])),
    }

    def __init__(self, cb, delay, n, *args, **kwargs):
        '''
        Create CallTimerThread

        Input:
            cb (function): callback
            delay (float): time delay in ms
            n (int): number of times to call
            *args: optional arguments to the callback
            **kwargs: optional named arguments to the callback
        '''

        GObjectThread.__init__(self)

        self._cb = cb
        self._delay = delay
        self._n = n
        self._args = args
        self._kwargs = kwargs

        self._stop_lock = threading.Lock()
        self._stop_requested = False

    def run(self):
        tstart = exact_time()
        extra_delay = 0

        i = 0
        while i < self._n:
            f = self._cb

            try:
                extra_delay += f(i, *self._args, **self._kwargs)
            except Exception, e:
                self.emit('finished')
                raise e

            if self.get_stop_request():
                logging.info('Stop requested')
                self.emit('finished', self._stop_message)
                return

            i += 1
            if i == self._n:
                break

            # delay
            tn = exact_time()
            if 'time_exact' in self._kwargs:
                req_delay = tstart + extra_delay / 1000.0 + float(i) * self._delay / 1000.0 - tn
                if req_delay > 0:
                    time.sleep(req_delay)
            else:
                time.sleep((extra_delay + self._delay) / 1000.0)

        self.emit('finished', 'ok')

    def set_stop_request(self, msg):
        self._stop_lock.acquire()
        self._stop_requested = True
        self._stop_message = msg
        self._stop_lock.release()

    def get_stop_request(self):
        self._stop_lock.acquire()
        ret = self._stop_requested
        self._stop_lock.release()
        return ret

    def get_stop_message(self):
        return self._stop_message

class CallTimer:
    '''
    Class to several times do a callback with a specified delay, blocking.
    '''

    def __init__(self, cb, delay, n, *args, **kwargs):
        '''
        Create CallTimer

        Input:
            cb (function): callback
            delay (float): time delay in ms
            n (int): number of times to call
            *args: optional arguments to the callback
            **kwargs: optional named arguments to the callback
        '''

        self._cb = cb
        self._delay = delay
        self._n = n
        self._args = args
        self._kwargs = kwargs

    def start(self):
        import qt
        tstart = exact_time()

        i = 0
        while i < self._n:
            self._cb(i, *self._args, **self._kwargs)

            i += 1
            if i == self._n:
                break

            # delay
            tn = exact_time()
            req_delay = tstart + float(i) * self._delay / 1000.0 - tn
            if req_delay > 0:
                qt.msleep(req_delay)

class ThreadCall(threading.Thread):
    '''
    Class to execute a function in a separate thread.
    '''

    def __init__(self, func, *args, **kwargs):
        '''
        Input:
            func (function): function to call
            *args: optional arguments to the function
            **kwargs: optional named arguments to the function
        '''

        threading.Thread.__init__(self)

        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._return_value = None

        self.start()

    def run(self):
        ret = self._func(*self._args, **self._kwargs)
        self._return_value = ret

    def get_return_value(self):
        return self._return_value
