# qtflow.py, handle 'flow control' in the QT lab environment
# Pieter de Groot, <pieterdegroot@gmail.com>, 2008
# Reinier Heeres, <reinier@heeres.eu>, 2008
# HR@KIT/2017 (python3 conversion & cleanup for QKIT)
# YS@KIT/2018: Further emancipated from qtlab
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
import time
import qkit
from qkit.core.lib.misc import get_traceback

AutoFormattedTB = get_traceback()

class FlowControl(object):
    '''
    Class for flow control of the QT measurement environment.
    '''

    STATUS_STOPPED = 0
    STATUS_RUNNING = 1

    def __init__(self):
        
        self._status = 'starting'
        self._measurements_running = 0
        self._abort = False
        self._pause = False
        self._exit_handlers = []
        self._callbacks = {}

    #########
    ### signals
    #########

    def measurement_start(self):
        '''
        Indicate the start of a measurement.

        FIXME: The following is disabled due to lack of exception catching.
        This will increment the internal measurement counter, and if a
        measurement was not running, it will emit the 'measurement-start'
        signal.
        '''

        self._measurements_running += 1
        if self._measurements_running == 1:
            self._set_status('running')

            # Handle callbacks
            self.run_mainloop(1, wait=False)

    def measurement_end(self, abort=False):
        '''
        Indicate the end of a measurement.

        FIXME: The following is disabled due to lack of exception catching.
        This will decrement the internal measurement counter if abort=False,
        and set it to 0 in abort=True. If the counter reached zero (e.g. the
        last measurement was stopped, it will emit the 'measurement-end'
        signal.
        '''

        if abort:
            self._measurements_running = 0
        elif self._measurements_running > 0:
            self._measurements_running -= 1

        if self._measurements_running == 0:
            self._set_status('stopped')

            # Handle callbacks
            self.run_mainloop(1, wait=False)

    def run_mainloop(self, delay, wait=True):
        '''
        Run mainloop for a maximum of <delay> seconds.
        If wait is True (default), sleep until <delay> seconds have passed.
        '''
        if wait and delay > 0:
            time.sleep(delay)

    def measurement_idle(self, delay=0.0):
        '''
        Indicate that the measurement is idle and handle events.

        This function will check whether an abort has been requested and
        handle queued events for a time up to 'delay' (in seconds).
        
        Be aware that both time.time and time.sleep have a granularity of around 15ms on windows.
        However, this should not be limiting.

        It starts by emitting the 'measurement-idle' signal to allow callbacks
        to be executed by the time this function handles the event queue.
        After that it handles events and sleeps for periods of 10msec. Every
        <emit_interval> seconds it will emit another measurement-idle signal.
        '''
        start = time.time()

        while self._pause:
            self.check_abort()
            self.run_mainloop(0.01,wait=True)

        while True:
            self.check_abort()

            dt = time.time() - start
            self.run_mainloop(delay-dt, wait=False)

            dt = time.time() - start
            if dt + 0.02 < delay:
                time.sleep(0.05)
            else:
                time.sleep(max(0, delay - dt))
                return

    def _run_script(self, scriptfile):
        return execfile(scriptfile)

    def register_exit_script(self, scriptfile):
        self.register_exit_handler(lambda: self._run_script(scriptfile))

    def register_exit_handler(self, func):
        if func not in self._exit_handlers:
            self._exit_handlers.append(func)

    def exit_request(self):
        '''Run all registered exit handlers.'''
        for func in self._exit_handlers:
            try:
                func()
            except Exception as e:
                print('Error in func %s: %s' % (func.__name__, str(e)))


    ############
    ### status
    ############

    def get_status(self):
        '''Get status, one of "running", "stopped", "starting" '''
        return self._status

    def _set_status(self, val):
        self._status = val

    def finished_starting(self):
        self._status = "stopped"

    def is_measuring(self):
        return self.get_status() == 'running'

    def check_abort(self):
        '''Check whether an abort has been requested.'''

        if self._abort:
            self._abort = False
            self.measurement_end(abort=True)
            raise ValueError('Human abort')

    def set_abort(self):
        '''Request an abort.'''
        self._abort = True

    def is_paused(self):
        return self._pause

    def set_pause(self, pause):
        '''Set / unset pause state.'''
        self._pause = pause

def exception_handler(self, etype, value, tb, tb_offset=None):
    # when the 'tb_offset' keyword argument is omitted above, ipython
    # raises an error.
    TB = AutoFormattedTB(mode='Context', color_scheme='Linux', tb_offset=1)

    fc = qkit.flow

    # for the unlikely event that an error occured after pushing the
    # stop button
    fc._abort = False

    if fc.is_measuring():
        # put qtlab back in 'stopped' state
        fc.measurement_end(abort=True)

    TB(etype, value, tb)

def qtlab_exit():
    print("Closing QKIT...")
