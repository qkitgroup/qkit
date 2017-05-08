# dropdowns.py, dropdown support for Instruments
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
import types

import lib.misc as misc

TEXT_ALL = '<All>'
TEXT_NONE = '<None>'

from lib.network.object_sharer import helper
import qtclient as qt

class QTComboBox(gtk.ComboBox):

    def __init__(self, model):
        gtk.ComboBox.__init__(self, model=model)
        cell = gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, 'text', 0)

    def set_item(self, item):
        model = self.get_model()
        for i in range(len(model)):
            if model[i][0] == item:
                self.set_active(i)
                return True
        return False

    def remove_item_from(self, item, items):
        i = items.get_iter_root()
        while i:
            if items.get_value(i, 0) == item:
                items.remove(i)
                break
            i = items.iter_next(i)

class InstrumentDropdown(QTComboBox):
    '''
    Dropdown to select an instrument.
    '''

    def __init__(self, types=[]):
        self._ins_list = gtk.ListStore(gobject.TYPE_STRING)
        QTComboBox.__init__(self, model=self._ins_list)

        self._types = types
        self._ins_list.append([TEXT_NONE])
        self._instruments = qt.instruments
        for insname in self._instruments.get_instrument_names():
            # This should perhaps go through qt.get_instrument_proxy()
            ins = helper.find_object('instrument_%s' % insname)
            if len(types) == 0 or ins.has_tag(types):
                self._ins_list.append([insname])

        self._instruments.connect('instrument-added', self._instrument_added_cb)
        self._instruments.connect('instrument-removed', self._instrument_removed_cb)
        self._instruments.connect('instrument-changed', self._instrument_changed_cb)

    def _instrument_added_cb(self, sender, insname):
        ins = qt.get_instrument_proxy(insname)
        if ins is None:
            return
        if len(self._types) == 0 or ins.has_tag(self._types):
            self._ins_list.append([ins.get_name()])

    def _instrument_removed_cb(self, sender, insname):
        logging.debug('Instrument removed: %s', insname)
        self.remove_item_from(insname, self._ins_list)

    def _instrument_changed_cb(self, sender, instrument, changes):
        return

    def get_instrument(self):
        item = self.get_active_iter()
        if item is None:
            return None
        ins_name = self._ins_list.get(item, 0)
        return qt.get_instrument_proxy(ins_name[0])

class InstrumentTypeDropdown(QTComboBox):
    '''
    Dropdown to select an instrument type.
    '''

    def __init__(self):
        self._type_list = gtk.ListStore(gobject.TYPE_STRING)
        QTComboBox.__init__(self, model=self._type_list)

        self._type_list.append([TEXT_NONE])
        for name in qt.instruments.get_types():
            self._type_list.append([name])

    def get_typename(self):
        item = self.get_active_iter()
        if item is None:
            return None
        type_name = self._type_list.get(item, 0)
        if type_name[0] == TEXT_NONE:
            return None
        else:
            return type_name[0]

    def select_none_type(self):
        self.set_active(0)

class InstrumentParameterDropdown(QTComboBox):
    '''
    Dropdown to select a parameter from a given instrument.
    '''

    def __init__(self, instrument=None, flags=3, types=[]):
        self._param_list = gtk.ListStore(gobject.TYPE_STRING)
        QTComboBox.__init__(self, model=self._param_list)

        self._instrument = None
        self._insname = ''
        self.set_instrument(instrument)
        self._param_list.set_sort_column_id(0, gtk.SORT_ASCENDING)

        self._flags = flags
        self._types = types

        self._instruments = qt.instruments
        self._instruments.connect('instrument-removed', self._instrument_removed_cb)

    def set_flags(self, flags):
        if flags != self._flags:
            ins = self._instrument
            self.set_instrument(None)
            self.set_instrument(ins)

    def set_types(self, types):
        if self._types != types:
            self._types = types
            return self.update_list()

    def _instrument_removed_cb(self, sender, insname):
        if insname == self._instrument:
            logging.debug('Instrument for dropdown removed: %s', instrument)
            self.set_instrument(None)

    def _parameter_added_cb(self, sender, param):
        #FIXME: this needs to be improved
        ins = self._instrument
        self.set_instrument(None)
        self.set_instrument(ins)

    def set_instrument(self, ins):
        if type(ins) == types.StringType:
            # This should perhaps go through qt.get_instrument_proxy()
            ins = helper.find_object('instruments_%s' % ins)

        if self._instrument == ins:
            return True

        if ins is not None:
            self._insname = ins.get_name()
        else:
            self._insname = ''

        self._instrument = ins
        self._param_list.clear()
        if ins is not None:
            self._param_list.append([TEXT_NONE])

            self._instrument.connect('parameter-added', self._parameter_added_cb)

            for (name, options) in misc.dict_to_ordered_tuples(ins.get_shared_parameters()):
                if len(self._types) > 0 and options['type'] not in self._types:
                    continue

                if options['flags'] & self._flags:
                    self._param_list.append([name])
        else:
            self._param_list.clear()

    def get_parameter(self):
        item = self.get_active_iter()
        if item is None:
            return None
        param_name = self._param_list.get(item, 0)
        return param_name[0]

class InstrumentFunctionDropdown(QTComboBox):
    '''
    Dropdown to select a function from a given instrument.
    '''

    def __init__(self, instrument=None):
        self._func_list = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
        QTComboBox.__init__(self, model=self._func_list)

        self._instrument = None
        self._insname = ''
        self.set_instrument(instrument)
        self._func_list.set_sort_column_id(0, gtk.SORT_ASCENDING)

        self._instruments = qt.instruments
        self._instruments.connect('instrument-removed', self._instrument_removed_cb)

    def _instrument_removed_cb(self, sender, insname):
        if insname == self._insname:
            logging.debug('Instrument for dropdown removed: %s', insname)
            self.set_instrument(None)

    def _instrument_changed_cb(self, sender, instrument, property, value):
        return

    def set_instrument(self, ins):
        if type(ins) == types.StringType:
            ins = qt.get_instrument_proxy(ins)

        if self._instrument == ins:
            return True

        if ins is not None:
            self._insname = ins.get_name()
        else:
            self._insname = ''

        self._instrument = ins
        self._func_list.clear()
        if ins is not None:
            self._func_list.append([TEXT_NONE, '<Nothing>'])

            funcs = ins.get_functions()
            for (name, options) in misc.dict_to_ordered_tuples(funcs):
                if 'doc' in options:
                    doc = options['doc']
                else:
                    doc = ''
                self._func_list.append([name, doc])
        else:
            self._func_list.clear()

    def get_function(self):
        item = self.get_active_iter()
        if item is None:
            return None
        func_name = self._func_list.get(item, 0)
        return func_name[0]

class AllParametersDropdown(QTComboBox):
    '''
    Dropdown to select a parameter from any instrument.
    '''

    def __init__(self, flags=3, types=[], tags=[]):
        self._param_list = gtk.ListStore(gobject.TYPE_STRING)
        QTComboBox.__init__(self, model=self._param_list)

        self._flags = flags
        self._types = types
        self._tags = tags

        self._do_update_hid = None
        self._param_info = {}
        self._ins_names = []
        self.add_instruments()
        self.update_list()

        self._param_list.set_sort_column_id(0, gtk.SORT_ASCENDING)

        self._instruments = qt.instruments
        self._instruments.connect('instrument-added', self._instrument_added_cb)
        self._instruments.connect('instrument-removed', self._instrument_removed_cb)
        self._instruments.connect('instrument-changed', self._instrument_changed_cb)

    def _instrument_added_cb(self, sender, insname):
        ins = qt.get_instrument_proxy(insname)
        if ins is not None:
            self.add_instrument(ins)

    def _instrument_removed_cb(self, sender, name):
        self.remove_instrument(name)

    def _instrument_changed_cb(self, sender, instrument, changes):
        return

    def add_instruments(self):
        inslist = qt.instruments.get_instrument_names()
        inslist.sort()
        for insname in inslist:
            # This should perhaps go through qt.get_instrument_proxy()
            ins = helper.find_object('instrument_%s' % insname)
            self.add_instrument(ins)

    def add_instrument(self, ins):
        insname = ins.get_name()
        if ins.get_name() in self._ins_names:
            return

        self._ins_names.append(insname)
        ins.connect('parameter-added', self._parameter_added_cb)
        params = misc.dict_to_ordered_tuples(ins.get_shared_parameters())
        for param, options in params:
            self.add_parameter(ins, param, options=options)

    def add_parameter(self, ins, param, options=None):
        if options is None:
            options = ins.get_shared_parameter_options(param)
        insname = ins.get_name()

        add_name = '%s.%s' % (insname, param)
        if add_name in self._param_info:
            return
        self._param_info[add_name] = {
            'insname': insname,
            'options': options,
            }

    def remove_instrument(self, name):
        remove_list = []
        for add_name, opts in self._param_info.iteritems():
            if opts['insname'] == name:
                remove_list.append(add_name)
        for name in remove_list:
            del self._param_info[name]
        self.update_list()

    def set_flags(self, flags):
        if self._flags != flags:
            self._flags = flags
            return self.update_list()

    def set_types(self, types):
        if self._types != types:
            self._types = types
            return self.update_list()

    def set_tags(self, tags):
        if self._tags != tags:
            self._tags = tags
            return self.update_list()

    def _should_add(self, options):
        if len(self._tags) > 0:
            tag_ok = False
            for tag in self._tags:
                if tag in options['tags']:
                    tag_ok = True
                    break
        else:
            tag_ok = True

        if options['flags'] & self._flags and tag_ok:
            return True
        else:
            return False

    def update_list(self):
        if self._do_update_hid is None:
            self._do_update_hid = gobject.idle_add(self._do_update_list)

    def _do_update_list(self):
        self._do_update_hid = None

        self._param_list.clear()
        self._param_list.append([TEXT_NONE])
        for add_name, opts in self._param_info.iteritems():
            if self._should_add(opts['options']):
                self._param_list.append([add_name])

    def get_selection(self):
        try:
            selstr = self.get_active_text()
            if selstr == '':
                return None

            insname, dot, parname = selstr.partition('.')
            logging.debug('Selected instrument %s, parameter %s', insname, parname)

            ins = qt.get_instrument_proxy(insname)
            if ins is None:
                return None

            return ins, parname

        except Exception, e:
            return None

    def _parameter_added_cb(self, sender, param):
        self.update_list()

class TagsDropdown(QTComboBox):

    def __init__(self):
        self._tags = gtk.ListStore(gobject.TYPE_STRING)
        QTComboBox.__init__(self, model=self._tags)

        self._instruments = qt.instruments
        self._instruments.connect('tags-added', self._tags_added_cb)

        self._tags.append([TEXT_ALL])
        self._tags.append([TEXT_NONE])
        for i in self._instruments.get_tags():
            self._tags.append([i])

        self._tags.set_sort_column_id(0, gtk.SORT_ASCENDING)

    def _tags_added_cb(self, sender, tags):
        for tag in tags:
            self._tags.append([tag])

class NamedListDropdown(QTComboBox):

    def __init__(self, namedlist):
        self._items = gtk.ListStore(gobject.TYPE_STRING)
        QTComboBox.__init__(self, model=self._items)

        self._namedlist = namedlist
        self._namedlist.connect('item-added', self._item_added_cb)
        self._namedlist.connect('item-changed', self._item_changed_cb)
        self._namedlist.connect('item-removed', self._item_removed_cb)

        for item in self._namedlist.get_items():
            self._items.append([item])

    def _item_added_cb(self, sender, item):
        self._items.append([item])

    def _item_removed_cb(self, sender, item):
        self.remove_item_from(item, self._items)

    def _item_changed_cb(self, sender, item):
        pass

    def get_item(self):
        item = self.get_active_iter()
        if item is None:
            return None
        name = self._items.get(item, 0)[0]
        objname = '%s_%s' % (self._namedlist.get_base_name(), name)
        return helper.find_object(objname)

class StringListDropdown(QTComboBox):

    def __init__(self, stringlist):
        self._items = gtk.ListStore(gobject.TYPE_STRING)
        QTComboBox.__init__(self, model=self._items)
        self.set_items(stringlist)

    def set_items(self, stringlist):
        self._items.clear()
        for item in stringlist:
            self._items.append([item])

    def get_item(self):
        item = self.get_active_iter()
        if item is None:
            return None
        name = self._items.get(item, 0)[0]
        return name
