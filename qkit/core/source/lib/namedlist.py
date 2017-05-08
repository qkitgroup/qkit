# namedlist.py, base class to implement named lists
# Reinier Heeres <reinier@heeres.eu>, 2008
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

import gobject
from lib.network.object_sharer import SharedGObject
from lib.misc import get_ipython

def _clear_ipython():
    # TODO: In ipython 0.11 IP no longer exists. Also, %clear magic (clearcmd.py) has been put in quarantine folder. It is not clear to me what has replaced the functionality. possiby ip.cleanup, ip.clear_instance or ip.clear_main_mod_cache.
    try:
        ip = get_ipython()
        ip.IP.ipmagic('clear out')
        import gc
        gc.collect()
    except:
        pass

class NamedList(SharedGObject):

    __gsignals__ = {
        'item-added': (gobject.SIGNAL_RUN_FIRST,
                    gobject.TYPE_NONE,
                    ([gobject.TYPE_PYOBJECT])),
        'item-changed': (gobject.SIGNAL_RUN_FIRST,
                    gobject.TYPE_NONE,
                    ([gobject.TYPE_PYOBJECT])),
        'item-removed': (gobject.SIGNAL_RUN_FIRST,
                    gobject.TYPE_NONE,
                    ([gobject.TYPE_PYOBJECT])),
    }

    TYPE_ACTIVE = 0
    TYPE_PASSIVE = 1

    def __init__(self, base_name='item', **kwargs):
        '''
        Construct new named list object.

        Input:
            base_name (string): the base name for new items
            type (constant): TYPE_ACTIVE or TYPE_PASSIVE.
                Active lists make sure that an item always exists, so if an
                item is requested that does not exist a new one will be
                created on the fly by calling the create() function
                Passive lists simply return None if an item does not exist.
        '''
        shared_name = kwargs.get('shared_name', 'namedlist_%s' % base_name)
        SharedGObject.__init__(self, shared_name)

        self._list = {}
        self._last_item = None
        self._auto_counter = 0
        self._base_name = base_name

        type = kwargs.get('type', NamedList.TYPE_PASSIVE)
        self._type = type

    def __repr__(self):
        s = "NamedList with %s" % str(self.get_items())
        return s

    def __getitem__(self, name):
        return self.get(name)

    def __delitem__(self, name):
        self.remove(name)

    def __iter__(self):
        return self._list.__iter__()

    def __contains__(self, key):
        return key in self._list

    def has_key(self, key):
        return key in self._list

    def new_item_name(self, item, name):
        '''Generate a new item name.'''

        if name != '':
            return name

        self._auto_counter += 1
        name = self._base_name + str(self._auto_counter)
        return name

    def get(self, name=''):
        '''
        Get an item from the list.

        If the list is of TYPE_ACTIVE it will create a new item if the
        requested one does not exist.

        If it is of TYPE_PASSIVE it will return None.
        '''

        if name in self._list:
            return self._list[name]

        if self._type == NamedList.TYPE_PASSIVE:
            return None

        item = self.create(name)
        name = self.new_item_name(item, name)
        self.add(name, item)
        return item

    def add(self, name, item):
        '''Add an item to the list.'''
        if name in self._list:
            self.remove(name)
        self._list[name] = item
        self._last_item = item
        self.emit('item-added', name)

    def remove(self, name):
        '''Remove an item from the list.'''
        if name in self._list:
            if self._last_item is self._list[name]:
                self._last_item = None
            del self._list[name]
            _clear_ipython()
        self.emit('item-removed', name)

    def clear(self):
        for name in self._list.keys():
            self.remove(name)

    def create(self, name, **kwargs):
        '''Function to create a new instance if type is TYPE_ACTIVE'''
        return None

    def get_items(self):
        '''Return a list of available items.'''
        keys = self._list.keys()
        keys.sort()
        return keys

    def get_last(self):
        '''Return last item added to the list.'''
        return self._last_item

    def get_base_name(self):
        return self._base_name

