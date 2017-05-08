# scipts.py, classes to use python scripts as functions
# Reinier Heeres <reinier@heeres.eu>, 2010
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

import os
import logging

class Script():

    def __init__(self, fn):
        self._fn = fn
        self._read_doc()

    def __repr__(self):
        repr = 'Script %s, doc:\n' % self._fn
        repr += self.__doc__
        return repr

    def _read_doc(self):
        self.__doc__ = ''
        if not os.path.exists(self._fn):
            return

        f = open(self._fn, 'r')
        for line in f:
            line2 = line.strip(' \t')
            if len(line2) > 0 and line2[0] == '#':
                self.__doc__ += line2
            # End of header
            elif len(line2.rstrip('\r\n')) != 0:
                break
        f.close()

    def _set_return(self, retval):
        self._ret_val = retval

    def _get_return(self):
        return self._ret_val

    def __call__(self, *args, **kwargs):
        self._set_return(None)

        locals = {
                'args': args,
                'kwargs': kwargs,
                'set_return': self._set_return,
        }
        execfile(self._fn, locals)

        return self._get_return()

class Scripts():

    def __init__(self):
        self._dirs = ['scripts', ]
        self._cache = {}

    def __repr__(self):
        s = 'Script list:'
        for scr in self.get_list():
            s += '\n\t%s' % scr
        return s

    def __getitem__(self, item):
        return self.get(item)

    def _find_script(self, name):
        for dname in self._dirs:
            fn = os.path.join(dname, name)
            if os.path.exists(fn):
                script = Script(fn)
                self._cache[name] = script
                return script
        return None

    def get(self, name, verbose=True):
        if name in self._cache:
            return self._cache[name]
        elif ('%s.py' % name) in self._cache:
            return self._cache['%s.py' % name]

        s = self._find_script(name)
        if s is None:
            s = self._find_script('%s.py' % name)
        if s is not None:
            return s

        if verbose:
            logging.warning('Script not found: %s', name)

    def get_list(self):
        return self._cache.keys()

    def _scan_dir(self, dirname):
        entries = os.listdir(dirname)
        for entry in entries:
            if (len(entry) > 0 and entry[0] == '.') or not entry.endswith('.py'):
                continue
            joined = os.path.join(dirname, entry)
            if os.path.isdir(joined):
                self._scan_dir(joined)
            else:
                self.get(entry)

    def scan(self):
        for dirname in self._dirs:
            self._scan_dir(dirname)

        return self.get_list()

    def add_directory(self, dirname, autoscan=True):
        if dirname in self._dirs:
            return

        self._dirs.append(dirname)
        if autoscan:
            self._scan_dir(dirname)

    def scripts_to_namespace(self, ns):
        for name, func in self._cache.iteritems():
            funcname, ext = os.path.splitext(name)
            ns[funcname] = func

