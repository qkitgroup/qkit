# measurement_window.py, window to do 1d/2d/3d measurements
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

import gtk
import gobject
import time
import types
import logging
from gettext import gettext as _L

import qtclient as qt
from lib.gui.qtwindow import QTWindow
from lib.gui.dropdowns import AllParametersDropdown
import lib.gui as gui

import lib.misc as misc
import lib.measurement as measurement

class StepToggleButton(gtk.ToggleButton):

    def __init__(self, items, cb, desc):
        gtk.ToggleButton.__init__(self)

        self.items = items
        self.callback = cb
        self.selected = 0

        self.set_label(items[0])
        if hasattr(self, 'set_tooltip_text'):
            self.set_tooltip_text(desc)

        self.connect('clicked', self._toggle_button)

    def _toggle_button(self, w):
        self.selected = (self.selected + 1) % len(self.items)
        but = self.items[self.selected]
        self.set_label(but)
        if self.callback is not None:
            self.callback(but)

class QTSweepVarSettings(gobject.GObject):

    def __init__(self, label=None):
        gobject.GObject.__init__(self)

        self._label = label

        self._layout = None
        self.create_layout()

    def get_layout(self):
        return self._frame

    def create_layout(self):
        self._frame = gtk.Frame()
        if self._label is not None:
            self._frame.set_label(self._label)

        self._vbox = gtk.VBox(spacing=4)
        self._vbox.set_border_width(4)

        self._variable_dropdown = AllParametersDropdown(
                                    flags=qt.constants.FLAG_SET,
                                    types=(types.IntType, types.FloatType),
                                    tags=['sweep'])
        self._variable_dropdown.connect('changed', self._parameter_changed_cb)
        self._vbox.pack_start(gui.pack_hbox([
            gtk.Label(_L('Sweep variable')),
            self._variable_dropdown]), False, False)

        self._start_val = gtk.SpinButton(climb_rate=0.1, digits=2)
        self._start_val.set_range(0, 0)
        self._start_val.set_increments(0.01, 0.1)

        self._end_val = gtk.SpinButton(climb_rate=0.1, digits=2)
        self._end_val.set_range(0, 0)
        self._end_val.set_increments(0.01, 0.1)

        self._n_steps = gtk.SpinButton(climb_rate=0.1, digits=0)
        self._n_steps.set_range(0, 100000)
        self._n_steps.set_increments(1, 2)

        self._steps_or_size = StepToggleButton([_L('< Steps'), _L('Size >')],
            self._steps_toggle_cb, _L('Set number of steps or stepsize'))
        self._steps_or_size.set_size_request(100, 0)

        self._step_size = gtk.SpinButton(climb_rate=0.1, digits=3)
        self._step_size.set_range(0, 1000)
        self._step_size.set_increments(0.001, 0.01)
        self._step_size.set_sensitive(False)

        self._units_label = gtk.Label()

        self._vbox.pack_start(gui.pack_hbox([
            gtk.Label(_L('Start')),
            self._start_val,
            gtk.Label(_L('End')),
            self._end_val,
            self._units_label]))

        self._vbox.pack_start(gui.pack_hbox([
            gtk.Label(_L('Nr of steps')),
            self._n_steps,
            self._steps_or_size,
            gtk.Label(_L('Step size')),
            self._step_size]))

        self._frame.add(self._vbox)

    def _steps_toggle_cb(self, item):
        from gettext import gettext as _
        steps_sel = (item == _L('< Steps'))
        self._n_steps.set_sensitive(steps_sel)
        self._step_size.set_sensitive(not steps_sel)

    def _parameter_changed_cb(self, widget):
        sel = self._variable_dropdown.get_selection()
        if sel is not None:
            ins, varname = sel
            if ins is None:
                return

            opt = ins.get_shared_parameter_options(varname)
            if 'minval' in opt and 'maxval' in opt:
                logging.debug('Setting range %s - %s', opt['minval'], opt['maxval'])
                self._start_val.set_range(opt['minval'], opt['maxval'])
                self._end_val.set_range(opt['minval'], opt['maxval'])
            else:
                logging.info('No default range defined, setting 0 - 1')
                self._start_val.set_range(0, 1)
                self._end_val.set_range(0, 1)

            if 'units' in opt:
                self._units_label.set_text(opt['units'])

    def get_instrument_var(self):
        return self._variable_dropdown.get_selection()

    def get_units(self):
        return self._units_label.get_text()

    def get_start(self):
        return self._start_val.get_value()

    def get_end(self):
        return self._end_val.get_value()

    def get_sweep_range(self):
        return self.get_start(), self.get_end()

    def get_steps(self):
        return int(self._n_steps.get_value())

    def set_sensitive(self, sensitive):
        self._variable_dropdown.set_sensitive(sensitive)
        self._start_val.set_sensitive(sensitive)
        self._end_val.set_sensitive(sensitive)
        self._n_steps.set_sensitive(sensitive)
        self._steps_or_size.set_sensitive(sensitive)
        self._step_size.set_sensitive(sensitive)

class QTMeasureVarSettings(gobject.GObject):

    def __init__(self, label=None):
        gobject.GObject.__init__(self)

        self._label = label

        self._layout = None
        self.create_layout()

    def get_layout(self):
        return self._frame

    def create_layout(self):
        self._frame = gtk.Frame()
        if self._label is not None:
            self._frame.set_label(self._label)

        self._vbox = gtk.VBox(spacing=4)
        self._vbox.set_border_width(4)

        self._variable_dropdown = AllParametersDropdown(
                                    flags=qt.constants.FLAG_GET,
                                    types=(types.IntType, types.FloatType),
                                    tags=['measure'])
        self._variable_dropdown.connect('changed', self._parameter_changed_cb)
        self._vbox.pack_start(gui.pack_hbox([
            gtk.Label(_L('Measurement variable')),
            self._variable_dropdown]), False, False)

        self._scale = gtk.Entry()
        self._scale.set_width_chars(12)
        self._scale.set_text('1')
        self._units = gtk.Entry()
        self._units.set_width_chars(12)

        self._vbox.pack_start(gui.pack_hbox([
            gtk.Label(_L('Scaling')),
            self._scale,
            gtk.Label(_L('Units')),
            self._units]))

        self._frame.add(self._vbox)

    def _parameter_changed_cb(self, widget):
        sel = self._variable_dropdown.get_selection()
        if sel is not None:
            ins, varname = sel
            if ins is None:
                return

            opt = ins.get_shared_parameter_options(varname)
            if 'units' in opt:
                self._units.set_text(opt['units'])

    def get_instrument_var(self):
        return self._variable_dropdown.get_selection()

    def set_sensitive(self, sensitive):
        self._variable_dropdown.set_sensitive(sensitive)
        self._scale.set_sensitive(sensitive)
        self._units.set_sensitive(sensitive)

class MeasurementWindow(QTWindow):

    PLOT_IMAGE  = 1
    PLOT_LINE   = 2

    def __init__(self):
        QTWindow.__init__(self, 'measure', 'Measure')

        self.connect("delete-event", self._delete_event_cb)

        self._create_layout()

        self._plot_type = self.PLOT_IMAGE
        self._hold = False
        self._plot = None

        self._measurement = None

    def _create_layout(self):
        self._option_frame = gtk.Frame()
        self._option_frame.set_label(_L('Options'))

        self._option_vbox = gtk.VBox()
        self._option_frame.add(self._option_vbox)

        self._name_entry = gtk.Entry()
        self._option_vbox.pack_start(gui.pack_hbox([
            gtk.Label(_L('Name')), self._name_entry]), False, False)

        self._delay = gtk.SpinButton(climb_rate=0.1, digits=0)
        self._delay.set_range(0, 100000)
        self._delay.set_increments(1, 2)
        self._delay.set_value(100)
        self._option_vbox.pack_start(gui.pack_hbox([
            gtk.Label(_L('Delay (ms)')), self._delay]), False, False)

        self._plot_type_combo = gtk.combo_box_new_text()
        self._plot_type_combo.append_text(_L('Image'))
        self._plot_type_combo.append_text(_L('Line'))
        self._plot_type_combo.connect('changed', self._plot_type_changed_cb)
        self._plot_type_combo.set_active(0)
        self._option_vbox.pack_start(gui.pack_hbox([
            gtk.Label(_L('Plot type')), self._plot_type_combo]))

        self._hold_check = gtk.CheckButton()
        self._hold_check.connect('toggled', self._hold_toggled_cb)
        self._option_vbox.pack_start(gui.pack_hbox([
            gtk.Label(_L('Hold')), self._hold_check]))

        self._sweep_z = QTSweepVarSettings('Z loop')
        self._sweep_y = QTSweepVarSettings('Y loop')
        self._sweep_x = QTSweepVarSettings('X loop')

        self._measure_1 = QTMeasureVarSettings('Measurement 1')
        self._measure_2 = QTMeasureVarSettings('Measurement 2')

        self._start_but = gtk.Button(_L('Start'))
        self._start_but.connect('clicked', self._start_clicked_cb)
        self._stop_but = gtk.Button(_L('Stop'))
        self._stop_but.connect('clicked', self._stop_clicked_cb)
        self._stop_but.set_sensitive(False)

        self._status_label =  gtk.Label(_L('Idle'))

        self._vbox = gtk.VBox()
        self._vbox.pack_start(self._option_frame, False, False)

        self._vbox.pack_start(self._sweep_z.get_layout(), False, False)
        self._vbox.pack_start(self._sweep_y.get_layout(), False, False)
        self._vbox.pack_start(self._sweep_x.get_layout(), False, False)

        self._vbox.pack_start(self._measure_1.get_layout(), False, False)
        self._vbox.pack_start(self._measure_2.get_layout(), False, False)

        self._vbox.pack_start(gui.pack_hbox([
            self._start_but,
            self._stop_but]), False, False)

        self._vbox.pack_start(self._status_label)

        self.add(self._vbox)

        self._vbox.show_all()

    def _delete_event_cb(self, widget, event, data=None):
        self.hide()
        return True

    def _add_loop_var(self, measurement, sweep):
        try:
            ins, var = sweep.get_instrument_var()
            start, end = sweep.get_sweep_range()
            steps = sweep.get_steps()
        except Exception, e:
            return

        if steps == 0:
            logging.warning('Not adding sweep variable with 0 steps')
            return
        units = sweep.get_units()
        measurement.add_coordinate(ins, var, start, end,
            steps=steps, units=units)

    def _add_measurement(self, measurement, meas):
        try:
            ins, var = meas.get_instrument_var()
        except Exception, e:
            return

        measurement.add_measurement(ins, var)

    def set_sensitive(self, sensitive):
        self._sweep_x.set_sensitive(sensitive)
        self._sweep_y.set_sensitive(sensitive)
        self._sweep_z.set_sensitive(sensitive)

        self._measure_1.set_sensitive(sensitive)
        self._measure_2.set_sensitive(sensitive)

        self._start_but.set_sensitive(sensitive)
        self._stop_but.set_sensitive(not sensitive)

    def _start_clicked_cb(self, widget):
        logging.debug('Starting measurement')
        if qt.config.get('threading_warning', True):
            logging.warning('The measurement window uses threading; this could result in QTLab becoming unstable!')

        self.set_sensitive(False)

        mname = self._name_entry.get_text()
        if mname == '':
            mname = 'auto'

        delay = self._delay.get_value()

        self._measurement = measurement.Measurement(mname, delay=delay)
        self._measurement.connect('finished', self._measurement_finished_cb)
        self._measurement.connect('progress', self._measurement_progress_cb)

        self._add_loop_var(self._measurement, self._sweep_x)
        self._add_loop_var(self._measurement, self._sweep_y)
        self._add_loop_var(self._measurement, self._sweep_z)

        self._add_measurement(self._measurement, self._measure_1)
        self._add_measurement(self._measurement, self._measure_2)

        data = self._measurement.get_data()
        ncoord = self._measurement.get_ncoordinates()
        nmeas = self._measurement.get_nmeasurements()
        if ncoord == 1:
            if not self._hold:
                self._plot = qt.Plot2D()
                self._plot.add_data(data)
                if nmeas > 1:
                    self._plot.add_data(data, valdim=2, right=True)
        elif ncoord == 2:
            if self._plot_type == self.PLOT_IMAGE:
                self._plot = qt.Plot3D(data)
            else:
                self._plot = qt.Plot2D(data, coorddim=0, valdim=2)
        else:
            self._plot = None
            logging.warning('No plot available')

        if self._plot:
            self._plot.set_labels()

        self._measurement_start = time.time()
        self._measurement.start()

    def _stop_clicked_cb(self, widget):
        logging.debug('Stopping measurement')
        if self._measurement is not None:
            self._measurement.stop('User interrupt')

    def _measurement_finished_cb(self, sender, msg):
        logging.debug('Measurement finished: %s', msg)
        self.set_sensitive(True)
        if self._plot is not None:
            self._plot.save_png()

        runtime = time.time() - self._measurement_start
        self._status_label.set_text(_L('Finished in %s') % \
            misc.seconds_to_str(runtime))

    def _measurement_progress_cb(self, sender, vals):
        running = time.time() - self._measurement_start

        if vals['current'] > 0:
            predicted = running / vals['current'] * vals['total'] - running
        else:
            predicted = 0

        text = _L('Step %d / %d, running: %s, remaining: %s') % \
            (vals['current'], vals['total'], misc.seconds_to_str(running), \
            misc.seconds_to_str(predicted))
        self._status_label.set_text(text)

    def _plot_type_changed_cb(self, sender):
        if self._plot_type_combo.get_active() == 0:
            self._plot_type = self.PLOT_IMAGE
        else:
            self._plot_type = self.PLOT_LINE

    def _hold_toggled_cb(self, sender):
        self._hold = sender.get_active()

Window = MeasurementWindow

