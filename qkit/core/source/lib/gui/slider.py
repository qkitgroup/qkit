# slider.py, class to create a slider for an instrument parameter
# Pieter de Groot <pieterdegroot@gmail.com>
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
from gettext import gettext as _L

import lib.gui as gui

import qtwindow
import qt

class SliderWindow(qtwindow.QTWindow):

    def __init__(self, ins, param, delay=50):
        if type(ins) is types.StringType:
            ins = qt.get_instrument_proxy(ins)
        self._instrument = ins
        self._parameter = param
        self._parameter_options = self._instrument.get_shared_parameter_options(param)
        if ins is not None and param in ins.get_parameter_names():
            name = '%s.%s' % (ins.get_name(), param)
        else:
            name = 'Paramter undefined'

        title = _L('Parameter: %s') % name
        qtwindow.QTWindow.__init__(self, name, title, add_to_main=False)
        self.connect('delete-event', self._delete_event_cb)

        self._delay = delay
        self._value_to_set = None
        self._set_hid = None

        if self._parameter_options.has_key('minval'):
            self._insmin = self._parameter_options['minval']
            self._min = self._insmin
        else:
            logging.warning('Be careful! Parameter has no \
                    minimum defined!')
            self._insmin = -1e20
            self._min = self._instrument.get(param)

        if self._parameter_options.has_key('maxval'):
            self._insmax = self._parameter_options['maxval']
            self._max = self._insmax
        else:
            logging.warning('Be careful! Parameter has no \
                    maximum defined!')
            self._insmax = 1e20
            self._max = self._instrument.get(param)

        self._range = self._max - self._min
        self._value = self._instrument.get(param)

        self._get_after_set = True

        ### start of gui init

        ### sliders frame

        slider = gtk.VScale()
        slider.set_inverted(True)
        slider.set_size_request(50, -1)
        slider.set_range(self._min, self._max)
        slider.set_digits(2)
        slider.set_draw_value(False)
        slider.connect('change-value', self._change_value_cb)
        self._main_slider = slider

        self._main_slider_label = gtk.Label('x1')

        vbox = gtk.VBox()
        vbox.pack_start(self._main_slider_label, False, False)
        vbox.pack_start(slider, True, True)
        self._main_slider_vbox = vbox

        self._fine_sliders = []
        self._fine_slider_vboxes = []
        self._fine_slider_labels = []
        for i in range(3):
            slider = gtk.VScale()
            slider.set_inverted(True)
            slider.set_size_request(50, -1)
            slider.set_range(-1, 1)
            slider.set_digits(2)
            slider.set_draw_value(False)
            slider.connect('change-value', self._change_value_cb)
            self._fine_sliders.append(slider)

            label = gtk.Label('x0.%s1' % (i*'0'))
            self._fine_slider_labels.append(label)

            vbox = gtk.VBox()
            vbox.pack_start(label, False, False)
            vbox.pack_start(slider, True, True)
            self._fine_slider_vboxes.append(vbox)

        self._slider_hbox = gui.pack_hbox([
            self._main_slider_vbox,
            self._fine_slider_vboxes[0],
            self._fine_slider_vboxes[1],
            self._fine_slider_vboxes[2],
            ])

        self._slframe = gtk.Frame()
        self._slframe.add(self._slider_hbox)

        ### controls frame

        self._max_label = gtk.Label('max:')
        self._max_value = gtk.Label('%e' % self._max)
        self._max_entry = gtk.Entry()
        self._max_but   = gtk.Button('Set')
        self._max_but.connect('clicked', self._set_max_clicked_cb)

        self._min_label = gtk.Label('min:')
        self._min_value = gtk.Label('%e' % self._min)
        self._min_entry = gtk.Entry()
        self._min_but   = gtk.Button('Set')
        self._min_but.connect('clicked', self._set_min_clicked_cb)

        self._delay_label = gtk.Label('delay:')
        self._delay_value = gtk.Label('%d' % self._delay)
        self._delay_entry = gtk.Entry()
        self._delay_but   = gtk.Button('Set')
        self._delay_but.connect('clicked', self._set_delay_clicked_cb)

        self._value_label = gtk.Label('value:')
        self._value_getbut = gtk.Button('Get')
        self._value_getbut.connect('clicked', self._get_value_clicked_cb)
        self._value_entry = gtk.Entry()
        self._value_but   = gtk.Button('Set')
        self._value_but.connect('clicked', self._set_value_clicked_cb)

        self._ctable = gtk.Table(4, 4, True)
        self._ctable.set_homogeneous(False)

        self._ctable.attach(self._max_label, 0, 1, 0, 1)
        self._ctable.attach(self._max_value, 1, 2, 0, 1)
        self._ctable.attach(self._max_entry, 2, 3, 0, 1)
        self._ctable.attach(self._max_but,   3, 4, 0, 1)

        self._ctable.attach(self._min_label, 0, 1, 1, 2)
        self._ctable.attach(self._min_value, 1, 2, 1, 2)
        self._ctable.attach(self._min_entry, 2, 3, 1, 2)
        self._ctable.attach(self._min_but,   3, 4, 1, 2)

        self._ctable.attach(self._delay_label, 0, 1, 2, 3)
        self._ctable.attach(self._delay_value, 1, 2, 2, 3)
        self._ctable.attach(self._delay_entry, 2, 3, 2, 3)
        self._ctable.attach(self._delay_but,   3, 4, 2, 3)

        self._ctable.attach(self._value_label, 0, 1, 3, 4)
        self._ctable.attach(self._value_getbut, 1, 2, 3, 4)
        self._ctable.attach(self._value_entry, 2, 3, 3, 4)
        self._ctable.attach(self._value_but,   3, 4, 3, 4)

        self._cframe = gtk.Frame()
        self._cframe.add(self._ctable)

        self._max_value.set_size_request(100, 1)

        ### value frame

        self._vallabel = gtk.Label('')
        self._vallabel.set_markup('<span size="xx-large">%e</span>' % self._value)
        self._valframe = gtk.Frame()
        self._valframe.add(self._vallabel)

        ### put together

        self._alltable = gtk.Table(2, 2, True)
        self._alltable.set_homogeneous(False)

        self._alltable.attach(self._cframe, 0, 1, 0, 1)
        self._alltable.attach(self._valframe, 0, 1, 1, 2)
        self._alltable.attach(self._slframe, 1, 2, 0, 2)

        ### end of gui init

        self._set_sliders()

        self.add(self._alltable)

        self.show_all()

    def _delete_event_cb(self, widget, event, data=None):
        self.hide()
        return True

    def _change_value_cb(self, sender, scroll, value):
        slm = self._main_slider.get_value()
        slf = []
        for i in range(len(self._fine_sliders)):
            slf.append( 10**(-i-1) * self._range * self._fine_sliders[i].get_value())

        value = min(max(slm + sum(slf), self._min), self._max)

        self._value_to_set = value
        if self._set_hid is None:
            self._set_hid = gobject.timeout_add(self._delay, self._set_value)

    def _set_max_clicked_cb(self, widget):
        _max = self._max_entry.get_text()
        if _max == '':
            return
        _max = float(_max)
        if _max < self._value:
            logging.warning('Cannot put maximum lower then current value: %f' % self._value)
            return
        if _max > self._insmax:
            logging.warning('Cannot override parameter maximum: %f' % self._insmax)
            return
        self._max = _max
        self._range = self._max - self._min
        self._max_value.set_label('%e' % self._max)
        self._max_entry.set_text('')
        self._main_slider.set_range(self._min, self._max)

    def _set_min_clicked_cb(self, widget):
        _min = self._min_entry.get_text()
        if _min == '':
            return
        _min = float(_min)
        if _min > self._value:
            logging.warning('Cannot put minimum higher then current value: %f' % self._value)
            return
        if _min < self._insmin:
            logging.warning('Cannot override parameter minimum: %f' % self._insmin)
            return
        self._min = _min
        self._range = self._max - self._min
        self._min_value.set_label('%e' % self._min)
        self._min_entry.set_text('')
        self._main_slider.set_range(self._min, self._max)

    def _set_delay_clicked_cb(self, widget):
        _delay = self._delay_entry.get_text()
        if _delay == '':
            return
        self._delay = int(_delay)
        self._delay_value.set_label('%d' % self._delay)
        self._delay_entry.set_text('')

    def _get_value_clicked_cb(self, widget):
        value = self._instrument.get(self._parameter)
        if value > self._max:
            self._max = value
            self._range = self._max - self._min
            self._max_value.set_label('%e' % self._max)
            self._main_slider.set_range(self._min, self._max)
        if value < self._min:
            self._min = value
            self._range = self._max - self._min
            self._min_value.set_label('%e' % self._min)
            self._main_slider.set_range(self._min, self._max)
        self._value = value
        self._set_sliders()
        self._vallabel.set_markup('<span size="xx-large">%e</span>' % self._value)

    def _set_value_clicked_cb(self, widget):
        value = self._value_entry.get_text()
        if value == '':
            return
        value = float(value)
        if value > self._max:
            logging.warning('Trying to put too high value: %f' % value)
            return
        if value < self._min:
            logging.warning('Trying to put too low value: %f' % value)
            return
        self._value_to_set = value
        self._set_value()
        self._value_entry.set_text('')
        self._set_sliders()

    def _set_value(self):
        self._set_hid = None
        self._instrument.set(self._parameter, self._value_to_set)
        if self._get_after_set:
            value = self._instrument.get(self._parameter)
        self._value = value
        self._vallabel.set_markup('<span size="xx-large">%e</span>' % self._value)

    def _set_sliders(self):
        self._main_slider.set_value(self._value)
        for item in self._fine_sliders:
            item.set_value(0.0)
