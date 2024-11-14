# Qkit driver for microwave source ERASynth
# filename: ERASynth.py
# Robert Gartmann <uwdqt@student.kit.edu>, 2019

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

from qkit.core.instrument_base import Instrument
import zerorpc
import types
import logging
import json
import warnings
from time import sleep
from enum import Enum


class ReferenceSource(Enum):
    EXTERNAL = 0
    OCXO = 1
    TCXO = 2


def _reference_class_conversion(reference):
    reference = {
        'EXTERNAL': ReferenceSource.EXTERNAL,
        'OCXO': ReferenceSource.OCXO,
        'TCXO': ReferenceSource.TCXO
    }.get(reference.upper(), None)
    if reference is None:
        raise ValueError("""Invalid reference. Valid options are (case insensitive): 
                            'EXTERNAL', 'OCXO', 'TCXO'""")
    return reference


class ERASynth(Instrument):
    '''This is the python driver for the ERASynth+ microwave source.
    It initializes the ZeroRPC Client to communicate with according Server (RPi).

    Usage:
    ----------
    Initialise with
    <name> = instruments.create('<name>', address='<TCP/IP>')

    Parameters:
    ----------
    name (string):
        Name of the instrument
    address (string):
        TCP/IP address including port, e.g. "141.52.65.185:4242"
    reference (string):
        Choose 10MHz reference (EXTERNAL, OCXO, TCXO).
        External will be checked for lock and defaults to Oven if not present.
    '''

    def __init__(self, name, address, reference='external', model='ERASynth'):
        logging.info(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name)
        self._address = "tcp://" + address
        self._model = model
        self._statusdict = {}
        self._reference = reference
        self._rpc = zerorpc.Client()
        self._rpc.connect(self._address)

        # Implement parameters
        self.add_parameter('frequency', type=float,
                           flags=Instrument.FLAG_GETSET,
                           minval=250e3, maxval=15e9,
                           units='Hz')
        self.add_parameter('power', type=float,
                           flags=Instrument.FLAG_GETSET,
                           minval=-60, maxval=20,  # 15 dBm Typ, up to 20 depending on F
                           units='dBm')
        self.add_parameter('status', type=bool,
                           flags=Instrument.FLAG_GETSET)

        # Initialize parameter values
        self.get_all(True)

        # Set 10MHz reference and check for lock if external
        # (if no reference is attached or quality is bad, it will switch to internal OCXO)
        lockcount = 0
        reference = _reference_class_conversion(reference)
        self.set_reference(ReferenceSource.OCXO)
        sleep(1)
        self.set_reference(reference)
        if reference == ReferenceSource.EXTERNAL:
            # Check if PLL has stable lock on external reference
            for _ in range(10):
                if self.get_diag()["lock_xtal"] == "1":
                    lockcount += 1
            if lockcount == 0:
                warnings.warn(
                    "No Lock possible. Check your reference. Defaulted to OCXO.")
                self.set_reference(ReferenceSource.OCXO)
            elif lockcount < 10:
                warnings.warn(
                    "External reference unstable. Check for sufficient amplitude & accuracy. Defaulted to OCXO.")
                self.set_reference(ReferenceSource.OCXO)

    def get_all(self, query=True):
        '''Get Parameters (frequency, amplitude, output on/off, clock reference) of Device as dictionary
        Input:
            query (bool): Query from device (true) or relay local info (false)
        Output:
            Dictionary of device
        '''
        if not query:
            return self._statusdict
        self._statusdict = json.loads(self._rpc.readall())
        self._frequency = float(self._statusdict["frequency"])
        self._power = float(self._statusdict["amplitude"])
        self._status = bool(int(self._statusdict["rfoutput"]))
        refext = bool(int(self._statusdict["reference_int_ext"]))
        refint = bool(int(self._statusdict["reference_tcxo_ocxo"]))
        if refext:
            self._reference = ReferenceSource.EXTERNAL
        elif refint:
            self._reference = ReferenceSource.OCXO
        else:
            self._reference = ReferenceSource.TCXO
        return self._statusdict

    def get_diag(self):
        '''Get diagnostics parameters (Firmware Versions, PLL locks status,
        Voltage, Temperature) of Device as dictionary

        Input:
            None
        Output:
            Dictionary diagnostics parameters
        '''
        return json.loads(self._rpc.readdiag())

    def set_reference(self, source):
        '''Set which 10MHz Reference to use

        Input:
            source (ReferenceSource | str):
                External (EXTERNAL), Oven stabilized (OCXO), Quarz stabilized (TCXO)
        Output:
            None
        '''
        try:
            # Source can also be specified as string, not only as ReferenceSource
            # so try to convert it here.
            source = _reference_class_conversion(source)
        except:
            pass
        if source is ReferenceSource.EXTERNAL:
            self._rpc.setrefext()
        elif source is ReferenceSource.OCXO:
            self._rpc.setrefint()
            self._rpc.setrefocxo()
        elif source is ReferenceSource.TCXO:
            self._rpc.setrefint()
            self._rpc.setreftcxo()
        else:
            raise ValueError(
                "Unknown ReferenceSource value ({}).".format(source))
        self._reference = source

    def get_reference(self, query=True):
        '''Get which 10MHz reference is in use

        Input:
            query (bool): Refresh parameters from device memory if True
        Output:
            ReferenceSource: External = 0, Oven stabilized = 1, Quarz stabilized = 0
        '''
        self.get_all(query)
        return self._reference

    def do_get_frequency(self, query=True):
        '''Get frequency of device

        Input:
            query (bool): Refresh parameters from device memory if True
        Output:
            microwave frequency (Hz)
        '''
        self.get_all(query)
        return self._frequency

    def do_set_frequency(self, frequency):
        '''Set frequency of device

        Input:
            freq (float): Frequency in Hz
        Output:
            None
        '''
        # logging.debug(__name__ + ' : setting frequency to %s Hz' % frequency)
        self._rpc.setfrequency(frequency)
        self._frequency = frequency

    def do_get_power(self, query=True):
        '''Get output power of device

        Input:
            query (bool): Refresh parameters from device memory if True
        Output:
            microwave power (dBm)
        '''
        self.get_all(query)
        return self._power

    def do_set_power(self, power=None):
        '''Typ. Max. Output 15 dB, Absolute Max. 20 dBm

        Input:
            power (float) : Power in dBm
        Output:
            None
        '''
        # logging.debug(__name__ + ' : setting power to %s dBm' % power)
        self._power = power
        self._rpc.setamplitude(power)

    def do_get_status(self, query=True):
        '''Get status of output channel

        Input:
            query (bool): Refresh parameters from device memory if True
        Output:
            True (on) or False (off)
        '''
        self.get_all(query)
        return self._status

    def do_set_status(self, status):
        '''Set status of output (Bool)

        Input:
            status (bool): Enable rf output (True), disable rf output (False)
        Output:
            None
        '''
        # logging.debug(__name__ + ' : setting status to "%s"' % status)
        if status:
            self._rpc.enableout()
        else:
            self._rpc.disableout()

    # shortcuts
    def off(self):
        '''Turn RF Output Off'''
        self.set_status(False)

    def on(self):
        '''Turn RF Output On'''
        self.set_status(True)
