# insproxy.py, class to act as a proxy for Instrument objects.
# Mostly to facilitate easy reloading of instruments.
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

import inspect
import types
import qt
import instrument

class Proxy():

    def __init__(self, name, include_do=None):
        self._name = name
        self._proxy_names = []
        self._setup_done = False
        self._padd_hid = None
        self._prem_hid = None

        if include_do is None:
            self._include_do = qt.config.get('proxy_include_do', False)
        else:
            self._include_do = include_do

        self._setup_proxy()
        qt.instruments.connect('instrument-added', self._ins_added_cb)
        qt.instruments.connect('instrument-removed', self._ins_removed_cb)

    def _setup_proxy(self):
        if self._setup_done:
            return
        self._setup_done = True

        self._ins = qt.instruments.get(self._name, proxy=False)
        members = inspect.getmembers(self._ins)

        toadd = instrument.Instrument.__dict__.keys()
        toadd += ['connect', 'disconnect']
        toadd += self._ins.__class__.__dict__.keys()
        toadd += self._ins._added_methods
        toadd += self._ins.get_function_names()
        for (name, item) in members:
            if name.startswith('do_') and not self._include_do:
                continue
            if callable(item) and not name.startswith('_') and name in toadd:
                self._proxy_names.append(name)
                setattr(self, name, item)

        self._padd_hid = self.connect('parameter-added',
                self._parameter_added_cb)
        self._prem_hid = self.connect('parameter-removed',
                self._parameter_removed_cb)

    def _remove_functions(self):
        if self._padd_hid is not None:
            self.disconnect(self._padd_hid)
            self.disconnect(self._prem_hid)
        self._padd_hid = None
        self._prem_hid = None

        self._setup_done = False
        for name in self._proxy_names:
            delattr(self, name)
        self._proxy_names = []
        self._ins = None

    def _ins_added_cb(self, sender, insname):
        if insname == self._name:
            self._setup_proxy()

    def _ins_removed_cb(self, sender, insname):
        if insname == self._name:
            self._remove_functions()

    def _parameter_added_cb(self, sender, name):
        for func in ('get_%s' % name, 'set_%s' % name):
            if hasattr(self._ins, func):
                setattr(self, func, getattr(self._ins, func))

    def _parameter_removed_cb(self, sender, name):
        for func in ('get_%s' % name, 'set_%s' % name):
            if hasattr(self, func):
                delattr(self, func)

