# instruments.py, code for a collection of instruments.
# Reinier heeres, <reinier@heeres.eu>, 2008
# HR @ KIT 2017

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
import qkit

import inspect
import os
import logging
import sys
import tomli
import qkit.core.instrument_base as instrument

import importlib


from qkit.core.lib.misc import get_traceback
TB = get_traceback()()

def _get_driver_module(name, do_reload=False):

    if name in sys.modules and not do_reload:
        return sys.modules[name]

    try:
        mod = importlib.import_module(name)
        if do_reload:
            importlib.reload(mod)
    except ImportError as e:
        fields = str(e).split(' ')
        if len(fields) > 0 and fields[-1] == name:
            logging.warning('Instrument driver %s not available', name)
        else:
            TB()
        return None
    except Exception as e:
        TB()
        logging.error('Error loading instrument driver %s', name)
        return None

    if name in sys.modules:
        return sys.modules[name]

    return None


class Insttools(object):

    __id = 1
    def __init__(self):
        Insttools.__id += 1

        self._instruments = {}
        self._instruments_info = {}
        self._tags = []
        self._instdir       = qkit.cfg.get('instruments_dir')
        self._user_instdir  = qkit.cfg.get('user_instruments_dir')
        lookup_dict_location = qkit.cfg.get('device_lookup_config')
        if lookup_dict_location is not None:
            self._lookup_dict = tomli.load(lookup_dict_location)
        else:
            self._lookup_dict = {}


    def __getitem__(self, key):
        return self.get(key)

    def __repr__(self):
        s = "Instruments list %s" % str(self.get_instrument_names())
        return s

    def add(self, ins, create_args={}):
        '''
        Add instrument to the internal instruments list and listen
        to signals emitted by the instrument.

        Input:  Instrument object
        Output: None
        '''

        self._instruments[ins.get_name()] = ins

        info = {'create_args': create_args}
        self._instruments_info[ins.get_name()] = info

        newtags = []
        for tag in ins.get_tags():
            if tag not in self._tags:
                self._tags.append(tag)
                newtags.append(tag)

    def get(self, name):
        '''
        Return Instrument object with name 'name'.

        Input:  name of instrument (string)
        Output: Instrument object
        '''

        if isinstance(name, instrument.Instrument):
            return name

        if type(name) == tuple:
            if len(name) != 1:
                return None
            name = name[0]

        if name in self._instruments:
            return self._instruments[name]
        else:
            return None

    def get_instrument_names(self):
        return sorted(self._instruments.keys())

    def get_instruments(self):
        '''
        Return the instruments dictionary of name -> Instrument.
        '''
        return self._instruments

    def get_types(self):
        '''
        Return list of supported instrument types
        '''
        ret = []
        filelist = os.listdir(self._instdir)
        for path_fn in filelist:
            path, fn = os.path.split(path_fn)
            name, ext = os.path.splitext(fn)
            if ext == '.py' and name[0] != '_':
                ret.append(name)
                
        if self._user_instdir:
            filelist = os.listdir(self._user_instdir)
            for path_fn in filelist:
                path, fn = os.path.split(path_fn)
                name, ext = os.path.splitext(fn)
                if ext == '.py' and name[0] != '_' and not ret.count(name) > 0:
                    ret.append(name)
        ret.sort()
        return ret

    def type_exists(self, typename):
        driverfn = os.path.join(self._instdir, '%s.py' % typename)
        if os.path.exists(driverfn):
            return True
        if self._user_instdir is None:
            return False
        driverfn = os.path.join(self._user_instdir, '%s.py' % typename)
        return os.path.exists(driverfn)
        
    def get_type_arguments(self, typename):
        '''
        Return info about the arguments of the constructor of 'typename'.

        Input:
            typename (string)
        Output:
            Tuple of (args, varargs, varkw, defaults)
            args: argument names
            varargs: name of '*' argument
            varkw: name of '**' argument
            defaults: default values
        '''

        module = _get_driver_module(typename)
        insclass = getattr(module, typename, None)
        if insclass is None:
            return None
        sig = inspect.signature(insclass.__init__)
        return list(sig.parameters.keys())

    def get_instruments_by_type(self, typename):
        '''
        Return all existing Instrument instances of type 'typename'.
        '''

        ret = []
        for name, ins in self._instruments.items():
            if ins.get_type() == typename:
                ret.append(ins)
        return ret

    def get_tags(self):
        '''
        Return list of tags present in instruments.
        '''

        return self._tags

    def _create_invalid_ins(self, name, instype, **kwargs):
        ins = instrument.InvalidInstrument(name, instype, **kwargs)
        self.add(ins, create_args=kwargs)
        return self.get(name)

    def create(self, name, instype, **kwargs):
        '''
        Create an instrument called 'name' of type 'type'.

        Input:  (1) name of the newly created instrument (string)
                (2) type of instrument (string)
                (3) optional: keyword arguments.
                    (1) tags, array of strings representing tags
                    (2) many instruments require address=<address>

        Output: Instrument object (Proxy)
        '''

        if not self.type_exists(instype):
            logging.error('Instrument type %s not supported', instype)
            return None

        if name in self._instruments:
            logging.warning('Instrument "%s" already exists, removing', name)
            self.remove(name)

        module = _get_driver_module(instype)
        if module is None:
            return self._create_invalid_ins(name, instype, **kwargs)
            
        importlib.reload(module)

        insclass = getattr(module, instype, None)
        if insclass is None:
            logging.error('Driver does not contain instrument class')
            return self._create_invalid_ins(name, instype, **kwargs)

        try:
            ins = insclass(name, **kwargs)
            for param_name in ins.get_parameter_names():
                if ins.get_parameter_options(param_name)['flags'] & ins.FLAG_GET: # do not query non-get or softget parameters
                    ins.get(param_name)  # Get all device parameters. This ensures that all get functions are working.
        except Exception as e:
            TB()
            logging.error('Error creating instrument %s: %s', name,e)
            return self._create_invalid_ins(name, instype, **kwargs)

        self.add(ins, create_args=kwargs)
        
        # Create a file where all created instruments with all parameters are stored once
        try:
            idn = ins.ask("*IDN?").strip()
        except:
            idn = "__none__"
        descr = str(name)+"#"+str(instype)+"#"+idn+"#"+str(kwargs)+"\r\n"
        fname = os.path.join(qkit.cfg['datadir'], "instrument.txt")  # save to datadir, because this is synced to backup server
        open(fname, "a").close() #create file if not existing
        with open(fname, "r+") as f:
            if not descr.strip() in [r.strip() for r in f.readlines()]:
                f.write(descr)
        return self.get(name)

    def create_from_config(self, name, **kwargs):
        """
        Check in the local config file for the device name. If it exists, take the config from there to create the device.
        
        Override with values from keyword arguments.
        """
        # This merges the configuration dict with
        config = {**self._lookup_dict[name], **kwargs, 'name': name}
        return self.create(**config)


    def reload_module(self, instype):
        module = _get_driver_module(instype, do_reload=True)
        return module is not None

    def reload(self, ins):
        '''
        Try to reload the module associated with instrument 'ins' and return
        the new instrument.

        In general about reloading: your milage may vary!

        Input:
            ins (Instrument or string): the instrument to reload

        Output:
            Reloaded instrument (Proxy)
        '''

        if type(ins) is bytes:
            ins = self.get(ins)
        if ins is None:
            return None

        insname = ins.get_name()
        instype = ins.get_type()
        kwargs = self._instruments_info[insname]['create_args']

        logging.info('reloading %r, type: %r, kwargs: %r',
                insname, instype, kwargs)

        self.remove(insname)
        reload_ok = self.reload_module(instype)
        if not reload_ok:
            return self._create_invalid_ins(insname, instype, **kwargs)

        return self.create(insname, instype, **kwargs)

    def auto_load(self, driver):
        '''
        Automatically load all instruments detected by 'driver' (an
        instrument_plugin module). This works only if it is supported by the
        driver by implementing a detect_instruments() function.
        '''

        module = _get_driver_module(driver)
        if module is None:
            return False
        importlib.reload(module)

        if not hasattr(module, 'detect_instruments'):
            logging.warning('Driver does not support instrument detection')
            return False

        devs = self.get_instruments_by_type(driver)
        for dev in devs:
            dev.remove()

        try:
            module.detect_instruments()
            return True
        except:
            return False

    def remove(self, name):
        '''
        Remove instrument from list and emit instrument-removed signal.

        Input:  (1) instrument name
        Output: None
        '''
        if name in self._instruments:
            del self._instruments[name]
            del self._instruments_info[name]

    class InstrumentBoundsError(ValueError):
        "Base Error to raise when instrument is out of bounds"
        pass

if __name__ == '__main__':
    i = Insttools()
    i.create('test1', 'HP1234')
