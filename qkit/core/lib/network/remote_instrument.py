# remote_instrument.py, TCP/IP client/server for sharing instruments between
# remote QTlab instances.
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

import logging
import qt
import copy
import object_sharer as objsh

class InstrumentServer(objsh.SharedObject):

    def __init__(self):
        objsh.SharedObject.__init__(self, name='instrument_server')

    def ins_get(self, insname, parname):
        return qt.instruments[insname].get(parname)

    def ins_set(self, insname, parname, val):
        return qt.instruments[insname].set(parname, val)

    def ins_call(self, insname, funcname, *args, **kwargs):
        func = getattr(qt.instruments[insname], funcname)
        return func(*args, **kwargs)

    def get_ins_list(self):
        return qt.instruments.get_instrument_names()

    def get_ins_parameters(self, insname):
        params = copy.copy(qt.instruments[insname].get_parameters())
        for name in params.keys():
            params[name] = copy.copy(params[name])
            params[name]['get_func'] = None
            params[name]['set_func'] = None
        return params

    def get_ins_functions(self, insname):
        funcs = copy.copy(qt.instruments[insname].get_functions())
        for name in funcs.keys():
            funcs[name] = copy.copy(funcs[name])
        return funcs

def create(remote_instance, remote_name, prefix='remote_', name=None):
    srv = objsh.helper.find_object('%s:instrument_server' % remote_instance)
    if srv is None:
        logging.error('Unable to locate remote instrument server')
        return None

    if name is None:
        name = prefix + remote_name
    ins = qt.instruments.create(name, 'Remote_Instrument',
            remote_name=remote_name, inssrv=srv)
    return ins

def create_all(remote_instance, prefix='remote_'):
    srv = objsh.helper.find_object('%s:instrument_server' % remote_instance)
    if srv is None:
        logging.error('Unable to locate remote instrument server')
        return None

    inslist = srv.get_ins_list()
    for insname in inslist:
        logging.info('Creating instrument: %s', insname)
        localname = '%s%s' % (prefix, insname)
        qt.instruments.create(localname, 'Remote_Instrument',
                remote_name=insname, inssrv=srv)


