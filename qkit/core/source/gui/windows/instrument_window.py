# instrument_window.py, window to monitor instruments
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

import logging
from gettext import gettext as _L

import lib.gui as gui
from lib.gui import dropdowns, qtwindow

from lib.network.object_sharer import helper

import qtclient as qt

class QTInstrumentFrame(gtk.VBox):

    def __init__(self, ins, show_range, show_rate, **kwargs):
        gtk.VBox.__init__(self, **kwargs)

        self._label = gtk.Label()
        self._label.set_tooltip_text(_L('Click to expand / collapse info'))
        self._label.set_alignment(0, 0)
        self._eventbox = gtk.EventBox()
        self._eventbox.add(self._label)
        self._eventbox.connect('button-press-event', self._label_clicked_cb)
        self._eventbox.show_all()
        self.pack_start(self._eventbox, False, False)

        self._table = gtk.Table(1, 5)
        self._table.set_col_spacings(10)
        self._table.set_col_spacing(0, 50)
        self._table.show()
        self.pack_start(self._table, False, False)

        self._instrument = ins
        self._instrument_name = ins.get_name()
        self._label_name = {}
        self._label_val = {}
        self._label_range = {}
        self._label_rate = {}
        self._update_dict = {}
        self._cur_val = {}
        self._row_num = {}
        self._reorder_hid = None

        # For formatting
        self._parameter_options = {}

        self._add_parameters()

        ins.connect('parameter-added', self._parameter_added_cb)
        ins.connect('parameter-changed', self._parameter_changed_cb)
        ins.connect('parameter-removed', self._parameter_removed_cb)

        self.show_table(True)
        self.show()
        self.show_range_column(show_range)
        self.show_rate_column(show_rate)

        # Update variables twice per second
        gobject.timeout_add(500, self._do_update_parameters_timer)

    def _add_parameter_by_name(self, param):
        if param in self._label_name:
            return

        popts = self._instrument.get_shared_parameter_options(param)
        self._parameter_options[param] = popts
        nrows = self._table.props.n_rows
        self._table.resize(nrows + 1, 5)

        if 'doc' in popts:
            plabel = gtk.Label(param + ' [?]')
            plabel.set_tooltip_text(popts['doc'])
        else:
            plabel = gtk.Label(param)

        plabel.set_alignment(0, 0)
        plabel.show()
        self._row_num[param] = nrows
        self._table.attach(plabel, 1, 2, nrows, nrows + 1)

        vlabel = gtk.Label()
        val = self._instrument.get(param, query=False)
        self._cur_val[param] = val
        vlabel.set_markup('<b>%s</b>' % \
                qt.format_parameter_value(self._parameter_options[param], val))
        vlabel.set_alignment(0, 0)
        vlabel.show()
        self._table.attach(vlabel, 2, 3, nrows, nrows + 1)

        self._add_range_info(param, nrows)
        self._add_rate_info(param, nrows)

        self._label_name[param] = plabel
        self._label_val[param] = vlabel

    def _add_range_info(self, param, rownum):
        text = self._instrument.format_range(param)
        rlabel = gtk.Label(text)
        rlabel.set_justify(gtk.JUSTIFY_LEFT)
        rlabel.show()
        self._table.attach(rlabel, 3, 4, rownum, rownum + 1)

        self._label_range[param] = rlabel

    def _add_rate_info(self, param, rownum):
        text = self._instrument.format_rate(param)
        rlabel = gtk.Label(text)
        rlabel.set_justify(gtk.JUSTIFY_LEFT)
        rlabel.show()
        self._table.attach(rlabel, 4, 5, rownum, rownum + 1)

        self._label_rate[param] = rlabel

    def _add_parameters(self):
        parameters = self._instrument.get_parameter_names()
        parameters.sort()
        for param in parameters:
            self._add_parameter_by_name(param)

        self.show()

    def _parameter_added_cb(self, sender, name):
        self._add_parameter_by_name(name)
        self._delayed_reorder()

    def _reorder_table(self, ofs):
        parameters = self._label_name.keys()
        nrows = len(parameters) + ofs
        self._table.resize(nrows + 1, 5)
        parameters.sort()
        for i, param in enumerate(parameters):
            if self._row_num[param] == ofs + i:
                continue

            self._table.remove(self._label_name[param])
            self._table.attach(self._label_name[param],
                    1, 2, i + ofs, i + ofs + 1)
            self._table.remove(self._label_val[param])
            self._table.attach(self._label_val[param],
                    2, 3, i + ofs, i + ofs + 1)
            self._table.remove(self._label_range[param])
            self._table.attach(self._label_range[param],
                    3, 4, i + ofs, i + ofs + 1)
            self._table.remove(self._label_rate[param])
            self._table.attach(self._label_rate[param],
                    4, 5, i + ofs, i + ofs + 1)

        self._reorder_hid = None

    def _delayed_reorder(self):
        if self._reorder_hid is None:
            self._reorder_hid = gobject.timeout_add(500,
                    lambda: self._reorder_table(1))

    def _parameter_removed_cb(self, sender, param):
        for i in self._label_name, self._label_val, self._label_range, self._label_rate:
            self._table.remove(i[param])
            del i[param]

        if param in self._update_dict:
            del self._update_dict[param]
        del self._cur_val[param]
        del self._row_num[param]
        del self._parameter_options[param]

        self._reorder_table(1)

    def _do_update_parameters_timer(self):
        gtk.gdk.threads_enter()

        for param, val in self._update_dict.iteritems():
            if param in self._label_val and self._cur_val[param] != val:
                self._label_val[param].set_markup('<b>%s</b>' % \
                    qt.format_parameter_value(self._parameter_options[param],
                        val))
                self._cur_val[param] = val

        self._update_dict = {}

        gtk.gdk.threads_leave()

        return True

    def update_parameter(self, param, val, force=False):
        """
        Set parameter to be updated on next refresh.
        """
        self._update_dict[param] = val
        if force:
            self._cur_val[param] = None

    def get_instrument(self):
        return self._instrument

    def show_range_column(self, show):
        for label in self._label_range.values():
            if not show:
                label.hide()
            else:
                label.show()

    def show_rate_column(self, show):
        for label in self._label_rate.values():
            if not show:
                label.hide()
            else:
                label.show()

    def _parameter_changed_cb(self, sender, param):
        if param not in self._label_range:
            return False

        self._label_range[param].set_text(self._instrument.format_range(param))
        self._label_rate[param].set_text(self._instrument.format_rate(param))
        self._parameter_options[param] = self._instrument.get_shared_parameter_options(param)
        self.update_parameter(param, self._instrument.get(param), force=True)

    def show_table(self, show):
        '''Show or hide the parameter info table.'''
        if show:
            self._table.show()
            self._label.set_markup('<b>- %s</b> [?]' % \
                    self._instrument_name)
        else:
            self._table.hide()
            self._label.set_markup('<b>+ %s</b> [?]' % \
                    self._instrument_name)

    def _label_clicked_cb(self, sender, param):
        self.show_table(not self._table.props.visible)

    def remove(self):
        #FIXME: required to kill all references to the instrument object.
        #This also suggests that InstrumentFrames are leaked.
        self._instrument = None

class InstrumentWindow(qtwindow.QTWindow):

    ORDERID = 20

    def __init__(self):
        qtwindow.QTWindow.__init__(self, 'instruments', 'Instrument View')

        self.connect("delete-event", self._delete_event_cb)

        self._instruments = qt.instruments

        qt.instruments.connect('instrument-added', self._instrument_added_cb)
        qt.instruments.connect('instrument-removed', \
            self._instrument_removed_cb)
        qt.instruments.connect('instrument-changed', \
            self._instrument_changed_cb)

        self._tags_dropdown = dropdowns.TagsDropdown()
        self._tags_dropdown.connect('changed', self._tag_changed_cb)

        self._outer_vbox = gtk.VBox()
        self._outer_vbox.set_border_width(4)
        self._vbox = gtk.VBox()
        self._vbox.set_border_width(4)

        self._outer_vbox.pack_start(gui.pack_hbox([
            gtk.Label(_L('Types')),
            self._tags_dropdown]), False, False)

        self._range_toggle = gtk.ToggleButton(_L('Range'))
        self._range_toggle.set_active(qt.config.get('Instrument View_show_range', True))
        self._range_toggle.connect('toggled', self._range_toggled_cb)
        self._rate_toggle = gtk.ToggleButton(_L('Rate'))
        self._rate_toggle.set_active(qt.config.get('Instrument View_show_rate', True))
        self._rate_toggle.connect('toggled', self._rate_toggled_cb)

        self._outer_vbox.pack_start(gui.pack_hbox([
            self._range_toggle,
            self._rate_toggle], True, True), False, False)

        self._ins_widgets = {}
        self._add_instruments()

        self._scrolled_win = gtk.ScrolledWindow()
        self._scrolled_win.set_policy(gtk.POLICY_AUTOMATIC, \
            gtk.POLICY_AUTOMATIC)
        self._scrolled_win.add_with_viewport(self._vbox)

        self._outer_vbox.pack_start(self._scrolled_win, True, True)

        self._outer_vbox.show_all()
        self._range_toggle.emit('toggled')
        self._rate_toggle.emit('toggled')
        self.add(self._outer_vbox)

    def _add_instrument(self, ins):
        name = ins.get_name()
        self._ins_widgets[name] = QTInstrumentFrame(ins,
            self._range_toggle.get_active(),
            self._rate_toggle.get_active())
        self._vbox.pack_start(self._ins_widgets[name], False, False)

    def _remove_instrument(self, insname):
        if insname in self._ins_widgets:
            self._vbox.remove(self._ins_widgets[insname])
            self._ins_widgets[insname].remove()
            del self._ins_widgets[insname]

    def _update_instrument(self, insname, changes):
        if insname in self._ins_widgets:
            for (param, val) in changes.iteritems():
                self._ins_widgets[insname].update_parameter(param, val)

    def _add_instruments(self):
        for name in self._instruments.get_instrument_names():
            ins = qt.get_instrument_proxy(name)
            self._add_instrument(ins)

    def _delete_event_cb(self, widget, event, data=None):
        self.hide()
        return True

    def _instrument_added_cb(self, sender, insname):
        ins = qt.get_instrument_proxy(insname)
        if ins is not None:
            self._add_instrument(ins)
        else:
            logging.warning('Unable to locate added instrument %s', insname)

    def _instrument_removed_cb(self, sender, insname):
        self._remove_instrument(insname)

    def _instrument_changed_cb(self, sender, instrument, changes):
        self._update_instrument(instrument, changes)

    def _tag_changed_cb(self, sender):
        tag = self._tags_dropdown.get_active_text()
        for name, widget in self._ins_widgets.iteritems():
            ins = widget.get_instrument()
            if tag == dropdowns.TEXT_ALL or tag in ins.get_tags():
                widget.show_table(True)
            else:
                widget.show_table(False)

    def _range_toggled_cb(self, sender):
        state = self._range_toggle.get_active()
        qt.config.set('Instrument View_show_range', state)
        for name, widget in self._ins_widgets.iteritems():
            widget.show_range_column(state)

    def _rate_toggled_cb(self, sender):
        state = self._rate_toggle.get_active()
        qt.config.set('Instrument View_show_rate', state)
        for name, widget in self._ins_widgets.iteritems():
            widget.show_rate_column(state)

Window = InstrumentWindow

