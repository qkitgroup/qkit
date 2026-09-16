# DSI_SG40000PRO.py
# Jonas Kaemmerer 08/26
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

from qkit.core.instrument_base import Instrument
from qkit import visa


import logging

import time

class DSI_SG40000PRO(Instrument):
    '''
    This is the driver for the DS Instruments SG40000PRO microwave signal generator

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'DSI_SG40000PRO', address='<address>', reset=`'<bool>')
    '''
    
    def __init__(self, name, address, reset=False):
        """Initialize the SG40000PRO.

        Args:
            name (str): qkit instrument name.
            address (str): VISA resource, for example
                ``TCPIP0::192.168.1.100::<port>::SOCKET``.
            reset (bool): Reset the device during initialization.
        """
        
        logging.info(
            "%s : Initializing DS Instruments SG40000PRO at %s",
            __name__, address,
        )
        super().__init__(name, tags=["physical"])

        self._address = address
        self._visainstrument = visa.instrument(self._address)
        self._visainstrument.write_termination = "\n"
        self._visainstrument.read_termination = "\n"
        self._visainstrument.timeout = 5000

        # Standard microwave-source interface. 
        
        self.add_parameter(
            "power",
            flags=Instrument.FLAG_GETSET,
            units="dBm",
            minval=-28.0,
            maxval=15.0,
            type=float,
        )
        
        self.add_parameter(
            "frequency",
            flags=Instrument.FLAG_GETSET,
            units="Hz",
            minval=50e6,
            maxval=41e9,
            type=float,
        )
        
        self.add_parameter(
            "status",
            flags=Instrument.FLAG_GETSET,
            type=bool,
        )
        
        self.add_parameter(
            "vernier",
            flags=Instrument.FLAG_GETSET,
            units="dB",
            minval=0.0,
            maxval=10.0,
            type=float,
        )

        self.add_function("reset")
        self.add_function("get_all")
        self.add_function("get_idn")
        self.add_function("get_error")
        self.add_function("get_debug")
        self.add_function("save_state")
        self.add_function("on")
        self.add_function("off")


        if reset:
            self.reset()
        else:
            self.get_all()



    def _query(self, command):
        """Send a SCPI query and return the response."""
        logging.debug("%s : query %s", __name__, command)
        return self._visainstrument.query(command).strip()

    def _write(self, command):
        """Send a SCPI command."""
        logging.debug("%s : write %s", __name__, command)
        self._visainstrument.write(command)

    def get_all(self):
        """Read all implemented parameters."""
        logging.info("%s : Reading all SG40000PRO parameters", __name__)
        self.get_power()
        self.get_frequency()
        self.get_status()
        self.get_vernier()

    def reset(self):
        """Reset the instrument and refresh all implemented parameters."""
        logging.info("%s : Resetting SG40000PRO", __name__)
        self._write("*RST")
        time.sleep(2.0)
        self.get_all()

    def do_get_frequency(self):
        """Return the CW output frequency in Hz."""
        response = self._query("FREQ:CW?")
        try:
            return float(response.replace("HZ", "").strip())
        except ValueError as error:
            raise ValueError(
                "Unexpected response to FREQ:CW?: {!r}".format(response)
            ) from error

    def do_set_frequency(self, frequency):
        """Set the CW output frequency in Hz."""
        logging.debug("%s : Setting frequency to %.12g Hz", __name__, frequency)
        self._write("FREQ:CW {:.12g}Hz".format(float(frequency)))

    def do_get_power(self):
        """Return the calibrated output-power setting in dBm."""
        response = self._query("POWER?")
        try:
            return float(response.replace("dBm", "").strip())
        except ValueError as error:
            raise ValueError(
                "Unexpected response to POWER?: {!r}".format(response)
            ) from error

    def do_set_power(self, power):
        """Set the calibrated output-power level in dBm.

        The available minimum power is frequency/band dependent. qkit checks
        the broad documented range; the instrument remains authoritative for
        the valid value at the currently selected frequency.
        """
        logging.debug("%s : Setting power to %.3f dBm", __name__, power)
        self._write("POWER {:.3f}".format(float(power)))

    def do_get_status(self):
        """Return True if the RF output is enabled."""
        response = self._query("OUTP:STAT?").upper()
        if response in ("1", "ON", "TRUE"):
            return True
        if response in ("0", "OFF", "FALSE"):
            return False
        raise ValueError(
            "Unexpected response to OUTP:STAT?: {!r}".format(response)
        )

    def do_set_status(self, status):
        """Enable or disable the RF output."""
        if not isinstance(status, bool):
            raise ValueError("status must be True or False")
        self._write("OUTP:STAT {}".format("ON" if status else "OFF"))

    def do_get_vernier(self):
        """Return the fine power-vernier setting in dB."""
        response = self._query("VERNIER?")
        try:
            return float(response.replace("dB", "").strip())
        except ValueError as error:
            raise ValueError(
                "Unexpected response to VERNIER?: {!r}".format(response)
            ) from error

    def do_set_vernier(self, vernier):
        """Set the fine power-vernier value in dB."""
        logging.debug("%s : Setting vernier to %.3f dB", __name__, vernier)
        self._write("VERNIER {:.3f}".format(float(vernier)))

    def get_idn(self):
        """Return the SCPI identification string."""
        return self._query("*IDN?")

    def get_error(self):
        """Return the next pending device error."""
        return self._query("SYST:ERR?")

    def get_debug(self):
        """Return the instrument's latest status/debug message."""
        return self._query("SYST:DBG?")

    def save_state(self):
        """Save frequency and attenuation as power-on defaults."""
        self._write("*SAVESTATE")

    def on(self):
        """Enable the RF output."""
        self.set_status(True)

    def off(self):
        """Disable the RF output."""
        self.set_status(False)
