# -*- coding: utf-8 -*-
# timedomain.py analysis class for qkit time domain measurements data
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
from qkit.analysis.qdata import qData
from qkit.analysis.qfit import QFIT

""" Error calculations with uncertainties package """
import uncertainties as uncert
from uncertainties import ufloat, unumpy as unp


class timedomain(qData):
    def __init__(self):
        super().__init__()
        self.qfit = QFIT()

    def load(self, uuid):
        super().load(uuid=uuid)
        if self.m_type != 'timedomain':
            raise AttributeError('No timedomain data loaded. Use data acquired with timedomain measurement class or general qData class.')
        self.scan_dim = self.df.data.amplitude_0.attrs['ds_type']  # scan dimension (1D, 2D, ...)
        self._get_xy_parameter(self.df.data.amplitude_0)

    def open_qviewkit(self, uuid=None, ds=None):
        """
        Opens qkit measurement data with given uuid <uuid> in qviewkit.

        Parameters
        ----------
        uuid: str
            Qkit identification name, that is looked for and opened in qviewkit.
        ds: str | list(str)
            Datasets that are opened instantaneously. Default for time-domain data is 'amplitude_0' and 'phase_0'.

        Returns
        -------
        None
        """
        if ds is None:
            ds = [_ds if _ds in self.df.data.__dict__.keys() else None for _ds in ['amplitude_0', 'phase_0']]
        super().open_qviewkit(uuid=uuid, ds=ds)

    def setup_T1_fit(self):
        self.qfit.load(self.path,
                       entries=['delay',
                                'phase_avg_0',
                                'amplitude_avg_0',
                                'phase_0',
                                'amplitude_0'])
        self.qfit.rotate_IQ_plane()

    def fit_T1(self, **kwargs):
        self.qfit.fit_exp(**kwargs)
        return ufloat(nominal_value=self.qfit.popt[0],
                      std_dev=np.sqrt(self.qfit.pcov[0, 0]))

    def setup_Ramsey_fit(self):
        self.qfit.load(self.path,
                       entries=['delay',
                                'phase_avg_0',
                                'amplitude_avg_0',
                                'phase_0',
                                'amplitude_0'])
        self.qfit.rotate_IQ_plane()

    def fit_Ramsey(self, **kwargs):
        self.qfit.fit_damped_sine(**kwargs)
        return ufloat(nominal_value=self.qfit.popt[1],
                      std_dev=np.sqrt(self.qfit.pcov[1, 1]))

    def setup_Echo_fit(self):
        self.qfit.load(self.path,
                       entries=['delay',
                                'phase_avg_0',
                                'amplitude_avg_0',
                                'phase_0',
                                'amplitude_0'])
        self.qfit.rotate_IQ_plane()

    def fit_Echo(self, **kwargs):
        self.qfit.fit_exp(**kwargs)
        return ufloat(nominal_value=self.qfit.popt[0],
                      std_dev=np.sqrt(self.qfit.pcov[0, 0]))

