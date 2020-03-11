# -*- coding: utf-8 -*-
# IV_curve.py analysis class for IV like transport measurements
# Micha Wildermuth, micha.wildermuth@kit.edu 2019

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

import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal as sig
from collections import defaultdict
# TODO: uncertainty analysis probably using import uncertainties

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
                setattr(self, a, [dict2obj(x) if isinstance(x, dict) else x for x in b])
            else:
                setattr(self, a, dict2obj(b) if isinstance(b, dict) else b)


class IV_curve3(object):
    """
    This is an analysis class IV like transport measurements taken by qkit.measure.transport.transport.py
    """

    def __init__(self):
        """
        Initializes an analysis class IV like transport measurements taken by qkit.measure.transport.transport.py

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

        >>> from qkit.analysis.IV_curve import IV_curve as IVC
        >>> ivc = IVC()
        Initialized the file info database (qkit.fid) in 0.000 seconds.
        """
        qkit.fid.update_file_db()  # update file database
        self.uuid, self.path, self.df = None, None, None
        self.settings = None
        self.mo = mc.Measurement()  # qkit-sample object
        self.m_type, self.scan_dim, self.sweeptype, self.sweeps, self.bias = None, None, None, None, None
        self.I, self.V, self.V_corr, self.dVdI, self.d2VdI2 = None, None, None, None, None
        self.I_offsets, self.V_offsets, self.I_offset, self.V_offset = None, None, None, None
        self.x_ds, self.x_coordname, self.x_unit, self.x_vec = None, None, None, None
        self.y_ds, self.y_coordname, self.y_unit, self.y_vec = None, None, None, None
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
                          'k': 1e3,  # kilo
                          'M': 1e6,  # mega
                          'G': 1e9,  # giga
                          'T': 1e12,  # tera
                          'P': 1e15,  # peta
                          'E': 1e18,  # exa
                          'Z': 1e21,  # zetta
                          'Y': 1e24,  # yotta
                          }
        self.scm = self.switching_current(sweeps=self.sweeps,
                                          settings=self.settings)  # subclass for switching current measurement analysis

    def load(self, uuid, dVdI='analysis0'):
        """
        Loads transport measurement data with given uuid <uuid>.

        Parameters
        ----------
        uuid: str
            Qkit identification name, that is looked for and loaded
        dVdI: str | boolean
            Folder, where numerical derivative dV/dI is tried to load form datafile, if this was already analyzed during the measurement. If False, dV/dI is not loaded. Default is 'analysis0'.

        Returns
        -------
        None

        Examples
        --------
        >>> ivc.load(uuid='XXXXXX')
        """
        if uuid != self.uuid and self.uuid is not None:
            self.__init__()
        self.uuid = uuid
        self.path = qkit.fid.get(self.uuid)
        self.df = Data(self.path)
        try:
            self.settings = dict2obj(json.loads(self.df.data.settings[0], cls=QkitJSONDecoder))
        except:
            self.settings = self.df.data.settings[:]
        self.scm.settings = self.settings
        try:
            self.mo.load(qkit.fid.measure_db[self.uuid])
        except:
            self.mo = dict2obj(json.loads(self.df.data.measurement[0], cls=QkitJSONDecoder))
        self.m_type = self.mo.measurement_type  # measurement type
        if self.m_type == 'transport':
            self.scan_dim = self.df.data.i_0.attrs['ds_type']  # scan dimension (1D, 2D, ...)
            self.bias = self.get_bias()
            self.sweeps = self.mo.sample.sweeps  # sweeps (start, stop, step)
            self.scm.sweeps = self.sweeps
            self.sweeptype = self.get_sweeptype()
            shape = np.concatenate([[len(self.sweeps)], np.max([self.df['entry/data0/i_{:d}'.format(j)].shape for j in range(len(self.sweeps))], axis=0)])  # (number of sweeps, eventually len y-values, eventually len x-values, maximal number of sweep points)
            self.I, self.V, self.dVdI = np.empty(shape=shape), np.empty(shape=shape), np.empty(shape=shape)
            for j in range(shape[0]):
                i = self.df['entry/data0/i_{:d}'.format(j)][:]
                v = self.df['entry/data0/v_{:d}'.format(j)][:]
                if dVdI:
                    try:
                        dvdi = self.df['entry/{:s}/dvdi_{:d}'.format(dVdI, j)][:]  # if analysis already done during measurement
                    except KeyError:
                        dvdi = self.get_dydx(x=self.I[j], y=self.V[j])
                pad_width = np.insert(np.diff([i.shape, shape[1:]], axis=0), (0,), np.zeros(self.scan_dim)).reshape(self.scan_dim, 2)
                if pad_width.any():
                    self.I[j] = np.pad(i, pad_width, 'constant', constant_values=np.nan)  # fill with current values (eventually add nans at the end, if sweeps have different lengths)
                    self.V[j] = np.pad(v, pad_width, 'constant', constant_values=np.nan)  # fill with voltage values (eventually add nans at the end, if sweeps have different lengths)
                    if dVdI:
                        self.dVdI[j] = np.pad(dvdi, pad_width, 'constant', constant_values=np.nan)  # fill with differential resistance values (eventually add nans at the end, if sweeps have different lengths)
                else:
                    self.I[j] = i
                    self.V[j] = v
                    if dVdI:
                        self.dVdI[j] = dvdi
            if self.scan_dim >= 2:  # 2D or 3D scan
                # x parameter
                self.x_ds = self.df[self.df.data.i_0.attrs['x_ds_url']]
                self.x_coordname = self.x_ds.attrs['name']
                self.x_unit = self.x_ds.attrs['unit']
                self.x_vec = self.x_ds[:]
                if self.scan_dim == 3:  # 3D scan
                    # y parameter
                    self.y_ds = self.df[self.df.data.i_0.attrs['y_ds_url']]
                    self.y_coordname = self.y_ds.attrs['name']
                    self.y_unit = self.y_ds.attrs['unit']
                    self.y_vec = self.y_ds[:]
                else:
                    self.y_ds, self.y_coordname, self.y_unit, self.y_vec = None, None, None, None
            else:
                self.x_ds, self.x_coordname, self.x_unit, self.x_vec = None, None, None, None
        else:
            raise ValueError('No data of transport measurements')
        return

    def merge(self, uuids, order=None):
        """
        Merges transport measurement data of several individual files with given uuids <uuids>.
        * 1D: all sweep data are stacked and views are merged.
        * 2D: values of x-parameter and its corresponding sweep data are merged in the order <order>.
        * 3D: values of x- and y-parameters and its corresponding sweep data are merged in the order <order>.

        Parameters
        ----------
        uuids: list of str
            Qkit identification names, that are looked for, loaded and merged.
        order: list of int (optional)
            Order by which data are merged. It is used to slice the data np.arrays via [::<order>], where 1 means same  and -1 opposite direction. Default is 1 (same direction).

        Returns
        -------
        uuid: str
            Qkit identification names of created file

        Examples
        --------
        >>> ivc.merge(uuid=['XXXXXX', 'YYYYYY'], order=[-1, 1])
        """
        def get_key(key, dct):
            """
            Check if key already exists and increases counter by one if so.
            """
            if key in dct.keys():
                parts = key.split('_')
                key = '_'.join([str(int(part)+1) if part.isdigit() else part for j, part in enumerate(parts)])
                return get_key(key, dct)
            else:
                return key
        def remove_duplicates(lst):
            res = []
            for x in lst:
                if x not in res:
                    res.append(x)
            """
            res = []
            for x in lst:
                if x not in res:
                    res.append(x)
            """
            if len(res) == 1:
                return res[0]
            else:
                return res
        def merge_dict(lstdct):
            dict_merged = defaultdict(list)
            for dct in lstdct:
                for key, val in dct.items():
                    dict_merged[key].append(val)
            return dict_merged

        #TODO: write additional files and plots
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
            run_user.append([self.mo.run_id, self.mo.user])
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
                        k = get_key(key=key, dct=keys)
                        keys[k] = (key, j)
                        data_merged[k] = [data[j][key]]*2
                        attrs_merged[k] = (attrs[j][key],)
                    elif ds_type == ds_types['txt']:
                        keys[key] = (key,)
                        data_merged[key] = [d[key] for d in data]
                        attrs_merged[key] = [a[key] for a in attrs]
                    elif ds_type == ds_types['view']:
                        keys[key] = (key, )
                        data_merged[key] = (data[j][key], )
                        if j == 0:
                            attrs_merged[key] = [dict(attrs[j][key])]*2
                        else:
                            for k, v in dict(attrs[j][key]).items():
                                # increase X of 'xy_X' and its values to the nex possible
                                if 'xy_' in k and '_filter' not in k:
                                    new_key = get_key(key=k, dct=attrs_merged[key][0])
                                    attrs_merged[key][0][new_key] = ':'.join(['_'.join([new_key.strip('xy_') if s.isdigit() else s for s in ulr.split('_')]) for ulr in str(v, encoding='utf-8').split(':')]).encode()
                                # increase X of 'xy_X_filter' to the nex possible
                                elif 'xy_' in k and '_filter' in k:
                                    attrs_merged[key][0][get_key(key=k, dct=attrs_merged[key][0])] = v
        else:
            keys = {key: (key, ) for key in data[0].keys()}
            data_merged = merge_dict(data)
            attrs_merged = merge_dict(attrs)
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
                txt_merged = merge_dict(json.loads(d[0], cls=QkitJSONDecoder) for d in val)
                ds[key] = _data_file.add_textlist(name)
                if 'settings' in key:
                    ds[key].append({kk: {k: remove_duplicates(map(lambda x: x[k], dic)) for k in dic[0]}
                                    for kk, dic in dict(txt_merged).items()})
                elif 'measurement' in key:
                    if set(scan_dim) == {1}:
                        # merge sweeps in sample object
                        for k, v in txt_merged.items():
                            if np.iterable(v) and type(v[0]) is dict:
                                txt_merged[k] = [{k: np.vstack(v) if 'sweeps' in k else remove_duplicates(v) for k, v in merge_dict(v).items()}]*2
                    ds[key].append({k: remove_duplicates(v) for k, v in txt_merged.items()})
            elif ds_type == ds_types['coordinate']:
                ds[key] = _data_file.add_coordinate(name=name,
                                                    unit=str(dict(attrs_merged[keys[key][0]][0])['unit'], encoding='utf-8'))
                if np.array_equal(*np.array(val)):
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
                if np.array_equal(*list(map(list, attrs_merged[key]))):
                    for j, xy in enumerate(filter(lambda k: 'xy_' in k and '_filter' not in k, dict(attrs_merged[key][0]).keys())):
                        x, y = [i.strip('/entry') for i in str(dict(attrs_merged[key][0])[xy], encoding='utf-8').split(':')]
                        if j == 0:
                            ds[key] = _data_file.add_view(name=name, x=ds[x], y=ds[y],
                                                          view_params=json.loads(dict(attrs_merged[key][0])['view_params']))
                        else:
                            ds[key].add(x=ds[x], y=ds[y])
        # close new file
        _data_file.close_file()
        return _data_file.__dict__['_uuid']

    def save(self, filename, params=None):
        """
        Saves the class variables
             * uuid,
             * path,
             * measurement_object,
             * measurement_type,
             * scan_dimension,
             * sweep_type,
             * sweeps,
             * bias,
             * I,
             * V,
             * V_corr (only if set
             * dVdI,
             * I_offsets,
             * V_offsets,
             * I_offset,
             * V_offset,
             * x_coordname,
             * x_unit,
             * x_vector,
             * y_coordname,
             * y_unit,
             * y_vector
        as well as <params> to a json-file.

        Parameters
        ----------
        filename: str
            Filename of the .json-file that is created.
        params: dict
            Additional variables that are saved. Default is None, so that only the above mentioned class variables are saved.

        Returns
        -------
        None
        """
        params = params if params else {}
        params = {**{'uuid': self.uuid,
                     'path': self.path,
                     'measurement_object': self.mo.get_JSON(),
                     'measurement_type': self.m_type,
                     'scan_dimension': self.scan_dim,
                     'sweep_type': self.sweeptype,
                     'sweeps': self.sweeps,
                     'bias': self.bias,
                     'I': self.I,
                     'V': self.V,
                     'dVdI': self.dVdI,
                     'I_offsets': self.I_offsets,
                     'V_offsets': self.V_offsets,
                     'I_offset': self.I_offset,
                     'V_offset': self.V_offset,
                     'x_coordname': self.x_coordname,
                     'x_unit': self.x_unit,
                     'x_vector': self.x_vec,
                     'y_coordname': self.y_coordname,
                     'y_unit': self.y_unit,
                     'y_vector': self.y_vec},
                  **params}
        if self.V_corr:
            params['V_corr'] = self.V_corr
        if '.json' not in filename:
            filename += '.json'
        with open(filename, 'w') as filehandler:
            json.dump(obj=params, fp=filehandler, indent=4, cls=QkitJSONEncoder, sort_keys=True)

    def open_qviewkit(self, uuid=None, ds=None):
        """

        uuid: str
        ds: str | list(str)
            Datasets that are opened instantaneously. Default is 'views/IV'
        """
        if uuid is None:
            df = self.df
        else:
            df = Data(qkit.fid.get(uuid))
        if ds is None:
            ds = ['views/IV']
            # try:
            #     if self.scan_dim > 1:
            #         for i in range(len(self.sweeps)):
            #             datasets.append('{:s}_{:d}'.format({0: 'I', 1: 'V'}[not self.bias].lower(), i))
        elif not np.iterable(ds) and type(ds) is str:
            ds = [ds]
        else:
            raise ValueError('Argument <ds> needs to be set properly.')
        qviewkit.plot(df.get_filepath(), datasets=ds)  # opens IV-view by default

    def get_bias(self, df=None):
        """
        Gets bias mode of the measurement. Evaluate 'x_ds_url' (1D), 'y_ds_url' (2D), 'z_ds_url' (3D) of i_0 and v_0 and checks congruence.

        Parameters
        ----------
        df: qkit.storage.store.Data (optional)
            Datafile of transport measurement. Default is None that means self.df

        Returns
        -------
        mode: int
            Bias mode. Meanings are 0 (current) and 1 (voltage).
        """
        #
        if df is None:
            df = self.df
        self.bias = {'i': 0, 'v': 1}[str(
            df.data.i_0.attrs.get('{:s}_ds_url'.format(chr(self.scan_dim + 119))) and
            df.data.v_0.attrs.get('{:s}_ds_url'.format(chr(self.scan_dim + 119)))).split('/')[-1][0]]
        return self.bias

    def get_sweeptype(self, sweeps=None):
        """
        Gets the sweeptype of predefined set of sweeps as generated by qkit.measure.transport.transport.py

        Parameters
        ----------
        sweeps: array_likes of array_likes of floats (optional)
            Set of sweeps containing start, stop and step size (e.g. sweep object using qkit.measure.transport.transport.sweep class). Default is None that means self.sweeps.

        Returns
        -------
        sweeptype: int
            Type of set of sweeps. Is 0 (halfswing), 1 (4 quadrants) or None (arbitrary set of sweeps).
        """
        if sweeps is None:
            sweeps = self.sweeps
        # check if sweeps are halfswing
        if len(sweeps) == 2:
            if all(np.array(sweeps[0])[[1, 0, 2]] == np.array(sweeps[1])[:3]):
                self.sweeptype = 0
        # check if sweeps are 4quadrants
        elif len(sweeps) == 4:
            if all(np.array(sweeps[0])[[1, 0, 2]] == np.array(sweeps[1])[:3]) and all(np.array(sweeps[2])[[1, 0, 2]] == np.array(sweeps[3])[:3]):
                self.sweeptype = 1
        else:
            self.sweeptype = None
        return self.sweeptype

    def get_dVdI(self, I=None, V=None, mode=sig.savgol_filter, **kwargs):
        """
        Calculates numerical derivative dV/dI.

        Parameters
        ----------
        I: numpy.array (optional)
            An N-dimensional array containing current values. Default is None that means self.I.
        V: numpy.array (optional)
            An N-dimensional array containing voltage values. Default is None that means self.V.
        mode: function (optional)
            Function that calculates the numerical gradient dx from a given array x. Default is scipy.signal.savgol_filter (Savitzky Golay filter).
        kwargs:
            Keyword arguments forwarded to the function <mode>.

        Returns
        -------
        dVdI: numpy.array
            Numerical derivative dV/dI

        Examples
        --------
        # Savitzky Golay filter
        >>> ivc.get_dVdI()

        # numerical gradient
        >>> ivc.get_dVdI(mode=np.gradient)
        """
        if V is None:
            y = self.V
        else:
            y = V
        if I is None:
            x = self.I
        else:
            x = I
        self.dVdI = self.get_dydx(y=y, x=x, mode=mode, **kwargs)
        return self.dVdI

    def get_dydx(self, y, x=None, mode=sig.savgol_filter, **kwargs):
        """
        Calculates numerical derivative dy/dx

        Parameters
        ----------
        y: numpy.array
            An N-dimensional array containing y-values
        x: numpy.array (optional)
            An N-dimensional array containing x-values. Default is None which means that x is considered as index.
        mode: function (optional)
            Function that calculates the numerical gradient dx from a given array x. Default is scipy.signal.savgol_filter (Savitzky Golay filter).
        kwargs:
            Keyword arguments forwarded to the function <mode>. Default for scipy.signal.savgol_filter is {'window_length': 15, 'polyorder': 3, 'deriv': 1} and for numpy.gradient {'axis': self.scan_dim}

        Returns
        -------
        dy/dx: numpy.array
            Numerical gradient quotient. If no x is given, dx = np.ones(nop)

        Examples
        --------
        Savitzky Golay filter
        >>> ivc.get_dydx(y=np.arange(1e1), mode=sig.savgol_filter, window_length=9, polyorder=3, deriv=1)
        array([1., 1., 1., 1., 1., 1., 1., 1., 1., 1.])

        numerical gradient
        >>> ivc.get_dydx(mode=np.gradient)
        ivc.get_dydx(y=np.arange(1e1), mode=np.gradient)
        """
        if mode == sig.savgol_filter:
            if 'window_length' not in kwargs.keys():
                kwargs['window_length'] = 15
            if 'polyorder' not in kwargs.keys():
                kwargs['polyorder'] = 3
            if 'deriv' not in kwargs.keys():
                kwargs['deriv'] = 1
        elif mode == np.gradient:
            if 'axis' not in kwargs.keys():
                kwargs['axis'] = self.scan_dim
        if x is None:
            if np.isnan(x).any():
                y_nans = np.isnan(y)
                dy = mode(np.nan_to_num(y, copy=True, nan=0.0), **kwargs)
                np.place(dy, y_nans, np.nan)
                return dy
            else:
                return mode(y, **kwargs)
        else:
            if np.isnan(x).any():
                x_nans = np.isnan(x)  # mask for np.nan
                y_nans = np.isnan(y)
                dx = mode(np.nan_to_num(x, copy=True, nan=0.0), **kwargs)  # derivation function with np.nan replaced by 0
                dy = mode(np.nan_to_num(y, copy=True, nan=0.0), **kwargs)
                np.place(dx, x_nans, np.nan)  # write np.nan using mask from above
                np.place(dy, y_nans, np.nan)
                return dy/dx
            else:
                return mode(y, **kwargs)/mode(x, **kwargs)

    def get_offsets(self, x=None, y=None, threshold=20e-6, offset=0, yr=False):
        """
        Calculates x- and y-offset for every trace. Therefore the branch where the y-values are nearly constant are evaluated. The average of all corresponding x-values is considered to be the x-offset and the average of the extreme y-values are considered as y-offset.

        Parameters
        ----------
        x: numpy.array (optional)
            An N-dimensional array containing x-values. Default is None, where x is considered as self.V and self.I in the current and voltage bias, respectively.
        y: numpy.array (optional)
            An N-dimensional array containing y-values. Default is None, where y is considered as self.I and self.V in the current and voltage bias, respectively.
        threshold: float (optional)
            Threshold voltage that limits the superconducting branch. Default is 20e-6.
        offset: float (optional)
            Voltage offset that shifts the limits of the superconducting branch which is set by <threshold>. Default is 0.
        yr: bool (optional)
            Condition, if critical or retrapping y-values are evaluated. Default is False.

        Returns
        -------
        I_offsets: numpy.array
            Current offsets of every single trace.
        V_offsets: numpy.array
            Voltage offsets of every single trace.
        """
        if x is None:
            x = [self.V, self.I][self.bias]
        if y is None:
            y = [self.I, self.V][self.bias]
        ''' constant range via threshold (for JJ superconducting range via threshold voltage) '''
        with np.errstate(invalid='ignore'):  # raises warning due to np.nan
            mask = np.logical_and(x >= -threshold + offset, x <= threshold + offset)
        x_const, y_const = np.copy(x), np.copy(y)
        np.place(x_const, np.logical_not(mask), np.nan)
        np.place(y_const, np.logical_not(mask), np.nan)
        if self.sweeptype == 0:  # halfswing
            ''' get x offset (for JJ voltage offset)'''
            x_offsets = np.mean(np.nanmean(x_const, axis=self.scan_dim), axis=0)
            ''' get y offset (for JJ current offset) '''
            if yr:  # retrapping y (for JJ retrapping current)
                y_rs = np.array([np.nanmax(y_const[0], axis=(self.scan_dim-1)),
                                 np.nanmin(y_const[1], axis=(self.scan_dim-1))])
                y_offsets = np.mean(y_rs, axis=0)
            else:  # critical y (for JJ critical current)
                y_cs = np.array([np.nanmin(y_const[0], axis=(self.scan_dim-1)),
                                 np.nanmax(y_const[1], axis=(self.scan_dim-1))])
                y_offsets = np.mean(y_cs, axis=0)
        elif self.sweeptype == 1:  # 4 quadrants
            ''' get x offset '''
            x_offsets = np.mean(np.nanmean(x_const, axis=self.scan_dim), axis=0)
            ''' get y offset '''
            if yr:  # retrapping y (for JJ retrapping current)
                y_rs = np.array([np.nanmax(y_const[1], axis=(self.scan_dim-1)),
                                 np.nanmin(y_const[3], axis=(self.scan_dim-1))])
                y_offsets = np.mean(y_rs, axis=0)
            else:  # critical y (for JJ critical current)
                y_cs = np.array([np.nanmax(y_const[0], axis=(self.scan_dim-1)),
                                 np.nanmin(y_const[2], axis=(self.scan_dim-1))])
                y_offsets = np.mean(y_cs, axis=0)
        else:  # custom sweeptype
            ''' get x offset '''
            x_offsets = np.nanmean(np.nanmean(x_const, axis=self.scan_dim), axis=0)
            ''' get y offset '''
            if yr:  # retrapping y (for JJ retrapping current)
                raise NotImplementedError('No algorithm implemented for custom sweeptype')
            else:
                y_cs = np.array([np.nanmax(y_const, axis=(self.scan_dim-1)),
                                 np.nanmin(y_const, axis=(self.scan_dim-1))])
                y_offsets = np.mean(y_cs, axis=0)
        self.I_offsets, self.V_offsets = [x_offsets, y_offsets][::int(np.sign(self.bias - .5))]
        return self.I_offsets, self.V_offsets

    def get_offset(self, *args, **kwargs):
        """
        Calculates x- and y-offset for the whole data set. Therefore the branch where the y-values are nearly constant are evaluated. The average of all corresponding x-values is considered to be the x-offset and the average of the extreme y-values are considered as y-offset.

        Parameters
        ----------
        x: numpy.array (optional)
            An N-dimensional array containing x-values. Default is None, where x is considered as self.V and self.I in the current and voltage bias, respectively.
        y: numpy.array (optional)
            An N-dimensional array containing y-values. Default is None, where y is considered as self.I and self.V in the current and voltage bias, respectively.
        threshold: float (optional)
            Threshold voltage that limits the superconducting branch. Default is 20e-6.
        offset: float (optional)
            Voltage offset that shifts the limits of the superconducting branch which is set by <threshold>. Default is 0.
        yr: bool (optional)
            Condition, if critical or retrapping y-values are evaluated. Default is False.

        Returns
        -------
        I_offsets: numpy.array
            Current offsets of the whole data set.
        V_offsets: numpy.array
            Voltage offsets of the whole data set.
        """
        self.I_offset, self.V_offset = np.fromiter(map(np.nanmean, self.get_offsets(*args, **kwargs)), dtype=float)
        return self.I_offset, self.V_offset

    def get_2wire_slope_correction(self, I=None, V=None, dVdI=None, peak_finder=sig.find_peaks, **kwargs):
        """
        Gets voltage values corrected by an ohmic slope such as occur in 2wire measurements.
        The two maxima in the differential resistivity <dVdI> are identified as critical and retrapping currents. The slope of the superconducting regime in between (which should ideally be infinity) is fitted using numpy.linalg.qr algorithm and subtracted from the raw data.

        Parameters
        ----------
        I: numpy.array (optional)
            An N-dimensional array containing current values. Default is None that means self.I.
        V: numpy.array (optional)
            An N-dimensional array containing voltage values. Default is None that means self.V.
        dVdI: numpy.array (optional)
            An N-dimensional array containing differential resistance (dV/dI) values. Default is None that means self.dVdI.
        peak_finder: function (optional)
            Peak finding algorithm. Default is scipy.signal.find_peaks.
        kwargs:
            Keyword arguments forwarded to the peak finding algorithm <peak_finder>.

        Returns
        -------
        V_corr: numpy.array
            Ohmic slope corrected voltage values
        """
        def lin_fit(x, y):
            X = np.stack((x, np.ones(len(x)))).T
            q, r = np.linalg.qr(X)
            p = np.dot(q.T, y)
            return np.dot(np.linalg.inv(r), p)
        if I is None:
            I = self.I
        if V is None:
            V = self.V
        if dVdI is None:
            dVdI = self.dVdI
        if peak_finder is sig.find_peaks and 'prominence' not in kwargs.keys():
            kwargs['prominence'] = 100
        if peak_finder is sig.find_peaks_cwt and 'widths' not in kwargs.keys():
            kwargs['widths'] = np.arange(10)
        ''' peak detection in dV/dI '''
        if self.scan_dim == 1:
            peaks = map(lambda dVdI1D:
                        peak_finder(dVdI1D, **kwargs),
                        dVdI)
            slices = map(lambda peaks1D:
                         slice(*np.sort(peaks1D[0][peaks1D[1]['prominences'].argsort()[-2:][::-1]])),
                         peaks)
            popts = map(lambda I1D, V1D, s1D:
                        lin_fit(I1D[s1D], V1D[s1D]),
                        I, V, slices)
            self.V_corr = np.array(list(map(lambda I1D, V1D, popt1D:
                                            V1D - (popt1D[0] * I1D + popt1D[1]),
                                            I, V, popts)),
                                   dtype=float)
            return self.V_corr
        elif self.scan_dim == 2:
            peaks = map(lambda dVdI2D:
                        map(lambda dVdI1D:
                            peak_finder(dVdI1D, **kwargs),
                            dVdI2D),
                        dVdI)
            slices = map(lambda peaks2D:
                         map(lambda peaks1D:
                             slice(*np.sort(peaks1D[0][peaks1D[1]['prominences'].argsort()[-2:][::-1]])),
                             peaks2D),
                         peaks)
            popts = map(lambda I2D, V2D, s2D:
                        map(lambda I1D, V1D, s1D:
                            lin_fit(I1D[s1D], V1D[s1D]),
                            I2D, V2D, s2D),
                        I, V, slices)
            self.V_corr = np.array(list(map(lambda I2D, V2D, popt2D:
                                            map(lambda I1D, V1D, popt1D:
                                                V1D - (popt1D[0] * I1D + popt1D[1]),
                                                I2D, V2D, popt2D),
                                            I, V, popts)),
                                   dtype=float)
            return self.V_corr
        elif self.scan_dim == 3:
            peaks = map(lambda dVdI3D:
                        map(lambda dVdI2D:
                            map(lambda dVdI1D:
                                peak_finder(dVdI1D, **kwargs),
                                dVdI2D),
                            dVdI3D),
                        dVdI)
            slices = map(lambda peaks3D:
                         map(lambda peaks2D:
                             map(lambda peaks1D:
                                 slice(*np.sort(peaks1D[0][peaks1D[1]['prominences'].argsort()[-2:][::-1]])),
                                 peaks2D),
                             peaks3D),
                         peaks)
            popts = map(lambda I3D, V3D, s3D:
                        map(lambda I2D, V2D, s2D:
                            map(lambda I1D, V1D, s1D:
                                lin_fit(I1D[s1D], V1D[s1D]),
                                I2D, V2D, s2D),
                            I3D, V3D, s3D),
                        I, V, slices)
            self.V_corr = np.array(list(map(lambda I3D, V3D, popt3D:
                                            map(lambda I2D, V2D, popt2D:
                                                map(lambda I1D, V1D, popt1D:
                                                    V1D - (popt1D[0] * I1D + popt1D[1]),
                                                    I2D, V2D, popt2D),
                                                I3D, V3D, popt3D),
                                            I, V, popts)),
                                   dtype=float)
            return self.V_corr
        else:
            raise ValueError('Scan dimension must be in {1, 2, 3}')

    def get_Rn(self, I=None, V=None, dVdI=None, mode=sig.savgol_filter, peak_finder=sig.find_peaks, **kwargs):
        """
        Get normal state resistance of over critical range. Therefore the curvature d^2V/dI^2 is computed using the second order derivation function <mode> and analysing peaks in it with <peak_finder>.
        The ohmic range is considered to range from the outermost tail of the peaks in the curvature to the start/end of the sweep and the resistance is calculated as mean of the differential resistance values <dVdI> within this range.

        Parameters
        ----------
        I: numpy.array (optional)
            An N-dimensional array containing current values. Default is None that means self.I.
        V: numpy.array (optional)
            An N-dimensional array containing voltage values. Default is None that means self.V.
        dVdI: numpy.array (optional)
            An N-dimensional array containing differential resistance (dV/dI) values. Default is None that means self.dVdI.
        mode: function (optional)
            Function that calculates the numerical gradient dx from a given array x. Default is scipy.signal.savgol_filter (Savitzky Golay filter).
        peak_finder: function (optional)
            Peak finding algorithm. Default is scipy.signal.find_peaks.
        kwargs:
            Keyword arguments forwarded to the function <mode> and the peak finding algorithm <peak_finder>. Default for scipy.signal.savgol_filter are {'window_length': 15, 'polyorder': 3, 'deriv': 2}, for numpy.diff {'n': 2, 'axis': self.scan_dim} and for scipy.signal.find_peaks {'prominence': np.max(np.abs(d2VdI2))/1e2)}

        Returns
        -------
        Rn: numpy.array
            Average normal state resistance
        """
        def _peak_finder(x, **_kwargs):
            ans = peak_finder(x, **_kwargs)
            if np.array_equal(ans[0], []):  # no peaks found
                return [np.array([False]), {}]
            else:
                return ans
        if I is None:
            I = self.I
        if V is None:
            V = self.V
        if dVdI is None:
            dVdI = self.dVdI
        if mode == sig.savgol_filter:
            kwargs_deriv = {'deriv': 2, 'window_length': kwargs.get('window_length', 15), 'polyorder': kwargs.get('polyorder', 3)}
        elif mode == np.diff:
            kwargs_deriv = {'n': 2, 'axis': kwargs.get('axis', self.scan_dim)}
        else:
            kwargs_deriv = {}
        ''' second derivative d^2V/dI^2 '''
        self.d2VdI2 = self.get_dydx(x=I, y=V, mode=mode, **kwargs_deriv)
        ''' peak detection in d^2V/dI^2 '''
        if len(V.shape)-1 == 1:
            if peak_finder == sig.find_peaks:
                kwargs_peak_finder = list(map(lambda d2VdI21D:
                                              {'prominence': kwargs.get('prominence', np.max(np.abs(d2VdI21D))/1e2)},
                                              self.d2VdI2))
            peaks = list(map(lambda j, d2VdI21D:
                             _peak_finder(d2VdI21D*np.sign(max(d2VdI21D.min(), d2VdI21D.max(), key=abs)),
                                          **kwargs_peak_finder[j]),  # sign, so that extremum is positiv
                             *zip(*enumerate(self.d2VdI2))))
            slcs = np.array(list(map(lambda peak1D, d2VdI21D:
                                     np.array((slice(0, np.min(peak1D[1]['left_bases'])),
                                               slice(max(peak1D[1]['right_bases']), d2VdI21D.size))),
                                     peaks, self.d2VdI2)))
            Rn = np.array([np.nanmean(np.concatenate([self.dVdI[k][s]
                                                      for k, s in enumerate(slc)]))
                           for j, slc in enumerate(np.transpose(slcs, axes=(1, 0)))])
            """
            popts, pcovs = np.ones(shape=(len(self.d2VdI2), 2)), np.ones(shape=(len(self.d2VdI2), 2, 2))
            for j in range(2):
                V_ohm = np.concatenate([V[k][slc] for k, slc in enumerate(slcs.T[j])])
                I_ohm = np.concatenate([I[k][slc] for k, slc in enumerate(slcs.T[j])])
                popts[j], pcovs[j] = np.polyfit(x=V_ohm,
                                                y=I_ohm,
                                                deg=1,
                                                cov=True
                                                )
            Rn = 1/np.mean(popts[:,0])
            """
        elif len(V.shape)-1 == 2:
            if peak_finder == sig.find_peaks:
                kwargs_peak_finder = list(map(lambda d2VdI22D:
                                              list(map(lambda d2VdI21D:
                                                       {'prominence': kwargs.get('prominence', np.max(np.abs(d2VdI21D))/1e2)},
                                                       d2VdI22D)),
                                              self.d2VdI2))
            peaks = list(map(lambda j, d2VdI22D:
                             list(map(lambda k, d2VdI21D:
                                      _peak_finder(d2VdI21D * np.sign(max(d2VdI21D.min(), d2VdI21D.max(), key=abs)),
                                                   **kwargs_peak_finder[j][k]),  # sign, so that extremum is positiv
                                      *zip(*enumerate(d2VdI22D)))),
                             *zip(*enumerate(self.d2VdI2))))
            slcs = np.array(list(map(lambda peak2D, d2VdI22D:
                                     list(map(lambda peak1D, d2VdI21D:
                                              np.array((slice(0, np.min(peak1D[1]['left_bases'])),
                                                        slice(max(peak1D[1]['right_bases']), d2VdI21D.size))),
                                              peak2D, d2VdI22D)),
                                     peaks, self.d2VdI2)))
            Rn = np.array([[np.nanmean(np.concatenate([self.dVdI[k][x][s]
                                                       for k, s in enumerate(slc)]))
                            for j, slc in enumerate(slcs1D)]
                           for x, slcs1D in enumerate(np.transpose(slcs, axes=(1, 2, 0)))])
        elif len(V.shape)-1 == 3:
            if peak_finder == sig.find_peaks:
                kwargs_peak_finder = list(map(lambda d2VdI23D:
                                              list(map(lambda d2VdI22D:
                                                       list(map(lambda d2VdI21D:
                                                                {'prominence': kwargs.get('prominence', np.max(np.abs(d2VdI21D))/1e2)},
                                                                d2VdI22D)),
                                                       d2VdI23D)),
                                              self.d2VdI2))
            peaks = list(map(lambda i, d2VdI23D:
                             list(map(lambda j, d2VdI22D:
                                      list(map(lambda k, d2VdI21D:
                                               _peak_finder(d2VdI21D * np.sign(max(d2VdI21D.min(), d2VdI21D.max(), key=abs)),
                                                            **kwargs_peak_finder[i][j][k]),  # sign, so that extremum is positiv
                                               *zip(*enumerate(d2VdI22D)))),
                                      *zip(*enumerate(d2VdI23D)))),
                             *zip(*enumerate(self.d2VdI2))))
            slcs = np.array(list(map(lambda peak3D, d2VdI23D:
                                     list(map(lambda peak2D, d2VdI22D:
                                              list(map(lambda peak1D, d2VdI21D:
                                                       np.array((slice(0, np.min(peak1D[1]['left_bases'])),
                                                                 slice(max(peak1D[1]['right_bases']), d2VdI21D.size)
                                                                 )),
                                                       peak2D, d2VdI22D)),
                                              peak3D, d2VdI23D)),
                                     peaks, self.d2VdI2)))
            Rn = np.array([[[np.nanmean(np.concatenate([self.dVdI[k][x][y][s]
                                                        for k, s in enumerate(slc)]))
                             for j, slc in enumerate(slcs1D)]
                            for y, slcs1D in enumerate(slcs2D)]
                           for x, slcs2D in enumerate(np.transpose(slcs, axes=(1, 2, 3, 0)))])
        else:
            raise ValueError('Scan dimension must be in {1, 2, 3}')
        return np.nanmean(Rn, axis=self.scan_dim-1)

    def get_Ic_threshold(self, I=None, V=None, dVdI=None, threshold=20e-6, offset=None, Ir=False):
        """
        Get critical current values. These are considered as currents, where the voltage jumps beyond threshold ± <threshold> - <offset>.

        Parameters
        ----------
        I: numpy.array (optional)
            An N-dimensional array containing current values. Default is None that means self.I.
        V: numpy.array (optional)
            An N-dimensional array containing voltage values. Default is None that means self.V.
        dVdI: numpy.array (optional)
            An N-dimensional array containing differential resistance (dV/dI) values. Default is None that means self.dVdI.
        threshold: float (optional)
            Threshold voltage that limits the superconducting branch. Default is 20e-6.
        offset: float (optional)
            Voltage offset that shifts the limits of the superconducting branch which is set by <threshold>. Default is None that means self.V_offset.
        Ir: bool (optional)
            Condition, if retrapping currents are returned, too. Default is False.

        Returns
        -------
        I_cs: numpy.array
            Critical current values.
        I_rs: numpy.array (optional)
            Retrapping current values.
        """
        if V is None:
            V = self.V
        if I is None:
            I = self.I
        if offset is None:
            if self.V_offset is None:
                offset = 0
            else:
                offset = self.V_offset
        if len(V.shape)-1 == 0:  # single trace used for in situ fit
            with np.errstate(invalid='ignore'):  # raises warning due to np.nan
                mask = np.logical_and(V >= -threshold + offset, V <= threshold + offset)
            I_sc = np.copy(I)
            np.place(I_sc, np.logical_not(mask), np.nan)
            return np.nanmax(I_sc)
        ''' constant range via threshold (for JJ superconducting range via threshold voltage) '''
        with np.errstate(invalid='ignore'):  # raises warning due to np.nan
            mask = np.logical_and(V >= -threshold + offset, V <= threshold + offset)
        V_sc, I_sc = np.copy(V), np.copy(I)
        np.place(V_sc, np.logical_not(mask), np.nan)
        np.place(I_sc, np.logical_not(mask), np.nan)
        if self.sweeptype == 0:  # halfswing
            ''' critical current '''
            I_cs = np.array([np.nanmin(I_sc[0], axis=(self.scan_dim-1)), np.nanmax(I_sc[1], axis=(self.scan_dim-1))])
            ''' retrapping current '''
            I_rs = np.array([np.nanmax(I_sc[0], axis=(self.scan_dim-1)), np.nanmin(I_sc[1], axis=(self.scan_dim-1))])
        elif self.sweeptype == 1:  # 4 quadrants
            ''' critical current '''
            I_cs = np.array([np.nanmax(I_sc[0], axis=(self.scan_dim-1)), np.nanmin(I_sc[2], axis=(self.scan_dim-1))])
            ''' retrapping current '''
            I_rs = np.array([np.nanmax(I_sc[1], axis=(self.scan_dim-1)), np.nanmin(I_sc[3], axis=(self.scan_dim-1))])
        else:  # custom sweeptype
            ''' critical current '''
            I_cs = np.array([np.nanmax(I_sc, axis=(self.scan_dim-1)),
                             np.nanmin(I_sc, axis=(self.scan_dim-1))])
            ''' retrapping current '''
            if Ir:
                raise NotImplementedError('No algorithm implemented for custom sweeptype')
        if Ir:
            return [I_cs, I_rs]
        else:
            return I_cs

    def get_Ic_deriv(self, I=None, V=None, dVdI=None, Ir=False, tol_offset=20e-6, window=5, peak_finder=sig.find_peaks, **kwargs):
        """
        Gets critical current values using the numerical derivative dV/dI.
        Peaks in these data correspond to voltage jumps, are detected with a peak finding algorithm <peak_finder> and checked, whether the corresponding voltage jumps out or in the superconducting branch, that is identified as critical or retrapping current, respectively. Therefore the average of half the window below and above the peak is considered. The superconducting branch, in turn, is assumed as the voltage offset <self.V_offset> within the tolerance <tol_offset>.

        Parameters
        ----------
        I: numpy.array (optional)
            An N-dimensional array containing current values. Default is None that means self.I.
        V: numpy.array (optional)
            An N-dimensional array containing voltage values. Default is None that means self.V.
        dVdI: numpy.array (optional)
            An N-dimensional array containing differential resistance (dV/dI) values. Default is None that means self.dVdI.
        Ir: bool (optional)
            Condition, if retrapping currents are returned, too. Default is False
        tol_offset: float (optional)
            Voltage offset tolerance that limits the superconducting branch around the voltage offset <self.V_offset>. Default is 20e-6.
        window: int (optional)
            Window around the jump, where the voltage is evaluated and classified as 'superconducting branch'. Default is 5 that considers two values below and 2 values above the jump.
        peak_finder: function (optional)
            Peak finding algorithm. Default is scipy.signal.find_peaks.
        kwargs:
            Keyword arguments forwarded to the peak finding algorithm <peak_finder>.

        Returns
        -------
        I_cs: numpy.array
            Critical current values.
        I_rs: numpy.array (optional)
            Retrapping current values.
        properties: dict
            Properties of all found peaks (not only I_c and I_r, but also further jumps), such as corresponding currents, voltages, differential resistances, indices as well as returns of the used peak finding algorithm.

        Examples
        --------
        >>> I_cs, props = ivc.get_Ic_deriv(prominence=100)
        >>> if ivc.scan_dim == 1:
        >>>     Is = np.array(list(map(lambda p1D: p1D['I'], props)))  # has shape (number of sweeps, number of peaks)
        >>> elif ivc.scan_dim == 2:
        >>>     Is = np.array(list(map(lambda p2D: list(map(lambda p1D: p1D['I'], p2D)), props)))  # has shape (number of sweeps, number of x-values, number of peaks)
        >>> elif ivc.scan_dim == 3:
        >>>     Is = np.array(list(map(lambda p3D: list(map(lambda p2D: list(map(lambda p1D: p1D['I'], p2D)), p3D)), props)))  # has shape (number of sweeps, number of y-values, number of x-values, number of peaks)
        """
        def _peak_finder(x, **_kwargs):
            ans = peak_finder(x, **_kwargs)
            if np.array_equal(ans[0], []):  # no peaks found
                return [np.array([False]), {}]
            else:
                return ans
        if I is None:
            I = self.I
        if V is None:
            V = self.V
        if dVdI is None:
            dVdI = self.dVdI
        if peak_finder is sig.find_peaks and 'prominence' not in kwargs.keys():
            kwargs['prominence'] = 100
        if peak_finder is sig.find_peaks_cwt and 'widths' not in kwargs.keys():
            kwargs['widths'] = np.arange(10)
        if len(V.shape)-1 == 0:  # single trace used for in situ fit
            peaks = _peak_finder(dVdI, **kwargs)
            try:
                return I[peaks[0]]
            except IndexError:  # if no peak found return np.nan
                return np.nan
        ''' peak detection in dV/dI '''
        if len(V.shape)-1 == 1:
            peaks = np.array(list(map(lambda dVdI1D:
                                      _peak_finder(dVdI1D, **kwargs),
                                      dVdI)))
        elif len(V.shape)-1 == 2:
            peaks = np.array(list(map(lambda dVdI2D:
                                      list(map(lambda dVdI1D:
                                               _peak_finder(dVdI1D, **kwargs),
                                               dVdI2D)),
                                      dVdI)))
        elif len(V.shape)-1 == 3:
            peaks = np.array(list(map(lambda dVdI3D:
                                      list(map(lambda dVdI2D:
                                               list(map(lambda dVdI1D:
                                                        _peak_finder(dVdI1D, **kwargs),
                                                        dVdI2D)),
                                               dVdI3D)),
                                      dVdI)))
        else:
            raise ValueError('Scan dimension must be in {1, 2, 3}')
        return self._classify_jump(I=I, V=V, Y=dVdI, peaks=peaks, tol_offset=tol_offset, window=window, Ir=Ir)

    def get_Ic_dft(self, I=None, V=None, dVdI=None, s=10, Ir=False, tol_offset=20e-6, window=5, peak_finder=sig.find_peaks, **kwargs):
        """
        Gets critical current values using a discrete Fourier transform, a smoothed derivation in the frequency domain and an inverse Fourier transform.
        Therefore the voltage values are corrected by the linear offset slope, fast Fourier transformed to the frequency domain, multiplied with a Gaussian smoothed derivation function if*exp(-s*f^2) in the frequency domain and inversely fast Fourier transformed to the time domain. This corresponds to the convolution of the voltage values with the Gaussian smoothed derivation function in the time domain.
        Peaks in these data correspond to voltage jumps, are detected with a peak finding algorithm <peak_finder> and checked, whether the corresponding voltage jumps out or in the superconducting branch, that is identified as critical or retrapping current, respectively. Therefore the average of half the window below and above the peak is considered. The superconducting branch, in turn, is assumed as the voltage offset <self.V_offset> within the tolerance <tol_offset>.

        Parameters
        ----------
        I: numpy.array (optional)
            An N-dimensional array containing current values. Default is None that means self.I.
        V: numpy.array (optional)
            An N-dimensional array containing voltage values. Default is None that means self.V.
        dVdI: numpy.array (optional)
            An N-dimensional array containing differential resistance (dV/dI) values. Default is None that means self.dVdI.
        s: float (optional)
            Smoothing factor of the derivative. Default is 10.
        Ir: bool (optional)
            Condition, if retrapping currents are returned, too. Default is False.
        tol_offset: float (optional)
            Voltage offset tolerance that limits the superconducting branch around the voltage offset <self.V_offset>. Default is 20e-6.
        window: int (optional)
            Window around the jump, where the voltage is evaluated and classified as 'superconducting branch'. Default is 5 that considers two values below and 2 values above the jump.
        peak_finder: function (optional)
            Peak finding algorithm. Default is scipy.signal.find_peaks
        kwargs:
            Keyword arguments forwarded to the peak finding algorithm <peak_finder>.

        Returns
        -------
        I_cs: numpy.array
            Critical current values.
        I_rs: numpy.array (optional)
            Retrapping current values.
        properties: dict
            Properties of all found peaks (not only I_c and I_r, but also further jumps), such as corresponding currents, voltages, differential resistances, indices as well as returns of the used peak finding algorithm.

        Examples
        --------
        >>> I_cs, props = ivc.get_Ic_dft(prominence=1)
        >>> if ivc.scan_dim == 1:
        >>>     Is = np.array(list(map(lambda p1D: p1D['I'], props)))  # has shape (number of sweeps, number of peaks)
        >>> elif ivc.scan_dim == 2:
        >>>     Is = np.array(list(map(lambda p2D: list(map(lambda p1D: p1D['I'], p2D)), props)))  # has shape (number of sweeps, number of x-values, number of peaks)
        >>> elif ivc.scan_dim == 3:
        >>>     Is = np.array(list(map(lambda p3D: list(map(lambda p2D: list(map(lambda p1D: p1D['I'], p2D)), p3D)), props)))  # has shape (number of sweeps, number of y-values, number of x-values, number of peaks)
        """
        def _get_deriv_dft(V_corr):
            V_fft = np.fft.fft(V_corr)  # Fourier transform of V from time to frequency domain
            f = np.fft.fftfreq(V.shape[-1])  # frequency values
            kernel = 1j * np.fft.fft(f * np.exp(-s * f ** 2))  # smoothed derivation function, how it would look like in time domain (with which V is convolved in the time domain)
            V_fft_smooth = 1j * f * np.exp(-s * f ** 2) * V_fft  # Fourier transform of a Gaussian smoothed derivation of V in the frequency domain
            dV_smooth = np.fft.ifft(V_fft_smooth)  # inverse Fourier transform of the smoothed derivation of V from reciprocal to time domain
            return dV_smooth

        def _peak_finder(x, **_kwargs):
            ans = peak_finder(x, **_kwargs)
            if np.array_equal(ans[0], []):  # no peaks found
                return [np.array([False]), {}]
            else:
                return ans

        if I is None:
            I = self.I
        if V is None:
            V = self.V
        if peak_finder is sig.find_peaks and 'prominence' not in kwargs.keys():
            kwargs['prominence'] = 1e-5
        if peak_finder is sig.find_peaks_cwt and 'widths' not in kwargs.keys():
            kwargs['widths'] = np.arange(10)
        if len(V.shape)-1 == 0:  # single trace used for in situ fit
            V_corr = V - np.linspace(start=V[0], stop=V[-1], num=V.shape[-1], axis=0)  # adjust offset slope
            dV_smooth = _get_deriv_dft(V_corr)
            peaks = _peak_finder(dV_smooth, **kwargs)
            print(len(peaks), peaks)
            try:
                return I[peaks[0]]
            except IndexError:  # if no peak found return np.nan
                return np.nan
        ''' differentiate and smooth in the frequency domain '''
        if self.scan_dim == 1:
            V_corr = V - np.linspace(start=V[:, 0], stop=V[:, -1], num=V.shape[-1], axis=1)  # adjust offset slope
        elif self.scan_dim == 2:
            V_corr = V - np.linspace(start=V[:, :, 0], stop=V[:, :, -1], num=V.shape[-1], axis=2)  # adjust offset slope
        elif self.scan_dim == 3:
            V_corr = V - np.linspace(start=V[:, :, :, 0], stop=V[:, :, :, -1], num=V.shape[-1], axis=3)  # adjust offset slope
        else:
            raise ValueError('Scan dimension must be in {1, 2, 3}')
        dV_smooth = _get_deriv_dft(V_corr=V_corr)
        ''' peak detection '''
        if self.scan_dim == 1:
            peaks = np.array(list(map(lambda dV_smooth1D:
                                      _peak_finder(np.abs(dV_smooth1D), **kwargs),
                                      dV_smooth)))
        elif self.scan_dim == 2:
            peaks = np.array(list(map(lambda dV_smooth2D:
                                      list(map(lambda dV_smooth1D:
                                               _peak_finder(np.abs(dV_smooth1D), **kwargs),
                                               dV_smooth2D)),
                                      dV_smooth)))
        elif self.scan_dim == 3:
            peaks = np.array(list(map(lambda dV_smooth3D:
                                      list(map(lambda dV_smooth2D:
                                               list(map(lambda dV_smooth1D:
                                                        _peak_finder(np.abs(dV_smooth1D), **kwargs),
                                                        dV_smooth2D)),
                                               dV_smooth3D)),
                                      dV_smooth)))
        else:
            raise ValueError('Scan dimension must be in {1, 2, 3}')
        return self._classify_jump(I=I, V=V, Y=dV_smooth, peaks=peaks, tol_offset=tol_offset, window=window, Ir=Ir)

    def _classify_jump(self, I, V, Y, peaks, tol_offset=20e-6, window=5, Ir=False):
        """
        Classifies voltage jumps as critical currents, retrapping currents of none of those.

        Parameters
        ----------
        I: numpy.array
            An N-dimensional array containing current values.
        V: numpy.array
            An N-dimensional array containing voltage values.
        Y: numpy.array
            An N-dimensional array containing data, whose peaks are already determined.
        peaks numpy.array
            An N-dimensional array containing indices and properties of peaks that are already determined, as obtained by e.g. scipy.signal.find_peaks()
        Ir: bool (optional)
            Condition, if retrapping currents are returned, too. Default is False
        tol_offset: float (optional)
            Voltage offset tolerance that limits the superconducting branch around the voltage offset <self.V_offset>. Default is 20e-6.
        window: int (optional)
            Window around the jump, where the voltage is evaluated and classified as 'superconducting branch'. Default is 5 that considers two values below and 2 values above the jump.

        Returns
        -------
        I_cs: numpy.array
            Critical current values.
        I_rs: numpy.array (optional)
            Retrapping current values.
        properties: dict
            Properties of all found peaks (not only I_c and I_r, but also further jumps), such as corresponding currents, voltages, differential resistances, indices as well as returns of the used peak finding algorithm.
        """
        Y_name = [key for key, val in sys._getframe().f_back.f_locals.items() if np.array_equal(val, Y)][0]
        if self.V_offset is None and self.sweeptype in [0, 1]:  # voltage offset to identify superconducting branch
            self.get_offset(x=V, y=I)
        if self.sweeptype == 0:  # halfswing
            V_c, I_c, peaks_c = np.copy(V), np.copy(I), np.copy(peaks)
            V_r, I_r, peaks_r = np.copy(V), np.copy(I), np.copy(peaks)
        elif self.sweeptype == 1:  # 4quadrants
            V_c, I_c, peaks_c = np.copy(V[::2]), np.copy(I[::2]), np.copy(peaks[::2])
            V_r, I_r, peaks_r = np.copy(V[1::2]), np.copy(I[1::2]), np.copy(peaks[1::2])
        else:  # custom sweeptype
            def f(ind1D, prop1D, I1D, V1D, Y1D):
                try:
                    return {**prop1D,
                            **{k: v for k, v in zip(('I', 'V', Y_name, 'index'),
                                                    (I1D[ind1D], V1D[ind1D], Y1D[ind1D], ind1D))}}
                except IndexError:  # if no peak found return np.nan
                    return {k: v for k, v in zip(('I', 'V', Y_name, 'index'),
                                                 (np.array([np.nan]), np.array([np.nan]), np.array([np.nan]), np.array([np.nan])))}
            if self.scan_dim == 1:
                return np.array(list(map(lambda ind1D, prop1D, I1D, V1D, Y1D:
                                         f(ind1D, prop1D, I1D, V1D, Y1D),
                                         *list(zip(*peaks)), I, V, Y)))
            elif self.scan_dim == 2:
                return np.array(list(map(lambda peaks2D, I2D, V2D, Y2D:
                                         list(map(lambda ind1D, prop1D, I1D, V1D, Y1D:
                                                  f(ind1D, prop1D, I1D, V1D, Y1D),
                                                  *list(zip(*peaks2D)), I2D, V2D, Y2D)),
                                         peaks, I, V, Y)))
            elif self.scan_dim == 3:
                return np.array(list(map(lambda peaks3D, I3D, V3D, Y3D:
                                         list(map(lambda peaks2D, I2D, V2D, Y2D:
                                                  list(map(lambda ind1D, prop1D, I1D, V1D, Y1D:
                                                           f(ind1D, prop1D, I1D, V1D, Y1D),
                                                           *list(zip(*peaks2D)), I2D, V2D, Y2D)),
                                                  peaks3D, I3D, V3D, Y3D)),
                                         peaks, I, V, Y)))
            else:
                raise NotImplementedError('No algorithm implemented for custom sweeptype and scan_dim > 3.')
        if self.scan_dim == 1:
            ''' critical current '''
            masks_c = map(lambda V_c1D, peak1D:
                          np.logical_and(np.logical_and((-tol_offset+self.V_offset) <= np.mean(V_c1D[peak1D[0]-np.tile([np.arange(int(window)//2)+1], [len(peak1D[0]), 1]).T], axis=0),
                                                        np.mean(V_c1D[peak1D[0]-np.tile([np.arange(int(window)//2)+1], [len(peak1D[0]), 1]).T], axis=0) <= (+tol_offset+self.V_offset)),
                                         np.logical_not(np.logical_and((-tol_offset+self.V_offset) <= np.mean(V_c1D[peak1D[0]+np.tile([np.arange(int(window)//2)+1], [len(peak1D[0]), 1]).T], axis=0),
                                                                       np.mean(V_c1D[peak1D[0]+np.tile([np.arange(int(window)//2)+1], [len(peak1D[0]), 1]).T], axis=0) <= (+tol_offset+self.V_offset)))),
                          V_c, peaks_c)
            I_cs = np.array(list(map(lambda I_c1D, peak1D, masks_c1D:
                                     I_c1D[peak1D[0][masks_c1D][0]],
                                     I_c, peaks_c, masks_c)),
                            dtype=float)
            ''' retrapping current '''
            masks_r = map(lambda V_r1D, peak1D:
                          np.logical_and(np.logical_not(np.logical_and((-tol_offset+self.V_offset) <= np.mean(V_r1D[peak1D[0]-np.tile([np.arange(int(window)//2)+1], [len(peak1D[0]), 1]).T], axis=0),
                                                                       np.mean(V_r1D[peak1D[0]-np.tile([np.arange(int(window)//2)+1], [len(peak1D[0]), 1]).T], axis=0) <= (+tol_offset+self.V_offset))),
                                         np.logical_and((-tol_offset+self.V_offset) <= np.mean(V_r1D[peak1D[0]+np.tile([np.arange(int(window)//2)+1], [len(peak1D[0]), 1]).T], axis=0),
                                                        np.mean(V_r1D[peak1D[0]+np.tile([np.arange(int(window)//2)+1], [len(peak1D[0]), 1]).T], axis=0) <= (+tol_offset+self.V_offset))),
                          V_r, peaks_r)
            I_rs = np.array(list(map(lambda I_r1D, peak1D, masks_r1D:
                                     I_r1D[peak1D[0][masks_r1D][0]+1],
                                     I_r, peaks_r, masks_r)),
                            dtype=float)
            ''' properties '''
            properties = np.array(list(map(lambda ind1D, prop1D, I1D, V1D, Y1D:
                                           {**prop1D,
                                            **{k: v for k, v in zip(('I', 'V', Y_name, 'index'),
                                                                    (I1D[ind1D], V1D[ind1D], Y1D[ind1D], ind1D))}},
                                           *list(zip(*peaks)), I, V, Y)))
        elif self.scan_dim == 2:
            ''' critical current '''
            masks_c = map(lambda V_c2D, peaks_c2D:
                          map(lambda V_c1D, peak1D: np.logical_and(np.logical_and((-tol_offset+self.V_offset) <= np.mean(V_c1D[peak1D[0]-np.tile([np.arange(int(window)//2)+1], [len(peak1D[0]), 1]).T], axis=0),
                                                                                  np.mean(V_c1D[peak1D[0]-np.tile([np.arange(int(window)//2)+1], [len(peak1D[0]), 1]).T], axis=0) <= (+tol_offset+self.V_offset)),
                                                                   np.logical_not(np.logical_and((-tol_offset+self.V_offset) <= np.mean(V_c1D[peak1D[0]+np.tile([np.arange(int(window)//2)+1], [len(peak1D[0]), 1]).T], axis=0),
                                                                                                 np.mean(V_c1D[peak1D[0]+np.tile([np.arange(int(window)//2)+1], [len(peak1D[0]), 1]).T], axis=0) <= (+tol_offset+self.V_offset)))),
                              V_c2D, peaks_c2D),
                          V_c, peaks_c)
            I_cs = np.array(list(map(lambda I_c2D, peaks_c2D, masks_c2D:
                                     list(map(lambda I_c1D, peak1D, masks_c1D:
                                              I_c1D[peak1D[0][masks_c1D][0]],
                                              I_c2D, peaks_c2D, masks_c2D)),
                                     I_c, peaks_c, masks_c)),
                            dtype=float)
            ''' retrapping current '''
            masks_r = map(lambda V_r2D, peaks_r2D:
                          map(lambda V_r1D, peak1D: np.logical_and(np.logical_not(np.logical_and((-tol_offset+self.V_offset) <= np.mean(V_r1D[peak1D[0]-np.tile([np.arange(int(window)//2)+1], [len(peak1D[0]), 1]).T], axis=0),
                                                                                                 np.mean(V_r1D[peak1D[0]-np.tile([np.arange(int(window)//2)+1], [len(peak1D[0]), 1]).T], axis=0) <= (+tol_offset + self.V_offset))),
                                                                   np.logical_and((-tol_offset+self.V_offset) <= np.mean(V_r1D[peak1D[0]+np.tile([np.arange(int(window)//2)+1], [len(peak1D[0]), 1]).T], axis=0),
                                                                                  np.mean(V_r1D[peak1D[0]+np.tile([np.arange(int(window)//2)+1], [len(peak1D[0]), 1]).T], axis=0) <= (+tol_offset+self.V_offset))),
                              V_r2D, peaks_r2D),
                          V_r, peaks_r)
            I_rs = np.array(list(map(lambda I_r2D, peaks_r2D, masks_r2D:
                                     list(map(lambda I_r1D, peaks_r1D, masks_r1D:
                                              I_r1D[peaks_r1D[0][masks_r1D][0]+1],
                                              I_r2D, peaks_r2D, masks_r2D)),
                                     I_r, peaks_r, masks_r)),
                            dtype=float)
            ''' properties '''
            properties = np.array(list(map(lambda peaks2D, I2D, V2D, Y2D:
                                           list(map(lambda ind1D, prop1D, I1D, V1D, Y1D:
                                                    {**prop1D,
                                                     **{k: v for k, v in zip(('I', 'V', Y_name, 'index'),
                                                                             (I1D[ind1D], V1D[ind1D], Y1D[ind1D], ind1D))}},
                                                    *list(zip(*peaks2D)), I2D, V2D, Y2D)),
                                           peaks, I, V, Y)))
        elif self.scan_dim == 3:
            ''' critical current '''
            masks_c = map(lambda V_c3D, peaks_c3D:
                          map(lambda V_c2D, peaks_c2D:
                              map(lambda V_c1D, peak1D: np.logical_and(np.logical_and((-tol_offset+self.V_offset) <= np.mean(V_c1D[peak1D[0]-np.tile([np.arange(int(window)//2)+1], [len(peak1D[0]), 1]).T], axis=0),
                                                                                      np.mean(V_c1D[peak1D[0]-np.tile([np.arange(int(window)//2)+1], [len(peak1D[0]), 1]).T], axis=0) <= (+tol_offset+self.V_offset)),
                                                                       np.logical_not(np.logical_and((-tol_offset+self.V_offset) <= np.mean(V_c1D[peak1D[0]+np.tile([np.arange(int(window)//2)+1], [len(peak1D[0]), 1]).T], axis=0),
                                                                                                     np.mean(V_c1D[peak1D[0]+np.tile([np.arange(int(window)//2)+1], [len(peak1D[0]), 1]).T], axis=0) <= (+tol_offset+self.V_offset)))),
                                  V_c2D, peaks_c2D),
                              V_c3D, peaks_c3D),
                          V_c, peaks_c)
            I_cs = np.array(list(map(lambda I_c3D, peaks_c3D, masks_c3D:
                                     list(map(lambda I_c2D, peaks_c2D, masks_c2D:
                                              list(map(lambda I_c1D, peak1D, masks_c1D:
                                                       I_c1D[peak1D[0][masks_c1D][0]],
                                                       I_c2D, peaks_c2D, masks_c2D)),
                                              I_c3D, peaks_c3D, masks_c3D)),
                                     I_c, peaks_c, masks_c)),
                            dtype=float)
            ''' retrapping current '''
            masks_r = map(lambda V_r3D, peaks_r3D:
                          map(lambda V_r2D, peaks_r2D:
                              map(lambda V_r1D, peak1D: np.logical_and(np.logical_not(np.logical_and((-tol_offset+self.V_offset) <= np.mean(V_r1D[peak1D[0]-np.tile([np.arange(int(window)//2)+1], [len(peak1D[0]), 1]).T], axis=0),
                                                                                                     np.mean(V_r1D[peak1D[0]-np.tile([np.arange(int(window)//2)+1], [len(peak1D[0]), 1]).T], axis=0) <= (+tol_offset + self.V_offset))),
                                                                       np.logical_and((-tol_offset+self.V_offset) <= np.mean(V_r1D[peak1D[0]+np.tile([np.arange(int(window)//2)+1], [len(peak1D[0]), 1]).T], axis=0),
                                                                                      np.mean(V_r1D[peak1D[0]+np.tile([np.arange(int(window)//2)+1], [len(peak1D[0]), 1]).T], axis=0) <= (+tol_offset+self.V_offset))),
                                  V_r2D, peaks_r2D),
                              V_r3D, peaks_r3D),
                          V_r, peaks_r)
            I_rs = np.array(list(map(lambda I_r3D, peaks_r3D, masks_r3D:
                                     list(map(lambda I_r2D, peaks_r2D, masks_r2D:
                                              list(map(lambda I_r1D, peak1D, masks_r1D:
                                                       I_r1D[peak1D[0][masks_r1D][0]],
                                                       I_r2D, peaks_r2D, masks_r2D)),
                                              I_r3D, peaks_r3D, masks_r3D)),
                                     I_r, peaks_r, masks_r)),
                            dtype=float)
            properties = np.array(list(map(lambda peaks3D, I3D, V3D, Y3D:
                                           list(map(lambda peaks2D, I2D, V2D, Y2D:
                                                    list(map(lambda ind1D, prop1D, I1D, V1D, Y1D:
                                                             {**prop1D,
                                                              **{k: v for k, v in zip(('I', 'V', Y_name, 'index'),
                                                                                      (I1D[ind1D], V1D[ind1D], Y1D[ind1D], ind1D))}},
                                                             *list(zip(*peaks2D)), I2D, V2D, Y2D)),
                                                    peaks3D, I3D, V3D, Y3D)),
                                           peaks, I, V, Y)))
        else:
            raise ValueError('Scan dimension must be in {1, 2, 3}')
        if Ir:
            return I_cs, I_rs, properties
        else:
            return I_cs, properties

    class switching_current(object):
        """ This is an analysis class for switching current measurements """
        def __init__(self, sweeps, settings):
            self.sweeps = sweeps
            self.settings = settings
            self.P, self.P_fit, self.edges, self.bins = None, None, None, None
            self.Delta_I, self.Delta_I_fit, self.dIdt = None, None, None
            self.Gamma, self.Gamma_fit, self.x, self.x_fit, self.y, self.y_fit = None, None, None, None, None, None
            self.popt, self.pcov, self.I_c = None, None, None
            self.fig, self.ax1, self.ax2, self.ax3 = None, None, None, None

        def fit(self, I_0, omega_0, dIdt=None, **kwargs):
            """
            Creates switching current histogram, calculates and escape rate and recalculates the fit to the switching current distribution.

            Parameters
            ----------
            I_0: array-like
                Switching currents.
            omega_0: float
                Plasma frequency used for fit.
            dIdt: float (optional)
                Sweep rate (in A/s). Default is sweeps stepwidth*nplc/plc.
            kwargs:
                Keyword arguments forwarded to numpy.histogram. Defaults are bins=10, range=(min(I_0), max(I_0)), normed=None, weights=None, density=None.

            Returns
            -------
            P: np.array
                Probability distribution
            P_fit: np.array
                Fitted probability distribution
            Gamma: np.array
                Escape rate
            Gamma_fit: np.array
                Fitted escape rate
            popt: list
                Optimal fit parameters
            pcov: list
                Covariance matrix
            I_c: float
                Fitted critical current

            Examples
            --------
            >>> ivc.scm.fit(I_0=I_0*1e6, omega_0=14e9, bins=50);
            """
            def get_P(Gamma, Delta_I, dIdt, norm):
                P = np.array([gamma/dIdt*np.exp(-np.sum(Gamma[:k+1])*Delta_I/dIdt) for k, gamma in enumerate(Gamma)])
                return P/np.sum(P)*norm

            ''' histogram '''
            if 'range' not in kwargs:
                kwargs['range'] = (np.nanmin(I_0), np.nanmax(I_0))
            if 'weights' not in kwargs:
                kwargs['weights'] = np.ones_like(I_0)/I_0.size  # normed to 1
            self.P, self.edges = np.histogram(a=I_0, **kwargs)
            self.bins = np.convolve(self.edges, np.ones((2,))/2, mode='valid')  # center of bins by moving average with window length 2
            ''' escape rate '''
            self.Delta_I = np.mean(np.gradient(self.bins))  # np.abs(np.max(self.bins)-np.min(self.bins))/(self.bins.size-1) #
            if dIdt is None:
                self.dIdt = self.sweeps[0][2]*self.settings.IVD.sense_nplc[0]/self.settings.IVD.plc
            else:
                self.dIdt = dIdt
            self.Gamma = self.dIdt/self.Delta_I*np.array([np.log(np.sum(self.P[j:])/np.sum(self.P[j+1:])) for j, _ in enumerate(self.P)])
            ''' fit norm. escape rate '''
            self.x = self.bins
            self.y = np.log(omega_0/(2*np.pi*self.Gamma))**(2/3)
            self.popt, self.pcov = np.polyfit(x=self.x[np.isfinite(self.y)],
                                              y=self.y[np.isfinite(self.y)],
                                              deg=1,
                                              cov=True)
            self.I_c = -self.popt[1]/self.popt[0]
            ''' calculate fitted escape rate and fitted switching current distribution '''
            alpha = 1  # factor for number of points of fit: nop = a*bins.size # FIXME: if e.g. alpha=10 fit shifts in x-direction
            self.x_fit = np.linspace(np.min(self.edges), np.max(self.edges), (self.edges.size-1)*alpha+1)
            self.y_fit = self.popt[0]*self.x_fit+self.popt[1]
            self.Delta_I_fit = np.mean(np.gradient(self.x_fit))  # np.abs(np.max(self.x_fit)-np.min(self.x_fit))/(self.x_fit.size-1) #
            self.Gamma_fit = omega_0/(2*np.pi*np.exp((self.popt[0]*self.x_fit+self.popt[1])**(3/2)))  # np.sum([p*self.x_fit**i for i, p in enumerate(self.popt[::-1])], axis=0)
            self.P_fit = get_P(Gamma=self.Gamma_fit,
                               Delta_I=self.Delta_I_fit,
                               dIdt=self.dIdt,
                               norm=alpha)
            return {'P': self.P,
                    'P_fit': self.P_fit,
                    'Gamma': self.Gamma,
                    'Gamma_fit': self.Gamma_fit,
                    'popt': self.popt,
                    'pcov': self.pcov,
                    'I_c': self.I_c,
                    }

        def plot(self,
                 xlabel='escape current $ I_{esc}~(A) $',
                 y1label='escape probability $ P $',
                 y2label='escape rate $ \Gamma_{esc}~(s^{-1}) $',
                 y3label='norm. escape rate $ \ln(\omega_0/2\pi\Gamma) $'):
            """
            Plots switching current histogram, escape rate and normalized escape rate as well as their fits

            Parameters
            ----------
            xlabel: str
                X-axis label. Default is 'escape current $ I_{esc}~(A) $'.
            y1label: str
                Y-axis label of histogram. Default is 'escape probability $ P $'.
            y2label: str
                Y-axis label of escape rate. Default is 'escape rate $ \Gamma_{esc}~(s^{-1}) $'.
            y3label: str
                Y-axis label of normalized escape rate. Default is 'norm. escape rate $ \ln(\omega_0/2\pi\Gamma) $'.

            Returns
            -------
            P: np.array
                Probability distribution
            P_fit: np.array
                Fitted probability distribution
            Gamma: np.array
                Escape rate
            Gamma_fit: np.array
                Fitted escape rate
            popt: list
                Optimal fit parameters
            pcov: list
                Covariance matrix
            I_c: float
                Fitted critical current

            Examples
            --------
            >>> ivc.scm.plot()
            """
            ''' plot '''
            self.fig, (self.ax1, self.ax2) = plt.subplots(nrows=2, ncols=1, sharex=True, figsize=(6, 6))
            self.ax3 = plt.twinx(self.ax2)
            self.ax2.set_xlabel(xlabel)
            self.ax1.set_ylabel(y1label)
            self.ax2.set_ylabel(y2label)
            self.ax3.set_ylabel(y3label)
            ''' histogram '''
            self.ax1.bar(x=self.bins,
                         height=self.P,
                         width=np.mean(np.gradient(self.edges)),
                         label='data'
                    )
            self.ax1.plot(self.x_fit,
                          self.P_fit,
                          label='fit',
                          ls='-',
                          color='black')
            self.ax1.legend(loc='upper left')
            ''' escape rate '''
            lgd21, = self.ax2.semilogy(self.bins,
                                       self.Gamma,
                                       'b.',
                                       label='$ \Gamma $')
            lgd22, = self.ax2.semilogy(self.x_fit,
                                      self.Gamma_fit,
                                      'b-',
                                      label='fit')
            ''' normalized escape rate '''
            lgd31, = self.ax3.plot(self.x,
                                  self.y,
                                  'r.',
                                  label='$ \ln(\omega_0/2\pi\Gamma) $')
            lgd32, = self.ax3.plot(self.x_fit,
                                  self.y_fit,
                                  'r-',
                                  label='fit')
            self.ax2.legend(((lgd21, lgd22), (lgd31, lgd32)), ('$ \Gamma $', '$ \ln(\omega_0/2\pi\Gamma) $'), loc='upper center')
            plt.subplots_adjust(hspace=0)
            plt.show()
