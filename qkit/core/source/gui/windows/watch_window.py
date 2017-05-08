# watch_window.py, window to watch one or more instrument parameters
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
import logging
import qtclient as qt

from gettext import gettext as _L

import lib.gui as gui
from lib.gui.qttable import QTTable
from lib.gui import dropdowns, qtwindow
from lib import temp

import numpy as np

def gptime():
    s = time.strftime('%Y-%m-%d %H:%M:%S')
    return s

_start = None
def timesec():
    global _start
    if _start is None:
        _start = time.time()
    return time.time() - _start

def do_print(r):
    print 'ret: %r' % (r, )

class WatchWindow(qtwindow.QTWindow):

    ORDERID = 22

    def __init__(self):
        qtwindow.QTWindow.__init__(self, 'watch', 'Watch')
        self.connect("delete-event", self._delete_event_cb)
        qt.flow.connect('measurement-start', self._mstart_cb)
        qt.flow.connect('measurement-end', self._mend_cb)

        self._watch = {}
        self._paused = False

        self._frame = gtk.Frame()
        self._frame.set_label(_L('Add variable'))

        self._ins_combo = dropdowns.InstrumentDropdown()
        self._ins_combo.connect('changed', self._instrument_changed_cb)

        self._param_combo = dropdowns.InstrumentParameterDropdown()
        self._param_combo.connect('changed', self._parameter_changed_cb)

        label = gtk.Label(_L('Interval'))
        self._interval = gtk.SpinButton(climb_rate=1, digits=0)
        self._interval.set_range(0, 100000)
        self._interval.set_value(500)
        interval = gui.pack_hbox([label, self._interval, gtk.Label('ms')],
                False, False)

        self._graph_check = gtk.CheckButton('Graph')
        self._graph_check.set_active(True)
        self._graph_check.connect('toggled', self._graph_toggled_cb)
        label = gtk.Label('Data points')
        self._npoints = gtk.SpinButton(climb_rate=1, digits=0)
        self._npoints.set_range(10, 1000)
        self._npoints.set_value(100)
        self._npoints.set_increments(1, 10)
        graph = gui.pack_hbox([self._graph_check, label, self._npoints],
                True, False)

        self._ma_check = gtk.CheckButton('Moving average')
        self._ma_check.set_active(False)
        self._ma_check.connect('toggled', self._ma_toggled_cb)
        label = gtk.Label('Constant')
        self._ma_const = gtk.SpinButton(climb_rate=0.01, digits=2)
        self._ma_const.set_sensitive(False)
        self._ma_const.set_range(0, 1.0)
        self._ma_const.set_increments(0.01, 0.1)
        self._ma_const.set_value(0.95)
        ma = gui.pack_hbox([self._ma_check, label, self._ma_const],
                True, False)

        self._add_button = gtk.Button(_L('Add'))
        self._add_button.connect('clicked', self._add_clicked_cb)
        self._remove_button = gtk.Button(_L('Remove'))
        self._remove_button.connect('clicked', self._remove_clicked_cb)
        self._pause_button = gtk.ToggleButton(_L('Pause'))
        self._pause_button.set_active(False)
        self._pause_button.connect('clicked', self._toggle_pause_cb)
        buttons = gui.pack_hbox([self._add_button, self._remove_button,
                self._pause_button], False, False)

        self._tree_model = gtk.ListStore(str, str, str)
        self._tree_view = QTTable([
            (_L('Parameter'), {}),
            (_L('Delay'), {}),
            (_L('Value'), {'scale': 3.0}),
            ], self._tree_model)

        vbox = gui.pack_vbox([
            self._ins_combo,
    		self._param_combo,
    		interval,
            graph,
            ma,
    		buttons,
    	], False, False)
        vbox.set_border_width(4)
        self._frame.add(vbox)

        vbox = gui.pack_vbox([
            self._frame,
            self._tree_view,
        ], False, False)
        self.add(vbox)

        vbox.show_all()

    def _delete_event_cb(self, widget, event, data=None):
        self.hide()
        return True

    def set_paused(self, paused):
        logging.info('Watch win: setting paused to %s', paused)
        self._pause_button.set_active(paused)
        self._paused = paused

    def get_paused(self):
        return self._paused

    def _mstart_cb(self, sender):
        self.set_paused(True)

    def _mend_cb(self, sender):
        self.set_paused(False)

    def _toggle_pause_cb(self, sender):
        self.set_paused(not self.get_paused())

    def _instrument_changed_cb(self, widget):
        ins = self._ins_combo.get_instrument()
        self._param_combo.set_instrument(ins)

    def _parameter_changed_cb(self, widget):
        param = self._param_combo.get_parameter()

    def _graph_toggled_cb(self, widget):
        active = self._graph_check.get_active()
        self._npoints.set_sensitive(active)

    def _ma_toggled_cb(self, widget):
        active = self._ma_check.get_active()
        self._ma_const.set_sensitive(active)

    def _receive_reply(self, ins_param, result):
        if ins_param not in self._watch:
            return

        # Update delay if we're querying too fast
        info = self._watch[ins_param]
        delta = time.time() - info['req_t']
        info['avgtime'] = info['avgtime'] * 0.9 + delta * 0.1
        if info['avgtime'] > info['delay'] / 1000.0:
            self._set_delay(ins_param, info['delay'] * 2)
        info['reply_received'] = True
        self._update_cb(None, ins_param, result)

    def _query_ins(self, ins_param):
        info = self._watch[ins_param]
        if not info['reply_received'] or self._paused:
            logging.info('Not querying...')
            return True

        info['reply_received']= False
        info['req_t']= time.time()
        ins = info['instrument']
        param = info['parameter']
        ins.get(param, callback=lambda x: self._receive_reply(ins_param, x))

        return True

    def _ins_changed_cb(self, sender, changes, param, ins_param):
        if ins_param not in self._watch or param not in changes:
            return
        info = self._watch[ins_param]
        self._update_cb(None, ins_param, changes[param])

    def _add_clicked_cb(self, widget):
        ins = self._ins_combo.get_instrument()
        param = self._param_combo.get_parameter()
        if ins is None or param is None:
            return
        delay = int(self._interval.get_value())
        ins_param = ins.get_name() + "." + param
        if ins_param in self._watch:
            return

        iter = self._tree_model.append((ins_param, '%d ms' % delay, ''))
        info = {
            'instrument': ins,
            'parameter': param,
            'delay': delay,
            'avgtime': delay / 1000.0,
            'reply_received': True,
            'iter': iter,
            'options': ins.get_shared_parameter_options(param),
            'graph': self._graph_check.get_active(),
            'points': self._npoints.get_value(),
            'ma': self._ma_check.get_active(),
            'ma_const': self._ma_const.get_value(),
        }

        self._watch[ins_param] = info
        if delay != 0:
            hid = gobject.timeout_add(int(delay), self._query_ins, ins_param)
        else:
            hid = ins.connect('changed', lambda sender, changes: \
                    self._ins_changed_cb(sender, changes, param, ins_param))

        self._watch[ins_param]['hid'] = hid

    def _get_ncols(self, info, val):
        nvals = 1
        try:
            nvals = len(val)
        except:
            pass
        if info['ma']:
            nvals *= 2
        return nvals + 1

    def _get_row(self, info, val, prevrow=None):
        row = [timesec()]
        mac = info['ma_const']
        try:
            for i, v in enumerate(val):
                row.append(v)
                if info['ma']:
                    if prevrow is not None and info['ma']:
                        row.append(prevrow[2*i+2] * mac + (1 - mac) * v)
                    else:
                        row.append(v)
        except:
            row.append(val)
            if info['ma']:
                if prevrow is not None:
                    row.append(prevrow[2] * mac + (1 - mac) * val)
                else:
                    row.append(val)

        return row

    def _update_cb(self, sender, ins_param, val):
        if ins_param not in self._watch:
            return

        info = self._watch[ins_param]
        ins = info['instrument']
        param = info['parameter']
        strval = qt.format_parameter_value(info['options'], val)
        self._tree_model.set(info['iter'], 2, strval)

        if not info.get('graph', False):
            return

        plotname = 'watch_%s.%s' % (ins.get_name(), param)
        if 'data' not in info or info['data'] is None:
            cols = self._get_ncols(info, val)
            d = np.zeros([info['points'], cols], dtype=np.float)
            r = self._get_row(info, val)
            d[0,:] = self._get_row(info, val)
            info['data'] = d
            info['tempfile'] = temp.File(mode='w')

            cmd = 'qt.plot_file("%s", name="%s", clear=True)' % (info['tempfile'].name, plotname)
            qt.cmd(cmd, callback=lambda *x: do_print(x))
            for i in range(cols - 2):
                cmd = 'qt.plot_file("%s", name="%s", valdim=%d)' % (info['tempfile'].name, plotname, i+2)
                qt.cmd(cmd, callback=lambda *x: do_print(x))

        else:
            info['tempfile'].reopen()

        info['data'][0:-1,:] = info['data'][1:,:]
        r = self._get_row(info, val, prevrow=info['data'][-2,:])
        info['data'][-1,:] = self._get_row(info, val, prevrow=info['data'][-2,:])
        np.savetxt(info['tempfile'].get_file(), info['data'])
        info['tempfile'].close()
        cmd = 'qt.plots["%s"].update()' % (plotname, )
        qt.cmd(cmd)

    def _set_delay(self, ins_param, delay):
        info = self._watch[ins_param]
        gobject.source_remove(info['hid'])
        info['hid'] = gobject.timeout_add(int(delay), self._query_ins, ins_param)
        info['delay'] = delay
        strval = '%d ms' % (delay,)
        self._tree_model.set(info['iter'], 1, strval)

    def _remove_clicked_cb(self, widget):
        (model, rows) = self._tree_view.get_selection().get_selected_rows()
        for row in rows:
            iter = model.get_iter(row)
            ins_param = model.get_value(iter, 0)
            model.remove(iter)

            info = self._watch[ins_param]
            if info['delay'] != 0:
                gobject.source_remove(info['hid'])
            else:
                info['ins'].disconnect(info['hid'])
            del self._watch[ins_param]

Window = WatchWindow

