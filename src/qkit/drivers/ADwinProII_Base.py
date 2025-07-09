# ADwinProII_SMU.py driver for using ADwin Pro II as an SMU
# Author: Marius Frohn (uzrfo@student.kit.edu)
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

import logging, time
from qkit.core.instrument_base import Instrument
import numpy as np
import ADwin
from typing import Callable

class ADwinProII_Base(Instrument):
    """
    The ADwin Pro II by Jäger Computergesteuerte Messtechnik GmbH provides slots for various 
    ADC/DAC or data in/out cards as well as an accessable FPGA-like processor for control. Our
    group's device currently has a 4-channel 16-bit ADC, a 50kHz filtered 8-channel 16-bit ADC 
    and an 8-channel 16-bit DAC card. Getting the device running requires some steps outlined
    below:

    - Selecting drivers from https://www.adwin.de/de/download/download.html. Installing the 
      full software package is recommended for potential debugging, analyzing timings, etc.
    - 'pip install ADwin' to the qkit virtual environment. (Note: despite being present, the 
      driver could not correctly read out the ADwin install directory from the windows registry
      on my machine. To fix this, I commented out the entire try/except block around line ~100 
      in *venv*/site-packages/ADwin.py and hardcoded 'self.ADwindir = *adwin_install_path*')
    - The tool *adwin_install_path*/Tools/ADconfig/ADconfig.exe finds ADwin devices in the 
      network and allows e.g. assigning their MAC-addresses to a fixed IP-address. This should
      already be done for this device. In either case one still needs to register it as an 
      adwin-device on the measurement pc and assign it an adwin-device-number (default: 1)
    - With *adwin_install_path*/Tools/Test/ADpro/ADpro.exe one can check if communication with
      device is now possible & what the id-numbers of the used cards are (should be 1, 2, 3)
    - For usage one needs to provide a bootloader and to be run processes. The bootloader can 
      be found under *adwin_install_path*/ADwin12.btl for the T12 processor type. A process 
      is defined in a compiled .TCx (x: process number) file. Tools and documentation for 
      creating, editing, testing and compiling are provided in the ADwin software package.
    """
    @staticmethod
    def _to_volt(x: np.ndarray) -> np.ndarray:
        return (np.array(x, dtype=np.int32).astype(np.float64) - 0x8000) * 20.0 / 0x10000
    @staticmethod
    def _to_reg(x: np.ndarray) -> np.ndarray:
        x_reg = np.round((x + 10.0)/20.0*0x10000)
        x_reg = np.where(x_reg == -1, 0, x_reg)
        return np.where(x_reg == 0x10000, 0xFFFF, x_reg)
    def __init__(self, name: str, btl_path: str = "C:\\ADwin\\ADwin12.btl", device_num: int = 1):
        """
        Use via e.g.
        adw_base = qkit.instruments.create("adw_base", "ADwinProII_Base", *kwargs*)        
        """
        Instrument.__init__(self, name, tags=["physical"])
        self.adw = ADwin.ADwin(device_num)
        self.adw.Boot(btl_path)
        logging.info("Booted ADwinProII with processor {}".format(self.adw.Processor_Type()))