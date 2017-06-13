# visafunc.py, NI VISA support functions.
# Reinier Heeres <reinier@heeres.eu>, 2009
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

import time
import logging
try:
    from visa import *
    from pyvisa import vpp43
except:
    logging.warning('VISA not available')

def get_navail(visains):
    '''
    Return number of bytes available to read from visains.
    '''
    return vpp43.get_attribute(visains, vpp43.VI_ATTR_ASRL_AVAIL_NUM)

def wait_data(visains, nbytes=1, maxdelay=1.0):
    '''
    Wait for maxdelay seconds for data available to read from visains.
    The loop consist of 1msec delays.
    '''
    start = exact_time()
    while exact_time() - start < maxdelay:
        if get_navail(visains) >= nbytes:
            return True
        time.sleep(0.001)
    return False

def readn(visains, n):
    return vpp43.read(visains, n)

_added_filter = False
def read_all(visains):
    """
    Read all available data from the input buffer of visins.
    """

    global _added_filter

    if not _added_filter:
        warnings.filterwarnings("ignore", "VI_SUCCESS_MAX_CNT")
        _added_filter = True

    try:
        buf = ""
        blen = get_navail(visains)
        while blen > 0:
            chunk = vpp43.read(visains, blen)
            buf += chunk
            blen = get_navail(visains)
    except:
        pass

    return buf

