# functionframe.py, classes to create input fields for a function according
# to it's argspec.
# Reinier Heeres <reinier@heeres.eu>, 2009
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
import dropdowns

class ArgumentTable(gtk.Table):

    def __init__(self, rows=0, cols=2, exclude=['self']):
        setrows = max(rows, 1)
        gtk.Table.__init__(self, setrows, cols)
        self._base_rows = rows
        self._base_cols = cols
        self._exclude = exclude
        self._arg_info = {}

    def _remove_arguments(self):
        for name, info in self._arg_info.iteritems():
            self.remove(info['label'])
            self.remove(info['entry'])
        self._arg_info = {}

    def set_arg_spec(self, argspec):
        self._remove_arguments()
        rows, cols = self._base_rows, self._base_cols
        if rows == 0:
            self.resize(1, cols)
        else:
            self.resize(rows, cols)

        if argspec is None:
            return

        names = argspec['args']
        defaults = argspec['defaults']
        for i, name in enumerate(names):
            if name in self._exclude:
                continue

            label = gtk.Label(name)
            entry = gtk.Entry()
            if defaults is not None and i >= len(names) - len(defaults):
                entry.set_text(str(defaults[i - len(names) + len(defaults)]))

            self._arg_info[name] = {'label': label, 'entry': entry}
            rows += 1
            self.resize(rows, cols)
            self.attach(label, 0, 1, rows, rows + 1)
            self.attach(entry, 1, 2, rows, rows + 1)

        self.show_all()

    def get_args(self):
        '''Return the currently set args as a dictionary.'''

        args = {}
        for param, info in self._arg_info.iteritems():
            value = info['entry'].get_text()
            try:
                value = eval(value)
            except:
                pass
            if value == '':
                value = None
            args[param] = value

        return args

class FunctionFrame(gtk.Frame):

    def __init__(self):
        gtk.Frame.__init__(self, 'Functions')

        self._ins = None
        self._func_combo = dropdowns.InstrumentFunctionDropdown()
        self._func_combo.connect('changed', self._func_changed_cb)

        self._doc_button = gtk.Button('Doc')
        self._doc_button.set_sensitive(False)
        self._doc_button.connect('clicked', self._doc_clicked_cb)

        self._arg_table = ArgumentTable()

        self._call_but = gtk.Button('Call')
        self._call_but.connect('clicked', self._call_clicked_cb)

        vbox = gtk.VBox()
        vbox.set_border_width(4)
        hbox = gtk.HBox()
        hbox.pack_start(self._func_combo, True, True)
        hbox.pack_start(self._doc_button, False, False)
        vbox.pack_start(hbox)
        vbox.pack_start(self._arg_table)
        vbox.pack_start(self._call_but)
        self.add(vbox)
        self.show_all()

    def _func_changed_cb(self, widget):
        sens = False
        name = self._func_combo.get_function()
        if self._ins is not None:
            opts = self._ins.get_function_options(name)
            if opts is not None:
                self._arg_table.set_arg_spec(opts['argspec'])
                sens = True

                f = self._get_function(name)
                if hasattr(f, '__doc__'):
                    self._doc_button.set_sensitive(True)
                    self._doc_button.set_tooltip_text(f.__doc__)
                else:
                    self._doc_button.set_sensitive(False)

        self._call_but.set_sensitive(sens)

    def set_instrument(self, ins):
        self._ins = ins
        self._func_combo.set_instrument(ins)

    def _get_function(self, name=None):
        if name is None:
            name = self._func_combo.get_function()

        if self._ins is not None and hasattr(self._ins, name):
            return getattr(self._ins, name)
        else:
            return None

    def _call_clicked_cb(self, sender):
        f = self._get_function()
        if f is not None:
            args = self._arg_table.get_args()
            f(**args)

    def _doc_clicked_cb(self, sender):
        #FIXME: pop-up tooltip
        pass

