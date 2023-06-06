# -*- coding: utf-8 -*-
# qData.py analysis class for qkit measurements data
# Micha Wildermuth, micha.wildermuth@kit.edu 2023

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

import numpy as np
from collections import defaultdict
import itertools

import qkit
from qkit.storage.store import Data
import qkit.measure.measurement_class as mc
from qkit.gui.plot import plot as qviewkit
from qkit.storage import store as hdf
from qkit.storage.hdf_constants import ds_types
import json
from qkit.measure.json_handler import QkitJSONEncoder, QkitJSONDecoder


class dict2obj(object):
    def __init__(self, d):
        for a, b in d.items():
            if isinstance(b, (list, tuple)):
                setattr(self, a.replace(' ', '_'), [dict2obj(x) if isinstance(x, dict) else x for x in b])
            else:
                setattr(self, a.replace(' ', '_'), dict2obj(b) if isinstance(b, dict) else b)


class qData(object):
    """
    This is an analysis class for qkit measurements.
    """

    def __init__(self):
        """
        Initializes an analysis class for qkit .

        Parameters
        ----------
        None

        Returns
        -------
        None

        Examples
        --------
        >>> import numpy as np
        >>> import qkit
        QKIT configuration initialized -> available as qkit.cfg[...]
        >>> qkit.start()
        Starting QKIT framework ... -> qkit.core.startup
        Loading module ... S10_logging.py
        Loading module ... S12_lockfile.py
        Loading module ... S14_setup_directories.py
        Loading module ... S20_check_for_updates.py
        Loading module ... S25_info_service.py
        Loading module ... S30_qkit_start.py
        Loading module ... S65_load_RI_service.py
        Loading module ... S70_load_visa.py
        Loading module ... S80_load_file_service.py
        Loading module ... S85_init_measurement.py
        Loading module ... S98_started.py
        Loading module ... S99_init_user.py
        Initialized the file info database (qkit.fid) in 0.000 seconds.

        >>> from qkit.analysis.qdata import qData
        >>> qd = qData()
        """
        # qkit.fid.update_file_db()  # update file database
        self.uuid = self.path = self.df = None
        self.analysis = self.views = None
        self.settings = None
        self.measurement = mc.Measurement()  # qkit-sample object
        self.m_type = self.scan_dim = None
        self.x_ds = self.x_coordname = self.x_unit = self.x_vec = None
        self.y_ds = self.y_coordname = self.y_unit = self.y_vec = None
        self.si_prefix = {'y': 1e-24,  # yocto
                          'z': 1e-21,  # zepto
                          'a': 1e-18,  # atto
                          'f': 1e-15,  # femto
                          'p': 1e-12,  # pico
                          'n': 1e-9,  # nano
                          'u': 1e-6,  # micro
                          'm': 1e-3,  # milli
                          'c': 1e-2,  # centi
                          'd': 1e-1,  # deci
                          '': 1e0,
                          'k': 1e3,  # kilo
                          'M': 1e6,  # mega
                          'G': 1e9,  # giga
                          'T': 1e12,  # tera
                          'P': 1e15,  # peta
                          'E': 1e18,  # exa
                          'Z': 1e21,  # zetta
                          'Y': 1e24,  # yotta
                          }

    def load(self, uuid):
        """
        Loads qkit measurement data with given uuid <uuid>.

        Parameters
        ----------
        uuid: str
            Qkit identification name, that is looked for and loaded

        Returns
        -------
        None

        Examples
        --------
        >>> qd.load(uuid='XXXXXX')
        """
        if uuid != self.uuid and self.uuid is not None:
            self.__init__()
        self.uuid = uuid
        self.path = qkit.fid.get(self.uuid)
        self.df = Data(self.path)

        ''' load all entries '''
        for key, val in self.df.__dict__.items():  # all entries in df, except for hf, analysis, data, views, and default_ds
            if key[0] == '_':
                setattr(self, key[1:], val)
        for key, val in self.df.data.__dict__.items():  # all entries in data
            if key == 'settings':
                try:
                    self.settings = dict2obj(json.loads(self.df.data.settings[0], cls=QkitJSONDecoder))
                except AttributeError:
                    self.settings = None
                except:
                    self.settings = self.df.data.settings[:]
            elif key == 'measurement':
                try:
                    self.measurement.load(qkit.fid.measure_db[self.uuid])
                except:
                    self.measurement = dict2obj(json.loads(self.df.data.measurement[0], cls=QkitJSONDecoder))
            else:
                setattr(self, key, val[:])
        self.analysis = dict2obj({key: val[:] for key, val in self.df.analysis.__dict__.items()})  # all entries in analysis
        self.views = dict2obj({key: val for key, val in self.df['entry/views'].items()})  # all entries in views
        for name, view in self.views.__dict__.items():
            for a, b in self.views.__dict__[name].attrs.items():
                if not hasattr(view, a):  # avoid conflicts with same keys
                    setattr(self.views.__dict__[name], a, b)  # set view attributes (e.g. xy_0) as attributes of qd.views.<view>
        self.m_type = self.measurement.measurement_type  # measurement type

    def _get_xy_parameter(self, measurand):
        """
        Identifies eventual x- and y-parameters.

        Parameters
        ----------
        measurand: HDF5 dataset
            Dataset, whose attributes 'x_ds_url' and 'y_ds_url' are used to identify eventual x- and y-parameters.

        Returns
        -------
        None
        """
        if self.scan_dim >= 2:  # 2D or 3D scan
            # x parameter
            self.x_ds = self.df[measurand.attrs['x_ds_url']]
            self.x_coordname = self.x_ds.attrs['name']
            self.x_unit = self.x_ds.attrs['unit']
            self.x_vec = self.x_ds[:]
            if self.scan_dim == 3:  # 3D scan
                # y parameter
                self.y_ds = self.df[measurand.attrs['y_ds_url']]
                self.y_coordname = self.y_ds.attrs['name']
                self.y_unit = self.y_ds.attrs['unit']
                self.y_vec = self.y_ds[:]
            else:
                self.y_ds, self.y_coordname, self.y_unit, self.y_vec = None, None, None, None
        else:
            self.x_ds, self.x_coordname, self.x_unit, self.x_vec = None, None, None, None
        return

    def merge(self, uuids, order=None):
        """
        Merges qkit measurement data of several individual files with given uuids <uuids>.
        * 1D: all sweep data are stacked and views are merged.
        * 2D: values of x-parameter and its corresponding sweep data are merged in the order <order>.
        * 3D: values of x- and y-parameters and its corresponding sweep data are merged in the order <order>.

        Parameters
        ----------
        uuids: list of str
            Qkit identification names, that are looked for, loaded and merged.
        order: list of int (optional)
            Order by which data are merged. It is used to slice the data np.arrays via [::<order>], where 1 means same
            and -1 opposite direction. Default is 1 (same direction).

        Returns
        -------
        uuid: str
            Qkit identification names of created file

        Examples
        --------
        >>> qd.merge(uuid=['XXXXXX', 'YYYYYY'], order=[-1, 1])
        """

        def get_key(_key, _dict):
            """
            Check if key already exists and increases counter by one if so.
            """
            if _key in _dict.keys():
                _parts = _key.split('_')
                _key = '_'.join([str(int(_part) + 1) if _part.isdigit() else _part for _part in _parts])
                return get_key(_key, _dict)
            else:
                return _key

        def remove_duplicates(_list):
            _res = []
            for _elem in _list:
                if _elem not in _res:
                    _res.append(_elem)
            if len(_res) == 1:
                return _res[0]
            else:
                return _res

        def merge_dict(_listdict):
            dict_merged = defaultdict(list)
            for _dict in _listdict:
                for _key, _val in _dict.items():
                    dict_merged[_key].append(_val)
            return dict_merged

        # TODO: write additional files and plots
        order = np.ones_like(uuids, dtype=int) if order is None else np.array(order, dtype=int)
        ''' load data from input files '''
        data = []
        attrs = []
        run_user = []
        scan_dim = []
        for i, uuid in enumerate(uuids):
            data.append({})
            attrs.append({})
            self.load(uuid)
            run_user.append([self.measurement.run_id, self.measurement.user])
            scan_dim.append(self.scan_dim)
            for group in self.df.hf.entry:
                for dataset in self.df.hf.entry[group]:
                    path = '/'.join((group, dataset))
                    data[i][path] = self.df.hf.entry[path][:][::order[i]]
                    attrs[i][path] = self.df.hf.entry[path].attrs.items()
        ''' merge data '''
        if set(scan_dim) == {1}:
            keys, data_merged, attrs_merged = {}, {}, {}
            for j, d in enumerate(data):
                for key, val in d.items():
                    ds_type = dict(attrs[j][key])['ds_type']
                    if ds_type < 5:  # coordinate, vector, matrix or box
                        k = get_key(_key=key, _dict=keys)
                        keys[k] = (key, j)
                        data_merged[k] = [data[j][key]] * 2
                        attrs_merged[k] = (attrs[j][key],)
                    elif ds_type == ds_types['txt']:
                        keys[key] = (key,)
                        data_merged[key] = [d[key] for d in data]
                        attrs_merged[key] = [a[key] for a in attrs]
                    elif ds_type == ds_types['view']:
                        keys[key] = (key,)
                        data_merged[key] = (data[j][key],)
                        if j == 0:
                            attrs_merged[key] = [dict(attrs[j][key])] * 2
                        else:
                            for k, v in dict(attrs[j][key]).items():
                                # increase X of 'xy_X' and its values to the next possible
                                if 'xy_' in k and '_filter' not in k:
                                    new_key = get_key(_key=k, _dict=attrs_merged[key][0])
                                    attrs_merged[key][0][new_key] = ':'.join(
                                        ['_'.join([new_key.strip('xy_') if s.isdigit() else s for s in ulr.split('_')])
                                         for ulr in str(v, encoding='utf-8').split(':')]).encode()
                                # increase X of 'xy_X_filter' to the next possible
                                elif 'xy_' in k and '_filter' in k:
                                    attrs_merged[key][0][get_key(_key=k, _dict=attrs_merged[key][0])] = v
        else:
            keys = {key: (key,) for key in data[0].keys()}
            data_merged = merge_dict(_listdict=data)
            attrs_merged = merge_dict(_listdict=attrs)
        ''' write data to new file '''
        # create new file
        qkit.cfg['run_id'], qkit.cfg['user'] = np.squeeze(np.vstack({tuple(row) for row in run_user}))
        _data_file = hdf.Data(name='+'.join(uuids), mode='a')
        # create and write measurement, settings and coordinates
        ds = {}
        for key, val in data_merged.items():
            name = key.split('/')[1]
            attr = dict(attrs_merged[key][0])
            ds_type = attr['ds_type']
            if ds_type == ds_types['txt']:  # measurement, settings
                txt_merged = merge_dict(_listdict=[json.loads(d[0], cls=QkitJSONDecoder) for d in val])
                ds[key] = _data_file.add_textlist(name)
                if 'settings' in key:
                    ds[key].append({kk: {k: remove_duplicates(_list=map(lambda x: x[k], dic)) for k in dic[0]}
                                    for kk, dic in dict(txt_merged).items()})
                elif 'measurement' in key:
                    if set(scan_dim) == {1}:
                        # merge sweeps in sample object
                        for k, v in txt_merged.items():
                            if np.iterable(v) and type(v[0]) is dict:
                                txt_merged[k] = [{k: np.vstack(v) if 'sweeps' in k else remove_duplicates(_list=v) for
                                                  k, v in merge_dict(_listdict=v).items()}] * 2
                    ds[key].append({k: remove_duplicates(_list=v) for k, v in txt_merged.items()})
            elif ds_type == ds_types['coordinate']:
                ds[key] = _data_file.add_coordinate(name=name,
                                                    unit=str(dict(attrs_merged[keys[key][0]][0])['unit'],
                                                             encoding='utf-8'))
                if np.array([np.array_equal(p[0], p[1])
                             for p in
                             itertools.combinations(np.array(list(itertools.zip_longest(*val, fillvalue=np.nan))).T,
                                                    2)]).all():
                    ds[key].add(val[0])
                else:
                    ds[key].add(np.concatenate(val))
        # create datasets
        for key, val in data_merged.items():
            name = key.split('/')[1]
            attr = dict(attrs_merged[key][0])
            ds_type = attr['ds_type']
            folder = key.split('0/')[0]
            if ds_type == ds_types['vector']:
                ds[key] = _data_file.add_value_vector(name=name,
                                                      x=ds[str(attr['x_ds_url'], encoding='utf-8').strip('/entry')],
                                                      unit=str(attr['unit'], encoding='utf-8'),
                                                      folder=folder,
                                                      save_timestamp=False)
            elif ds_type == ds_types['matrix']:
                ds[key] = _data_file.add_value_matrix(name=name,
                                                      x=ds[str(attr['x_ds_url'], encoding='utf-8').strip('/entry')],
                                                      y=ds[str(attr['y_ds_url'], encoding='utf-8').strip('/entry')],
                                                      unit=str(attr['unit'], encoding='utf-8'),
                                                      folder=folder,
                                                      save_timestamp=False)
            elif ds_type == ds_types['box']:
                ds[key] = _data_file.add_value_box(name=name,
                                                   x=ds[str(attr['x_ds_url'], encoding='utf-8').strip('/entry')],
                                                   y=ds[str(attr['y_ds_url'], encoding='utf-8').strip('/entry')],
                                                   z=ds[str(attr['z_ds_url'], encoding='utf-8').strip('/entry')],
                                                   unit=str(attr['unit'], encoding='utf-8'),
                                                   folder=folder,
                                                   save_timestamp=False)
        # write values to datasets and create and write views
        for key, val in data_merged.items():
            name = key.split('/')[1]
            attr = dict(attrs_merged[key][0])
            ds_type = attr['ds_type']
            if ds_type == ds_types['vector']:
                ds[key].append(val[0])
            elif ds_type == ds_types['matrix']:
                [ds[key].append(x) for x in np.concatenate(val)]
            elif ds_type == ds_types['box']:
                for xs in np.concatenate(val):
                    [ds[key].append(x) for x in xs]
                    ds[key].next_matrix()
            elif ds_type == ds_types['view']:
                if np.array([np.array_equal(p[0], p[1]) for p in
                             itertools.combinations(list(map(list, attrs_merged[key])), 2)]).all():
                    for j, xy in enumerate(
                            filter(lambda k: 'xy_' in k and '_filter' not in k, dict(attrs_merged[key][0]).keys())):
                        x, y = [i.strip('/entry') for i in
                                str(dict(attrs_merged[key][0])[xy], encoding='utf-8').split(':')]
                        if j == 0:
                            ds[key] = _data_file.add_view(name=name, x=ds[x], y=ds[y],
                                                          view_params=json.loads(
                                                              dict(attrs_merged[key][0])['view_params']))
                        else:
                            ds[key].add(x=ds[x], y=ds[y])
        # close new file
        _data_file.close_file()
        return _data_file.__dict__['_uuid']

    def open_qviewkit(self, uuid=None, ds=None):
        """
        Opens qkit measurement data with given uuid <uuid> in qviewkit.

        Parameters
        ----------
        uuid: str
            Qkit identification name, that is looked for and opened in qviewkit
        ds: str | list(str)
            Datasets that are opened instantaneously.

        Returns
        -------
        None

        See also
        --------
        qkit.gui.plot.plot
            qviewkit gui to display qkit .h5-files.
        """
        if uuid is None:
            path = self.path
        else:
            path = qkit.fid.get(uuid)
        if ds is None or np.iterable(ds) and all(isinstance(x, str) for x in ds):
            pass
        elif type(ds) is str:
            ds = [ds]
        else:
            raise ValueError('Argument <ds> needs to be set properly.')
        qviewkit.plot(path, datasets=ds, live=False)  # opens ds by default



