import gtk
import gobject

from gettext import gettext as _L

from lib import namedlist
from lib.config import get_config
config = get_config()

class QTWindow(gtk.Window):

    _window_list = namedlist.NamedList(shared_name='namedlist_window')
    _name_counters = {}

    def __init__(self, name, title, add_to_main=True):
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)

        self._name = self.generate_name(name)
        self._title = title

        winx, winy = config.get('%s_pos' % title, (250, 40))
        self.move(winx, winy)

        width, height = config.get('%s_size' % self._title, (200, 400))
        self.set_size_request(50, 50)
        self.resize(width, height)

        self.set_border_width(1)

        self.set_title(_L(title))

        show = config.get('%s_show' % self._title, False)
        if show:
            gobject.timeout_add(100, self._do_show)

        self.connect('configure-event', self._configure_event_cb)
        self.connect('show', lambda x: self._show_hide_cb(x, True))
        self.connect('hide', lambda x: self._show_hide_cb(x, False))

        QTWindow._window_list.add(self._name, self)

        if add_to_main:
            self._add_to_main()

    def generate_name(self, name):
        if name not in QTWindow._name_counters:
            QTWindow._name_counters[name] = 1
            return name
        else:
            ret = '%s%d' % (name, QTWindow._name_counters[name])
            QTWindow._name_counters[name] += 1
            return ret

    def _do_show(self):
        self.show()

    def _show_hide_cb(self, sender, show):
        config.set('%s_show' % self._title, show)

    def _configure_event_cb(self, sender, *args):
        pos = self.get_position()
        pos = [max(i, 0) for i in pos]
        config.set('%s_pos' % self._title, pos)

        w, h = self.get_size()
        config.set('%s_size' % self._title, (w, h))

    def get_title(self):
        '''Return window title.'''
        return self._title

    def _add_to_main(self):
        winlist = self.get_named_list()
        mainwin = winlist['main']
        if mainwin is not None:
            mainwin.add_window(self)

    @staticmethod
    def get_named_list():
        return QTWindow._window_list

