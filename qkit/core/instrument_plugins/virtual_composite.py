# virtual_composite.py, virtual instrument to scale/combine other variables
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

from instrument import Instrument
import types

class virtual_composite(Instrument):

    def __init__(self, name):
        Instrument.__init__(self, name, tags=['virtual'])

        self._combine_info = {}
        self._instrument_watch = []

    def _update_options(self, kwargs, ins, parameter):
        opt = ins.get_parameter_options(parameter)
        copyopt = ['flags', 'type']
        for i in copyopt:
            if i in opt and i not in kwargs:
                kwargs[i] = opt[i]

        # FLAG_SOFTGET and FLAG_GET_AFTER_SET have to be disabled
        kwargs['flags'] &= ~(Instrument.FLAG_SOFTGET | Instrument.FLAG_GET_AFTER_SET)
        # FLAG_GET needs to be set
        kwargs['flags'] |= Instrument.FLAG_GET

        # Set to sweep by default
        if 'tags' not in kwargs:
            kwargs['tags'] = []
        if 'sweep' not in kwargs['tags']:
            kwargs['tags'].append('sweep')

    def add_variable_scaled(self, scaled_name, ins, parameter, scale, ofs, **kwargs):
        '''
        Shortcut for created a scaled variable, see add_variable_combined for info.
        '''

        self.add_variable_combined(scaled_name, [{
                'instrument': ins,
                'parameter': parameter,
                'scale': scale,
                'offset': ofs
            }], **kwargs)

    def add_variable_couple(self, combined_name, ins1, par1, ins2, par2, **kwargs):
        '''
        Shortcut for creating a pair of variables that should be set to the
        same value. See add_variable_combined for more info.
        '''

        if 'units' not in kwargs:
            opt = ins1.get_parameter_options(par1)
            if 'units' in opt:
                kwargs['units'] = opt['units']

        self.add_variable_combined(combined_name, [
            {
                'instrument': ins1,
                'parameter': par1,
                'scale': 1,
                'offset': 0
            }, {
                'instrument': ins2,
                'parameter': par2,
                'scale': 1,
                'offset': 0
            }], **kwargs)

    def add_variable_combined(self, combined_name, info_array, **kwargs):
        '''
        Create a new variable that consists of one or more other variables
        
        Input:
            combined_name (string): name of new variable
            info_array (array): array with dictionary information for variables
                instrument: which instrument
                parameter: which parameter
                scale: scale value
                offset: offset
            kwargs: keyword argument options for the new parameter

        Output:
            None
        '''

        self._update_options(kwargs, info_array[0]['instrument'], info_array[0]['parameter'])

        self._combine_info[combined_name] = info_array

        for info in info_array:
            if info['instrument'] not in self._instrument_watch:
                self._instrument_watch.append(info['instrument'])
                info['instrument'].connect('changed', self._instrument_changed_cb)

        funcname = 'do_get_%s' % combined_name
        setattr(self, funcname, lambda: self._get_combined(combined_name))
        funcname = 'do_set_%s' % combined_name
        setattr(self, funcname, lambda v: self._set_combined(combined_name, v))

        self.add_parameter(combined_name, **kwargs)

    def _get_combined(self, varname):
        ret = 0
        info = self._combine_info[varname]
        for pinfo in info:
            val = pinfo['instrument'].get(pinfo['parameter'], query=False)
            if val is not None:
                ret += (val + pinfo['offset']) / pinfo['scale']

        return ret

    def _set_combined(self, varname, val):
        info = self._combine_info[varname]
        for pinfo in info:
            newval = val * pinfo['scale'] - pinfo['offset']
            pinfo['instrument'].set(pinfo['parameter'], newval)

    def _instrument_changed_cb(self, sender, changes):
        for combined_name, info in self._combine_info.iteritems():
            for pinfo in info:
                if pinfo['instrument'] == sender:
                    if pinfo['parameter'] in changes:
                        self.get(combined_name)

