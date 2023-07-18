# -*- coding: utf-8 -*-
# IV_curve.py analysis class for IV like transport measurement data
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
import scipy as sp
from scipy import stats, signal as sig, optimize as opt, constants as const
const.Phi_0 = const.h / (2 * const.e)

import json
from qkit.measure.json_handler import QkitJSONEncoder, QkitJSONDecoder
from qkit.analysis.qdata import qData, dict2obj

""" Error calculations with uncertainties package """
import uncertainties as uncert
from uncertainties import ufloat, unumpy as unp
from qkit.analysis.uncertainties_utilities import sem, nansem, umean, unanmean, uaverage, unanaverage
np.sem, np.nansem = sem, nansem
uncert.umean, uncert.unanmean = umean, unanmean
uncert.uaverage, uncert.unanaverage = uaverage, unanaverage


class IV_curve3(qData):
    """
    This is an analysis class for IV-like transport measurements taken by `qkit.measure.transport.transport.py`.
    """

    def __init__(self):
        """
        Initializes an analysis class for IV-like transport measurements taken by `qkit.measure.transport.transport.py`.

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
        # qkit.fid.update_file_db()  # update file database
        super().__init__()
        self.sweeptype = self.sweeps = self.bias = None
        self.I = self.V = self.V_corr = self.dVdI = self.R_n = self.d2VdI2 = None
        self.I_offsets = self.V_offsets = self.I_offset = self.V_offset = None
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
            Folder, where numerical derivative dV/dI is tried to load form datafile, if this was already analyzed during
            the measurement. If False, dV/dI is not loaded. Default is 'analysis0'.

        Returns
        -------
        None

        Examples
        --------
        >>> ivc.load(uuid='XXXXXX')
        """
        super().load(uuid=uuid)
        if self.m_type != 'transport':
            raise AttributeError('No transport data loaded. Use data acquired with transport measurement class or general qData class.')
        self.scan_dim = self.df.data.i_0.attrs['ds_type']  # scan dimension (1D, 2D, ...)
        self.bias = self.get_bias()
        try:
            self.sweeps = self.measurement.sample.sweeps  # sweeps (start, stop, step)
            self.sweeptype = self.get_sweeptype()
        except AttributeError:
            self.sweeps = [sample.sweeps for sample in self.measurement.sample]
            self.sweeptype = np.unique([self.get_sweeptype(sweeps=sweep) for sweep in self.sweeps])
        shape = np.concatenate([[len(self.sweeps)],
                                np.max([self.df['entry/data0/i_{:d}'.format(j)].shape for j in range(len(self.sweeps))],
                                       axis=0)])  # (number of sweeps, eventually len y-values, eventually len x-values, maximal number of sweep points)
        self.I, self.V, self.dVdI = np.empty(shape=shape), np.empty(shape=shape), np.empty(shape=shape)
        for j in range(shape[0]):
            i = self.df['entry/data0/i_{:d}'.format(j)][:]
            v = self.df['entry/data0/v_{:d}'.format(j)][:]
            if dVdI:
                try:
                    dvdi = self.df['entry/{:s}/dvdi_{:d}'.format(dVdI, j)][:]  # if analysis already done during measurement
                except KeyError:
                    dvdi = self.get_dydx(x=self.I[j], y=self.V[j])
            pad_width = np.insert(np.diff([i.shape, shape[1:]], axis=0),
                                  (0,),
                                  np.zeros(self.scan_dim)).reshape(self.scan_dim, 2)
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
        self._get_xy_parameter(self.df.data.i_0)

        self.scm.sweeps = self.sweeps
        self.scm.settings = self.settings

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
            Additional variables that are saved. Default is None, so that only the class variables mentioned above are saved.

        Returns
        -------
        None
        """
        params = params if params else {}
        params = {**{'uuid': self.uuid,
                     'path': self.path,
                     'measurement_object': self.measurement.get_JSON(),
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
        Opens qkit measurement data with given uuid <uuid> in qviewkit.

        Parameters
        ----------
        uuid: str
            Qkit identification name, that is looked for and opened in qviewkit
        ds: str | list(str)
            Datasets that are opened instantaneously. Default is data 'views/IV' and sense values for 2D or 3D.

        Returns
        -------
        None
        """
        if ds is None:
            ds = ['views/IV']
            if self.scan_dim > 1:  # for 2D and 3D: open sense values
                for i in range(len(self.sweeps)):
                    y = '{:s}_{:d}'.format({0: 'I', 1: 'V'}[not self.bias].lower(), i)
                    if y in self.df.data.__dict__.keys():
                        ds.append(y)
        super().open_qviewkit(uuid=uuid, ds=ds)

    def get_bias(self, df=None):
        """
        Gets bias mode of the measurement. Evaluate 'x_ds_url' (1D), 'y_ds_url' (2D), 'z_ds_url' (3D) of i_0 and v_0 and
        checks congruence.

        Parameters
        ----------
        df: qkit.storage.store.Data (optional)
            Datafile of transport measurement. Default is None that means <self.df>.

        Returns
        -------
        mode: int
            Bias mode. Meanings are 0 (current) and 1 (voltage).
        """
        #
        if df is None:
            df = self.df
        self.bias = {'i': 0, 'v': 1}[str(df.data.i_0.attrs.get('{:s}_ds_url'.format(chr(self.scan_dim + 119))) and
                                         df.data.v_0.attrs.get('{:s}_ds_url'.format(chr(self.scan_dim + 119)))).split('/')[-1][0]]
        return self.bias

    def get_sweeptype(self, sweeps=None):
        """
        Gets the sweep type of predefined set of sweeps as generated by `qkit.measure.transport.transport.py`.

        Parameters
        ----------
        sweeps: array_likes of array_likes of floats (optional)
            Set of sweeps containing start, stop and step size (e.g. sweep object using 
            `qkit.measure.transport.transport.sweep` class). Default is None that means self.sweeps.

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
            if all(np.array(sweeps[0])[[1, 0, 2]] == np.array(sweeps[1])[:3]) and \
               all(np.array(sweeps[2])[[1, 0, 2]] == np.array(sweeps[3])[:3]):
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
            An N-dimensional array containing current values. Default is None that means <self.I>.
        V: numpy.array (optional)
            An N-dimensional array containing voltage values. Default is None that means <self.V>.
        mode: function (optional)
            Function that calculates the numerical gradient dx from a given array x.
            Default is `scipy.signal.savgol_filter` (Savitzky Golay filter).
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
            An N-dimensional array containing x-values. Default is None which means that <x> is considered as index.
        mode: function (optional)
            Function that calculates the numerical gradient dx from a given array <x>.
            Default is `scipy.signal.savgol_filter` (Savitzky Golay filter).
        kwargs:
            Keyword arguments forwarded to the function <mode>. Default is for 
            * `scipy.signal.savgol_filter`: {'window_length': 15, 'polyorder': 3, 'deriv': 1},
            * `numpy.gradient`: {'axis': <self.scan_dim>}

        Returns
        -------
        dy/dx: numpy.array
            Numerical gradient quotient. If no <x> is given, dx = np.ones(nop)

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
            if np.isnan(y).any():
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
                return dy / dx
            else:
                return mode(y, **kwargs) / mode(x, **kwargs)

    def get_offsets(self, x=None, y=None, dxdy=None, threshold=20e-6, offset=None, yr=False, keepdims=np._NoValue):
        """
        Calculates x- and y-offset for every trace. Therefore, the branch where the y-values are nearly constant are
        evaluated. The average of all corresponding x-values is considered to be the x-offset and the average of the 
        extreme y-values are considered as y-offset.

        Parameters
        ----------
        x: numpy.array (optional)
            An N-dimensional array containing x-values. Default is None, where <x> is considered as <self.V> or <self.I> 
            in the current or voltage bias, respectively.
        y: numpy.array (optional)
            An N-dimensional array containing y-values. Default is None, where <y> is considered as <self.I> or <self.V> 
            in the current or voltage bias, respectively.
        dydx: numpy.array (optional)
            Numerical gradient quotient. Default is None that means
            * the differential resistance <self.dVdI> in the current bias,
            * the differential conductance <self.dIdV> in the voltage bias.
        threshold: float (optional)
            Threshold voltage that limits the superconducting branch. Default is 20e-6.
        offset: float (optional)
            Voltage offset that shifts the limits of the superconducting branch which is set by <threshold>.
            Default is None, which uses voltage at maximal slope dy/dx.
        yr: bool (optional)
            Condition, if critical or retrapping y-values are evaluated. Default is False.
        keepdims : bool (optional)
            If this is set to True, the axes which are reduced are left in the result as dimensions with size one. With
            this option, the result will broadcast correctly against the input array.

            If the default value is passed, then `keepdims` will not be passed through to the `mean` method of
            subclasses of `ndarray`, however any non-default value will be.  If the subclass' method does not implement
            `keepdims` any exceptions will be raised.


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
        if dxdy is None:
            dxdy = [self.dVdI, 1/self.dVdI][self.bias]
        if offset is None:
            amax = np.argmax(1 / sp.ndimage.uniform_filter(dxdy, size=3, mode='constant') if dxdy is not None
                   else np.grandient(y)/np.grandient(x), axis=-1)  # maximal slope
            if len(x.shape) - 1 == 1:
                offset = np.nanmean(x[np.indices(amax.shape)[0], amax])
            elif len(x.shape) - 1 == 2:
                offset = np.nanmean(x[np.indices(amax.shape)[0], np.indices(amax.shape)[1], amax])
            elif len(x.shape) - 1 == 3:
                offset = np.nanmean(x[np.indices(amax.shape)[0], np.indices(amax.shape)[1], np.indices(amax.shape)[2], amax])
        ''' constant range via threshold (for JJ superconducting range via threshold voltage) '''
        with np.errstate(invalid='ignore'):  # raises warning due to np.nan
            mask = np.logical_and(x >= -threshold + offset, x <= threshold + offset)
        x_const, y_const = np.copy(x), np.copy(y)
        np.place(x_const, np.logical_not(mask), np.nan)
        np.place(y_const, np.logical_not(mask), np.nan)
        if self.sweeptype == 0:  # halfswing
            ''' get x offset (for JJ voltage offset)'''
            # x_offsets = np.mean(np.nanmean(x_const, axis=self.scan_dim), axis=0)
            x_offsets = np.atleast_1d(uncert.unanaverage(unp.uarray(nominal_values=np.nanmean(x_const,
                                                                                              axis=self.scan_dim),
                                                                    std_devs=np.nansem(x_const,
                                                                                       axis=self.scan_dim)),
                                                         axis=0))
            ''' get y offset (for JJ current offset) '''
            # TODO: calculate std_devs correct
            if yr:  # retrapping y (for JJ retrapping current)
                y_rs = np.array([np.nanmax(y_const[0], axis=(self.scan_dim - 1)),
                                 np.nanmin(y_const[1], axis=(self.scan_dim - 1))])
                # y_offsets = np.mean(y_rs, axis=0)
                y_offsets = unp.uarray(nominal_values=np.nanmean(y_rs, axis=0),
                                       std_devs=np.nansem(np.abs(y_rs), axis=0))
            else:  # critical y (for JJ critical current)
                y_cs = np.array([np.nanmin(y_const[0], axis=(self.scan_dim - 1)),
                                 np.nanmax(y_const[1], axis=(self.scan_dim - 1))])
                # y_offsets = np.mean(y_cs, axis=0)
                y_offsets = unp.uarray(nominal_values=np.nanmean(y_cs, axis=0),
                                       std_devs=np.nansem(np.abs(y_cs), axis=0))
        elif self.sweeptype == 1:  # 4 quadrants
            ''' get x offset '''
            # x_offsets = np.mean(np.nanmean(x_const, axis=self.scan_dim), axis=0)
            x_offsets = np.atleast_1d(
                uncert.unanaverage(unp.uarray(nominal_values=np.nanmean(x_const,
                                                                        axis=self.scan_dim),
                                              std_devs=np.nansem(x_const,
                                                                 axis=self.scan_dim)),
                                   axis=0))
            ''' get y offset '''
            # TODO: calculate std_devs correct
            if yr:  # retrapping y (for JJ retrapping current)
                y_rs = np.array([np.nanmax(y_const[1], axis=(self.scan_dim - 1)),
                                 np.nanmin(y_const[3], axis=(self.scan_dim - 1))])
                # y_offsets = np.mean(y_rs, axis=0)
                y_offsets = unp.uarray(nominal_values=np.nanmean(y_rs, axis=0),
                                       std_devs=np.nansem(np.abs(y_rs), axis=0))
            else:  # critical y (for JJ critical current)
                y_cs = np.array([np.nanmax(y_const[0], axis=(self.scan_dim - 1)),
                                 np.nanmin(y_const[2], axis=(self.scan_dim - 1))])
                # y_offsets = np.mean(y_cs, axis=0)
                y_offsets = unp.uarray(nominal_values=np.nanmean(y_cs, axis=0),
                                       std_devs=np.nansem(np.abs(y_cs), axis=0))
        else:  # custom sweep type
            ''' get x offset '''
            # x_offsets = np.nanmean(np.nanmean(x_const, axis=self.scan_dim), axis=0)
            x_offsets = np.atleast_1d(
                uncert.unanaverage(unp.uarray(nominal_values=np.nanmean(x_const, axis=self.scan_dim),
                                              std_devs=np.nansem(x_const, axis=self.scan_dim)),
                                   axis=0))
            ''' get y offset '''
            # TODO: calculate std_devs correct
            if yr:  # retrapping y (for JJ retrapping current)
                raise NotImplementedError('No algorithm implemented for custom sweep type')
            else:
                y_cs = np.array([np.nanmax(np.nanmax(y_const, axis=0), axis=self.scan_dim - 1),
                                 np.nanmin(np.nanmin(y_const, axis=0), axis=self.scan_dim - 1)])
                # y_offsets = np.mean(y_cs, axis=0)
                y_offsets = unp.uarray(nominal_values=np.nanmean(y_cs, axis=0),
                                       std_devs=np.nansem(np.abs(y_cs), axis=0))
        self.I_offsets, self.V_offsets = [x_offsets, y_offsets][::int(np.sign(self.bias - .5))]
        if keepdims is not np._NoValue:
            if len(x.shape) - 1 == 1:
                self.I_offsets = self.I_offsets[np.newaxis]
                self.V_offsets = self.V_offsets[np.newaxis]
            elif len(x.shape) - 1 == 2:
                self.I_offsets = self.I_offsets[np.newaxis, :, np.newaxis]
                self.V_offsets = self.V_offsets[np.newaxis, :, np.newaxis]
            elif len(x.shape) - 1 == 3:
                self.I_offsets = self.I_offsets[np.newaxis, :, :, np.newaxis]
                self.V_offsets = self.V_offsets[np.newaxis, :, :, np.newaxis]
        return self.I_offsets, self.V_offsets

    def get_offset(self, *args, **kwargs):
        """
        Calculates x- and y-offset for the whole data set. Therefore, the branch where the y-values are nearly constant
        are evaluated. The average of all corresponding x-values is considered to be the x-offset and the average of the
        extreme y-values are considered as y-offset.

        Parameters
        ----------
        x: numpy.array (optional)
            An N-dimensional array containing x-values. Default is None, where <x> is considered as <self.V> or <self.I>
            in the current or voltage bias, respectively.
        y: numpy.array (optional)
            An N-dimensional array containing y-values. Default is None, where <y> is considered as <self.I> or <self.V>
            in the current or voltage bias, respectively.
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
        self.I_offset, self.V_offset = list(map(np.nanmean, self.get_offsets(*args, **kwargs)))
        return self.I_offset, self.V_offset

    def get_2wire_slope_correction(self, I=None, V=None, dVdI=None, peak_finder=sig.find_peaks, **kwargs):
        """
        Gets voltage values corrected by an ohmic slope such as occur in 2wire measurements.
        The two maxima in the differential resistivity <dVdI> are identified as critical and retrapping currents. The
        slope of the superconducting regime in between (which should ideally be infinity) is fitted using
        numpy.linalg.qr algorithm and subtracted from the raw data.

        Parameters
        ----------
        I: numpy.array (optional)
            An N-dimensional array containing current values. Default is None that means <self.I>.
        V: numpy.array (optional)
            An N-dimensional array containing voltage values. Default is None that means <self.V>.
        dVdI: numpy.array (optional)
            An N-dimensional array containing differential resistance (dV/dI) values. Default is None that means
            <self.dVdI>.
        peak_finder: function (optional)
            Peak finding algorithm. Default is `scipy.signal.find_peaks`.
        kwargs:
            Keyword arguments forwarded to the peak finding algorithm <peak_finder>.

        Returns
        -------
        V_corr: numpy.array
            Ohmic slope corrected voltage values
        """

        # TODO: uncertainties
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
        if len(V.shape) - 1 == 1:
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
        elif len(V.shape) - 1 == 2:
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
        elif len(V.shape) - 1 == 3:
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

    def get_Rn(self, I=None, V=None, dVdI=None, deriv_func=sig.savgol_filter, peak_finder=sig.find_peaks, mode=0,
               **kwargs):
        """
        Get normal state resistance of over critical range. Therefore, the curvature d²V/dI² is computed using the second
        order derivation function <deriv_func> and analysing peaks in it with <peak_finder>.
        The ohmic range is considered to range from the outermost tail of the peaks in the curvature to the start/end of
        the sweep and the resistance is calculated as mean of the differential resistance values <dVdI> within this range.

        Parameters
        ----------
        I: numpy.array (optional)
            An N-dimensional array containing current values. Default is None that means <self.I>.
        V: numpy.array (optional)
            An N-dimensional array containing voltage values. Default is None that means <self.V>.
        dVdI: numpy.array (optional)
            An N-dimensional array containing differential resistance (dV/dI) values. Default is None that means
            <self.dVdI>.
        deriv_func: function (optional)
            Function that calculates the numerical gradient dx from a given array x. Default is
            `scipy.signal.savgol_filter` (Savitzky Golay filter).
        peak_finder: function (optional)
            Peak finding algorithm. Default is `scipy.signal.find_peaks`.
        mode: int (optional)
            Mode how Rn is determined from the ohmic range found. Must be 0 (slope of linear fit) or 1 (average of dV/dI).
        kwargs:
            Keyword arguments forwarded to the function <mode> and the peak finding algorithm <peak_finder>. Default is for
            * `scipy.signal.savgol_filter`: {'window_length': 15, 'polyorder': 3, 'deriv': 2},
            * `numpy.diff`: {'n': 2, 'axis': <self.scan_dim}>,
            * `scipy.signal.find_peaks`: {'prominence': np.max(np.abs(<self.d2VdI2>))/1e2)}

        Returns
        -------
        Rn: numpy.array
            Average normal state resistance
        """

        def _peak_finder(a, **_kwargs):
            ans = peak_finder(a, **_kwargs)
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
        if deriv_func == sig.savgol_filter:
            kwargs_deriv = {'deriv': 2, 'window_length': kwargs.get('window_length', 15),
                            'polyorder': kwargs.get('polyorder', 3)}
        elif deriv_func == np.diff:
            kwargs_deriv = {'n': 2, 'axis': kwargs.get('axis', self.scan_dim)}
        else:
            kwargs_deriv = {}
        ''' second derivative d^2V/dI^2 '''
        self.d2VdI2 = self.get_dydx(x=I, y=V, mode=deriv_func, **kwargs_deriv)
        ''' peak detection in d^2V/dI^2 '''
        if len(V.shape) - 1 == 1:
            if peak_finder == sig.find_peaks:
                kwargs_peak_finder = np.array(list(map(lambda d2VdI21D:
                                                       {'prominence': kwargs.get('prominence',
                                                                                 np.max(np.abs(d2VdI21D)) / 1e2)},
                                                       self.d2VdI2)))
            peaks = map(lambda j, d2VdI21D:
                        _peak_finder(d2VdI21D * np.sign(max(d2VdI21D.min(), d2VdI21D.max(), key=abs)),
                                     **kwargs_peak_finder[j]),  # sign, so that extremum is positiv
                        *zip(*enumerate(self.d2VdI2)))
            slcs = np.array(list(map(lambda peak1D, d2VdI21D:
                                     np.array((slice(0, np.min(peak1D[1]['left_bases'])),
                                               slice(max(peak1D[1]['right_bases']), d2VdI21D.size))),
                                     peaks, self.d2VdI2)))
            if mode == 0:
                popts, pcovs = np.ones(shape=(len(self.d2VdI2), 2)), np.ones(shape=(len(self.d2VdI2), 2, 2))
                for j in range(2):
                    V_ohm = np.concatenate([V[k, slc] for k, slc in enumerate(slcs.T[j])])
                    I_ohm = np.concatenate([I[k, slc] for k, slc in enumerate(slcs.T[j])])
                    popts[j], pcovs[j] = np.polyfit(x=I_ohm,
                                                    y=V_ohm,
                                                    deg=1,
                                                    cov=True)
                # self.R_n = np.mean(popts[:, 0])
                self.R_n = np.nanmean(unp.uarray(nominal_values=popts,
                                                 std_devs=np.array(list(map(lambda pcov:
                                                                            np.sqrt(np.diagonal(pcov)),
                                                                            pcovs))))[:, 0])
            elif mode == 1:
                # self.R_n = np.array([np.nanmean(np.concatenate([dVdI[k, x, y, s] for k, s in enumerate(slc)]))
                #                     for j, slc in enumerate(np.transpose(slcs, axes=(1, 0)))])
                self.R_n = np.array(
                    [ufloat(nominal_value=np.nanmean(np.concatenate([dVdI[k, s] for k, s in enumerate(slc)])),
                            std_dev=np.nansem(np.concatenate([dVdI[k, s] for k, s in enumerate(slc)])))
                     for j, slc in enumerate(np.transpose(slcs, axes=(1, 0)))])
                self.R_n = np.nanmean(self.R_n, axis=self.scan_dim - 1)
        elif len(V.shape) - 1 == 2:
            if peak_finder == sig.find_peaks:
                kwargs_peak_finder = np.array(list(map(lambda d2VdI22D:
                                                       list(map(lambda d2VdI21D:
                                                                {'prominence': kwargs.get('prominence', np.max(
                                                                    np.abs(d2VdI21D)) / 1e2)},
                                                                d2VdI22D)),
                                                       self.d2VdI2)))
            peaks = map(lambda j, d2VdI22D:
                        list(map(lambda k, d2VdI21D:
                                 _peak_finder(d2VdI21D * np.sign(max(d2VdI21D.min(), d2VdI21D.max(), key=abs)),
                                              **kwargs_peak_finder[j, k]),  # sign, so that extremum is positiv
                                 *zip(*enumerate(d2VdI22D)))),
                        *zip(*enumerate(self.d2VdI2)))
            slcs = np.array(list(map(lambda peak2D, d2VdI22D:
                                     list(map(lambda peak1D, d2VdI21D:
                                              np.array((slice(0, np.min(peak1D[1]['left_bases'])),
                                                        slice(max(peak1D[1]['right_bases']), d2VdI21D.size))),
                                              peak2D, d2VdI22D)),
                                     peaks, self.d2VdI2)))
            if mode == 0:
                popts = np.ones(shape=(len(self.x_vec), len(self.d2VdI2), 2))
                pcovs = np.ones(shape=(len(self.x_vec), len(self.d2VdI2), 2, 2))
                for x, slcs1D in enumerate(np.transpose(slcs, axes=(1, 0, 2))):
                    for j in range(2):
                        V_ohm = np.concatenate([V[k, x, slc] for k, slc in enumerate(slcs1D.T[j])])
                        I_ohm = np.concatenate([I[k, x, slc] for k, slc in enumerate(slcs1D.T[j])])
                        popts[x, j], pcovs[x, j] = np.polyfit(x=I_ohm,
                                                              y=V_ohm,
                                                              deg=1,
                                                              cov=True)
                # self.R_n = np.nanmean(popts[:, :, 0], axis=1)
                self.R_n = np.nanmean(unp.uarray(nominal_values=popts,
                                                 std_devs=np.array(list(map(lambda pcov1D:
                                                                            list(map(lambda pcov:
                                                                                     np.sqrt(np.diagonal(pcov)),
                                                                                     pcov1D)),
                                                                            pcovs))))[:, :, 0],
                                      axis=1)
            elif mode == 1:
                # self.R_n = np.array([[np.nanmean(np.concatenate([dVdI[k, x, y, s] for k, s in enumerate(slc)]))
                #                      for j, slc in enumerate(slcs1D)]
                #                     for x, slcs1D in enumerate(np.transpose(slcs, axes=(1, 2, 0)))])
                self.R_n = np.array(
                    [[ufloat(nominal_value=np.nanmean(np.concatenate([dVdI[k, s] for k, s in enumerate(slc)])),
                             std_dev=np.nansem(np.concatenate([dVdI[k, s] for k, s in enumerate(slc)])))
                      for j, slc in enumerate(slcs1D)]
                     for x, slcs1D in enumerate(np.transpose(slcs, axes=(1, 2, 0)))])
                self.R_n = np.nanmean(self.R_n, axis=self.scan_dim - 1)
        elif len(V.shape) - 1 == 3:
            if peak_finder == sig.find_peaks:
                kwargs_peak_finder = np.array(list(map(lambda d2VdI23D:
                                                       list(map(lambda d2VdI22D:
                                                                list(map(lambda d2VdI21D:
                                                                         {'prominence': kwargs.get('prominence', np.max(
                                                                             np.abs(d2VdI21D)) / 1e2)},
                                                                         d2VdI22D)),
                                                                d2VdI23D)),
                                                       self.d2VdI2)))
            peaks = map(lambda i, d2VdI23D:
                        list(map(lambda j, d2VdI22D:
                                 list(map(lambda k, d2VdI21D:
                                          _peak_finder(d2VdI21D * np.sign(max(d2VdI21D.min(), d2VdI21D.max(), key=abs)),
                                                       **kwargs_peak_finder[i, j, k]),
                                          # sign, so that extremum is positiv
                                          *zip(*enumerate(d2VdI22D)))),
                                 *zip(*enumerate(d2VdI23D)))),
                        *zip(*enumerate(self.d2VdI2)))
            slcs = np.array(list(map(lambda peak3D, d2VdI23D:
                                     list(map(lambda peak2D, d2VdI22D:
                                              list(map(lambda peak1D, d2VdI21D:
                                                       np.array((slice(0, np.min(peak1D[1]['left_bases'])),
                                                                 slice(max(peak1D[1]['right_bases']), d2VdI21D.size)
                                                                 )),
                                                       peak2D, d2VdI22D)),
                                              peak3D, d2VdI23D)),
                                     peaks, self.d2VdI2)))
            if mode == 0:
                popts = np.ones(shape=(len(self.x_vec), len(self.y_vec), len(self.d2VdI2), 2))
                pcovs = np.ones(shape=(len(self.x_vec), len(self.y_vec), len(self.d2VdI2), 2, 2))
                for x, slcs2D in enumerate(np.transpose(slcs, axes=(1, 2, 0, 3))):
                    for y, slcs1D in enumerate(slcs2D):
                        for j in range(2):
                            V_ohm = np.concatenate([V[k, x, y, slc] for k, slc in enumerate(slcs1D.T[j])])
                            I_ohm = np.concatenate([I[k, x, y, slc] for k, slc in enumerate(slcs1D.T[j])])
                            popts[x, y, j], pcovs[x, y, j] = np.polyfit(x=I_ohm,
                                                                        y=V_ohm,
                                                                        deg=1,
                                                                        cov=True)
                # self.R_n = np.nanmean(popts[:, :, :, 0], axis=2)
                self.R_n = np.nanmean(unp.uarray(nominal_values=popts,
                                                 std_devs=np.array(list(map(lambda pcov2D:
                                                                            list(map(lambda pcov1D:
                                                                                     list(map(lambda pcov:
                                                                                              np.sqrt(
                                                                                                  np.diagonal(pcov)),
                                                                                              pcov1D)),
                                                                                     pcov2D)),
                                                                            pcovs))))[:, :, :, 0],
                                      axis=2)
            elif mode == 1:
                # self.R_n = np.array([[[np.nanmean(np.concatenate([dVdI[k, x, y, s] for k, s in enumerate(slc)]))
                #                       for j, slc in enumerate(slcs1D)]
                #                      for y, slcs1D in enumerate(slcs2D)]
                #                     for x, slcs2D in enumerate(np.transpose(slcs, axes=(1, 2, 3, 0)))])
                self.R_n = np.array([[[ufloat(nominal_value=np.nanmean(np.concatenate([dVdI[k, s]
                                                                                       for k, s in enumerate(slc)])),
                                              std_dev=np.nansem(np.concatenate([dVdI[k, s]
                                                                                for k, s in enumerate(slc)])))
                                       for j, slc in enumerate(slcs1D)]
                                      for y, slcs1D in enumerate(slcs2D)]
                                     for x, slcs2D in enumerate(np.transpose(slcs, axes=(1, 2, 3, 0)))])
                self.R_n = np.nanmean(self.R_n, axis=self.scan_dim - 1)
        else:
            raise ValueError('Scan dimension must be in {1, 2, 3}')
        return self.R_n

    def get_Ic_threshold(self, I=None, V=None, dVdI=None, threshold=20e-6, offset=None, Ir=False):
        """
        Get critical current values. These are considered as currents, where the voltage jumps beyond threshold
        ± <threshold> - <offset>.

        Parameters
        ----------
        I: numpy.array (optional)
            An N-dimensional array containing current values. Default is None that means <self.I>.
        V: numpy.array (optional)
            An N-dimensional array containing voltage values. Default is None that means <self.V>.
        dVdI: numpy.array (optional)
            An N-dimensional array containing differential resistance (dV/dI) values. Default is None that means
            <self.dVdI>.
        threshold: float (optional)
            Threshold voltage that limits the superconducting branch. Default is 20e-6.
        offset: float (optional)
            Voltage offset that shifts the limits of the superconducting branch which is set by <threshold>. Default is
            None that means <self.V_offset>.
        Ir: bool (optional)
            Condition, if retrapping currents are returned, too. Default is False.

        Returns
        -------
        I_cs: numpy.array
            Critical current values.
        I_rs: numpy.array (optional)
            Retrapping current values.
        """
        # TODO: uncertainties
        if V is None:
            V = self.V
        if I is None:
            I = self.I
        if dVdI is None:
            dVdI = self.dVdI
        if offset is None:
            if self.V_offset is None:
                amax = np.argmax(1 / dVdI if dVdI is not None else np.grandient(I)/np.grandient(V), axis=-1)  # maximal slope
                if len(V.shape) - 1 == 1:
                    offset = np.nanmean(V[np.indices(amax.shape)[0], amax])
                elif len(V.shape) - 1 == 2:
                    offset = np.nanmean(V[np.indices(amax.shape)[0], np.indices(amax.shape)[1], amax])
                elif len(V.shape) - 1 == 3:
                    offset = np.nanmean(V[np.indices(amax.shape)[0], np.indices(amax.shape)[1], np.indices(amax.shape)[2], amax])
            else:
                offset = self.V_offset
        if len(V.shape) - 1 == 0:  # single trace used for in situ fit
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
            I_cs = np.array([np.nanmin(I_sc[0], axis=(self.scan_dim - 1)),
                             np.nanmax(I_sc[1], axis=(self.scan_dim - 1))])
            ''' retrapping current '''
            I_rs = np.array([np.nanmax(I_sc[0], axis=(self.scan_dim - 1)),
                             np.nanmin(I_sc[1], axis=(self.scan_dim - 1))])
        elif self.sweeptype == 1:  # 4 quadrants
            ''' critical current '''
            I_cs = np.array([np.nanmax(I_sc[0], axis=(self.scan_dim - 1)),
                             np.nanmin(I_sc[2], axis=(self.scan_dim - 1))])
            ''' retrapping current '''
            I_rs = np.array([np.nanmax(I_sc[1], axis=(self.scan_dim - 1)),
                             np.nanmin(I_sc[3], axis=(self.scan_dim - 1))])
        else:  # custom sweep type
            ''' critical current '''
            I_cs = np.array([np.nanmax(I_sc, axis=(self.scan_dim - 1)),
                             np.nanmin(I_sc, axis=(self.scan_dim - 1))])
            ''' retrapping current '''
            if Ir:
                raise NotImplementedError('No algorithm implemented for custom sweep type')
        if Ir:
            return [I_cs, I_rs]
        else:
            return I_cs

    def get_Ic_deriv(self, I=None, V=None, dVdI=None, Ir=False, Vg=False, tol_offset=20e-6, window=5,
                     peak_finder=sig.find_peaks, **kwargs):
        """
        Gets critical current values using the numerical derivative dV/dI.
        Peaks in these data correspond to voltage jumps, are detected with a peak finding algorithm <peak_finder> and
        checked, whether the corresponding voltage jumps out or in the superconducting branch, that is identified as
        critical or retrapping current, respectively. Therefore, the average of half the window below and above the peak
        is considered. The superconducting branch, in turn, is assumed as the voltage offset <self.V_offset> within the
        tolerance <tol_offset>.

        Parameters
        ----------
        I: numpy.array (optional)
            An N-dimensional array containing current values. Default is None that means <self.I>.
        V: numpy.array (optional)
            An N-dimensional array containing voltage values. Default is None that means <self.V>.
        dVdI: numpy.array (optional)
            An N-dimensional array containing differential resistance (dV/dI) values. Default is None that means
            <self.dVdI>.
        Ir: bool (optional)
            Condition, if retrapping currents are returned, too. Default is False
        Vg: bool (optional)
            Condition, if gap voltages are returned, too. Default is False
        tol_offset: float (optional)
            Voltage offset tolerance that limits the superconducting branch around the voltage offset <self.V_offset>.
            Default is 20e-6.
        window: int (optional)
            Window around the jump, where the voltage is evaluated and classified as 'superconducting branch'. Default
            is 5 that considers two values below and 2 values above the jump.
        peak_finder: function (optional)
            Peak finding algorithm. Default is `scipy.signal.find_peaks`.
        kwargs:
            Keyword arguments forwarded to the peak finding algorithm <peak_finder>.

        Returns
        -------
        I_cs: numpy.array
            Critical current values.
        I_rs: numpy.array (optional)
            Retrapping current values.
        properties: dict
            Properties of all found peaks (not only I_c and I_r, but also further jumps), such as corresponding currents,
            voltages, differential resistances, indices as well as returns of the used peak finding algorithm.

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
        if len(V.shape) - 1 == 0:  # single trace used for in situ fit
            peaks = _peak_finder(dVdI, **kwargs)
            try:
                return I[peaks[0]]
            except IndexError:  # if no peak found return np.nan
                return np.nan
        ''' peak detection in dV/dI '''
        if len(V.shape) - 1 == 1:
            peaks = np.array(list(map(lambda dVdI1D:
                                      _peak_finder(dVdI1D, **kwargs),
                                      dVdI)),
                             dtype=object)
        elif len(V.shape) - 1 == 2:
            peaks = np.array(list(map(lambda dVdI2D:
                                      list(map(lambda dVdI1D:
                                               _peak_finder(dVdI1D, **kwargs),
                                               dVdI2D)),
                                      dVdI)),
                             dtype=object)
        elif len(V.shape) - 1 == 3:
            peaks = np.array(list(map(lambda dVdI3D:
                                      list(map(lambda dVdI2D:
                                               list(map(lambda dVdI1D:
                                                        _peak_finder(dVdI1D, **kwargs),
                                                        dVdI2D)),
                                               dVdI3D)),
                                      dVdI)),
                             dtype=object)
        else:
            raise ValueError('Scan dimension must be in {1, 2, 3}')
        return self._classify_jump(I=I, V=V, Y=dVdI, peaks=peaks, tol_offset=tol_offset, window=window, Ir=Ir, Vg=Vg)

    def get_Ic_dft(self, I=None, V=None, dVdI=None, s=10, Ir=False, Vg=False, tol_offset=20e-6, window=5,
                   peak_finder=sig.find_peaks, **kwargs):
        """
        Gets critical current values using a discrete Fourier transform, a smoothed derivation in the frequency domain
        and an inverse Fourier transform.
        Therefore, the voltage values are corrected by the linear offset slope, fast Fourier transformed to the frequency
        domain, multiplied with a Gaussian smoothed derivation function if*exp(-s*f²) in the frequency domain and
        inversely fast Fourier transformed to the time domain. This corresponds to the convolution of the voltage values
        with the Gaussian smoothed derivation function in the time domain.
        Peaks in these data correspond to voltage jumps, are detected with a peak finding algorithm <peak_finder> and
        checked, whether the corresponding voltage jumps out or in the superconducting branch, that is identified as
        critical or retrapping current, respectively. Therefore, the average of half the window below and above the peak
        is considered. The superconducting branch, in turn, is assumed as the voltage offset <self.V_offset> within the
        tolerance <tol_offset>.

        Parameters
        ----------
        I: numpy.array (optional)
            An N-dimensional array containing current values. Default is None that means <self.I>.
        V: numpy.array (optional)
            An N-dimensional array containing voltage values. Default is None that means <self.V>.
        dVdI: numpy.array (optional)
            An N-dimensional array containing differential resistance (dV/dI) values. Default is None that means
            <self.dVdI>.
        s: float (optional)
            Smoothing factor of the derivative. Default is 10.
        Ir: bool (optional)
            Condition, if retrapping currents are returned, too. Default is False.
        Vg: bool (optional)
            Condition, if gap voltages are returned, too. Default is False.
        tol_offset: float (optional)
            Voltage offset tolerance that limits the superconducting branch around the voltage offset <self.V_offset>.
            Default is 20e-6.
        window: int (optional)
            Window around the jump, where the voltage is evaluated and classified as 'superconducting branch'. Default
            is 5 that considers two values below and 2 values above the jump.
        peak_finder: function (optional)
            Peak finding algorithm. Default is `scipy.signal.find_peaks`.
        kwargs:
            Keyword arguments forwarded to the peak finding algorithm <peak_finder>.

        Returns
        -------
        I_cs: numpy.array
            Critical current values.
        I_rs: numpy.array (optional)
            Retrapping current values.
        properties: dict
            Properties of all found peaks (not only I_c and I_r, but also further jumps), such as corresponding currents,
            voltages, differential resistances, indices as well as returns of the used peak finding algorithm.

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

        def _get_deriv_dft(_V):
            V_fft = np.fft.fft(_V)  # Fourier transform of V from time to frequency domain
            f = np.fft.fftfreq(_V.shape[-1])  # frequency values
            kernel = 1j * np.fft.fft(f * np.exp(-s * f ** 2))  # smoothed derivation function, how it would look like in time domain (with which V is convolved in the time domain)
            V_fft_smooth = 1j * f * np.exp(-s * f ** 2) * V_fft  # Fourier transform of a Gaussian smoothed derivation of V in the frequency domain
            return np.fft.ifft(V_fft_smooth)  # inverse Fourier transform of the smoothed derivation of V from reciprocal to time domain

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
        if len(V.shape) - 1 == 0:  # single trace used for in situ fit
            V_corr = V - np.linspace(start=V[0], stop=V[-1], num=V.shape[-1], axis=0)  # adjust offset slope
            dV_smooth = _get_deriv_dft(_V=V_corr)
            peaks = _peak_finder(dV_smooth, **kwargs)
            try:
                return I[peaks[0]]
            except IndexError:  # if no peak found return np.nan
                return np.nan
        ''' differentiate and smooth in the frequency domain '''
        if len(V.shape) - 1 == 1:
            V_corr = V - np.linspace(start=V[:, 0],
                                     stop=V[:, -1],
                                     num=V.shape[-1],
                                     axis=1)  # adjust offset slope
        elif len(V.shape) - 1 == 2:
            V_corr = V - np.linspace(start=V[:, :, 0],
                                     stop=V[:, :, -1],
                                     num=V.shape[-1],
                                     axis=2)  # adjust offset slope
        elif len(V.shape) - 1 == 3:
            V_corr = V - np.linspace(start=V[:, :, :, 0],
                                     stop=V[:, :, :, -1],
                                     num=V.shape[-1],
                                     axis=3)  # adjust offset slope
        else:
            raise ValueError('Scan dimension must be in {1, 2, 3}')
        dV_smooth = _get_deriv_dft(_V=V_corr)
        ''' peak detection '''
        if len(V.shape) - 1 == 1:
            peaks = np.array(list(map(lambda dV_smooth1D:
                                      _peak_finder(np.abs(dV_smooth1D), **kwargs),
                                      dV_smooth)),
                             dtype=object)
        elif len(V.shape) - 1 == 2:
            peaks = np.array(list(map(lambda dV_smooth2D:
                                      list(map(lambda dV_smooth1D:
                                               _peak_finder(np.abs(dV_smooth1D), **kwargs),
                                               dV_smooth2D)),
                                      dV_smooth)),
                             dtype=object)
        elif len(V.shape) - 1 == 3:
            peaks = np.array(list(map(lambda dV_smooth3D:
                                      list(map(lambda dV_smooth2D:
                                               list(map(lambda dV_smooth1D:
                                                        _peak_finder(np.abs(dV_smooth1D), **kwargs),
                                                        dV_smooth2D)),
                                               dV_smooth3D)),
                                      dV_smooth)),
                             dtype=object)
        else:
            raise ValueError('Scan dimension must be in {1, 2, 3}')
        return self._classify_jump(I=I, V=V, Y=dV_smooth, peaks=peaks, tol_offset=tol_offset, window=window, Ir=Ir,
                                   Vg=Vg)

    def _classify_jump(self, I, V, Y, peaks, tol_offset=20e-6, window=5, Ir=False, Vg=False):
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
            An N-dimensional array containing indices and properties of peaks that are already determined, as obtained
            by e.g. `scipy.signal.find_peaks`.
        Ir: bool (optional)
            Condition, if retrapping currents are returned, too. Default is False
        Vg: bool (optional)
            Condition, if gap voltages are returned, too. Default is False
        tol_offset: float (optional)
            Voltage offset tolerance that limits the superconducting branch around the voltage offset <self.V_offset>.
            Default is 20e-6.
        window: int (optional)
            Window around the jump, where the voltage is evaluated and classified as 'superconducting branch'. Default
            is 5 that considers two values below and 2 values above the jump.

        Returns
        -------
        I_cs: numpy.array
            Critical current values.
        I_rs: numpy.array (optional)
            Retrapping current values.
        properties: dict
            Properties of all found peaks (not only I_c and I_r, but also further jumps), such as corresponding currents,
            voltages, differential resistances, indices as well as returns of the used peak finding algorithm.
        """

        def get_fwhm(y, peak, mask):
            """ Get bounds of full width at half maximum """
            left, right = peak[1]['left_bases'][mask].item(), peak[1]['right_bases'][mask].item()
            y = y[slice(left, right)] - np.nanmean(y)  # use left and right bases as bounds and subtract floor (mean(y))
            hm = np.max(y) / 2  # half maximum
            max_idx = np.argmax(y)  # index of maximum
            d = np.sign(hm - y[:-1]) - np.sign(hm - y[1:])
            left_idx = np.argwhere(d[:max_idx] > 0)[-1]
            right_idx = max_idx + np.argwhere(d[max_idx:] < 0)[0] + 1
            return np.concatenate((left_idx, right_idx)) + left

        Y_name = [key for key, val in sys._getframe().f_back.f_locals.items() if np.array_equal(val, Y)][0]
        if self.V_offset is None and self.sweeptype in [0, 1]:  # voltage offset to identify superconducting branch
            self.get_offset(x=V, y=I)
        if self.sweeptype == 0:  # halfswing
            V_c, I_c, peaks_c = np.copy(V), np.copy(I), np.copy(peaks)
            V_r, I_r, peaks_r = np.copy(V), np.copy(I), np.copy(peaks)
        elif self.sweeptype == 1:  # 4quadrants
            V_c, I_c, peaks_c = np.copy(V[::2]), np.copy(I[::2]), np.copy(peaks[::2])
            V_r, I_r, peaks_r = np.copy(V[1::2]), np.copy(I[1::2]), np.copy(peaks[1::2])
        else:  # custom sweep type
            def f(ind1D, prop1D, I1D, V1D, Y1D):
                try:
                    return {**prop1D,
                            **{k: v for k, v in zip(('I', 'V', Y_name, 'index'),
                                                    (I1D[ind1D], V1D[ind1D], Y1D[ind1D], ind1D))}}
                except IndexError:  # if no peak found return np.nan
                    return {k: v for k, v in zip(('I', 'V', Y_name, 'index'),
                                                 (np.array([np.nan]), np.array([np.nan]), np.array([np.nan]),
                                                  np.array([np.nan])))}

            if len(V.shape) - 1 == 1:
                return np.array(list(map(lambda ind1D, prop1D, I1D, V1D, Y1D:
                                         f(ind1D, prop1D, I1D, V1D, Y1D),
                                         *list(zip(*peaks)), I, V, Y)))
            elif len(V.shape) - 1 == 2:
                return np.array(list(map(lambda peaks2D, I2D, V2D, Y2D:
                                         list(map(lambda ind1D, prop1D, I1D, V1D, Y1D:
                                                  f(ind1D, prop1D, I1D, V1D, Y1D),
                                                  *list(zip(*peaks2D)), I2D, V2D, Y2D)),
                                         peaks, I, V, Y)))
            elif len(V.shape) - 1 == 3:
                return np.array(list(map(lambda peaks3D, I3D, V3D, Y3D:
                                         list(map(lambda peaks2D, I2D, V2D, Y2D:
                                                  list(map(lambda ind1D, prop1D, I1D, V1D, Y1D:
                                                           f(ind1D, prop1D, I1D, V1D, Y1D),
                                                           *list(zip(*peaks2D)), I2D, V2D, Y2D)),
                                                  peaks3D, I3D, V3D, Y3D)),
                                         peaks, I, V, Y)))
            else:
                raise NotImplementedError('No algorithm implemented for custom sweep type and scan_dim > 3.')
        if len(V.shape) - 1 == 1:
            ''' critical current '''
            masks_c = list(map(lambda V_c1D, peak1D:
                               np.logical_and(np.logical_and((-tol_offset + self.V_offset) <= np.mean(
                                   V_c1D[peak1D[0] - np.tile([np.arange(int(window) // 2) + 1], [len(peak1D[0]), 1]).T],
                                   axis=0),
                                                             np.mean(V_c1D[peak1D[0] - np.tile(
                                                                 [np.arange(int(window) // 2) + 1],
                                                                 [len(peak1D[0]), 1]).T], axis=0) <= (
                                                                     +tol_offset + self.V_offset)),
                                              np.logical_not(np.logical_and((-tol_offset + self.V_offset) <= np.mean(
                                                  V_c1D[peak1D[0] + np.tile([np.arange(int(window) // 2) + 1],
                                                                            [len(peak1D[0]), 1]).T], axis=0),
                                                                            np.mean(V_c1D[peak1D[0] + np.tile(
                                                                                [np.arange(int(window) // 2) + 1],
                                                                                [len(peak1D[0]), 1]).T], axis=0) <= (
                                                                                    +tol_offset + self.V_offset)))),
                               V_c, peaks_c))
            if not np.all(np.any(masks_c, axis=1)):
                for i in np.argwhere(~np.any(masks_c, axis=1)):
                    masks_c[i.item()][1] = True
            # I_cs = np.array(list(map(lambda I_c1D, peak1D, masks_c1D:
            #                         I_c1D[peak1D[0][masks_c1D][0]],
            #                         I_c, peaks_c, masks_c)),
            #                dtype=float)
            I_cs = np.array(list(map(lambda I_c1D, Y1D, peak1D, masks_c1D:
                                     ufloat(nominal_value=I_c1D[peak1D[0][masks_c1D][0]],
                                            std_dev=np.abs(
                                                np.diff(I_c1D[get_fwhm(Y1D, peak1D, masks_c1D)])).item() / 2),
                                     # half width half maximum
                                     I_c, Y, peaks_c, masks_c)),
                            dtype=object)
            ''' retrapping current '''
            masks_r = list(map(lambda V_r1D, peak1D:
                               np.logical_and(np.logical_not(np.logical_and((-tol_offset + self.V_offset) <= np.mean(
                                   V_r1D[peak1D[0] - np.tile([np.arange(int(window) // 2) + 1], [len(peak1D[0]), 1]).T],
                                   axis=0),
                                                                            np.mean(V_r1D[peak1D[0] - np.tile(
                                                                                [np.arange(int(window) // 2) + 1],
                                                                                [len(peak1D[0]), 1]).T], axis=0) <= (
                                                                                    +tol_offset + self.V_offset))),
                                              np.logical_and((-tol_offset + self.V_offset) <= np.mean(V_r1D[peak1D[
                                                                                                                0] + np.tile(
                                                  [np.arange(int(window) // 2) + 1], [len(peak1D[0]), 1]).T], axis=0),
                                                             np.mean(V_r1D[peak1D[0] + np.tile(
                                                                 [np.arange(int(window) // 2) + 1],
                                                                 [len(peak1D[0]), 1]).T], axis=0) <= (
                                                                     +tol_offset + self.V_offset))),
                               V_r, peaks_r))
            if not np.all(np.any(masks_r, axis=1)):
                for i in np.argwhere(~np.any(masks_r, axis=1)):
                    masks_r[i.item()][0] = True
            # I_rs = np.array(list(map(lambda I_r1D, peak1D, masks_r1D:
            #                         I_r1D[peak1D[0][masks_r1D][0]+1],
            #                         I_r, peaks_r, masks_r)),
            #                dtype=float)
            I_rs = np.array(list(map(lambda I_r1D, Y1D, peak1D, masks_r1D:
                                     ufloat(nominal_value=I_r1D[peak1D[0][masks_r1D][0]],
                                            std_dev=np.abs(
                                                np.diff(I_r1D[get_fwhm(Y1D, peak1D, masks_r1D)])).item() / 2),
                                     # half width half maximum
                                     I_r, Y, peaks_r, masks_r)),
                            dtype=object)
            ''' properties '''
            properties = np.array(list(map(lambda ind1D, prop1D, I1D, V1D, Y1D:
                                           {**prop1D,
                                            **{k: v for k, v in zip(('I', 'V', Y_name, 'index'),
                                                                    (I1D[ind1D], V1D[ind1D], Y1D[ind1D], ind1D))}},
                                           *list(zip(*peaks)), I, V, Y)))
            ''' gap voltage '''
            if Vg:
                slcs_g = list(map(lambda j, m:
                                  slice(-peaks[int(not j)][0][m[0]].item() - 1, peaks[j][0][m[1]].item()),
                                  *zip(*enumerate(zip(*(masks_c, masks_r))))))
                V_gs = unp.uarray(nominal_values=[np.nanmean(V[j][slc]) for j, slc in enumerate(slcs_g)],
                                  std_devs=[np.nansem(V[j][slc]) for j, slc in enumerate(slcs_g)])
        elif len(V.shape) - 1 == 2:
            ''' critical current '''
            masks_c = map(lambda V_c2D, peaks_c2D:
                          map(lambda V_c1D, peak1D: np.logical_and(np.logical_and(
                              (-tol_offset + self.V_offset) <= np.mean(
                                  V_c1D[peak1D[0] - np.tile([np.arange(int(window) // 2) + 1], [len(peak1D[0]), 1]).T],
                                  axis=0),
                              np.mean(
                                  V_c1D[peak1D[0] - np.tile([np.arange(int(window) // 2) + 1], [len(peak1D[0]), 1]).T],
                                  axis=0) <= (+tol_offset + self.V_offset)),
                              np.logical_not(np.logical_and(
                                  (-tol_offset + self.V_offset) <= np.mean(V_c1D[
                                                                               peak1D[
                                                                                   0] + np.tile(
                                                                                   [
                                                                                       np.arange(
                                                                                           int(
                                                                                               window) // 2) + 1],
                                                                                   [
                                                                                       len(
                                                                                           peak1D[
                                                                                               0]),
                                                                                       1]).T],
                                                                           axis=0),
                                  np.mean(V_c1D[peak1D[0] + np.tile(
                                      [np.arange(int(window) // 2) + 1],
                                      [len(peak1D[0]), 1]).T], axis=0) <= (
                                          +tol_offset + self.V_offset)))),
                              V_c2D, peaks_c2D),
                          V_c, peaks_c)
            # I_cs = np.array(list(map(lambda I_c2D, peaks_c2D, masks_c2D:
            #                         list(map(lambda I_c1D, peak1D, masks_c1D:
            #                                  I_c1D[peak1D[0][masks_c1D][0]],
            #                                  I_c2D, peaks_c2D, masks_c2D)),
            #                         I_c, peaks_c, masks_c)),
            #                dtype=float)
            I_cs = np.array(list(map(lambda I_c2D, Y2D, peaks_c2D, masks_c2D:
                                     list(map(lambda I_c1D, Y1D, peak1D, masks_c1D:
                                              ufloat(nominal_value=I_c1D[peak1D[0][masks_c1D][0]],
                                                     std_dev=np.abs(
                                                         np.diff(I_c1D[get_fwhm(Y1D, peak1D, masks_c1D)])).item() / 2),
                                              # half width half maximum
                                              I_c2D, Y2D, peaks_c2D, masks_c2D)),
                                     I_c, Y, peaks_c, masks_c)),
                            dtype=object)
            ''' retrapping current '''
            masks_r = map(lambda V_r2D, peaks_r2D:
                          map(lambda V_r1D, peak1D: np.logical_and(np.logical_not(np.logical_and(
                              (-tol_offset + self.V_offset) <= np.mean(
                                  V_r1D[peak1D[0] - np.tile([np.arange(int(window) // 2) + 1], [len(peak1D[0]), 1]).T],
                                  axis=0),
                              np.mean(
                                  V_r1D[peak1D[0] - np.tile([np.arange(int(window) // 2) + 1], [len(peak1D[0]), 1]).T],
                                  axis=0) <= (+tol_offset + self.V_offset))),
                              np.logical_and(
                                  (-tol_offset + self.V_offset) <= np.mean(V_r1D[
                                                                               peak1D[
                                                                                   0] + np.tile(
                                                                                   [
                                                                                       np.arange(
                                                                                           int(
                                                                                               window) // 2) + 1],
                                                                                   [
                                                                                       len(
                                                                                           peak1D[
                                                                                               0]),
                                                                                       1]).T],
                                                                           axis=0),
                                  np.mean(V_r1D[peak1D[0] + np.tile(
                                      [np.arange(int(window) // 2) + 1],
                                      [len(peak1D[0]), 1]).T], axis=0) <= (
                                          +tol_offset + self.V_offset))),
                              V_r2D, peaks_r2D),
                          V_r, peaks_r)
            # I_rs = np.array(list(map(lambda I_r2D, peaks_r2D, masks_r2D:
            #                         list(map(lambda I_r1D, peaks_r1D, masks_r1D:
            #                                  I_r1D[peaks_r1D[0][masks_r1D][0]+1],
            #                                  I_r2D, peaks_r2D, masks_r2D)),
            #                         I_r, peaks_r, masks_r)),
            #                dtype=float)
            I_rs = np.array(list(map(lambda I_r2D, Y2D, peaks_r2D, masks_r2D:
                                     list(map(lambda I_r1D, Y1D, peak1D, masks_r1D:
                                              ufloat(nominal_value=I_r1D[peak1D[0][masks_r1D][0]],
                                                     std_dev=np.abs(
                                                         np.diff(I_r1D[get_fwhm(Y1D, peak1D, masks_r1D)])).item() / 2),
                                              # half width half maximum
                                              I_r2D, Y2D, peaks_r2D, masks_r2D)),
                                     I_r, Y, peaks_r, masks_r)),
                            dtype=object)
            ''' properties '''
            properties = np.array(list(map(lambda peaks2D, I2D, V2D, Y2D:
                                           list(map(lambda ind1D, prop1D, I1D, V1D, Y1D:
                                                    {**prop1D,
                                                     **{k: v for k, v in zip(('I', 'V', Y_name, 'index'),
                                                                             (I1D[ind1D], V1D[ind1D], Y1D[ind1D],
                                                                              ind1D))}},
                                                    *list(zip(*peaks2D)), I2D, V2D, Y2D)),
                                           peaks, I, V, Y)))
        elif len(V.shape) - 1 == 3:
            ''' critical current '''
            masks_c = map(lambda V_c3D, peaks_c3D:
                          map(lambda V_c2D, peaks_c2D:
                              map(lambda V_c1D, peak1D: np.logical_and(np.logical_and(
                                  (-tol_offset + self.V_offset) <= np.mean(V_c1D[peak1D[0] - np.tile(
                                      [np.arange(int(window) // 2) + 1], [len(peak1D[0]), 1]).T], axis=0),
                                  np.mean(V_c1D[peak1D[0] - np.tile([np.arange(int(window) // 2) + 1],
                                                                    [len(peak1D[0]), 1]).T], axis=0) <= (
                                          +tol_offset + self.V_offset)),
                                  np.logical_not(np.logical_and(
                                      (-tol_offset + self.V_offset) <= np.mean(
                                          V_c1D[peak1D[0] + np.tile(
                                              [np.arange(int(window) // 2) + 1],
                                              [len(peak1D[0]), 1]).T], axis=0),
                                      np.mean(V_c1D[peak1D[0] + np.tile(
                                          [np.arange(int(window) // 2) + 1],
                                          [len(peak1D[0]), 1]).T], axis=0) <= (
                                              +tol_offset + self.V_offset)))),
                                  V_c2D, peaks_c2D),
                              V_c3D, peaks_c3D),
                          V_c, peaks_c)
            # I_cs = np.array(list(map(lambda I_c3D, peaks_c3D, masks_c3D:
            #                         list(map(lambda I_c2D, peaks_c2D, masks_c2D:
            #                                  list(map(lambda I_c1D, peak1D, masks_c1D:
            #                                           I_c1D[peak1D[0][masks_c1D][0]],
            #                                           I_c2D, peaks_c2D, masks_c2D)),
            #                                  I_c3D, peaks_c3D, masks_c3D)),
            #                         I_c, peaks_c, masks_c)),
            #                dtype=float)
            I_cs = np.array(list(map(lambda I_c3D, Y3D, peaks_c3D, masks_c3D:
                                     list(map(lambda I_c2D, Y2D, peaks_c2D, masks_c2D:
                                              list(map(lambda I_c1D, Y1D, peak1D, masks_c1D:
                                                       ufloat(nominal_value=I_c1D[peak1D[0][masks_c1D][0]],
                                                              std_dev=np.abs(np.diff(
                                                                  I_c1D[get_fwhm(Y1D, peak1D, masks_c1D)])).item() / 2),
                                                       # half width half maximum
                                                       I_c2D, Y2D, peaks_c2D, masks_c2D)),
                                              I_c3D, Y3D, peaks_c3D, masks_c3D)),
                                     I_c, Y, peaks_c, masks_c)),
                            dtype=object)
            ''' retrapping current '''
            masks_r = map(lambda V_r3D, peaks_r3D:
                          map(lambda V_r2D, peaks_r2D:
                              map(lambda V_r1D, peak1D: np.logical_and(np.logical_not(np.logical_and(
                                  (-tol_offset + self.V_offset) <= np.mean(V_r1D[peak1D[0] - np.tile(
                                      [np.arange(int(window) // 2) + 1], [len(peak1D[0]), 1]).T], axis=0),
                                  np.mean(V_r1D[peak1D[0] - np.tile([np.arange(int(window) // 2) + 1],
                                                                    [len(peak1D[0]), 1]).T], axis=0) <= (
                                          +tol_offset + self.V_offset))),
                                  np.logical_and(
                                      (-tol_offset + self.V_offset) <= np.mean(
                                          V_r1D[peak1D[0] + np.tile(
                                              [np.arange(int(window) // 2) + 1],
                                              [len(peak1D[0]), 1]).T], axis=0),
                                      np.mean(V_r1D[peak1D[0] + np.tile(
                                          [np.arange(int(window) // 2) + 1],
                                          [len(peak1D[0]), 1]).T], axis=0) <= (
                                              +tol_offset + self.V_offset))),
                                  V_r2D, peaks_r2D),
                              V_r3D, peaks_r3D),
                          V_r, peaks_r)
            # I_rs = np.array(list(map(lambda I_r3D, peaks_r3D, masks_r3D:
            #                         list(map(lambda I_r2D, peaks_r2D, masks_r2D:
            #                                  list(map(lambda I_r1D, peak1D, masks_r1D:
            #                                           I_r1D[peak1D[0][masks_r1D][0]],
            #                                           I_r2D, peaks_r2D, masks_r2D)),
            #                                  I_r3D, peaks_r3D, masks_r3D)),
            #                         I_r, peaks_r, masks_r)),
            #                dtype=float)
            I_rs = np.array(list(map(lambda I_r3D, Y3D, peaks_r3D, masks_r3D:
                                     list(map(lambda I_r2D, Y2D, peaks_r2D, masks_r2D:
                                              list(map(lambda I_r1D, Y1D, peak1D, masks_r1D:
                                                       ufloat(nominal_value=I_r1D[peak1D[0][masks_r1D][0]],
                                                              std_dev=np.abs(np.diff(
                                                                  I_r1D[get_fwhm(Y1D, peak1D, masks_r1D)])).item() / 2),
                                                       # half width half maximum
                                                       I_r2D, Y2D, peaks_r2D, masks_r2D)),
                                              I_r3D, Y3D, peaks_r3D, masks_r3D)),
                                     I_r, Y, peaks_r, masks_r)),
                            dtype=object)
            properties = np.array(list(map(lambda peaks3D, I3D, V3D, Y3D:
                                           list(map(lambda peaks2D, I2D, V2D, Y2D:
                                                    list(map(lambda ind1D, prop1D, I1D, V1D, Y1D:
                                                             {**prop1D,
                                                              **{k: v for k, v in zip(('I', 'V', Y_name, 'index'),
                                                                                      (I1D[ind1D], V1D[ind1D],
                                                                                       Y1D[ind1D], ind1D))}},
                                                             *list(zip(*peaks2D)), I2D, V2D, Y2D)),
                                                    peaks3D, I3D, V3D, Y3D)),
                                           peaks, I, V, Y)))
        else:
            raise ValueError('Scan dimension must be in {1, 2, 3}')
        """
        ans = {'I_c': I_cs, 'prop': properties}
        if Ir:
            ans['I_r'] = I_rs
        if Vg:
            ans['V_g': V_gs]
        return dict2obj(ans)
        """
        if Ir:
            if Vg:
                return I_cs, I_rs, V_gs, properties
            else:
                return I_cs, I_rs, properties
        else:
            if Vg:
                return I_cs, V_gs, properties
            else:
                return I_cs, properties

    def get_Vg(self, V=None, binwidth=2e-6, subgap=False):
        """
        Gets gap voltages. Therefore, all measured voltages are collected in bins with bin width <binwidth> and the 3
        most prominent peaks are interpreted as superconducting branch (2nd) and gap (1st and 3rd). Each peak is fitted
        to a Gaussian distribution using a fine histogram ranging from `left_bases` to `right_bases` obtained from the
        peak finder `scipy.signal.find_peaks`. The returned gap voltage equals the mean ± std of the differences of the
        3 peaks.
        If wanted, the sub-gap voltage is calculated as maximal absolute voltage between two neighboring peaks, where
        outliers are removed by considering only the median ± median absolute deviation. The returned sub-gap voltage
        equals the maximal absolute voltage and the error is estimated as difference of the two maximal absolute voltages.

        Parameters
        ----------
        V: numpy.array (optional)
            An N-dimensional array containing voltage values. Default is None that means <self.V>.
        binwidth: float (optional)
            Histograms bin width in Volts. Default is 2e-6.
        subgap: bool (optional)
            Condition, if sub-gap voltages are returned, too. Default is False.

        Returns
        -------
        V_g: numpy.array
            Gap voltage.
        V_sg: numpy.array (optional)
            Sub-gap voltage.
        """

        def gaussian(x, A, mu, sigma, k):
            return A * np.exp(-0.5 * ((x - mu) / sigma) ** 2) + k

        if V is None:
            V = self.V
        ''' prepare numpy array of voltage values to handle different scan-dimensions '''
        if len(V.shape) - 1 == 1:
            _V = V[:, np.newaxis, np.newaxis, :]  # insert dummy x- and y-axis
        elif len(V.shape) - 1 == 2:
            _V = V[:, :, np.newaxis, :]  # insert dummy y-axis
        elif len(V.shape) - 1 == 3:
            _V = V
        else:
            raise ValueError('Scan dimension must be in {1, 2, 3}')
        ''' find gap (and sub-gap) voltages '''
        nop = 3  # number of peaks to find
        V_g = np.ones(shape=(*_V.shape[1:3], nop), dtype=object) * np.nan
        V_sg = np.ones(shape=(*_V.shape[1:3], nop - 1), dtype=object) * np.nan
        for x in range(_V.shape[1]):  # iterate x-values
            for y in range(_V.shape[2]):  # iterate y-values
                ''' raw histogram '''
                p, edges = np.histogram(np.concatenate(_V[:, x, y]),
                                        bins=int((np.nanmax(_V[:, x, y]) - np.nanmin(_V[:, x, y])) / binwidth))
                # find <nop> peaks
                prominence = np.max(p)
                while True:
                    peaks = sig.find_peaks(p, prominence=prominence)
                    if peaks[0].size < nop:
                        prominence /= 2
                    elif peaks[0].size == nop:
                        break
                    else:
                        raise ValueError('V_g: Too many peaks found. Probably adjust bin width!')
                ''' fine histogram '''
                for i in range(nop):
                    p1, edges1 = np.histogram(np.concatenate(_V[:, x, y]),
                                              bins=100,
                                              range=(edges[peaks[1]['left_bases'][i]],
                                                     edges[peaks[1]['right_bases'][i] + 1]))
                    bins1 = np.convolve(edges1, np.ones((2,)) / 2, mode='valid')
                    p0 = [np.max(p1),
                          np.median(list(filter(lambda val: edges[peaks[1]['left_bases'][i]] <= val <= edges[
                              peaks[1]['right_bases'][i] + 1],
                                                np.concatenate(_V[:, x, y])))),
                          np.std(list(filter(lambda val: edges[peaks[1]['left_bases'][i]] <= val <= edges[
                              peaks[1]['right_bases'][i] + 1],
                                             np.concatenate(_V[:, x, y])))),
                          0.]
                    popt, pcov = opt.curve_fit(gaussian, bins1, p1, p0=p0, maxfev=1000)
                    V_g[x, y, i] = ufloat(nominal_value=popt[1],
                                          std_dev=np.sqrt(pcov[1, 1]) + np.abs(popt[2]))
                if subgap:
                    for i in range(nop - 1):
                        sg = np.array(list(filter(lambda val: edges[peaks[1]['right_bases'][i]] <= val <= edges[
                            peaks[1]['left_bases'][i + 1] + 1],
                                                  np.concatenate(_V[:, x, y]))))
                        # find outliers
                        sg_median = ufloat(nominal_value=np.median(sg),
                                           std_dev=stats.median_abs_deviation(sg))
                        V_sg[x, y, i] = ufloat(
                            nominal_value=[np.nanmin, np.nanmax][i](sg[np.logical_and(sg_median.n - sg_median.s < sg,
                                                                                      sg < sg_median.n + sg_median.s)]),
                            std_dev=np.abs(np.diff(sorted(sg[np.logical_and(sg_median.n - sg_median.s < sg,
                                                                            sg < sg_median.n + sg_median.s)],
                                                          reverse=~bool(i))[-2:]).item()))
        if subgap:
            return np.squeeze(V_g), np.squeeze(V_sg)
        else:
            return np.squeeze(V_g)

    class switching_current(object):
        """
        This is an analysis class for switching current measurements.
        """
        def __init__(self, sweeps, settings):
            self.sweeps = sweeps
            self.settings = settings

            self.P = self.P_fit = self.edges = self.edges_fit = self.bins = self.bins_fit = None
            self.Delta_I = self.Delta_I_fit = self.dIdt = None
            self.Gamma = self.Gamma_fit = self.x = self.x_fit = self.y = self.y_fit = None
            self.popt = self.pcov = self.fit_res = self.I_c = self.omega_0 = self.T_esc = None
            self.fig = self.ax1 = self.ax2 = self.ax3 = None

        def fit(self, I_0, omega_0, dIdt=None, **kwargs):
            """
            Creates switching current histogram, calculates and escape rate and recalculates the fit to the switching
            current distribution.

            Parameters
            ----------
            I_0: array-like
                Switching currents.
            omega_0: float
                Plasma frequency used for fit.
            dIdt: float (optional)
                Sweep rate (in A/s). Default is sweeps step width * nplc / plc.
            kwargs:
                Keyword arguments forwarded to numpy.histogram. Defaults are
                * bins=10,
                * range=(min(<I_0>), max(<I_0>)),
                * normed=None,
                * weights=None,
                * density=None.

            Returns
            -------
            P: np.array
                Probability distribution
            Gamma: np.array
                Escape rate
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
            self.omega_0 = omega_0
            ''' histogram '''
            if 'range' not in kwargs:
                kwargs['range'] = (np.nanmin(I_0), np.nanmax(I_0))
            if 'weights' not in kwargs:
                kwargs['weights'] = np.ones_like(I_0) / I_0.size  # normed to 1
            with np.errstate(invalid='ignore'):
                self.P, self.edges = np.histogram(a=I_0, **kwargs)
            self.bins = np.convolve(self.edges, np.ones((2,)) / 2,
                                    mode='valid')  # center of bins by moving average with window length 2
            ''' escape rate '''
            self.Delta_I = np.nanmean(np.diff(self.edges))
            if dIdt is None:
                self.dIdt = self.sweeps[0][2] * np.squeeze(np.unique(self.settings.IVD.sense_nplc)) / self.settings.IVD.plc
            else:
                self.dIdt = dIdt
            with np.errstate(divide='ignore'):  # raises warning due to divide by zero
                self.Gamma = self.dIdt / self.Delta_I * np.array([np.log(np.sum(self.P[k:]) / np.sum(self.P[k + 1:])) for k, _ in enumerate(self.P)])
            ''' fit norm. escape rate '''
            self.x = self.bins
            with np.errstate(divide='ignore'):  # raises warning due divide by zero
                self.y = np.log(unp.nominal_values(self.omega_0) / (2 * np.pi * self.Gamma)) ** (2 / 3)
            self.popt, self.pcov = np.polyfit(x=self.x[np.isfinite(self.y)],
                                              y=self.y[np.isfinite(self.y)],
                                              cov=True,
                                              deg=1)
            self.fit_res = unp.uarray(nominal_values=self.popt,
                                      std_devs=np.sqrt(np.diagonal(self.pcov)))
            self.I_c = -self.fit_res[1] / self.fit_res[0]
            self.T_esc = -4 * np.sqrt(2) * const.Phi_0 / (3 * 2 * np.pi * const.k) / (self.fit_res[0] * unp.sqrt(self.fit_res[1]))
            return dict2obj({'P': self.P,
                             'Gamma': self.Gamma,
                             'popt': self.popt,
                             'pcov': self.pcov,
                             'I_c': self.I_c,
                             'T_esc': self.T_esc,
                             })

        def plot(self,
                 xlabel='escape current $ I_{esc}~(A) $',
                 y1label='escape probability $ P $',
                 y2label='escape rate $ \Gamma_{esc}~(s^{-1}) $',
                 y3label='norm. escape rate $ \ln(\omega_0/2\pi\Gamma) $',
                 errors=False,
                 alpha=1,
                 figsize=(6, 6)):
            """
            Plots switching current histogram, escape rate and normalized escape rate as well as their fits.

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
            errors: bool
                If this is set to True, error bands are plotted.
            alpha: int
                Multiplier for nop of fit. Default is 1, which uses histogram bins for the fit.
                Note that alpha > 1 shifts the fit in x-direction for unknown reasons, which is corrected in the plot
            figsize : (float, float)
                Width, height in inches. Default is :rc:`figure.figsize`


            Returns
            -------
            fig: matplotlib.figure.Figure
                Plot figure, which shows the data and the fit of the  switching current distribution.
            ax: matplotlib.axes._subplots.AxesSubplot array of Axes objects
                ax[0], ax[1] and ax[2] contains switching current distribution, escape rate and normalized escape rate,
                respectively.

            Examples
            --------
            >>> ivc.scm.plot()
            """
            ''' calculate fitted escape rate and fitted switching current distribution '''
            self.edges_fit, self.Delta_I_fit = np.linspace(np.min(self.edges), np.max(self.edges), self.bins.size * alpha + 1, retstep=True)
            self.bins_fit = np.convolve(self.edges_fit, np.ones((2,)) / 2, mode='valid')
            self.x_fit = self.bins_fit
            if errors:  # this works also for errors=True, but is much slower
                self.y_fit = self.fit_res[0] * self.x_fit + self.fit_res[1]
                self.Gamma_fit = self.omega_0 / (2 * np.pi) * unp.exp(-self.y_fit ** (3 / 2))
                self.P_fit = np.array([self.Gamma_fit[k] / self.dIdt * unp.exp(
                    -np.sum(self.Gamma_fit[:k + 1]) * self.Delta_I_fit / self.dIdt) for k, _ in enumerate(self.x_fit)])
            else:
                self.y_fit = self.popt[0] * self.x_fit + self.popt[1]
                self.Gamma_fit = unp.nominal_values(self.omega_0) / (2 * np.pi) * np.exp(-self.y_fit ** (3 / 2))
                self.P_fit = np.array([self.Gamma_fit[k] / self.dIdt * np.exp(
                    -np.sum(self.Gamma_fit[:k + 1]) * self.Delta_I_fit / self.dIdt) for k, _ in enumerate(self.x_fit)])
            self.P_fit /= np.sum(self.P_fit) / alpha
            ''' plot '''
            self.fig, (self.ax1, self.ax2) = plt.subplots(nrows=2,
                                                          ncols=1,
                                                          sharex=True,
                                                          figsize=figsize)
            self.ax3 = plt.twinx(self.ax2)
            self.ax2.set_xlabel(xlabel)
            self.ax1.set_ylabel(y1label)
            self.ax2.set_ylabel(y2label)
            self.ax3.set_ylabel(y3label)
            ''' histogram '''
            lgd11 = self.ax1.bar(x=self.bins,
                                 height=self.P,
                                 width=np.mean(np.gradient(self.edges)))
            # self.ax1.plot(self.x_fit,
            #              self.P_fit,
            #              label='fit',
            #              ls='-',
            #              color='black')
            lgd12, = self.ax1.plot(self.x_fit - self.Delta_I / 2,
                                   unp.nominal_values(self.P_fit),
                                   ls='-',
                                   color='black')
            if errors:
                self.ax1.fill_between(x=self.x_fit,
                                      y1=(unp.nominal_values(self.P_fit) - unp.std_devs(self.P_fit)).clip(0),
                                      # replace negative values by 0
                                      y2=unp.nominal_values(self.P_fit) + unp.std_devs(self.P_fit),
                                      color='black', alpha=0.2)
                lgd13, = self.ax1.fill(np.NaN, np.NaN, 'black', alpha=0.2)  # dummy for legend
                self.ax1.legend(((lgd11,), (lgd12, lgd13)), ('data', 'fit'), loc='upper left')
            else:
                self.ax1.legend(((lgd11,), (lgd12,)), ('data', 'fit'), loc='upper left')
            # self.ax1.legend(loc='upper left')
            ''' escape rate '''
            lgd21, = self.ax2.semilogy(self.x,
                                       self.Gamma,
                                       'b.',
                                       label='$ \Gamma $')
            # lgd22, = self.ax2.semilogy(self.x_fit,
            #                           self.Gamma_fit,
            #                           'b-',
            #                           label='fit')
            lgd22, = self.ax2.semilogy(self.x_fit,
                                       unp.nominal_values(self.Gamma_fit),
                                       'b-',
                                       label='fit')
            if errors:
                self.ax2.fill_between(x=self.x_fit,
                                      y1=unp.nominal_values(self.Gamma_fit) - unp.std_devs(self.Gamma_fit),
                                      y2=unp.nominal_values(self.Gamma_fit) + unp.std_devs(self.Gamma_fit),
                                      color='b', alpha=0.2)
                # lgd23, = self.ax2.fill(np.NaN, np.NaN, 'b', alpha=0.2)  # dummy for legend
            ''' normalized escape rate '''
            lgd31, = self.ax3.plot(self.x,
                                   self.y,
                                   'r.',
                                   label='$ \ln(\omega_0/2\pi\Gamma) $')
            # lgd32, = self.ax3.plot(self.x_fit,
            #                       self.y_fit,
            #                       'r-',
            #                       label='fit')
            lgd32, = self.ax3.plot(self.x_fit,
                                   unp.nominal_values(self.y_fit),
                                   'r-',
                                   label='fit')
            if errors:
                pass
                self.ax3.fill_between(x=self.x_fit,
                                      y1=unp.nominal_values(self.y_fit) - unp.std_devs(self.y_fit),
                                      y2=unp.nominal_values(self.y_fit) + unp.std_devs(self.y_fit),
                                      color='r', alpha=0.2)
                # lgd33, = self.ax3.fill(np.NaN, np.NaN, 'r', alpha=0.2)  # dummy for legend
                # self.ax2.legend(((lgd21, lgd22, lgd23), (lgd31, lgd32, lgd33)), ('$ \Gamma $', '$ \ln(\omega_0/2\pi\Gamma) $'), loc='upper center')
            else:
                self.ax2.legend(((lgd21, lgd22), (lgd31, lgd32)), ('$ \Gamma $', '$ \ln(\omega_0/2\pi\Gamma) $'),
                                loc='upper center')
            plt.subplots_adjust(hspace=0)
            plt.show()

            return self.fig, (self.ax1, self.ax2, self.ax3)
