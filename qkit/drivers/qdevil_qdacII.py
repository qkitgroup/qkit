# MG@KIT 04/2022
"""
qkit instrument driver for qdevil QDAC-II
 +- 24 channel low noise voltage source.
"""

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

import qkit
from qkit.core.instrument_base import Instrument
from qkit import visa


class QDAC_II(Instrument):
    """
    Instrument class for QDevil QDAC-II.
    """

    def __init__(self, name, address, port=5025):
        """
        Initialize qkit paramters and connect to the device.
        """

        logging.info(__name__ + " : Initializing Instrument")
        Instrument.__init__(self, name, tags=["physical"])

        self._address = address
        self._port = port
        try:
            self._visainstrument = visa.instrument(
                "TCPIP::{:s}::{:i}::SOCKET".format(self._address, self._port)
            )
        except Exception as detail:
            logging.error(
                "Connection to QDvil Instrument not possible. Original error: {:s}".format(
                    detail
                )
            )
        self._visainstrument.read_termination = "\n"
        self._visainstrument.write_termination = "\n"

    def write(self, msg):
        return self._visainstrument.write(msg)

    def query(self, msg):
        return self._visainstrument.query(msg)

    def close_connection(self):
        logging.info(
            __name__
            + " : Closing connection to QDAC-II server {:s}".format(self._address)
        )
        self._visainstrument.close()
