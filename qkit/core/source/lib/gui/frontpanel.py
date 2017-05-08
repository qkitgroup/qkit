# frontpanel.py, class to create a front panel for an instrument
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

import types
import gobject
import gtk
import logging

import qtwindow
import qtclient as qt

from lib.misc import dict_to_ordered_tuples
from lib.network.object_sharer import helper

from gettext import gettext as _L

def _enable_widget(w):
    if w is not None:
        w.set_sensitive(True)

class StringLabel(gtk.Label):

    def __init__(self, ins, param, opts, autoupdate=True):
        gtk.Label.__init__(self)
        self._instrument = ins
        self._parameter = param
        self._param_opts = ins.get_shared_parameter_options(param)

        self._autoupdate = autoupdate
        if self._autoupdate:
            ins.connect('changed', self._parameter_changed_cb)

    def _update_value(self, val, widget=None):
        _enable_widget(widget)
        fmtval = qt.format_parameter_value(self._param_opts, val)
        self.set_text(fmtval)

    def do_get(self, widget=None, query=True):
        ins = self._instrument
        ins.get(self._parameter, query=query,
            callback=lambda x: self._update_value(x, widget=widget))

    def do_set(self):
        return

    def _parameter_changed_cb(self, sender, params):
        if self._parameter in params:
            self._update_value(params[self._parameter])

class StringEntry(gtk.Entry):

    def __init__(self, ins, param, opts, autoupdate=True):
        gtk.Entry.__init__(self)
        self._instrument = ins
        self._parameter = param
        self._dirty = False

        self._autoupdate = autoupdate
        if self._autoupdate:
            ins.connect('changed', self._parameter_changed_cb)

        self.connect('changed', self._entry_changed_cb)

    def _update_value(self, val, widget=None):
        _enable_widget(widget)
        self._dirty = False
        if val is None:
            val = ''
        self.set_text(val)

    def do_get(self, widget=None, query=True):
        self._instrument.get(self._parameter, query=query,
                callback=lambda x: self._update_value(x, widget=widget))

    def do_set(self, widget=None):
        self._dirty = False
        val = self.get_text()
        self._instrument.set(self._parameter, val, \
            callback=lambda x: _enable_widget(widget))

    def _parameter_changed_cb(self, sender, params):
        if self._parameter in params and not self._dirty:
            self._update_value(params[self._parameter])

    def _entry_changed_cb(self, sender, *args):
        # FIXME: how to detect whether we're dirty?
        pass

class NumberEntry(gtk.SpinButton):

    def __init__(self, ins, param, opts, autoupdate=True):
        gtk.SpinButton.__init__(self)
        self._instrument = ins
        self._parameter = param
        self._dirty = False

        minval = -1e12
        if 'minval' in opts:
            minval = opts['minval']
        maxval = 1e12
        if 'maxval' in opts:
            maxval = opts['maxval']
        self.set_range(minval, maxval)

        if 'type' in opts:
            if opts['type'] is types.IntType:
                self.set_digits(0)
                self.set_increments(1, 10)
            elif opts['type'] is types.FloatType:
                self.set_digits(2)
                self.set_increments(0.01, 0.1)

        self._autoupdate = autoupdate
        if self._autoupdate:
            ins.connect('changed', self._parameter_changed_cb)

        self.connect('changed', self._spin_changed_cb)

    def _update_value(self, val, widget=None):
        _enable_widget(widget)
        self._dirty = False
        if val is None:
            self.set_value(0)
        else:
            self.set_value(val)

    def do_get(self, widget=None, query=True):
        self._instrument.get(self._parameter, query=query,
                callback=lambda x: self._update_value(x, widget=widget))

    def do_set(self, widget=None):
        val = self.get_value()
        self._instrument.set(self._parameter, val, \
            callback=lambda *x: _enable_widget(widget))

    def _parameter_changed_cb(self, sender, params):
        if self._parameter in params and not self._dirty:
            self._update_value(params[self._parameter])

    def _spin_changed_cb(self, sender, *args):
        pass

class ComboEntry(gtk.ComboBox):

    def __init__(self, ins, param, opts, autoupdate=True):
        self._instrument = ins
        self._parameter = param
        self._dirty = False

        self._model = gtk.ListStore(gobject.TYPE_STRING)
        if 'format_map' in opts:
            self._map = opts['format_map']
            for k, v in dict_to_ordered_tuples(self._map):
                self._model.append([str(v)])
        elif 'option_list' in opts:
            self._map = opts['option_list']
            for k in self._map:
                self._model.append([str(k)])

        gtk.ComboBox.__init__(self, model=self._model)

        cell = gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, 'text', 0)

        self._autoupdate = autoupdate
        if self._autoupdate:
            ins.connect('changed', self._parameter_changed_cb)

        self.connect('changed', self._combo_changed_cb)

    def _update_value(self, val, widget=None):
        _enable_widget(widget)

        if val is None:
            return

        if type(self._map) is types.DictType and val in self._map:
            valstr = str(self._map[val])
        else:
            valstr = str(val)

        for row in self._model:
            if row[0] == valstr:
                self.set_active_iter(row.iter)
                self._dirty = False
                break

    def do_get(self, widget=None, query=True):
        self._instrument.get(self._parameter, query=query,
                callback=lambda x: self._update_value(x, widget=widget))

    def do_set(self, widget=None):
        val = self._model[self.get_active()][0]
        if val is None:
            return

        if type(self._map) is types.DictType:
            for k, v in self._map.iteritems():
                if v == val:
                    self._instrument.set(self._parameter, k, \
                        callback=lambda *x: _enable_widget(widget))
                    return
        else:
            self._instrument.set(self._parameter, val, \
                callback=lambda *x: _enable_widget(widget))

    def _parameter_changed_cb(self, sender, params):
        if self._parameter in params and not self._dirty:
            self._update_value(params[self._parameter])

    def _combo_changed_cb(self, sender, *args):
        pass

class FrontPanel(qtwindow.QTWindow):

    def __init__(self, ins):
        if type(ins) is types.StringType:
            ins = qt.instruments[ins]

        self._instrument = ins
        if ins is not None:
            name = ins.get_name()
        else:
            name = 'Instrument undefined'

        title = _L('Instrument: %s') % name
        qtwindow.QTWindow.__init__(self, name, title, add_to_main=False)
        self.connect('delete-event', self._delete_event_cb)

        self._param_info = {}

        self._table = gtk.Table(1, 3)
        self._add_parameters()
        self._add_functions()

        self._get_all_but = gtk.Button('Get all')
        self._get_all_but.connect('clicked', self._get_all_clicked_cb)

        self._vbox = gtk.VBox()
        self._vbox.pack_start(self._table)
        self._vbox.pack_start(self._get_all_but, False, False)
        self.add(self._vbox)

        self.show_all()

    def _delete_event_cb(self, widget, event, data=None):
        self.hide()
        return True

    def _create_entry(self, param, opts):
        if not opts['flags'] & qt.constants.FLAG_SET:
            entry = StringLabel(self._instrument, param, opts)
        elif 'format_map' in opts or 'option_list' in opts:
            entry = ComboEntry(self._instrument, param, opts)
        elif opts['type'] in (types.IntType, types.FloatType):
            entry = NumberEntry(self._instrument, param, opts)
        elif opts['type'] is types.BooleanType:
            opts['format_map'] = {False: 'False', True: 'True'}
            entry = ComboEntry(self._instrument, param, opts)
        else:
            entry = StringEntry(self._instrument, param, opts)

        entry.do_get(query=False)

        return entry

    def _add_parameters(self):
        rows = 0
        parameters = self._instrument.get_shared_parameters()
        for name, opts in dict_to_ordered_tuples(parameters):
            self._table.resize(rows + 1, 2)

            label = gtk.Label(name)
            self._table.attach(label, 0, 1, rows, rows + 1)

            entry = self._create_entry(name, opts)
            self._table.attach(entry, 1, 2, rows, rows + 1)

            self._param_info[name] = {
                'entry': entry,
                'flags': opts['flags'],
            }

            hbox = gtk.HBox()
            if opts['flags'] & qt.constants.FLAG_SET:
                but = gtk.Button(_L('Set'))
                but.connect('clicked', self._set_clicked, name)
                if not isinstance(entry, ComboEntry):
                   entry.connect('activate', self._set_clicked, name)
                hbox.pack_start(but)
            if opts['flags'] & qt.constants.FLAG_GET or \
                    opts['flags'] & qt.constants.FLAG_SOFTGET:
                but = gtk.Button(_L('Get'))
                but.connect('clicked', self._get_clicked, name)
                hbox.pack_start(but)

            self._table.attach(hbox, 2, 3, rows, rows + 1)
            rows += 1

    def _enable_func(self, fname, enable):
        self._func_buttons[fname].set_sensitive(enable)

    def _func_clicked_cb(self, sender, fname):
        if not hasattr(self._instrument, fname):
            logging.error('Instrument does not have function %s', fname)
            return
        func = getattr(self._instrument, fname)
        self._enable_func(fname, False)
        try:
            func(callback=lambda x: self._enable_func(fname, True))
        except Exception, e:
            logging.warning('Function call failed: %s', e)

    def _add_functions(self):
        self._func_buttons = {}
        rows = self._table.props.n_rows
        functions = self._instrument.get_functions()
        for fname, fopts in dict_to_ordered_tuples(functions):
            anames = fopts['argspec']['args']
            adefaults = fopts['argspec']['defaults']
            for i, aname in enumerate(anames):
                if aname == 'self':
                    continue
                if adefaults is not None and i >= len(anames) - len(adefaults):
                    default = adefaults[i - len(anames) + len(adefaults)]
                else:
                    default = ''

            but = gtk.Button(fname)
            self._func_buttons[fname] = but
            but.connect('clicked', self._func_clicked_cb, fname)
            self._table.attach(but, 0, 3, rows, rows + 1)
            rows += 1

    def _set_clicked(self, widget, param):
        widget.set_sensitive(False)
        val = self._param_info[param]['entry'].do_set(widget=widget)

    def _get_clicked(self, widget, param):
        widget.set_sensitive(False)
        self._param_info[param]['entry'].do_get(widget=widget)

    def _get_all_clicked_cb(self, sender):
        for key, info in self._param_info.iteritems():
            if info['flags'] & qt.constants.FLAG_GET or \
                    info['flags'] & qt.constants.FLAG_SOFTGET:
                info['entry'].do_get()

