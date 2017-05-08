# control_window.py, window to tune instrument parameter
# Reinier Heeres, <reinier@heeres.eu>, 2008-2009
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

import logging
from gettext import gettext as _L

import qtclient as qt
import lib.gui as gui
from lib.gui import dropdowns, qtwindow, frontpanel, slider
from lib.gui.flexscale import FlexScale
from lib.gui.functionframe import ArgumentTable, FunctionFrame

class QTManageInstrumentFrame(gtk.VBox):

    def __init__(self, **kwargs):
        gtk.VBox.__init__(self, **kwargs)

        self._instruments = qt.instruments
        self._frontpanels = qt.frontpanels

        self._action_frame = gtk.Frame()
        self._action_frame.set_label(_L('Manage'))

        self._ins_dropdown = dropdowns.InstrumentDropdown()

        self._frontpanel_button = gtk.Button(_L('Frontpanel'))
        self._frontpanel_button.connect('clicked', self._fp_clicked_cb)

        self._reload_button = gtk.Button(_L('Reload'))
        self._reload_button.connect('clicked', self._reload_clicked_cb)

        self._remove_button = gtk.Button(_L('Remove'))
        self._remove_button.connect('clicked', self._remove_clicked_cb)

        vbox = gui.pack_vbox([
            self._ins_dropdown,
            gui.pack_hbox([
                self._frontpanel_button,
                self._reload_button,
                self._remove_button
                ], True, True)
            ], False, False)
        vbox.set_border_width(4)
        self._action_frame.add(vbox)

        vbox = gui.pack_vbox([
            self._action_frame
            ], False,False)
        vbox.set_border_width(4)

        self.add(vbox)

        self.show_all()

    def _fp_clicked_cb(self, sender):
        ins = self._ins_dropdown.get_instrument()
        if ins is not None:
            name = ins.get_name()
            if name not in self._frontpanels:
                self._frontpanels[name] = frontpanel.FrontPanel(ins)
            self._frontpanels[name].show()
            self._frontpanels[name].present()

    def _reload_clicked_cb(self, sender):
        ins = self._ins_dropdown.get_instrument()
        if ins is not None:
            return self._instruments.reload(ins)

    def _remove_clicked_cb(self, sender):
        ins = self._ins_dropdown.get_instrument()
        if ins is not None:
            return ins.remove()

class QTCreateInstrumentFrame(gtk.VBox):

    def __init__(self, **kwargs):
        gtk.VBox.__init__(self, **kwargs)

        self._instruments = qt.instruments

        self._add_frame = gtk.Frame()
        self._add_frame.set_label(_L('Create'))

        name_label = gtk.Label(_L('Name'))
        self._name_entry = gtk.Entry()
        self._name_entry.connect('changed', self._name_changed_cb)

        type_label = gtk.Label(_L('Type'))
        self._type_dropdown = dropdowns.InstrumentTypeDropdown()
        self._type_dropdown.connect('changed', self._dropdown_changed_cb)
        self._add_button = gtk.Button(_L('Add'))
        self._add_button.connect('clicked', self._add_clicked_cb)
        self._add_button.set_sensitive(False)

        self._argument_table = ArgumentTable(2, 2, exclude=['self', 'name'])
        self._argument_table.attach(name_label, 0, 1, 0, 1)
        self._argument_table.attach(self._name_entry, 1, 2, 0, 1)
        self._argument_table.attach(type_label, 0, 1, 1, 2)
        self._argument_table.attach(self._type_dropdown, 1, 2, 1, 2)

        vbox = gui.pack_vbox([
            self._argument_table,
            self._add_button
            ], False, False)
        vbox.set_border_width(4)
        self._add_frame.add(vbox)

        vbox = gui.pack_vbox([
            self._add_frame,
            ], False,False)
        vbox.set_border_width(4)
        self.add(vbox)

        self.show_all()

    def _dropdown_changed_cb(self, widget):
        type_name = self._type_dropdown.get_typename()
        if type_name is None:
            args = None
        else:
            args = self._instruments.get_type_arguments(type_name)
        self._argument_table.set_arg_spec(args)

        self._update_add_button_sensitivity()

    def _add_clicked_cb(self, widget):
        name = self._name_entry.get_text()
        typename = self._type_dropdown.get_typename()
        args = self._argument_table.get_args()
        logging.debug("Creating %s as %s, **args: %r", name, typename, args)
        ins = qt.instruments.create(name, typename, **args)
        if ins is not None:
            self._name_entry.set_text('')
            self._type_dropdown.select_none_type()

    def _name_changed_cb(self, widget):
        self._update_add_button_sensitivity()

    def _update_add_button_sensitivity(self):
        typename = self._type_dropdown.get_typename()
        namelen = len(self._name_entry.get_text())

        if typename is not None and typename != '' and namelen > 0:
            self._add_button.set_sensitive(True)
        else:
            self._add_button.set_sensitive(False)

class QTSetInstrumentFrame(gtk.VBox):

    def __init__(self, **kwargs):
        gtk.VBox.__init__(self, **kwargs)

        self._frontpanels = qt.frontpanels
        self._sliders = qt.sliders

        self._ins = None
        self._ins_combo = dropdowns.InstrumentDropdown()
        self._ins_combo.connect('changed', self._instrument_changed_cb)

        self._param_combo = dropdowns.InstrumentParameterDropdown()
        self._param_combo.connect('changed', self._parameter_changed_cb)

        self._get_but = gtk.Button('Get')
        self._get_but.connect('clicked', self._get_param_clicked_cb)
        self._param_edit = gtk.Entry()
        self._param_edit.set_alignment(0.93)
        self._set_but = gtk.Button('Set')
        self._set_but.connect('clicked', self._set_param_clicked_cb)
        param_getset = gui.pack_hbox([self._get_but, \
                self._set_but])

        self._function_frame = FunctionFrame()

        self._make_fp = gtk.Button('Frontpanel')
        self._make_fp.connect('clicked', self._fp_clicked_cb)

        self._make_sl = gtk.Button('Slider')
        self._make_sl.connect('clicked', self._slider_clicked_cb)

        h1 = gui.pack_hbox([
            gtk.Label(_L('Instrument')),
            self._ins_combo])
        h2 = gui.pack_hbox([
            gtk.Label(_L('Parameter')),
            self._param_combo])

        self._table = gtk.Table(4, 2, True)
        self._table.set_homogeneous(False)

        self._table.attach(h1, 0, 1, 0, 1)
        self._table.attach(h2, 0, 1, 1, 2)
        self._table.attach(self._param_edit, 0, 1, 2, 3)
        self._table.attach(self._function_frame, 0, 2, 3, 4)

        self._table.attach(self._make_fp, 1, 2, 0, 1)
        self._table.attach(self._make_sl, 1, 2, 1, 2)
        self._table.attach(param_getset, 1, 2, 2, 3)

        self._table.set_border_width(4)
        self.add(self._table)

        self._parameter_changed_cb(None)
        self.show_all()

    def _instrument_changed_cb(self, widget):
        self._ins = self._ins_combo.get_instrument()
        self._param_combo.set_instrument(self._ins)
        self._function_frame.set_instrument(self._ins)

    def _parameter_changed_cb(self, widget):
        param = self._param_combo.get_parameter()
        sget, sset = False, False
        if self._ins is not None:
            opts = self._ins.get_shared_parameter_options(param)
            if opts is not None:
                sget = opts['flags'] & \
                    (qt.constants.FLAG_GET | qt.constants.FLAG_SOFTGET)
                sset = opts['flags'] & qt.constants.FLAG_SET
        self._get_but.set_sensitive(sget)
        self._set_but.set_sensitive(sset)
        self._make_sl.set_sensitive(sset)

    def _param_get_cb(self, val):
        self._param_edit.set_text('%s' % val)
        self._get_but.set_sensitive(True)

    def _param_set_cb(self, boolsucces):
        self._set_but.set_sensitive(True)

    def _get_param_clicked_cb(self, widget):
        param = self._param_combo.get_parameter()
        self._get_but.set_sensitive(False)
        self._ins.get(param, callback=self._param_get_cb)

    def _set_param_clicked_cb(self, widget):
        param = self._param_combo.get_parameter()
        val = self._param_edit.get_text()
        self._set_but.set_sensitive(False)
        self._ins.set(param, val, callback=self._param_set_cb)

    def _fp_clicked_cb(self, sender):
        ins = self._ins_combo.get_instrument()
        if ins is not None:
            name = ins.get_name()
            if name not in self._frontpanels:
                self._frontpanels[name] = frontpanel.FrontPanel(ins)
            self._frontpanels[name].show()
            self._frontpanels[name].present()

    def _slider_clicked_cb(self, sender):
        ins = self._ins_combo.get_instrument()
        param = self._param_combo.get_parameter()
        if ins is not None and param is not None:
            name = '%s.%s' % (ins.get_name(), param)
            if name not in self._sliders:
                self._sliders[name] = slider.SliderWindow(ins, param)
            self._sliders[name].show()
            self._sliders[name].present()

class ControlWindow(qtwindow.QTWindow):

    ORDERID = 21

    def __init__(self):
        qtwindow.QTWindow.__init__(self, 'control', 'Instrument Control')
        self.connect("delete-event", self._delete_event_cb)

        self._set_frame = QTSetInstrumentFrame()
        self._manage_frame = QTManageInstrumentFrame()
        self._create_frame = QTCreateInstrumentFrame()

        self._notebook = gtk.Notebook()
        self._notebook.append_page(self._set_frame,
            gtk.Label(_L('Set')))
        self._notebook.append_page(self._manage_frame,
            gtk.Label(_L('Manage')))
        self._notebook.append_page(self._create_frame,
            gtk.Label(_L('Create')))
        self._notebook.show_all()
        self._notebook.set_current_page(0)
        self.add(self._notebook)

    def _delete_event_cb(self, widget, event, data=None):
        self.hide()
        return True

Window = ControlWindow

