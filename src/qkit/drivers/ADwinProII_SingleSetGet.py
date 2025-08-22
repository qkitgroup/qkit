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
from  qkit.drivers.ADwinProII_Base import ADwinProII_Base

class ADwinProII_SingleSetGet(Instrument):
    """
    To be used with the FPGA process 'SMU_SingleSetGet.TC1', enabling single set/get commands
    for the ADC/DACs.
    """
    # static stuff
    ADC_CARD_OFFSET = 10
    ADC_FILTER_CARD_OFFSET = 20
    DAC_CARD_OFFSET = 30
    def __init__(self, name: str, adw_base: ADwinProII_Base, proc_path="C:\\ADwin\\SMU_SingleSetGet.TC1"):
        Instrument.__init__(self, name, tags=["virtual"])
        self.add_parameter("adc", type = float, flags = Instrument.FLAG_GET, channels = (1, 4), minval = -10.0, maxval = 10.0, units = "V")
        self.add_parameter("adc_filtered", type = float, flags = Instrument.FLAG_GET, channels = (1, 8), minval = -10.0, maxval = 10.0, units = "V")
        self.add_parameter("dac", type = float, flags = Instrument.FLAG_SET, channels = (1, 8), minval = -10.0, maxval = 10.0, units = "V")
        self.adw = adw_base.adw
        self.adw.Load_Process(proc_path)
        self.adw.Start_Process(int(proc_path[-1]))
        logging.info("Loaded process '{}' for ADwinProII's FPGA".format(proc_path))
    def do_get_adc(self, channel: int) -> float:
        """
        This is a very nice docstring
        """
        if channel in range(1, 5):
            self.adw.Set_Par(channel + self.ADC_CARD_OFFSET, 1)
            for i in range(500):
                if self.adw.Get_Par(channel + self.ADC_CARD_OFFSET) == 0:
                    return self.adw.Get_FPar(channel + self.ADC_CARD_OFFSET)
                time.sleep(0.01)
            raise TimeoutError("ADwin Pro II did not confirm ADC read within 5s")
        else:
            raise ValueError("Channel must be 1...4")
    def do_get_adc_filtered(self, channel: int) -> float:
        """
        This is a very nice docstring
        """
        if channel in range(1, 9):
            self.adw.Set_Par(channel + self.ADC_FILTER_CARD_OFFSET, 1)
            for i in range(5000):
                if self.adw.Get_Par(channel + self.ADC_FILTER_CARD_OFFSET) == 0:
                    return self.adw.Get_FPar(channel + self.ADC_FILTER_CARD_OFFSET)
                time.sleep(0.001)
            raise TimeoutError("ADwin Pro II did not confirm ADC read within 5s")
        else:
            raise ValueError("Channel must be 1...8")
    def do_set_dac(self, volt: float, channel: int) -> None:
        """
        This is a very nice docstring
        """
        if channel in range(1, 9):
            self.adw.Set_FPar(channel + self.DAC_CARD_OFFSET, volt)
            self.adw.Set_Par(channel + self.DAC_CARD_OFFSET, 1)
        else:
            raise ValueError("Channel must be 1...8")
    def reset(self):
        for i in range(1, 9):
            self.do_set_dac(0.0, i)