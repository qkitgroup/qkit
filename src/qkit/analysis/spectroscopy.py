# -*- coding: utf-8 -*-
# spectroscopy.py analysis class for qkit spectroscopy measurement data
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
from qkit.analysis.circle_fit.circle_fit_2019 import circuit


class spectrum(qData):
    """
    This is an analysis class for spectrum-like spectroscopy measurements taken by
    `qkit.measure.spectroscopy.spectroscopy.py`.
    """

    def __init__(self):
        """
        Initializes an analysis class for spectrum-like spectroscopy measurements taken by
        `qkit.measure.spectroscopy.spectroscopy.py`.

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

        >>> from qkit.analysis.qdata import spectrum
        >>> s = spectrum()
        """
        super().__init__()
        self.circuit = circuit

    def load(self, uuid):
        """
        Loads qkit spectroscopy data with given uuid <uuid>.

        Parameters
        ----------
        uuid: str
            Qkit identification name, that is looked for and loaded.

        Returns
        -------
        None

        Examples
        --------
        >>> s.load(uuid='XXXXXX')
        """
        super().load(uuid=uuid)
        if self.m_type != 'spectroscopy':
            raise AttributeError('No spectroscopy data loaded. Use data acquired with spectroscopy measurement class or general qData class.')
        self.scan_dim = self.df.data.amplitude.attrs['ds_type']  # scan dimension (1D, 2D, ...)
        self._get_xy_parameter(self.df.data.amplitude)
        self.circlefit = None

    def open_qviewkit(self, uuid=None, ds=None):
        """
        Opens qkit measurement data with given uuid <uuid> in qviewkit.

        Parameters
        ----------
        uuid: str
            Qkit identification name, that is looked for and opened in qviewkit.
        ds: str | list(str)
            Datasets that are opened instantaneously. Default for spectroscopy data is 'amplitude' and 'phase'.

        Returns
        -------
        None
        """
        if ds is None:
            ds = [_ds if _ds in self.df.data.__dict__.keys() else None for _ds in ['amplitude', 'phase']]
        super().open_qviewkit(uuid=uuid, ds=ds)

    def setup_circlefit(self, type, f_data=None, z_data_raw=None):
        if f_data is None:
            f_data = self.frequency
        if z_data_raw is None:
            if hasattr(self, 'real') and hasattr(self, 'imag'):
                z_data_raw = self.real + 1j * self.imag
            elif hasattr(self, 'amplitude') and hasattr(self, 'phase'):
                z_data_raw = self.amplitude + np.exp(1j * self.phase)
            else:
                raise NameError('no S21 data available. Please load either real and imaginary data or amplitude and phase data.')
        self.circlefit = {'reflection': self.circuit.reflection_port,
                          'notch': self.circuit.notch_port}[type](f_data=f_data,
                                                                  z_data_raw=z_data_raw)
