import qkit
from qkit.core.instrument_base import Instrument
import types
import logging
import numpy
# from plot_engines.qtgnuplot import get_gnuplot
# from plot import plot
import time
import os

from lib.scheduler import Scheduler


class virtual_Tlogger(Instrument):

    def __init__(self, name, igh=None):
        Instrument.__init__(self, name, tags=['virtual'])

        self._igh = qkit.instruments.get(igh)

        self.add_parameter('timeout',
                           type=float,
                           flags=Instrument.FLAG_GETSET,
                           units='sec')
        self.add_parameter('idle_mintime',
                           type=float,
                           flags=Instrument.FLAG_GETSET,
                           units='sec')
        self.add_parameter('slow_mintime',
                           type=float,
                           flags=Instrument.FLAG_GETSET,
                           units='sec')
        self.add_parameter('disk_mintime',
                           type=float,
                           flags=Instrument.FLAG_GETSET,
                           units='sec')
        self.add_parameter('timeout_mode',
                           type=bool,
                           flags=Instrument.FLAG_GET)
        self.add_parameter('idle_mode',
                           type=bool,
                           flags=Instrument.FLAG_GET)
        self.add_parameter('plot_enable',
                           type=bool,
                           flags=Instrument.FLAG_GET)
        self.add_parameter('status',
                           type=str,
                           flags=Instrument.FLAG_GET)

        self.add_function('start')
        self.add_function('stop')
        self.add_function('plot_start')
        self.add_function('plot_stop')
        self.add_function('set_default_fast')
        self.add_function('set_default_slow')

        self._debug_counter = 0

        self._timeout = 10
        self._idle_mintime = 10
        self._slow_mintime = 300
        self._disk_mintime = 10

        self._slow_lasttime = 0
        self._disk_lasttime = 0

        self.plot_stop()

        self._dir = os.path.join(qkit.cfg.get('datadir'), 'Tlog')
        self._filebasename = 'temperature_log'
        self._this_month = None

        if not os.path.isdir(self._dir):
            os.makedirs(self._dir)

        self._last_hour = TimeBuffer(60 * 60, self._dir, 'last_hour.dat')
        self._last_12hour = TimeBuffer(60 * 60 * 12, self._dir, 'last_12hour.dat')

        self._task = Scheduler(self._run_all, self._timeout, self._idle_mintime, timeout_mode=True, idle_mode=True)
        self._status = 'running'

        self.get_all()

    def get_all(self):
        self.get_timeout()
        self.get_idle_mintime()
        self.get_slow_mintime()
        self.get_disk_mintime()

        self.get_timeout_mode()
        self.get_idle_mode()

        self.get_plot_enable()
        self.get_status()

    def set_default_fast(self):
        self.set_timeout(10)
        self.set_idle_mintime(10)
        self.set_slow_mintime(300)
        self.set_disk_mintime(10)

    def set_default_slow(self):
        self.set_timeout(300)
        self.set_idle_mintime(300)
        self.set_slow_mintime(300)
        self.set_disk_mintime(300)

    def _do_set_timeout(self, to):
        self._task.set_timeout(to)

    def _do_get_timeout(self):
        return self._task.get_timeout()

    def _do_set_idle_mintime(self, imt):
        self._task.set_idle_mintime(imt)

    def _do_get_idle_mintime(self):
        return self._task.get_idle_mintime()

    def _do_set_slow_mintime(self, smt):
        self._slow_mintime = smt

    def _do_get_slow_mintime(self):
        return self._slow_mintime

    def _do_set_disk_mintime(self, dmt):
        self._disk_mintime = dmt

    def _do_get_disk_mintime(self):
        return self._disk_mintime

    def _do_get_timeout_mode(self):
        return self._task.get_timeout_mode()

    def _do_get_idle_mode(self):
        return self._task.get_idle_mode()

    def _do_get_status(self):
        return self._status

    def _do_get_plot_enable(self):
        return self._plot_enable

    def start_idle(self):
        self._task.set_idle_mode(True)
        self.get_idle_mode()

    def stop_idle(self):
        self._task.set_idle_mode(False)
        self.get_idle_mode()

    def start_timeout(self):
        self._task.set_timeout_mode(True)
        self.get_timeout_mode()

    def stop_timeout(self):
        self._task.set_timeout_mode(False)
        self.get_timeout_mode()

    def start(self):
        self._task.start()
        self._status = 'running'
        self.get_status()

    def stop(self):
        self._task.stop()
        self._status = 'stopped'
        self.get_status()

    def _get_all_sensors(self):
        try:
            self._temperature = self._igh.get_temp_mc()
        except:
            logging.error(__name__ + ': failed to retrieve temperature.')

    def _get_all_sensors_dummy(self):
        self._temperature = numpy.sin(time.time() / 60 / 10 * 2 * numpy.pi)

    def _run_all(self):

        self._debug_counter += 1

        now = time.time()

        # get temperature
        # self._get_all_sensors_dummy()
        self._get_all_sensors()

        # add last points to 'fast' buffer (last hour).
        # self.fast_time, turn off fast?
        self._last_hour.add([now, self._temperature])

        # add points to 'slow' buffer (last 24 hour) if last point was written more then self.slow_time ago.
        if (now - self._slow_lasttime) > self._slow_mintime:
            self._slow_lasttime = now
            self._last_12hour.add([now, self._temperature])

        # add points to diskfile if last write was more then self.disk_time ago
        if (now - self._disk_lasttime) > self._disk_mintime:
            self._disk_lasttime = now
            self.write_to_logfile()

        # update plot, if plotting is enabled.
        self.plot()

        # leave here for checking timing:
        # print 'time it took: %f' % (time.time() - now)

    def plot_start(self):
        self._plot_enable = True
        self.get_plot_enable()

    def plot_stop(self):
        self._plot_enable = False
        self.get_plot_enable()

    def plot(self):
        plot(self._last_hour.get(), name='Temperature 1 hr', clear=True)
        plot(self._last_12hour.get(), name='Temperature 12 hr', clear=True)

    def write_to_logfile(self):
        # TODO close file? probably not necessary
        now = time.time()
        now_tuple = time.localtime(now)
        this_month = now_tuple[0:1]
        if self._this_month is None:
            self._this_month = this_month
            file_prefix = time.strftime('%Y_%m', now_tuple)
            self.filename = '%s_%s.txt' % (file_prefix, self._filebasename)
            self.filepath = os.path.join(self._dir, self.filename)
            self.file = file(self.filepath, 'a')
        elif self._this_month is not this_month:
            self.file.close()
            self._this_month = this_month
            file_prefix = time.strftime('%Y_%m', now_tuple)
            self.filename = '%s_%s.txt' % (file_prefix, self._filebasename)
            self.filepath = os.path.join(self._dir, self.filename)
            self.file = file(self.filepath, 'a')

        self.file.write('%f\t%s\t%f\n' % (now, time.asctime(now_tuple), self._temperature))

        self.file.flush()


#    def plot_init(self):
#        self._g = get_gnuplot('Tlog')
#
#        #self._g.cmd('set terminal x11 enhanced font "arial,15"') # TODO make windows proof
#        #self._g.cmd('set terminal win enhanced font "arial,15"')
#        #self._g.cmd('set terminal win enhanced')
#
#        self._g.cmd('unset key')
#        self._g.cmd('unset mouse')
#
#        self._g.cmd('set grid')
#        #self._g.cmd('set multiplot')
#        self._g.cmd('set size 0.45,0.5')
#
#        self._g.cmd('set xdata time')
#        self._g.cmd('set timefmt "%s"')
#        self._g.cmd('set format x "%H:%M:%S"')
#        self._g.cmd('set xtics rotate by -90') # put tilted when enhanced works
#
#        #self._g.cmd('set offsets 0.1,0.1,0.1,0.1')
#
#        self._g.cmd('set label 1 at screen 0.43,0.98')
#        self._g.cmd('set label 1 "last hour" center')
#
#        self._g.cmd('set label 2 at screen 0.83,0.98')
#        self._g.cmd('set label 2 "last 24 hours" center')
#
#        self._g.cmd('set label 11 at screen 0.01,0.85')
#        self._g.cmd('set label 12 at screen 0.01,0.8')
#        self._g.cmd('set label 13 at screen 0.01,0.7')
#        self._g.cmd('set label 21 at screen 0.01,0.4')
#        self._g.cmd('set label 22 at screen 0.01,0.35')
#        self._g.cmd('set label 23 at screen 0.01,0.25')

#    def plot(self):
#        if (not self._config['auto-update']) or (not self._plot_enable):
#            return
#
#        if not self._g.is_alive():
#            self.plot_init()
#
#        now = time.time()
#
#        fpA = self._last_hour_A.dump_to_file()
#        dA_xrange = self._last_hour_A.get_xrange()
#        dA_yrange = self._last_hour_A.get_yrange()
#
#        fpA24 = self._last_24hour_A.dump_to_file()
#        dA24_xrange = self._last_24hour_A.get_xrange()
#        dA24_yrange = self._last_24hour_A.get_yrange()
#
#        fpB = self._last_hour_B.dump_to_file()
#        dB_xrange = self._last_hour_B.get_xrange()
#        dB_yrange = self._last_hour_B.get_yrange()
#
#        fpB24 = self._last_24hour_B.dump_to_file()
#        dB24_xrange = self._last_24hour_B.get_xrange()
#        dB24_yrange = self._last_24hour_B.get_yrange()
#
#        self._g.cmd('clear')
#
#        self._g.cmd('set label 11 "%s"' % self._sensorA.channel_name)
#
#        self._g.cmd('set label 12 "%s\\n(%s)"' % (self._sensorA.sensor_name, self._sensorA.vbias))
#
#        t = '%f' % self._sensorA.temperature
#        t = t[0:8]
#        self._g.cmd('set label 13 "%s %s"' % (t, self._sensorA.unit)) # enhanced mode in windows gives plotting bug after ~ 600 x plotting
#        #self._g.cmd('set label 13 "{/=20 %s %s} "' % (t, self._sensorA.unit)) # space after } must be there because of gnuplot bug!
#
#        self._g.cmd('set label 21 "%s"' % self._sensorB.channel_name)
#
#        self._g.cmd('set label 22 "%s\\n(%s)"' % (self._sensorB.sensor_name, self._sensorB.vbias))
#
#        t = '%f' % self._sensorB.temperature
#        t = t[0:8]
#        self._g.cmd('set label 23 "%s %s"' % (t, self._sensorB.unit)) # enhanced mode in windows gives plotting bug after ~600 x plotting
#        #self._g.cmd('set label 23 "{/=20 %s %s} "' % (t, self._sensorB.unit)) # space after } must be there because of gnuplot bug!
#
#        self._g.cmd('set multiplot')
#
#        self._g.cmd('set origin 0.15,0.45')
#        self._g.cmd('set xrange ["%f":"%f"]' % dA_xrange)
#        self._g.cmd('set yrange [%f:%f]' % dA_yrange)
#        #self._g.cmd('set xtics %i' % (20*60))
#        self._g.cmd('plot "%s" using 1:2' % fpA)
#
#        self._g.cmd('set origin 0.55,0.45')
#        self._g.cmd('set xrange ["%f":"%f"]' % dA24_xrange)
#        self._g.cmd('set yrange [%f:%f]' % dA24_yrange)
#        self._g.cmd('plot "%s" using 1:2' % fpA24)
#
#        self._g.cmd('set origin 0.15,0.0')
#        self._g.cmd('set xrange ["%f":"%f"]' % dB_xrange)
#        self._g.cmd('set yrange [%f:%f]' % dB_yrange)
#        self._g.cmd('plot "%s" using 1:2' % fpB)
#
#        self._g.cmd('set origin 0.55,0.0')
#        self._g.cmd('set xrange ["%f":"%f"]' % dB24_xrange)
#        self._g.cmd('set yrange [%f:%f]' % dB24_yrange)
#        self._g.cmd('plot "%s" using 1:2' % fpB24)
#
#        self._g.cmd('unset multiplot')


class TimeBuffer():

    def __init__(self, maxtime, dir, filename):
        self.maxtime = maxtime

        self.fp = os.path.join(dir, filename)
        self.fp = self.fp.replace('\\', '/')

    def add(self, list):
        try:
            self.buffer
        except AttributeError:
            self.buffer = [list]
            return
        self.buffer.append(list)
        self.flush()

    def flush(self):
        i = 0
        now = time.time()
        while (now - self.buffer[i][0]) > self.maxtime:
            i += 1
        self.buffer = self.buffer[i:]

    def get(self):
        return self.buffer

    def dump_to_file(self):
        f = file(self.fp, 'w')
        for i in range(len(self.buffer)):
            f.write('%f\t%f\n' % (self.buffer[i][0], self.buffer[i][1]))
        f.close()
        return self.fp

    def get_xrange(self):
        xmin = min([self.buffer[i][0] for i in range(len(self.buffer))])
        xmax = max([self.buffer[i][0] for i in range(len(self.buffer))])
        xspan = xmax - xmin
        if xspan == 0:
            xmin = xmin - 1
            xmax = xmax + 1
        else:
            xmin = xmin - 0.1 * xspan
            xmax = xmax + 0.1 * xspan
        return (xmin, xmax)

    def get_yrange(self):
        ymin = min([self.buffer[i][1] for i in range(len(self.buffer))])
        ymax = max([self.buffer[i][1] for i in range(len(self.buffer))])
        yspan = ymax - ymin
        if yspan == 0:
            ymin = ymin - 0.01
            ymax = ymax + 0.01
        else:
            ymin = ymin - 0.1 * yspan
            ymax = ymax + 0.1 * yspan
        return (ymin, ymax)
