import gtk
from gettext import gettext as _L

import qtclient as qt

class StopButton(gtk.Button):

    def __init__(self):
        gtk.Button.__init__(self, _L('Stop'))

        self.set_sensitive(qt.flow.is_measuring())
        self.connect('clicked', self._toggle_stop_cb)

        qt.flow.connect('measurement-start', self._measurement_start_cb)
        qt.flow.connect('measurement-end', self._measurement_end_cb)

    def _toggle_stop_cb(self, sender):
        qt.flow.set_abort(callback=lambda x: True)

    def _measurement_start_cb(self, widget):
        self.set_sensitive(True)

    def _measurement_end_cb(self, widget):
        self.set_sensitive(False)

class PauseButton(gtk.ToggleButton):

    def __init__(self):
        gtk.ToggleButton.__init__(self)

        self.set_sensitive(qt.flow.is_measuring())
        self.set_active(qt.flow.is_paused())
        self._update_label()

        self.connect('clicked', self._toggle_cb)

        qt.flow.connect('measurement-start', self._measurement_start_cb)
        qt.flow.connect('measurement-end', self._measurement_end_cb)

    def _update_label(self, pause=None):
        if pause is None:
            pause = qt.flow.is_paused()
        if pause:
            self.set_label(_L('Continue'))
        else:
            self.set_label(_L('Pause'))

    def _toggle_cb(self, sender):
        pause = qt.flow.is_paused()
        qt.flow.set_pause(not pause, callback=lambda *args: True)
        self._update_label()

    def _measurement_start_cb(self, widget):
        self.set_sensitive(True)

    def _measurement_end_cb(self, widget):
        self.set_sensitive(False)

